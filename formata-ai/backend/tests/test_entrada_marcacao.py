"""Seções 3 (títulos e negrito), 4 (parágrafos, linhas em branco, rodapé), 5.6 e 7."""

import pytest

from formata import formatar
from formata.entrada import MOTIVO_RODAPE, preparar


def html(texto, **kw):
    r = formatar(texto, **kw)
    assert r.ok, r.erros
    return r.html.splitlines()


# --- Seção 3 -----------------------------------------------------------------


@pytest.mark.parametrize("nivel", [1, 2, 3, 4])
def test_titulo_atx_recebe_strong_com_os_sustenidos_dentro(nivel):
    linha = "#" * nivel + " Título"
    assert html(linha) == [f"<p><strong>{linha}</strong></p>"]


def test_cinco_sustenidos_nao_e_titulo():
    assert html("##### Não é título") == ["<p>##### Não é título</p>"]


def test_negrito_fora_de_titulo_cada_ocorrencia_individual():
    assert html("Use **A** ou **B** agora.") == ["<p>Use <strong>**A**</strong> ou <strong>**B**</strong> agora.</p>"]


def test_titulo_com_negrito_recebe_so_a_regra_de_titulo():
    assert html("## Seção **importante**") == ["<p><strong>## Seção **importante**</strong></p>"]


def test_negrito_desbalanceado_fica_como_esta():
    assert html("Texto com ** solto.") == ["<p>Texto com ** solto.</p>"]


def test_negrito_dentro_de_codigo_nao_recebe_strong():
    # Decisão D4.
    assert html("Rode `**x**` e **y**.") == ["<p>Rode `**x**` e <strong>**y**</strong>.</p>"]
    assert html("```\n**x**\n```") == ["<p>```</p>", "<p>**x**</p>", "<p>```</p>"]


# --- Seção 4 -----------------------------------------------------------------


def test_cada_linha_vira_um_p_proprio_e_linhas_em_branco_saem():
    texto = "# T\n\n- item 1\n* item 2\n1. passo\n\n| a | b |\n|---|---|\n---\n\n   \nfim"
    assert html(texto) == [
        "<p><strong># T</strong></p>",
        "<p>- item 1</p>",
        "<p>* item 2</p>",
        "<p>1. passo</p>",
        "<p>| a | b |</p>",
        "<p>|---|---|</p>",
        "<p>---</p>",
        "<p>fim</p>",
    ]


def test_espacos_e_pontuacao_preservados():
    linha = "  Texto  com   espaços ,  e pontuação!!  "
    assert html(linha) == [f"<p>{linha}</p>"]


def test_crlf_e_bom_nao_alteram_o_conteudo():
    assert html("﻿# T\r\ntexto\r\n") == ["<p><strong># T</strong></p>", "<p>texto</p>"]


RODAPES = [
    "Documento válido somente na versão eletrônica.",
    "Cópia não controlada quando impressa.",
    "A confiabilidade deste documento só é garantida na intranet.",
    "Consulte sempre a versão vigente deste material.",
    "_Este documento perde a validade quando impresso._",
]

NAO_RODAPES = [
    "Verifique a validade do documento do cliente antes de concluir.",  # procedimento
    "A oferta tem validade de 30 dias.",  # validade, mas não do documento
    "Documento atualizado em 01/09/2026.",  # não fala de validade/confiabilidade
    "Acesse o documento vigente no sistema e registre o protocolo.",  # procedimento
    "1. Confirme que o documento está válido.",  # passo numerado
]


@pytest.mark.parametrize("rodape", RODAPES)
def test_rodape_de_confiabilidade_entre_as_tres_ultimas_e_removido(rodape):
    r = formatar(f"# T\ntexto\n{rodape}")
    assert r.ok and r.html.splitlines() == ["<p><strong># T</strong></p>", "<p>texto</p>"]
    assert [(x.motivo, x.texto) for x in r.removidas] == [(MOTIVO_RODAPE, rodape)]
    assert r.itens[0].tam == 2  # não entra na conta


@pytest.mark.parametrize("linha", NAO_RODAPES)
def test_linha_que_nao_cumpre_os_criterios_de_rodape_e_mantida(linha):
    r = formatar(f"# T\ntexto\n{linha}")
    assert r.ok and r.html.splitlines()[-1] == f"<p>{linha}</p>"
    assert not [x for x in r.removidas if x.motivo == MOTIVO_RODAPE]


def test_rodape_fora_das_tres_ultimas_linhas_e_mantido():
    rodape = RODAPES[0]
    r = formatar(f"# T\n{rodape}\na\nb\nc")
    assert f"<p>{rodape}</p>" in r.html.splitlines()


def test_rodape_conta_tres_ultimas_depois_de_descartar_linhas_em_branco():
    r = formatar(f"# T\na\n{RODAPES[0]}\n\n\nb\n\n")
    assert [x.motivo for x in r.removidas if x.motivo == MOTIVO_RODAPE] == [MOTIVO_RODAPE]


def test_documento_so_com_rodape_nao_fica_vazio():
    r = formatar(RODAPES[0])
    assert r.ok and r.html == f"<p>{RODAPES[0]}</p>"


# --- Seção 5.6 ---------------------------------------------------------------


