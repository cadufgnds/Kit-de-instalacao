"""Equivalência entre o motor PHP (php/nucleo/formata.php) e o motor de referência em Python.

O hub de ferramentas roda PHP; o motor em Python é a referência validada.
Para cada entrada, o resultado completo (lista, itens, HTML, remoções,
avisos e erros) tem de ser idêntico nas duas implementações.
Pulado quando o executável `php` não está disponível.
"""

import json
import os
import random
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

from formata import formatar

from test_regressao import _documento_aleatorio
from util import bloco, documento

# FORMATA_PHP_CMD permite outra versão do PHP, por exemplo dentro de um contêiner:
#   FORMATA_PHP_CMD="docker run --rm -i -v $PWD/..:$PWD/.. php:5.6-apache php"
PHP = os.environ.get("FORMATA_PHP_CMD") or shutil.which("php")
CLI = Path(__file__).resolve().parents[2] / "php" / "ferramentas" / "formatar_cli.php"
FIXTURE = Path(__file__).parent / "fixtures" / "kit_unico_v13.md"

pytestmark = pytest.mark.skipif(PHP is None, reason="php não instalado")


def _php(pedidos):
    proc = subprocess.run(
        [*shlex.split(PHP), "-d", "memory_limit=1G", str(CLI)],
        input=json.dumps(pedidos, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")[-3000:]
    return json.loads(proc.stdout.decode("utf-8"))


def _python(pedido):
    r = formatar(pedido["texto"], pedido.get("modo", "auto"), **pedido.get("limites", {}))
    return json.loads(json.dumps(r.como_dict(), ensure_ascii=False))


def _comparar(pedidos):
    resultados_php = _php(pedidos)
    assert len(resultados_php) == len(pedidos)
    for pedido, php in zip(pedidos, resultados_php):
        py = _python(pedido)
        diferentes = [k for k in py if py[k] != php.get(k)]
        assert not diferentes, f"Campos diferentes {diferentes} para a entrada {pedido['texto'][:200]!r}"
        assert set(php) == set(py)


CASOS_FIXOS = [
    "",
    "   \n\t\n",
    "<p></p>\n<p>&nbsp;</p>",
    "abc\x00def",
    "# Título\nTexto curto.",
    "##### Cinco\n#SemEspaço\n#  só espaço",
    "Use **A** ou **B** agora. Texto com ** solto. ***x*** e **a****b**",
    "## Seção **importante**",
    "Rode `**x**` e **y**. ``dupla `crase` **z**`` fim",
    "```\n**x**\n# não é título\n```\n~~~~\n## dentro\n~~~\n~~~~\n# fora",
    "```python\nsem fechamento\n# título?",
    "﻿# T\r\ntexto\r\noutra\rlinha\r\n",
    "# T\n- item 1\n* item 2\n1. passo\n| a | b |\n|---|---|\n---\nfim",
    "  Texto  com   espaços ,  e pontuação!!  \t",
    "# T\ntexto\nDocumento válido somente na versão eletrônica.",
    "# T\ntexto\nCópia não controlada quando impressa.",
    "# T\ntexto\nA confiabilidade deste documento só é garantida na intranet.",
    "# T\ntexto\nVerifique a validade do documento do cliente antes de concluir.",
    "# T\ntexto\nA oferta tem validade de 30 dias.",
    "# T\ntexto\n1. Confirme que o documento está válido.",
    "# T\nDOCUMENTO VÁLIDO SOMENTE NA VERSÃO ELETRÔNICA.\na\nb",
    "Documento válido somente na versão eletrônica.",
    "# T\ntexto\n[Imagem 1]\n\n![tela](b.png)",
    "# T\n[Figura 1 – tela de login]\ntexto final",
    "# T\n![a](a.png)\ntexto\n<img src='x.png'>\n[Print 1]\n[PRINT 2]\n[Captura de tela 3]\n[ILUSTRAÇÃO 4]",
    "# T\nA figura 1 mostra a tela.\n[Atenção] leia",
    "[Imagem 1]\n[Imagem 2]",
    "<p><strong># T</strong></p>\n<p></p>\n<p>&nbsp;</p>\n<p><br></p>\n"
    '<p class="quebra-pagina" style="page-break-before: always;">Texto com <strong>**negrito**</strong> e **outro**.</p>\n'
    '<p style="text-align:center">centro</p>',
    "<p><strong>Atenção:</strong> use **isto**.</p>",
    "<p><strong>##</strong> Seção</p>",
    "<p><strong>a <strong>b</strong> c</strong> **d**</p>",
    "<p><strong>início **meio</strong> fim**</p>",
    "<p>sem fechamento <strong>x</p>\n<p></strong> y</p>",
    "<P CLASS='x'>maiúsculo</P >\ntexto solto fora\n<p>linha\ninterna</p>",
    "<p>a</p><p>b</p>   <p>c</p>",
    "# T\n<script>alert(1)</script>\n<a href='x'>link</a> <BR/> <Div>",
    "Preâmbulo.\nMais preâmbulo.\n# Título\ntexto\n# Outro\nx",
    "## Seção\nIntrodução.\n### Tópico\ncorpo\n## Seção 2\n### Tópico 2\ncorpo",
    "### Começa no tópico\n# Depois o título\n## Seção\ntexto",
    "x" * 61 + "ção " * 30,
    "Ação " * 20 + "\n# T",
    " separador \n\x1c\x1d\x1e\x1f\n　　\n# T\n \n😀 emoji **😀** fim",
    "# T\n" + "a" * 85 + "\n" + "b" * 86 + "\n" + "ç" * 170 + "\n" + "😀" * 171,
]


def _pedidos_fixos():
    pedidos = [{"texto": t} for t in CASOS_FIXOS]
    pedidos += [{"texto": "<p>texto</p>", "modo": "markdown"}, {"texto": "<p>texto</p>", "modo": "html"}]
    pedidos += [{"texto": "a" * 101, "limites": {"limite_caracteres": 100}}]
    pedidos += [{"texto": "a\n" * 30, "limites": {"limite_linhas": 20}}]
    pedidos += [{"texto": "x", "modo": "word"}]
    return pedidos


def test_casos_de_borda_identicos():
    _comparar(_pedidos_fixos())


def test_cenarios_de_paginacao_identicos():
    tams = [(20, 14), (20, 15), (10, 60), (30, 45), (14, 75), (14, 61), (26, 48), (34, 1), (50, 30), (100, 5), (30, 130), (30, 120)]
    docs = [documento(bloco("## Doc", a), bloco("## B", b), bloco("## C", 7)) for a, b in tams]
    docs += [documento(["# Documento", "## 1. Seção"] + bloco("### 1.1 Tópico", 4), bloco("### 1.2 Tópico", 3))]
    _comparar([{"texto": d} for d in docs])


def test_documento_real_e_reformatacao_identicos():
    texto = FIXTURE.read_text(encoding="utf-8")
    _comparar([{"texto": texto}, {"texto": formatar(texto).html}, {"texto": texto[:9000] + "\n[Imagem 1]"}])


@pytest.mark.parametrize("lote", range(4))
def test_documentos_aleatorios_identicos(lote):
    pedidos = []
    for semente in range(lote * 200, (lote + 1) * 200):
        texto = _documento_aleatorio(random.Random(semente))
        pedidos.append({"texto": texto})
        r = formatar(texto)
        if r.ok:
            pedidos.append({"texto": r.html})  # reformatação (documento com <p>)
    _comparar(pedidos)


ALFABETO = (
    list("abcçãéíõúAÇÃÉ  \t\n\n\n#*`~|-[]()!<>/=\"'.,;:0123456789_")
    + [" ", " ", "　", "\x1c", "\x85", "😀", "𝒜", "́", "\r", "\r\n"]
    + ["**", "```", "~~~", "<p>", "</p>", "<strong>", "</strong>", "<P class='q'>", "<br>", "&nbsp;"]
    + ["[Imagem ", "![x](y.png)", "<img src=x>", "# ", "## ", "### ", "#### ", "Documento válido ", "versão "]
)


@pytest.mark.parametrize("lote", range(5))
def test_textos_unicode_aleatorios_identicos(lote):
    pedidos = []
    for semente in range(lote * 200, (lote + 1) * 200):
        rnd = random.Random(10_000 + semente)
        texto = "".join(rnd.choice(ALFABETO) for _ in range(rnd.randint(0, 400)))
        pedidos.append({"texto": texto, "modo": rnd.choice(["auto", "auto", "markdown", "html"])})
    _comparar(pedidos)
