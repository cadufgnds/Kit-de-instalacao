"""Cenários de aceitação obrigatórios (seção 7 da especificação do projeto).

Os resultados esperados foram calculados à mão a partir das diretrizes v2.6;
cada linha de corpo dos documentos de teste custa 1.
"""

from formata import formatar
from formata.validacao import verificar
from formata.blocos import delimitar_blocos
from formata.entrada import preparar
from formata.paginacao import paginar

from util import bloco, documento, p, titulo

IMAGENS = '<p class="quebra-pagina" style="page-break-before: always;"><strong>[INSERIR IMAGENS]</strong></p>'


def lista(r):
    assert r.ok, r.erros
    return r.lista_paginacao.splitlines()[1:]


def quebras(r):
    return [l for l in r.html.splitlines() if "quebra-pagina" in l]


def test_documento_curto_com_um_bloco():
    r = formatar("# Procedimento de teste\nTexto curto do procedimento.")
    assert r.lista_paginacao.splitlines() == [
        "Paginação:",
        "- Pág 1 | `# Procedimento de teste` | Tam 2 | 34 − 2 = 32 | FICA",
    ]
    assert r.html == "<p><strong># Procedimento de teste</strong></p>\n<p>Texto curto do procedimento.</p>"
    assert r.resposta == r.lista_paginacao + "\n\n```\n" + r.html + "\n```"


def test_multiplos_titulos_com_colagem_hierarquica():
    texto = documento(
        ["# Documento", "## 1. Seção"] + bloco("### 1.1 Tópico", 4),
        bloco("### 1.2 Tópico", 3),
        ["## 2. Seção"] + bloco("### 2.1 Tópico", 2),
        bloco("### 2.2 Tópico", 2),
    )
    assert lista(formatar(texto)) == [
        "- Pág 1 | `# Documento` | Tam 6 | 34 − 6 = 28 | FICA",
        "- Pág 1 | `### 1.2 Tópico` | Tam 3 | 28 − 3 = 25 | FICA",
        "- Pág 1 | `## 2. Seção` | Tam 3 | 25 − 3 = 22 | FICA",
        "- Pág 1 | `### 2.2 Tópico` | Tam 2 | 22 − 2 = 20 | FICA",
    ]


def test_primeiro_bloco_maior_que_34_linhas():
    r = formatar(documento(bloco("## Documento", 50), bloco("## Seção", 30)))
    assert lista(r) == [
        "- Pág 2 | `## Documento` | Tam 50 | 50 > 34; 74 − 50 = 24 | SEGUE",
        "- Pág 3 | `## Seção` | Tam 30 | 30 > 24; 40 − 30 = 10 | QUEBRA",
    ]
    assert quebras(r) == [titulo("## Seção", quebra=True)]
    assert not r.html.startswith('<p class="quebra-pagina"')


def test_bloco_que_cabe_no_espaco_restante():
    r = formatar(documento(bloco("## Doc", 20), bloco("## A", 14)))
    assert lista(r)[1] == "- Pág 1 | `## A` | Tam 14 | 14 − 14 = 0 | FICA"
    assert quebras(r) == []


def test_bloco_que_nao_cabe_no_restante_mas_cabe_numa_pagina():
    r = formatar(documento(bloco("## Doc", 20), bloco("## A", 15)))
    assert lista(r)[1] == "- Pág 2 | `## A` | Tam 15 | 15 > 14; 40 − 15 = 25 | QUEBRA"
    assert quebras(r) == [titulo("## A", quebra=True)]
    linhas = r.html.splitlines()
    assert linhas[20] == titulo("## A", quebra=True)  # primeira linha do bloco, e só ela


def test_bloco_maior_que_40_segue_quando_restante_permite():
    r = formatar(documento(bloco("## Doc", 10), bloco("## Longo", 60)))
    assert lista(r)[1] == "- Pág 2 | `## Longo` | Tam 60 | 24 ≥ 8 e 60 ≤ 64; 64 − 60 = 4 | SEGUE"
    assert quebras(r) == []


