"""API HTTP do Formata.AI Web e entrega da landing page.

Rotas:
    GET  /api/saude              estado do serviço
    GET  /api/configuracao       limites e formatos aceitos (usado pela interface)
    POST /api/formatar           JSON {"texto": "...", "modo": "auto"}
    POST /api/formatar/arquivo   multipart: arquivo (+ modo)
    GET  /api/docs               documentação interativa (OpenAPI)

Nenhum documento é gravado em disco ou em log: o texto existe só durante a
requisição. Os logs registram tamanho, código do resultado e duração.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from pathlib import PurePath
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from formata.motor import VERSAO_DIRETRIZES

from .config import EXTENSOES_ACEITAS, Configuracao
from .execucao import FalhaExecucao, TempoEsgotado, executar

VERSAO_APP = "0.3.0"
log = logging.getLogger("formata.api")

STATUS_POR_CODIGO = {
    "ok": 200,
    "documento_vazio": 400,
    "entrada_invalida": 400,
    "requisicao_invalida": 400,
    "modo_invalido": 400,
    "tamanho_desconhecido": 411,
    "documento_muito_extenso": 413,
    "tipo_nao_suportado": 415,
    "falha_validacao": 422,
    "erro_interno": 500,
    "tempo_esgotado": 504,
}

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; "
    "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)


class PedidoTexto(BaseModel):
    texto: str = Field(description="Conteúdo do documento: Markdown, texto ou HTML com <p>.")
    modo: Literal["auto", "markdown", "html"] = Field(
        "auto", description="'auto' detecta documento já formatado com <p> (seção 7)."
    )


class ErroRequisicao(Exception):
    def __init__(self, codigo: str, mensagem: str):
        self.codigo = codigo
        self.mensagem = mensagem


def resposta_erro(codigo: str, mensagem: str, erros: list[str] | None = None) -> JSONResponse:
    corpo = {"ok": False, "codigo": codigo, "mensagem": mensagem, "erros": erros or []}
    return JSONResponse(corpo, status_code=STATUS_POR_CODIGO.get(codigo, 400))


def criar_app(config: Configuracao | None = None) -> FastAPI:
    config = config or Configuracao.do_ambiente()
    logging.basicConfig(level=config.nivel_log, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    vagas = asyncio.Semaphore(max(1, config.max_processos))

    app = FastAPI(
        title="Formata.AI Web — API",
        version=VERSAO_APP,
        description="Paginação e marcação HTML determinísticas conforme as Diretrizes Formata.AI v2.6.",
        docs_url="/api/docs" if config.docs_api else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if config.docs_api else None,
    )
    app.state.config = config
    if config.origens_cors:
        app.add_middleware(
            CORSMiddleware, allow_origins=list(config.origens_cors), allow_methods=["GET", "POST"], allow_headers=["*"]
        )

    @app.middleware("http")
    async def protecoes(request: Request, chamar_proximo):
        rota = request.url.path
        if request.method == "POST" and rota.startswith("/api/formatar"):
            tamanho = request.headers.get("content-length")
            if tamanho is None:
                return resposta_erro("tamanho_desconhecido", "Envie o cabeçalho Content-Length.")
            if not tamanho.isdigit() or int(tamanho) > config.limite_corpo_requisicao:
                return resposta_erro("documento_muito_extenso", _mensagem_limite(config))
        resposta = await chamar_proximo(request)
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["Referrer-Policy"] = "no-referrer"
        resposta.headers["X-Frame-Options"] = "DENY"
        resposta.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if not rota.startswith("/api/docs"):
            resposta.headers["Content-Security-Policy"] = CSP
        if rota.startswith("/api/"):
            resposta.headers["Cache-Control"] = "no-store"
        return resposta

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, exc: RequestValidationError):
        campos = [".".join(str(p) for p in e.get("loc", ())) for e in exc.errors()]
        return resposta_erro("requisicao_invalida", "Requisição inválida.", [f"Campo inválido: {c}" for c in campos])

    @app.exception_handler(ErroRequisicao)
    async def _erro_requisicao(_: Request, exc: ErroRequisicao):
        return resposta_erro(exc.codigo, exc.mensagem)

    @app.exception_handler(json.JSONDecodeError)
    async def _json(_: Request, __: Exception):
        return resposta_erro("requisicao_invalida", "O corpo da requisição não é um JSON válido.")

    async def processar(texto: str, modo: str, origem: str) -> JSONResponse:
        try:
            tamanho = len(texto.encode("utf-8"))
        except UnicodeEncodeError:
            raise ErroRequisicao("entrada_invalida", "O texto contém caracteres inválidos (surrogates isolados).") from None
        if tamanho > config.limite_bytes:
            raise ErroRequisicao("documento_muito_extenso", _mensagem_limite(config))
        id_req = uuid.uuid4().hex[:12]
        inicio = time.perf_counter()
        limites = {"limite_caracteres": config.limite_bytes, "limite_linhas": config.limite_linhas}
        try:
            async with vagas:
                dados = await run_in_threadpool(
                    executar, texto, modo, limites, config.tempo_limite, config.isolamento
                )
        except TempoEsgotado:
            _registrar(id_req, origem, tamanho, "tempo_esgotado", inicio)
            return resposta_erro(
                "tempo_esgotado",
                f"O processamento passou de {config.tempo_limite:g} s e foi interrompido. Tente novamente.",
            )
        except FalhaExecucao as exc:
            log.error("req=%s falha na execução: %s", id_req, exc)
            _registrar(id_req, origem, tamanho, "erro_interno", inicio)
            return resposta_erro("erro_interno", "Falha técnica no processamento. Tente novamente.")
        _registrar(id_req, origem, tamanho, dados["codigo"], inicio, dados)
        return JSONResponse(dados, status_code=STATUS_POR_CODIGO.get(dados["codigo"], 400))

    @app.get("/api/saude", tags=["serviço"])
    async def saude():
        return {"status": "ok", "versao": VERSAO_APP, "versao_diretrizes": VERSAO_DIRETRIZES}

    @app.get("/api/configuracao", tags=["serviço"])
    async def configuracao():
        return {
            "limite_bytes": config.limite_bytes,
            "limite_linhas": config.limite_linhas,
            "tempo_limite_segundos": config.tempo_limite,
            "extensoes_aceitas": list(EXTENSOES_ACEITAS),
            "modos": ["auto", "markdown", "html"],
            "versao_diretrizes": VERSAO_DIRETRIZES,
        }

    @app.post("/api/formatar", tags=["formatação"])
    async def formatar_texto(pedido: PedidoTexto):
        """Formata o texto enviado e devolve a lista de paginação, o HTML e as mensagens de validação."""
        return await processar(pedido.texto, pedido.modo, "texto")

    @app.post("/api/formatar/arquivo", tags=["formatação"])
    async def formatar_arquivo(request: Request):
        """Recebe um arquivo .md, .markdown, .txt, .html ou .htm em UTF-8 (campo `arquivo`, multipart)."""
        async with request.form(max_files=1, max_fields=4) as formulario:
            arquivo = formulario.get("arquivo")
            modo = formulario.get("modo") or "auto"
            if not isinstance(arquivo, UploadFile):
                raise ErroRequisicao("requisicao_invalida", "Envie o arquivo no campo 'arquivo'.")
            if modo not in ("auto", "markdown", "html"):
                raise ErroRequisicao("modo_invalido", "Modo deve ser auto, markdown ou html.")
            texto = decodificar_arquivo(arquivo.filename or "", await arquivo.read(config.limite_bytes + 1), config)
        return await processar(texto, modo, "arquivo")

    if config.pasta_frontend and config.pasta_frontend.is_dir():
        app.mount("/", StaticFiles(directory=config.pasta_frontend, html=True), name="frontend")
    return app


def decodificar_arquivo(nome: str, conteudo: bytes, config: Configuracao) -> str:
    extensao = PurePath(nome).suffix.lower()
    if extensao == ".docx" or conteudo.startswith(b"PK\x03\x04"):
        raise ErroRequisicao(
            "tipo_nao_suportado",
            "Arquivos do Word ainda não são aceitos. Exporte o documento como .md ou .txt, ou cole o conteúdo.",
        )
    if extensao not in EXTENSOES_ACEITAS:
        raise ErroRequisicao(
            "tipo_nao_suportado", f"Formato não aceito. Envie um destes: {', '.join(EXTENSOES_ACEITAS)}."
        )
    if len(conteudo) > config.limite_bytes:
        raise ErroRequisicao("documento_muito_extenso", _mensagem_limite(config))
    if b"\x00" in conteudo:
        raise ErroRequisicao("entrada_invalida", "O arquivo parece ser binário, não texto.")
    try:
        return conteudo.decode("utf-8")
    except UnicodeDecodeError:
        raise ErroRequisicao(
            "entrada_invalida",
            "O arquivo não está em UTF-8. Salve-o como UTF-8 e envie de novo; nenhum caractere foi convertido.",
        ) from None


def _mensagem_limite(config: Configuracao) -> str:
    return f"O documento passa do limite de {config.limite_bytes // 1024} KB."


def _registrar(id_req: str, origem: str, tamanho: int, codigo: str, inicio: float, dados: dict | None = None) -> None:
    """Registro técnico sem o conteúdo do documento."""
    extra = ""
    if dados and dados.get("itens"):
        extra = f" blocos={len(dados['itens'])} paginas={dados.get('total_paginas_texto')}"
    log.info(
        "req=%s origem=%s bytes=%d codigo=%s ms=%d%s",
        id_req,
        origem,
        tamanho,
        codigo,
        (time.perf_counter() - inicio) * 1000,
        extra,
    )
