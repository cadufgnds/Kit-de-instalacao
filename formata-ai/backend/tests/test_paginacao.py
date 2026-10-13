"""Seções 5.3 (decisão) e 5.4 (lista de paginação), isoladas do texto."""

import random

import pytest

from formata.paginacao import paginar, texto_lista
from formata.validacao import _verificar_lista


def _decidir(*tams):
    return paginar([(f"### B{i}", t) for i, t in enumerate(tams, start=1)])


def _resumo(itens):
    return [(it.pagina, it.tam, it.conta, it.resultado) for it in itens]


def test_exemplo_da_secao_5_4_reproduzido_literalmente():
    itens = paginar(
        [("# Título do documento", 27), ("### 1.2 Nome do tópico", 12), ("### 2.1 Nome do tópico", 50)]
    )
    assert texto_lista(itens, tem_imagens=False).splitlines() == [
        "Paginação:",
        "- Pág 1 | `# Título do documento` | Tam 27 | 34 − 27 = 7 | FICA",
        "- Pág 2 | `### 1.2 Nome do tópico` | Tam 12 | 12 > 7; 40 − 12 = 28 | QUEBRA",
        "- Pág 3 | `### 2.1 Nome do tópico` | Tam 50 | 28 ≥ 8 e 50 ≤ 68; 68 − 50 = 18 | SEGUE",
    ]


def test_primeiro_bloco_que_cabe_fica():
    assert _resumo(_decidir(34)) == [(1, 34, "34 − 34 = 0", "FICA")]


def test_primeiro_bloco_maior_que_34_segue_sem_quebra():
    assert _resumo(_decidir(35)) == [(2, 35, "35 > 34, primeiro bloco sem quebra; 74 − 35 = 39", "SEGUE")]


def test_primeiro_bloco_maior_que_74_avanca_paginas_regra_4():
    assert _resumo(_decidir(100)) == [
        (3, 100, "100 > 34, primeiro bloco sem quebra; 74 − 100 = −26; −26 + 40 = 14", "SEGUE")
    ]


def test_fica_quando_tam_igual_ao_restante():
    assert _resumo(_decidir(30, 4))[1] == (1, 4, "4 − 4 = 0", "FICA")


def test_quebra_quando_tam_passa_do_restante_por_uma_linha():
    assert _resumo(_decidir(30, 5))[1] == (2, 5, "5 > 4; 40 − 5 = 35", "QUEBRA")


def test_quebra_com_bloco_de_pagina_inteira():
    assert _resumo(_decidir(30, 40))[1] == (2, 40, "40 > 4; 40 − 40 = 0", "QUEBRA")


def test_restante_zero_leva_o_proximo_bloco_para_nova_pagina():
    itens = _decidir(34, 1)
    assert _resumo(itens)[1] == (2, 1, "1 > 0; 40 − 1 = 39", "QUEBRA")


def test_segue_no_limite_restante_8():
    # 34 − 26 = 8; bloco 48 = 8 + 40 → SEGUE, termina exatamente na página seguinte.
    assert _resumo(_decidir(26, 48))[1] == (2, 48, "8 ≥ 8 e 48 ≤ 48; 48 − 48 = 0", "SEGUE")


def test_quebra_quando_restante_7_mesmo_com_bloco_maior_que_40():
    # 34 − 27 = 7 < 8 → QUEBRA: abre a página seguinte e termina na outra.
    assert _resumo(_decidir(27, 41))[1] == (3, 41, "41 > 7; 7 < 8; 80 − 41 = 39", "QUEBRA")


def test_quebra_quando_bloco_passa_de_restante_mais_40():
    # Restante 20, Tam 61 > 60 → QUEBRA.
    assert _resumo(_decidir(14, 61))[1] == (3, 61, "61 > 20; 61 > 60; 80 − 61 = 19", "QUEBRA")


def test_quebra_de_bloco_gigante_avanca_paginas_regra_4():
    item = _decidir(30, 130)[1]
    assert (item.pagina_inicio, item.pagina) == (2, 5)
    assert item.conta == "130 > 4; 4 < 8; 80 − 130 = −50; −50 + 40 = −10; −10 + 40 = 30"
    assert item.restante_novo == 30


def test_quebra_que_preenche_paginas_exatas_termina_com_restante_zero():
    item = _decidir(30, 120)[1]
    assert (item.pagina, item.restante_novo) == (4, 0)
    assert item.conta.endswith("80 − 120 = −40; −40 + 40 = 0")


def test_segue_maximo_no_restante_mais_40():
    # Restante 20 → SEGUE até Tam 60.
    assert _resumo(_decidir(14, 60))[1] == (2, 60, "20 ≥ 8 e 60 ≤ 60; 60 − 60 = 0", "SEGUE")


def test_lista_termina_com_item_de_imagens():
    assert texto_lista(_decidir(5), tem_imagens=True).splitlines()[-1] == "- `[INSERIR IMAGENS]` | QUEBRA"


@pytest.mark.parametrize("semente", range(300))
def test_sequencias_aleatorias_passam_na_conferencia_e_na_simulacao(semente):
    rnd = random.Random(semente)
    tams = [rnd.choice([rnd.randint(1, 12), rnd.randint(1, 40), rnd.randint(30, 140)]) for _ in range(rnd.randint(1, 25))]
    itens = _decidir(*tams)
    assert _verificar_lista(itens) == []
    for it in itens:
        assert it.restante_novo >= 0
        if it.resultado == "QUEBRA":
            assert it.tam > it.restante_anterior


def test_conferencia_detecta_quebra_com_espaco_sobrando():
    itens = _decidir(10, 5)
    adulterado = [itens[0], itens[1].__class__(**{**itens[1].__dict__, "resultado": "QUEBRA"})]
    assert any("quebra com espaço sobrando" in e for e in _verificar_lista(adulterado))


def test_conferencia_detecta_pagina_errada():
    itens = _decidir(30, 20)
    adulterado = [itens[0], itens[1].__class__(**{**itens[1].__dict__, "pagina": 3})]
    assert any("simulação indica" in e for e in _verificar_lista(adulterado))
