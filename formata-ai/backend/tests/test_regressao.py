"""Regressão: saída de referência, determinismo, idempotência e integridade em massa.

Para regravar a referência depois de uma mudança aprovada nas regras:
    FORMATA_REGRAVAR=1 python -m pytest tests/test_regressao.py
"""

import os
import random
import re
from pathlib import Path

import pytest

from formata import formatar
from formata import regras as R

AQUI = Path(__file__).parent
FIXTURE = AQUI / "fixtures" / "kit_unico_v13.md"
REFERENCIA = AQUI / "golden" / "kit_unico_v13.resposta.txt"


def test_documento_real_igual_a_referencia():
    r = formatar(FIXTURE.read_text(encoding="utf-8"))
    assert r.ok, r.erros
    if os.environ.get("FORMATA_REGRAVAR"):
        REFERENCIA.write_text(r.resposta + "\n", encoding="utf-8")
    assert r.resposta + "\n" == REFERENCIA.read_text(encoding="utf-8")


def test_documento_real_reformatado_e_identico():
    r1 = formatar(FIXTURE.read_text(encoding="utf-8"))
    r2 = formatar(r1.html)
    assert r2.ok and r2.html == r1.html and r2.lista_paginacao == r1.lista_paginacao


# --- Documentos aleatórios ---------------------------------------------------

PALAVRAS = (
    "cliente operador sistema fatura plano recarga prazo atendimento açãoção São "
    "R$ 17,00 30% (URA) — Next Smart: protocolo; código, consulta. **destaque** `cmd`"
).split()


def _frase(rnd, minimo=1, maximo=300):
    alvo = rnd.randint(minimo, maximo)
    partes = []
    while len(" ".join(partes)) < alvo:
        partes.append(rnd.choice(PALAVRAS))
    return " ".join(partes)[:alvo].rstrip() or "x"


def _documento_aleatorio(rnd):
    linhas = []
    for _ in range(rnd.randint(1, 120)):
        tipo = rnd.random()
        if tipo < 0.12:
            linhas.append("#" * rnd.randint(1, 3) + " " + _frase(rnd, 3, 60))
        elif tipo < 0.15:
            linhas.append("#" * rnd.randint(4, 6) + " " + _frase(rnd, 3, 40))
        elif tipo < 0.25:
            linhas.append(rnd.choice(["- ", "* ", "1. ", "| "]) + _frase(rnd, 1, 120))
        elif tipo < 0.30:
            linhas.append(rnd.choice(["", "   ", "\t", "&nbsp;"]))
        elif tipo < 0.32:
            linhas.append(rnd.choice(["---", "```", "~~~", "|---|---|"]))
        elif tipo < 0.34:
            linhas.append(rnd.choice(["![tela](a.png)", "[Imagem 3]", "[Figura 2 – login]"]))
        else:
            linhas.append(rnd.choice(["", "  "]) + _frase(rnd) + rnd.choice(["", " ", "  "]))
    if rnd.random() < 0.3:
        linhas += ["", rnd.choice(["[Imagem 1]", "![x](x.png)"]), "[Imagem 2]"]
    if rnd.random() < 0.3:
        linhas.append("Documento válido somente na versão eletrônica.")
    return rnd.choice(["\n", "\r\n"]).join(linhas)


def _texto_sem_marcacao(html):
    """Remove apenas o que o motor pode acrescentar: <p>, quebra, <strong> e a linha de imagens."""
    linhas = []
    for linha in html.split("\n"):
        if linha == R.LINHA_IMAGENS:
            continue
        linha = linha.removeprefix(R.P_ABRE_QUEBRA).removeprefix(R.P_ABRE).removesuffix(R.P_FECHA)
        linhas.append(R.RE_STRONG_TAG.sub("", linha))
    return linhas


@pytest.mark.parametrize("semente", range(400))
def test_documentos_aleatorios(semente):
    rnd = random.Random(semente)
    texto = _documento_aleatorio(rnd)
    r = formatar(texto)
    if not r.ok:
        assert r.codigo == "documento_vazio" and not texto.replace("&nbsp;", "").strip()
        return

    # Determinismo: mesma entrada, mesmo resultado.
    assert formatar(texto).resposta == r.resposta

    # Integridade: o texto de saída é a entrada menos as remoções autorizadas, na mesma ordem.
    removidas = {x.numero for x in r.removidas}
    linhas_entrada = texto.replace("\r\n", "\n").split("\n")
    esperado = [l for i, l in enumerate(linhas_entrada, start=1) if i not in removidas]
    assert _texto_sem_marcacao(r.html) == esperado
    for x in r.removidas:
        assert x.motivo != "linha_em_branco" or not linhas_entrada[x.numero - 1].strip()

    # Quebras: uma por item QUEBRA, mais a linha de imagens; nenhuma a mais.
    n_quebra = sum(1 for it in r.itens if it.resultado == "QUEBRA") + (1 if r.tem_imagens else 0)
    assert r.html.count('class="quebra-pagina"') == n_quebra

    # Sem parágrafo vazio, sem linha em branco, sem strong aninhado.
    assert "<p></p>" not in r.html and "\n\n" not in r.html
    assert not re.search(r"<strong>(?:(?!</strong>).)*<strong>", r.html)

    # Idempotência: reformatar a saída não muda nada (seção 7, documento com <p>).
    r2 = formatar(r.html)
    assert r2.ok and r2.html == r.html and r2.lista_paginacao == r.lista_paginacao
