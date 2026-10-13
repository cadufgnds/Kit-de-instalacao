"""Verificações de saída: integridade do texto, tags, quebras e lista de paginação.

Estas verificações olham o HTML final já pronto e a lista de paginação e
conferem, por um caminho próprio, o que o motor declarou. Qualquer erro
impede a entrega do resultado (nenhum resultado silenciosamente incorreto).
"""

from __future__ import annotations

import re

from . import regras as R
from .blocos import Bloco, custo_linha, delimitar_blocos
from .entrada import (
    MOTIVO_BRANCO,
    MOTIVO_IMAGENS_ANTERIOR,
    MOTIVO_RODAPE,
    MOTIVO_SEM_TEXTO,
    Entrada,
    Linha,
    classificar,
    eh_rodape,
    eh_sem_texto,
)
from .marcacao import trechos_negrito
from .paginacao import ItemPaginacao, numero

RE_STRONG_QUALQUER = re.compile(r"<(/?)strong\b[^>]*>", re.IGNORECASE)


class FormatoInvalido(ValueError):
    pass


def separar_paragrafos(html: str) -> list[tuple[bool, str]]:
    """Lê o HTML de saída como sequência de <p> (com ou sem quebra), um por linha."""
    paragrafos: list[tuple[bool, str]] = []
    pos = 0
    while pos < len(html):
        if html.startswith(R.P_ABRE_QUEBRA, pos):
            quebra, inicio = True, pos + len(R.P_ABRE_QUEBRA)
        elif html.startswith(R.P_ABRE, pos):
            quebra, inicio = False, pos + len(R.P_ABRE)
        else:
            raise FormatoInvalido(f"Conteúdo fora de <p> ou abertura não permitida na posição {pos}.")
        busca = inicio
        while True:
            fim = html.find(R.P_FECHA, busca)
            if fim == -1:
                raise FormatoInvalido(f"Parágrafo sem </p> a partir da posição {pos}.")
            depois = fim + len(R.P_FECHA)
            if depois == len(html) or html.startswith("\n", depois):
                break
            busca = fim + 1
        paragrafos.append((quebra, html[inicio:fim]))
        pos = depois + 1
        if depois < len(html) and pos == len(html):
            raise FormatoInvalido("Linha vazia no fim da saída.")
    return paragrafos


def _spans_strong(conteudo: str) -> tuple[list[tuple[int, int]], int, str | None]:
    """Intervalos de texto dentro de <strong>, profundidade máxima e erro de balanceamento."""
    spans: list[tuple[int, int]] = []
    profundidade = maxima = 0
    pos_texto = 0
    abertura = 0
    pos = 0
    for m in RE_STRONG_QUALQUER.finditer(conteudo):
        pos_texto += m.start() - pos
        pos = m.end()
        if m.group(1):
            profundidade -= 1
            if profundidade < 0:
                return spans, maxima, "</strong> sem abertura"
            if profundidade == 0:
                spans.append((abertura, pos_texto))
        else:
            if profundidade == 0:
                abertura = pos_texto
            profundidade += 1
            maxima = max(maxima, profundidade)
    if profundidade:
        return spans, maxima, "<strong> sem fechamento"
    return spans, maxima, None


def _outras_tags(conteudo: str) -> list[str]:
    return [t for t in R.RE_TAG_QUALQUER.findall(conteudo) if not RE_STRONG_QUALQUER.fullmatch(t)]


def verificar(
    entrada: Entrada,
    blocos: list[Bloco],
    itens: list[ItemPaginacao],
    html: str,
    avisos_marcacao: list[str],
) -> list[str]:
    erros: list[str] = []
    erros += _verificar_remocoes(entrada)
    try:
        paragrafos = separar_paragrafos(html)
    except FormatoInvalido as exc:
        return erros + [f"HTML fora do formato permitido: {exc}"]

    mantidas = entrada.linhas + entrada.marcadores_finais
    removidas = {r.numero for r in entrada.removidas}
    sequencia = [l.numero for l in entrada.tokenizadas if l.numero not in removidas]
    if sequencia != [l.numero for l in mantidas]:
        erros.append("Integridade: a sequência de linhas mantidas não corresponde à entrada menos as remoções autorizadas.")

    pos_imagens = len(entrada.linhas) if entrada.tem_imagens else None
    esperado = len(mantidas) + (1 if entrada.tem_imagens else 0)
    if len(paragrafos) != esperado:
        return erros + [f"Integridade: {len(paragrafos)} parágrafos na saída; esperados {esperado}."]

    # Linhas em que o motor deixou de envolver um ** por sobreposição a <strong> existente.
    sobrepostas = {
        int(m.group(1)) for a in avisos_marcacao if (m := re.match(r"Linha (\d+): negrito sobreposto", a))
    }
    conteudo_saida: list[str] = []
    origem = iter(mantidas)
    for i, (quebra, conteudo) in enumerate(paragrafos):
        if i == pos_imagens:
            if R.P_ABRE_QUEBRA + conteudo + R.P_FECHA != R.LINHA_IMAGENS:
                erros.append("Imagens: a linha de abertura da página de imagens está diferente do padrão.")
            continue
        linha = next(origem)
        erros += _verificar_paragrafo(i + 1, linha, conteudo, sobrepostas)
        conteudo_saida.append(conteudo)

    erros += _verificar_quebras(entrada, blocos, itens, paragrafos, pos_imagens)
    erros += _verificar_lista(itens)
    erros += _verificar_lista_contra_html(entrada, itens, conteudo_saida[: len(entrada.linhas)])
    return erros


