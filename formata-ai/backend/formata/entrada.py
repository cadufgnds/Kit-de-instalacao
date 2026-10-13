"""Leitura e normalização permitida da entrada (seções 4, 5.6 e 7).

Transforma o texto recebido em uma sequência de linhas, descarta apenas o
que as diretrizes autorizam (linhas em branco, rodapé de confiabilidade e,
em documento já formatado, parágrafos sem texto, quebras antigas e a linha
de imagens de uma formatação anterior) e registra cada remoção.

Nenhuma função deste módulo altera o conteúdo de uma linha mantida.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import regras as R

MODO_MARKDOWN = "markdown"
MODO_HTML = "html"

MOTIVO_BRANCO = "linha_em_branco"
MOTIVO_SEM_TEXTO = "paragrafo_sem_texto"
MOTIVO_RODAPE = "rodape_confiabilidade"
MOTIVO_IMAGENS_ANTERIOR = "linha_imagens_anterior"


class EntradaInvalida(ValueError):
    """Entrada que não pode ser processada (vazia, binária ou grande demais)."""

    def __init__(self, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


@dataclass
class Linha:
    numero: int  # posição na entrada: linha (Markdown) ou parágrafo (HTML)
    bruto: str  # conteúdo como recebido, sem o <p> externo
    texto: str = ""  # bruto sem as tags <strong> e </strong>
    em_codigo: bool = False
    nivel_titulo: int = 0  # 1 a 4 para título ATX; 0 caso contrário

    def __post_init__(self) -> None:
        self.texto = R.RE_STRONG_TAG.sub("", self.bruto)


@dataclass
class Remocao:
    numero: int
    motivo: str
    texto: str


@dataclass
class Entrada:
    modo: str
    tokenizadas: list[Linha]  # todas as linhas lidas, antes das remoções
    linhas: list[Linha]  # linhas que entram na paginação
    marcadores_finais: list[Linha]  # marcadores de imagem do fim (fora da conta)
    removidas: list[Remocao]
    tem_imagens: bool
    avisos: list[str] = field(default_factory=list)


def detectar_modo(texto: str) -> str:
    return MODO_HTML if R.RE_P_ABERTURA.search(texto) else MODO_MARKDOWN


def normalizar_quebras_de_linha(texto: str) -> str:
    """CRLF e CR isolado viram LF; o BOM inicial (marca de codificação) sai."""
    if texto.startswith("﻿"):
        texto = texto[1:]
    return texto.replace("\r\n", "\n").replace("\r", "\n")


def tokenizar(texto: str, modo: str) -> tuple[list[Linha], list[str]]:
    if modo == MODO_MARKDOWN:
        return [Linha(i, l) for i, l in enumerate(texto.split("\n"), start=1)], []
    return _tokenizar_html(texto)


def _tokenizar_html(texto: str) -> tuple[list[Linha], list[str]]:
    """Seção 7: em documento que já chega com <p>, cada <p>...</p> é uma linha."""
    linhas: list[Linha] = []
    avisos: list[str] = []
    fora_de_p = quebras_antigas = outros_atributos = multilinha = 0

    def adicionar_trecho_solto(trecho: str) -> None:
        nonlocal fora_de_p
        for parte in trecho.split("\n"):
            if parte.strip():
                fora_de_p += 1
                linhas.append(Linha(len(linhas) + 1, parte))

    pos = 0
    while (m := R.RE_P_ABERTURA.search(texto, pos)) is not None:
        fecha = R.RE_P_FECHAMENTO.search(texto, m.end())
        if fecha is None:
            break  # <p> sem fechamento: o resto é texto solto
        adicionar_trecho_solto(texto[pos : m.start()])
        atributos = (m.group(1) or "").strip()
        if atributos:
            if "quebra-pagina" in atributos or "page-break" in atributos:
                quebras_antigas += 1
            else:
                outros_atributos += 1
        conteudo = texto[m.end() : fecha.start()]
        if "\n" in conteudo:
            multilinha += 1
        linhas.append(Linha(len(linhas) + 1, conteudo))
        pos = fecha.end()
    adicionar_trecho_solto(texto[pos:])

    if quebras_antigas:
        avisos.append(f"{quebras_antigas} quebra(s) de página antiga(s) descartada(s); as quebras foram recalculadas.")
    if outros_atributos:
        avisos.append(f"{outros_atributos} parágrafo(s) com atributos não permitidos; os atributos foram descartados.")
    if fora_de_p:
        avisos.append(f"{fora_de_p} linha(s) com texto fora de <p> tratadas como linhas comuns.")
    if multilinha:
        avisos.append(f"{multilinha} parágrafo(s) com quebra de linha interna mantidos como uma linha só.")
    return linhas, avisos


def eh_sem_texto(texto: str) -> bool:
    """Linha em branco, ou parágrafo só com espaços, &nbsp; ou <br>."""
    return not R.RE_SEM_TEXTO.sub("", texto).strip()


def nivel_titulo(texto: str) -> int:
    m = R.RE_TITULO.match(texto)
    return len(m.group(1)) if m else 0


def classificar(linhas: list[Linha]) -> list[str]:
    """Marca blocos de código cercados e títulos ATX. Devolve avisos."""
    cerca: tuple[str, int] | None = None
    for linha in linhas:
        m = R.RE_CERCA.match(linha.texto)
        if cerca is None:
            if m:
                cerca = (m.group(1)[0], len(m.group(1)))
                linha.em_codigo = True
            else:
                linha.nivel_titulo = nivel_titulo(linha.texto)
            continue
        linha.em_codigo = True
        if m and m.group(1)[0] == cerca[0] and len(m.group(1)) >= cerca[1] and not linha.texto[m.end() :].strip():
            cerca = None
    if cerca is not None:
        return ["Bloco de código aberto sem fechamento: o restante do documento foi tratado como código."]
    return []


def eh_marcador_so(linha: Linha) -> bool:
    return not linha.em_codigo and bool(R.RE_LINHA_SO_MARCADORES.match(linha.texto))


def eh_rodape(linha: Linha) -> bool:
    """Seção 4: refere-se à confiabilidade ou validade do documento e não é procedimento."""
    t = linha.texto.strip()
    if linha.em_codigo or linha.nivel_titulo or t.startswith(("#", "|")) or eh_marcador_so(linha):
        return False
    if re.match(r"^\d+[.)]\s", t) or len(t) > R.RODAPE_TAMANHO_MAXIMO:
        return False
    return bool(
        R.RE_RODAPE_CONFIABILIDADE.search(t)
        and R.RE_RODAPE_DOCUMENTO.search(t)
        and not R.RE_RODAPE_PROCEDIMENTO.search(t)
    )


def preparar(
    texto: str,
    modo: str = "auto",
    limite_caracteres: int = R.LIMITE_CARACTERES_PADRAO,
    limite_linhas: int = R.LIMITE_LINHAS_PADRAO,
) -> Entrada:
    if not isinstance(texto, str):
        raise EntradaInvalida("entrada_invalida", "O conteúdo enviado não é texto.")
    if "\x00" in texto:
        raise EntradaInvalida("entrada_invalida", "O conteúdo enviado parece ser um arquivo binário.")
    if len(texto) > limite_caracteres:
        raise EntradaInvalida(
            "documento_muito_extenso",
            f"O documento tem {len(texto)} caracteres; o limite é {limite_caracteres}.",
        )

    texto = normalizar_quebras_de_linha(texto)
    if modo == "auto":
        modo = detectar_modo(texto)
    if modo not in (MODO_MARKDOWN, MODO_HTML):
        raise EntradaInvalida("modo_invalido", f"Modo desconhecido: {modo}.")

    tokenizadas, avisos = tokenizar(texto, modo)
    if len(tokenizadas) > limite_linhas:
        raise EntradaInvalida(
            "documento_muito_extenso",
            f"O documento tem {len(tokenizadas)} linhas; o limite é {limite_linhas}.",
        )

    removidas: list[Remocao] = []

    # Seção 4: linha em branco é descartada, em qualquer posição.
    linhas: list[Linha] = []
    for linha in tokenizadas:
        if eh_sem_texto(linha.texto):
            motivo = MOTIVO_BRANCO if not linha.texto.strip() else MOTIVO_SEM_TEXTO
            if modo == MODO_HTML and not linha.bruto.strip():
                motivo = MOTIVO_SEM_TEXTO
            removidas.append(Remocao(linha.numero, motivo, linha.bruto))
        else:
            linhas.append(linha)

    if not linhas:
        raise EntradaInvalida("documento_vazio", R.MENSAGEM_DOCUMENTO_VAZIO)

    avisos += classificar(linhas)

    # Seção 5.6: a linha de imagens é a única acrescentada; a de uma formatação
    # anterior sai aqui e é recolocada conforme a nova lista.
    tem_imagens = False
    mantidas: list[Linha] = []
    for linha in linhas:
        # Reconhecida mesmo dentro de código: é sempre a linha que o próprio motor acrescenta.
        if linha.texto.strip() == R.TEXTO_LINHA_IMAGENS:
            tem_imagens = True
            removidas.append(Remocao(linha.numero, MOTIVO_IMAGENS_ANTERIOR, linha.bruto))
        else:
            mantidas.append(linha)
    linhas = mantidas
    if not linhas:
        raise EntradaInvalida("documento_vazio", R.MENSAGEM_DOCUMENTO_VAZIO)

    # Seção 4: rodapé de confiabilidade entre as três últimas linhas.
    janela = linhas[-R.RODAPE_JANELA :]
    rodapes = [l for l in janela if eh_rodape(l)]
    if rodapes and len(rodapes) == len(linhas):
        avisos.append("O documento só contém linha(s) com cara de rodapé; nada foi removido.")
        rodapes = []
    for linha in janela:
        if linha not in rodapes and not linha.em_codigo and R.RE_RODAPE_CONFIABILIDADE.search(linha.texto):
            avisos.append(
                f"Linha {linha.numero} cita validade ou confiabilidade, mas não cumpre os critérios "
                "de rodapé da seção 4 e foi mantida."
            )
    for linha in rodapes:
        removidas.append(Remocao(linha.numero, MOTIVO_RODAPE, linha.bruto))
    linhas = [l for l in linhas if l not in rodapes]

    # Seção 5.6: documento com imagem ou marcador de imagem.
    tem_imagens = tem_imagens or any(
        not l.em_codigo and R.RE_MARCADOR_IMAGEM.search(l.texto) for l in linhas
    )

    # Marcadores que já vêm no fim ficam depois da linha de imagens, fora da conta.
    fim = len(linhas)
    while fim > 0 and eh_marcador_so(linhas[fim - 1]):
        fim -= 1
    if fim == 0:
        avisos.append("O documento só contém marcadores de imagem; eles foram tratados como texto.")
        fim = len(linhas)
    marcadores_finais = linhas[fim:]
    linhas = linhas[:fim]

    removidas.sort(key=lambda r: r.numero)
    return Entrada(modo, tokenizadas, linhas, marcadores_finais, removidas, tem_imagens, avisos)
