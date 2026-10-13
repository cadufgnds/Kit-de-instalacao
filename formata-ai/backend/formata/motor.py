"""Orquestra a ordem de trabalho da seção 0 e monta o resultado."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from . import regras as R
from .blocos import delimitar_blocos
from .entrada import EntradaInvalida, Remocao, preparar
from .marcacao import gerar_html
from .paginacao import ItemPaginacao, paginar, texto_lista
from .validacao import verificar

VERSAO_DIRETRIZES = "2.6"


@dataclass
class Resultado:
    ok: bool
    codigo: str  # "ok", "documento_vazio", "entrada_invalida", "falha_validacao"...
    mensagem: str
    modo: str = ""
    lista_paginacao: str = ""
    itens: list[ItemPaginacao] = field(default_factory=list)
    html: str = ""
    resposta: str = ""  # lista + bloco de código, no formato da seção 8
    total_paginas_texto: int = 0
    tem_imagens: bool = False
    removidas: list[Remocao] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)

    def como_dict(self) -> dict:
        dados = asdict(self)
        dados["versao_diretrizes"] = VERSAO_DIRETRIZES
        return dados


def bloco_de_codigo(html: str) -> str:
    """Seção 8: bloco único; com crases triplas no documento, cerca mais longa."""
    maior = max((len(m) for m in re.findall(r"`{3,}", html)), default=0)
    cerca = "`" * max(3, maior + 1)
    return f"{cerca}\n{html}\n{cerca}"


def formatar(texto: str, modo: str = "auto", **limites: int) -> Resultado:
    try:
        entrada = preparar(texto, modo, **limites)
    except EntradaInvalida as exc:
        return Resultado(ok=False, codigo=exc.codigo, mensagem=exc.mensagem)

    blocos = delimitar_blocos(entrada.linhas)
    itens = paginar([(b.rotulo, b.tam) for b in blocos])
    inicios_quebra = {b.inicio for b, it in zip(blocos, itens) if it.resultado == R.QUEBRA}

    avisos = list(entrada.avisos)
    avisos_marcacao: list[str] = []
    html = gerar_html(entrada.linhas, inicios_quebra, entrada.marcadores_finais, entrada.tem_imagens, avisos_marcacao)
    avisos += avisos_marcacao
    outras_tags = sorted({t.split()[0].strip("<>/").lower() for l in entrada.linhas for t in R.RE_TAG_QUALQUER.findall(l.texto)})
    if outras_tags:
        avisos.append(
            "O documento já contém tags além de <p> e <strong> ("
            + ", ".join(outras_tags)
            + "); foram mantidas como conteúdo, sem alteração."
        )

    lista = texto_lista(itens, entrada.tem_imagens)
    erros = verificar(entrada, blocos, itens, html, avisos_marcacao)
    base = dict(
        modo=entrada.modo,
        lista_paginacao=lista,
        itens=itens,
        total_paginas_texto=itens[-1].pagina if itens else 0,
        tem_imagens=entrada.tem_imagens,
        removidas=entrada.removidas,
        avisos=avisos,
    )
    if erros:
        # Nada de resultado silenciosamente incorreto: sem HTML quando a verificação falha.
        return Resultado(
            ok=False,
            codigo="falha_validacao",
            mensagem="O resultado não passou nas verificações e não foi entregue.",
            erros=erros,
            **base,
        )
    return Resultado(
        ok=True,
        codigo="ok",
        mensagem="Documento formatado.",
        html=html,
        resposta=f"{lista}\n\n{bloco_de_codigo(html)}",
        **base,
    )