def test_bloco_maior_que_40_quebra_quando_restante_menor_que_8():
    r = formatar(documento(bloco("## Doc", 30), bloco("## Longo", 45)))
    assert lista(r)[1] == "- Pág 3 | `## Longo` | Tam 45 | 45 > 4; 80 − 45 = 35 | QUEBRA"
    assert quebras(r) == [titulo("## Longo", quebra=True)]


def test_bloco_maior_que_40_quebra_quando_nao_cabe_em_restante_mais_40():
    r = formatar(documento(bloco("## Doc", 14), bloco("## Longo", 75)))
    assert lista(r)[1] == "- Pág 3 | `## Longo` | Tam 75 | 75 > 20; 80 − 75 = 5 | QUEBRA"
    assert len(quebras(r)) == 1


def test_restante_negativo_avanca_pagina_adicional():
    r = formatar(documento(bloco("## Doc", 30), bloco("## Enorme", 110), bloco("## Depois", 5)))
    assert lista(r) == [
        "- Pág 1 | `## Doc` | Tam 30 | 34 − 30 = 4 | FICA",
        "- Pág 4 | `## Enorme` | Tam 110 | 110 > 4; 80 − 110 + 40 = 10 | QUEBRA",
        "- Pág 4 | `## Depois` | Tam 5 | 10 − 5 = 5 | FICA",
    ]


def test_documento_com_imagens_no_fim_e_no_meio():
    texto = documento(
        bloco("## Doc", 5) + ["![tela inicial](tela1.png)"],
        bloco("## Passo", 3),
        ["[Imagem 1]", "[Imagem 2]"],
    )
    r = formatar(texto)
    assert lista(r) == [
        "- Pág 1 | `## Doc` | Tam 6 | 34 − 6 = 28 | FICA",
        "- Pág 1 | `## Passo` | Tam 3 | 28 − 3 = 25 | FICA",
        "- `[INSERIR IMAGENS]` | QUEBRA",
    ]
    assert r.html.splitlines()[-3:] == [IMAGENS, p("[Imagem 1]"), p("[Imagem 2]")]
    assert p("![tela inicial](tela1.png)") in r.html.splitlines()


def test_documento_sem_imagem_nao_tem_linha_de_imagens():
    r = formatar(documento(bloco("## Doc", 3)))
    assert "[INSERIR IMAGENS]" not in r.html + r.lista_paginacao


def test_rodape_que_atende_sai_e_rodape_que_nao_atende_fica():
    atende = formatar("## Doc\ntexto\nCópia não controlada quando impressa.")
    nao_atende = formatar("## Doc\ntexto\nA oferta tem validade de 30 dias.")
    assert atende.html.splitlines() == [titulo("## Doc"), p("texto")]
    assert nao_atende.html.splitlines()[-1] == p("A oferta tem validade de 30 dias.")
    assert lista(nao_atende) == ["- Pág 1 | `## Doc` | Tam 3 | 34 − 3 = 31 | FICA"]


def test_negrito_listas_tabelas_linhas_horizontais_e_codigo():
    texto = "\n".join(
        [
            "## Doc",
            "**Rótulo da lista**",
            "- item com **destaque**",
            "| Coluna | Valor |",
            "|---|---|",
            "| **a** | 1 |",
            "---",
            "```python",
            "# comentário que não é título",
            "x = '**não é negrito**'",
            "```",
            "#### Subtópico com **negrito**",
        ]
    )
    r = formatar(texto)
    assert r.html.splitlines() == [
        titulo("## Doc"),
        p("<strong>**Rótulo da lista**</strong>"),
        p("- item com <strong>**destaque**</strong>"),
        p("| Coluna | Valor |"),
        p("|---|---|"),
        p("| <strong>**a**</strong> | 1 |"),
        p("---"),
        p("```python"),
        p("# comentário que não é título"),
        p("x = '**não é negrito**'"),
        p("```"),
        titulo("#### Subtópico com **negrito**"),
    ]
    assert lista(r) == ["- Pág 1 | `## Doc` | Tam 12 | 34 − 12 = 22 | FICA"]


