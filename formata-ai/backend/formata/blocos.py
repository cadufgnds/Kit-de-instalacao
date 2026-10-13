"""Delimitação (seção 5.1) e medida (seção 5.2) dos blocos de paginação."""

from __future__ import annotations

from dataclasses import dataclass

from . import regras as R
from .entrada import Linha

TAMANHO_ROTULO_SEM_TITULO = 60


def custo_linha(texto: str) -> int:
    """Caracteres ÷ 85, arredondado para cima, no mínimo 1 (linha contada como está)."""
    return max(1, -(-len(texto) // R.CARACTERES_POR_LINHA))


@dataclass
class Bloco:
    indice: int  # 1, 2, 3...
    inicio: int  # posição da primeira linha na lista de linhas de conteúdo
    linhas: list[Linha]

    @property
    def custos(self) -> list[int]:
        return [custo_linha(l.texto) for l in self.linhas]

    @property
    def tam(self) -> int:
        return sum(self.custos)

    @property
    def rotulo(self) -> str:
        for linha in self.linhas:
            if abre_bloco(linha):
                return linha.texto
        texto = self.linhas[0].texto.strip()
        if len(texto) > TAMANHO_ROTULO_SEM_TITULO:
            texto = texto[:TAMANHO_ROTULO_SEM_TITULO].rstrip() + "…"
        return texto


def abre_bloco(linha: Linha) -> bool:
    return not linha.em_codigo and 1 <= linha.nivel_titulo <= R.NIVEL_MAXIMO_BLOCO


def delimitar_blocos(linhas: list[Linha]) -> list[Bloco]:
    """Cada #, ## ou ### abre bloco; cabeçalho seguinte mais profundo cola no anterior.

    Linhas antes do primeiro cabeçalho pertencem ao primeiro bloco; sem
    cabeçalho, o documento é um bloco só.
    """
    if not linhas:
        return []
    inicios = [0]
    anterior: tuple[int, int] | None = None  # (nível, posição) do último cabeçalho
    for i, linha in enumerate(linhas):
        if not abre_bloco(linha):
            continue
        nivel = linha.nivel_titulo
        if anterior is not None:
            cola = nivel > anterior[0]
            if R.COLAGEM_SOMENTE_ADJACENTES:
                cola = cola and i == anterior[1] + 1
            if not cola:
                inicios.append(i)
        anterior = (nivel, i)
    fins = inicios[1:] + [len(linhas)]
    return [
        Bloco(indice=n, inicio=ini, linhas=linhas[ini:fim])
        for n, (ini, fim) in enumerate(zip(inicios, fins), start=1)
    ]