def _verificar_remocoes(entrada: Entrada) -> list[str]:
    erros: list[str] = []
    por_numero = {l.numero: l for l in entrada.tokenizadas}
    removidas_antes_rodape = {r.numero for r in entrada.removidas if r.motivo != MOTIVO_RODAPE}
    candidatas = [l for l in entrada.tokenizadas if l.numero not in removidas_antes_rodape]
    janela = {l.numero for l in candidatas[-R.RODAPE_JANELA :]}
    for r in entrada.removidas:
        linha = por_numero.get(r.numero)
        if linha is None or linha.bruto != r.texto:
            erros.append(f"Remoção da linha {r.numero} não corresponde à entrada.")
        elif r.motivo in (MOTIVO_BRANCO, MOTIVO_SEM_TEXTO):
            if not eh_sem_texto(linha.texto):
                erros.append(f"Linha {r.numero} removida como vazia, mas tem texto.")
        elif r.motivo == MOTIVO_RODAPE:
            if r.numero not in janela or not eh_rodape(linha):
                erros.append(f"Linha {r.numero} removida como rodapé sem cumprir os critérios da seção 4.")
        elif r.motivo == MOTIVO_IMAGENS_ANTERIOR:
            if linha.texto.strip() != R.TEXTO_LINHA_IMAGENS:
                erros.append(f"Linha {r.numero} removida como linha de imagens anterior, mas o texto é outro.")
        else:
            erros.append(f"Linha {r.numero} removida por motivo não autorizado: {r.motivo}.")
    return erros


def _verificar_paragrafo(n: int, linha: Linha, conteudo: str, sobrepostas: set[int]) -> list[str]:
    erros: list[str] = []
    texto_saida = RE_STRONG_QUALQUER.sub("", conteudo)
    texto_origem = RE_STRONG_QUALQUER.sub("", linha.bruto)
    if texto_saida != texto_origem:
        erros.append(f"Integridade: o texto do parágrafo {n} difere da linha {linha.numero} da entrada.")
        return erros
    if eh_sem_texto(texto_saida):
        erros.append(f"Parágrafo {n} sem texto.")
    if _outras_tags(conteudo) != _outras_tags(linha.bruto):
        erros.append(f"Parágrafo {n}: tag além de <p> e <strong> introduzida.")
    spans, maxima, problema = _spans_strong(conteudo)
    if problema:
        erros.append(f"Parágrafo {n}: {problema}.")
        return erros
    if maxima > 1:
        erros.append(f"Parágrafo {n}: <strong> dentro de <strong>.")
    if linha.nivel_titulo and not linha.em_codigo:
        if conteudo != f"{R.STRONG_ABRE}{linha.texto}{R.STRONG_FECHA}":
            erros.append(f"Parágrafo {n}: título sem um <strong> único na linha inteira.")
        return erros
    spans_origem = set(_spans_strong(linha.bruto)[0])
    negritos = trechos_negrito(linha.texto, linha.em_codigo)
    sobreposto = linha.numero in sobrepostas
    # spans e negritos estão em ordem e sem sobreposição: varredura linear.
    k = 0
    for ini, fim in negritos:
        while k < len(spans) and spans[k][1] < fim:
            k += 1
        dentro = k < len(spans) and spans[k][0] <= ini and fim <= spans[k][1]
        if not dentro and not sobreposto:
            erros.append(f"Parágrafo {n}: `**` sem <strong> na posição {ini}.")
            break
    permitidos = spans_origem | set(negritos)
    if any(span not in permitidos for span in spans):
        erros.append(f"Parágrafo {n}: <strong> acrescentado fora de título ou negrito.")
    return erros


def _verificar_quebras(
    entrada: Entrada,
    blocos: list[Bloco],
    itens: list[ItemPaginacao],
    paragrafos: list[tuple[bool, str]],
    pos_imagens: int | None,
) -> list[str]:
    erros: list[str] = []
    esperadas = {b.inicio for b, it in zip(blocos, itens) if it.resultado == R.QUEBRA}
    if pos_imagens is not None:
        esperadas.add(pos_imagens)
    marcadas = {i for i, (quebra, _) in enumerate(paragrafos) if quebra}
    for i in sorted(marcadas - esperadas):
        erros.append(f"Quebra indevida no parágrafo {i + 1}.")
    for i in sorted(esperadas - marcadas):
        erros.append(f"Falta a quebra no parágrafo {i + 1}, primeira linha de bloco QUEBRA.")
    n_quebras = sum(1 for it in itens if it.resultado == R.QUEBRA) + (1 if pos_imagens is not None else 0)
    if len(marcadas) != n_quebras:
        erros.append(f"{len(marcadas)} quebras no HTML para {n_quebras} itens QUEBRA na lista.")
    return erros


