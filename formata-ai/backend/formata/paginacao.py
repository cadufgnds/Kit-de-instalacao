"""Decisão FICA, QUEBRA e SEGUE (seção 5.3) e lista de paginação (seção 5.4)."""

from __future__ import annotations

from dataclasses import dataclass

from . import regras as R


@dataclass(frozen=True)
class ItemPaginacao:
    bloco: int
    rotulo: str
    tam: int
    restante_anterior: int
    restante_novo: int
    pagina_inicio: int
    pagina: int  # "Pág": página onde o bloco termina
    resultado: str
    conta: str

    def linha_lista(self) -> str:
        return f"- Pág {self.pagina} | `{self.rotulo}` | Tam {self.tam} | {self.conta} | {self.resultado}"


def numero(n: int) -> str:
    """Formata como nas diretrizes: sinal de menos tipográfico (−)."""
    return f"−{abs(n)}" if n < 0 else str(n)


def paginar(blocos: list[tuple[str, int]]) -> list[ItemPaginacao]:
    """Percorre os blocos (rótulo, Tam) na ordem e decide cada um.

    Restante começa em 34. O primeiro bloco nunca leva quebra: se passar de
    34, é SEGUE. Um Restante negativo soma 40 e avança uma página até deixar
    de ser negativo (regra 4).

    Conta nos casos sem exemplo na seção 5.4 (decisão D2, formato enxuto):
    só a comparação principal e o cálculo final, com as páginas somadas pela
    regra 4 incluídas no cálculo: "110 > 4; 80 − 110 + 40 = 10".
    """
    itens: list[ItemPaginacao] = []
    pagina = 1
    restante = R.LIMITE_PAGINA_1
    pag_cheia = R.LIMITE_DEMAIS_PAGINAS
    for indice, (rotulo, tam) in enumerate(blocos, start=1):
        if tam < 1:
            raise ValueError(f"Bloco {indice} com Tam {tam}: todo bloco tem ao menos uma linha.")
        anterior = restante
        inicio = pagina
        aplica_regra_4 = False  # só o primeiro SEGUE e a QUEBRA acima de 40 podem dar negativo
        if tam <= restante:
            resultado = R.FICA
            novo = restante - tam
            conta = f"{restante} − {tam} = {numero(novo)}"
        elif indice == 1:
            resultado = R.SEGUE
            base = restante + pag_cheia
            novo = base - tam
            pagina += 1
            conta = f"{tam} > {restante}; {base} − {tam}"
            aplica_regra_4 = True
        elif tam <= pag_cheia:
            resultado = R.QUEBRA
            novo = pag_cheia - tam
            pagina += 1
            inicio = pagina
            conta = f"{tam} > {restante}; {pag_cheia} − {tam} = {numero(novo)}"
        elif restante >= R.RESTANTE_MINIMO_SEGUE and tam <= restante + pag_cheia:
            resultado = R.SEGUE
            base = restante + pag_cheia
            novo = base - tam
            pagina += 1
            conta = f"{restante} ≥ {R.RESTANTE_MINIMO_SEGUE} e {tam} ≤ {base}; {base} − {tam} = {numero(novo)}"
        else:
            resultado = R.QUEBRA
            base = 2 * pag_cheia
            novo = base - tam
            inicio = pagina + 1
            pagina += 2
            conta = f"{tam} > {restante}; {base} − {tam}"
            aplica_regra_4 = True
        if aplica_regra_4:
            avancos = 0
            while novo < 0:
                novo += pag_cheia
                pagina += 1
                avancos += 1
            if avancos:
                conta += f" + {avancos * pag_cheia}"
            conta += f" = {numero(novo)}"
        restante = novo
        itens.append(ItemPaginacao(indice, rotulo, tam, anterior, novo, inicio, pagina, resultado, conta))
    return itens


def texto_lista(itens: list[ItemPaginacao], tem_imagens: bool) -> str:
    linhas = ["Paginação:"] + [item.linha_lista() for item in itens]
    if tem_imagens:
        linhas.append(f"- `{R.TEXTO_LINHA_IMAGENS}` | {R.QUEBRA}")
    return "\n".join(linhas)
