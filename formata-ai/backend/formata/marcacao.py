"""Marcação HTML: <p> por linha (seção 4), <strong> (seção 3), quebra (5.5) e imagens (5.6).

A marcação só acrescenta tags em volta do texto; o texto de cada linha
sai exatamente como entrou.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import regras as R
from .entrada import Linha


@dataclass
class Token:
    tipo: str  # "texto", "abre", "fecha"
    valor: str


def tokenizar_strong(bruto: str) -> list[Token] | None:
    """Separa as tags <strong> do texto. None se as tags estiverem desbalanceadas."""
    tokens: list[Token] = []
    profundidade = 0
    pos = 0
    for m in R.RE_STRONG_TAG.finditer(bruto):
        if m.start() > pos:
            tokens.append(Token("texto", bruto[pos : m.start()]))
        fecha = m.group(0)[1] == "/"
        profundidade += -1 if fecha else 1
        if profundidade < 0:
            return None
        tokens.append(Token("fecha" if fecha else "abre", m.group(0)))
        pos = m.end()
    if pos < len(bruto):
        tokens.append(Token("texto", bruto[pos:]))
    return tokens if profundidade == 0 else None


def mascarar_codigo_inline(texto: str) -> str:
    """Troca o conteúdo de `código` por um caractere neutro, mantendo as posições."""
    return R.RE_CODIGO_INLINE.sub(lambda m: "\x00" * len(m.group(0)), texto)


def trechos_negrito(texto: str, em_codigo: bool) -> list[tuple[int, int]]:
    """Posições [início, fim) de cada ocorrência de **texto** a envolver."""
    if em_codigo and not R.NEGRITO_EM_CODIGO:
        return []
    alvo = texto if R.NEGRITO_EM_CODIGO else mascarar_codigo_inline(texto)
    return [(m.start(), m.end()) for m in R.RE_NEGRITO.finditer(alvo)]


def marcar_conteudo(linha: Linha, avisos: list[str]) -> str:
    """Conteúdo interno do <p> de uma linha, com os <strong> das regras da seção 3."""
    texto = linha.texto
    if linha.nivel_titulo and not linha.em_codigo:
        # Título: um <strong> na linha inteira, com os # dentro; nada aninhado.
        if linha.bruto not in (texto, f"{R.STRONG_ABRE}{texto}{R.STRONG_FECHA}"):
            avisos.append(f"Linha {linha.numero}: <strong> interno do título substituído pelo <strong> da linha inteira.")
        return f"{R.STRONG_ABRE}{texto}{R.STRONG_FECHA}"

    tokens = tokenizar_strong(linha.bruto)
    if tokens is None:
        avisos.append(f"Linha {linha.numero}: tags <strong> desbalanceadas foram descartadas e o negrito foi reaplicado.")
        tokens = [Token("texto", texto)]

    # Profundidade de <strong> já existente em cada caractere do texto.
    profundidade_por_char: list[int] = []
    profundidade = 0
    for token in tokens:
        if token.tipo == "abre":
            profundidade += 1
        elif token.tipo == "fecha":
            profundidade -= 1
        else:
            profundidade_por_char.extend([profundidade] * len(token.valor))

    aberturas: set[int] = set()
    fechamentos: set[int] = set()
    for inicio, fim in trechos_negrito(texto, linha.em_codigo):
        dentro = [profundidade_por_char[i] > 0 for i in range(inicio, fim)]
        if all(dentro):
            continue  # já está em negrito: não duplicar a tag
        if any(dentro):
            avisos.append(
                f"Linha {linha.numero}: negrito sobreposto a <strong> existente; mantido como recebido."
            )
            continue
        aberturas.add(inicio)
        fechamentos.add(fim - 1)

    return _render(tokens, aberturas, fechamentos)


def _render(tokens: list[Token], aberturas: set[int], fechamentos: set[int]) -> str:
    partes: list[str] = []
    i = 0
    for token in tokens:
        if token.tipo != "texto":
            partes.append(token.valor)
            continue
        for ch in token.valor:
            if i in aberturas:
                partes.append(R.STRONG_ABRE)
            partes.append(ch)
            if i in fechamentos:
                partes.append(R.STRONG_FECHA)
            i += 1
    return "".join(partes)


def paragrafo(conteudo: str, quebra: bool) -> str:
    return f"{R.P_ABRE_QUEBRA if quebra else R.P_ABRE}{conteudo}{R.P_FECHA}"


def gerar_html(
    linhas: list[Linha],
    inicios_quebra: set[int],
    marcadores_finais: list[Linha],
    tem_imagens: bool,
    avisos: list[str],
) -> str:
    """Um <p> por linha, sem linha vazia entre as tags.

    inicios_quebra: posições (na lista de linhas) da primeira linha de cada bloco QUEBRA.
    """
    saida = [paragrafo(marcar_conteudo(l, avisos), i in inicios_quebra) for i, l in enumerate(linhas)]
    if tem_imagens:
        saida.append(R.LINHA_IMAGENS)
    saida += [paragrafo(marcar_conteudo(l, avisos), False) for l in marcadores_finais]
    return "\n".join(saida)