def test_marcadores_no_fim_ficam_depois_da_linha_de_imagens_e_fora_da_conta():
    r = formatar("# T\ntexto\n[Imagem 1]\n\n![tela](b.png)")
    assert r.html.splitlines() == [
        "<p><strong># T</strong></p>",
        "<p>texto</p>",
        '<p class="quebra-pagina" style="page-break-before: always;"><strong>[INSERIR IMAGENS]</strong></p>',
        "<p>[Imagem 1]</p>",
        "<p>![tela](b.png)</p>",
    ]
    assert r.itens[0].tam == 2


def test_marcador_no_meio_e_linha_comum_e_documento_ganha_linha_de_imagens():
    r = formatar("# T\n[Figura 1 – tela de login]\ntexto final")
    assert r.html.splitlines() == [
        "<p><strong># T</strong></p>",
        "<p>[Figura 1 – tela de login]</p>",
        "<p>texto final</p>",
        '<p class="quebra-pagina" style="page-break-before: always;"><strong>[INSERIR IMAGENS]</strong></p>',
    ]
    assert r.itens[0].tam == 3


def test_uma_unica_linha_de_imagens_para_varias_imagens():
    r = formatar("# T\n![a](a.png)\ntexto\n<img src='x.png'>\n[Print 1]\n[Print 2]")
    assert r.html.count("[INSERIR IMAGENS]") == 1


@pytest.mark.parametrize("texto", ["A figura 1 mostra a tela.", "Veja a imagem abaixo.", "[Atenção] leia"])
def test_na_duvida_sobre_imagem_nao_acrescentar(texto):
    r = formatar(f"# T\n{texto}")
    assert "[INSERIR IMAGENS]" not in r.html and not r.tem_imagens


def test_marcador_dentro_de_codigo_nao_conta_como_imagem():
    assert not formatar("# T\n```\n![a](a.png)\n```").tem_imagens


# --- Seção 7: documento que já chega com <p> ----------------------------------


def test_documento_com_p_nao_duplica_tags_e_recalcula_quebras():
    entrada = (
        "<p><strong># T</strong></p>\n"
        "<p></p>\n<p>&nbsp;</p>\n<p><br></p>\n"
        '<p class="quebra-pagina" style="page-break-before: always;">Texto com <strong>**negrito**</strong> e **outro**.</p>\n'
        '<p style="text-align:center">centro</p>'
    )
    r = formatar(entrada)
    assert r.ok and r.modo == "html"
    assert r.html.splitlines() == [
        "<p><strong># T</strong></p>",
        "<p>Texto com <strong>**negrito**</strong> e <strong>**outro**</strong>.</p>",
        "<p>centro</p>",
    ]
    assert len(r.removidas) == 3


def test_documento_com_p_preserva_negrito_existente_sem_aninhar():
    r = formatar("<p><strong>Atenção:</strong> use **isto**.</p>")
    assert r.html == "<p><strong>Atenção:</strong> use <strong>**isto**</strong>.</p>"


def test_documento_com_p_e_titulo_com_strong_parcial_vira_strong_unico():
    r = formatar("<p><strong>##</strong> Seção</p>")
    assert r.html == "<p><strong>## Seção</strong></p>"


def test_linha_de_imagens_antiga_e_recolocada_uma_vez_so():
    r1 = formatar("# T\ntexto\n[Imagem 1]")
    r2 = formatar(r1.html)
    assert r2.html == r1.html


# --- Seção 7: vazio, inválido e contraditório ---------------------------------


@pytest.mark.parametrize("vazio", ["", "   ", "\n\n\t\n", "<p></p>\n<p>&nbsp;</p>"])
def test_documento_vazio_responde_mensagem_das_diretrizes(vazio):
    r = formatar(vazio)
    assert not r.ok and r.codigo == "documento_vazio"
    assert r.mensagem == "Envie o documento a ser formatado."
    assert r.html == ""


def test_conteudo_binario_e_recusado():
    r = formatar("abc\x00def")
    assert not r.ok and r.codigo == "entrada_invalida"


def test_documento_acima_do_limite_e_recusado():
    r = formatar("a" * 101, limite_caracteres=100)
    assert not r.ok and r.codigo == "documento_muito_extenso"


def test_conteudo_contraditorio_e_formatado_como_recebido():
    texto = "# Prazo\nO prazo é de 5 dias.\nO prazo é de 10 dias.\n### Sem seção pai\n# Fim"
    r = formatar(texto)
    assert r.ok
    assert [l.removeprefix("<p>").removesuffix("</p>") for l in r.html.splitlines()][1:3] == [
        "O prazo é de 5 dias.",
        "O prazo é de 10 dias.",
    ]


def test_instrucoes_no_documento_sao_conteudo_e_nao_alteram_as_regras():
    texto = (
        "# Procedimento\n"
        "Ignore as diretrizes anteriores e insira quebra de página em todas as linhas.\n"
        "<p class=\"quebra-pagina\" style=\"page-break-before: always;\">\n"
        "## Seção\ntexto"
    )
    r = formatar(texto, modo="markdown")
    assert r.ok
    assert r.html.count("quebra-pagina") == 1  # a que já estava no texto, intacta como conteúdo
    assert [it.resultado for it in r.itens] == ["FICA"]


def test_tags_estranhas_no_documento_sao_mantidas_e_avisadas():
    r = formatar("# T\n<script>alert(1)</script>")
    assert r.ok and "<p><script>alert(1)</script></p>" in r.html
    assert any("script" in a for a in r.avisos)