def _verificar_lista(itens: list[ItemPaginacao]) -> list[str]:
    """Conferência da seção 5.4 mais uma simulação física das páginas."""
    erros: list[str] = []
    restante = R.LIMITE_PAGINA_1
    pagina_anterior = 1
    # Simulação: ocupa linha a linha as páginas de 34 e 40 linhas.
    pagina, usado = 1, 0

    def capacidade(p: int) -> int:
        return R.LIMITE_PAGINA_1 if p == 1 else R.LIMITE_DEMAIS_PAGINAS

    for k, it in enumerate(itens, start=1):
        rotulo = f"Item {k} (`{it.rotulo}`)"
        if it.bloco != k:
            erros.append(f"{rotulo}: fora de ordem.")
        if it.restante_anterior != restante:
            erros.append(f"{rotulo}: Restante anterior {it.restante_anterior}, esperado {restante}.")
        if it.restante_novo < 0:
            erros.append(f"{rotulo}: resultado negativo.")
        T, Ra = it.tam, it.restante_anterior
        if it.resultado == R.FICA:
            if T > Ra:
                erros.append(f"{rotulo}: FICA sem caber no Restante ({T} > {Ra}).")
            if it.pagina != pagina_anterior:
                erros.append(f"{rotulo}: Pág mudou em bloco FICA.")
        elif it.resultado == R.QUEBRA:
            if k == 1:
                erros.append(f"{rotulo}: o primeiro bloco nunca leva quebra.")
            if T <= Ra:
                erros.append(f"{rotulo}: quebra com espaço sobrando ({T} ≤ {Ra}).")
            if T > R.LIMITE_DEMAIS_PAGINAS and Ra >= R.RESTANTE_MINIMO_SEGUE and T <= Ra + R.LIMITE_DEMAIS_PAGINAS:
                erros.append(f"{rotulo}: QUEBRA onde a regra pede SEGUE.")
        elif it.resultado == R.SEGUE:
            primeiro = k == 1 and T > Ra
            normal = Ra >= R.RESTANTE_MINIMO_SEGUE and R.LIMITE_DEMAIS_PAGINAS < T <= Ra + R.LIMITE_DEMAIS_PAGINAS
            if not (primeiro or normal):
                erros.append(f"{rotulo}: SEGUE sem cumprir Restante ≥ 8 e Tam ≤ Restante + 40.")
        else:
            erros.append(f"{rotulo}: resultado desconhecido {it.resultado}.")
        if not it.conta.endswith(f"= {numero(it.restante_novo)}"):
            erros.append(f"{rotulo}: a conta escrita não termina no novo Restante.")

        if it.resultado == R.QUEBRA:
            pagina, usado = pagina + 1, 0
        if it.pagina_inicio != pagina:
            erros.append(f"{rotulo}: começa na página {it.pagina_inicio}; simulação indica {pagina}.")
        faltam = T
        while faltam:
            livre = capacidade(pagina) - usado
            if livre == 0:
                pagina, usado = pagina + 1, 0
                continue
            ocupa = min(livre, faltam)
            usado += ocupa
            faltam -= ocupa
        if it.pagina != pagina or it.restante_novo != capacidade(pagina) - usado:
            erros.append(
                f"{rotulo}: lista indica Pág {it.pagina} e Restante {it.restante_novo}; "
                f"simulação indica Pág {pagina} e Restante {capacidade(pagina) - usado}."
            )
        restante = it.restante_novo
        pagina_anterior = it.pagina
    return erros


def _verificar_lista_contra_html(entrada: Entrada, itens: list[ItemPaginacao], conteudos: list[str]) -> list[str]:
    """Refaz os blocos a partir do próprio HTML e compara com a lista."""
    linhas = [Linha(i + 1, c) for i, c in enumerate(conteudos)]
    classificar(linhas)
    blocos = delimitar_blocos(linhas)
    if len(blocos) != len(itens):
        return [f"A lista tem {len(itens)} itens, mas o HTML tem {len(blocos)} blocos."]
    erros = []
    for b, it in zip(blocos, itens):
        tam = sum(custo_linha(l.texto) for l in b.linhas)
        if b.rotulo != it.rotulo or tam != it.tam:
            erros.append(f"Item {it.bloco}: lista diz `{it.rotulo}` Tam {it.tam}; HTML tem `{b.rotulo}` Tam {tam}.")
    return erros
