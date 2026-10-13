"""Construtores de documentos de teste com Tam conhecido.

Cada linha de corpo tem menos de 85 caracteres (custo 1), então um bloco
criado com bloco("### X", 12) tem exatamente Tam 12.
"""

from formata import regras as R


def bloco(titulo: str, tam: int) -> list[str]:
    assert tam >= 1
    return [titulo] + [f"Linha {i} do bloco {titulo.lstrip('# ')}." for i in range(1, tam)]


def documento(*blocos: list[str], separador: str = "\n\n") -> str:
    return separador.join("\n".join(b) for b in blocos)


def p(conteudo: str, quebra: bool = False) -> str:
    return f"{R.P_ABRE_QUEBRA if quebra else R.P_ABRE}{conteudo}{R.P_FECHA}"


def titulo(conteudo: str, quebra: bool = False) -> str:
    return p(f"<strong>{conteudo}</strong>", quebra)