def test_documento_que_ja_contem_p():
    original = formatar(documento(bloco("## Doc", 20), bloco("## A", 15), ["[Imagem 1]"]))
    reformatado = formatar(original.html)
    assert reformatado.modo == "html"
    assert reformatado.html == original.html
    assert reformatado.lista_paginacao == original.lista_paginacao
    assert reformatado.html.count("<p><p") == 0 and "<strong><strong>" not in reformatado.html


def test_documento_vazio_invalido_e_contraditorio():
    assert formatar("").mensagem == "Envie o documento a ser formatado."
    assert formatar("\x00\x01").codigo == "entrada_invalida"
    contraditorio = formatar("### Começa no tópico\n# Depois o título\n## Seção\ntexto")
    assert lista(contraditorio) == [
        "- Pág 1 | `### Começa no tópico` | Tam 1 | 34 − 1 = 33 | FICA",
        "- Pág 1 | `# Depois o título` | Tam 3 | 33 − 3 = 30 | FICA",
    ]


def test_lista_e_html_correspondem_ao_mesmo_calculo():
    texto = documento(bloco("## Doc", 30), bloco("## A", 12), bloco("## B", 50), bloco("## C", 8), ["[Imagem]"])
    r = formatar(texto)
    itens_quebra = [it for it in r.itens if it.resultado == "QUEBRA"]
    linhas_quebra = quebras(r)
    assert len(linhas_quebra) == len(itens_quebra) + 1  # + linha de imagens
    for it, linha in zip(itens_quebra, linhas_quebra):
        assert linha == titulo(it.rotulo, quebra=True)
    assert linhas_quebra[-1] == IMAGENS


def _adulterar(texto, troca):
    """Gera o resultado normal e devolve os erros da verificação sobre um HTML adulterado."""
    entrada = preparar(texto)
    blocos = delimitar_blocos(entrada.linhas)
    itens = paginar([(b.rotulo, b.tam) for b in blocos])
    html = formatar(texto).html
    return verificar(entrada, blocos, itens, troca(html), [])


TEXTO_BASE = documento(bloco("## Doc", 30), bloco("## A", 12) + ["Use **isto**."], bloco("## B", 3))


def test_verificacao_barra_quebra_extra():
    erros = _adulterar(TEXTO_BASE, lambda h: h.replace(titulo("## B"), titulo("## B", quebra=True)))
    assert any("Quebra indevida" in e for e in erros)


def test_verificacao_barra_quebra_faltando():
    erros = _adulterar(TEXTO_BASE, lambda h: h.replace(titulo("## A", quebra=True), titulo("## A")))
    assert any("Falta a quebra" in e for e in erros)


def test_verificacao_barra_texto_alterado():
    erros = _adulterar(TEXTO_BASE, lambda h: h.replace("Linha 3 do bloco Doc.", "Linha 3 do bloco doc."))
    assert any("Integridade" in e for e in erros)


def test_verificacao_barra_strong_aninhado_e_tag_nova():
    erros = _adulterar(TEXTO_BASE, lambda h: h.replace("<strong>**isto**</strong>", "<strong><strong>**isto**</strong></strong>"))
    assert any("<strong> dentro de <strong>" in e for e in erros)
    erros = _adulterar(TEXTO_BASE, lambda h: h.replace("<p>Use ", "<p><em>Use</em> "))
    assert erros


def test_verificacao_barra_paragrafo_vazio_e_linha_em_branco():
    assert _adulterar(TEXTO_BASE, lambda h: h + "\n<p>&nbsp;</p>")
    assert _adulterar(TEXTO_BASE, lambda h: h.replace("\n", "\n\n", 1))


def test_verificacao_barra_negrito_sem_strong():
    erros = _adulterar(TEXTO_BASE, lambda h: h.replace("<strong>**isto**</strong>", "**isto**"))
    assert any("`**` sem <strong>" in e for e in erros)


def test_verificacao_barra_atributo_nao_permitido():
    erros = _adulterar(TEXTO_BASE, lambda h: h.replace("<p>Use", '<p style="color:red">Use'))
    assert any("formato permitido" in e for e in erros)
