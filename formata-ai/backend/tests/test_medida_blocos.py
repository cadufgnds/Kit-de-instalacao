"""Seções 5.1 (blocos) e 5.2 (medida)."""

import pytest

from formata import regras as R
from formata.blocos import custo_linha, delimitar_blocos
from formata.entrada import preparar


@pytest.mark.parametrize(
    "tamanho, custo",
    [(1, 1), (84, 1), (85, 1), (86, 2), (170, 2), (171, 3), (255, 3), (256, 4)],
)
def test_custo_caracteres_divididos_por_85_arredondado_para_cima(tamanho, custo):
    assert custo_linha("a" * tamanho) == custo


def test_custo_minimo_de_uma_linha():
    assert custo_linha("") == 1
    assert custo_linha("-") == 1


def test_custo_conta_a_linha_como_esta_com_marcas_markdown():
    # 83 letras + "**" = 85 → 1; 84 letras + "**" = 86 → 2
    assert custo_linha("**" + "a" * 83) == 1
    assert custo_linha("**" + "a" * 84) == 2
    assert custo_linha("### " + "a" * 82) == 2


def test_custo_conta_caracteres_acentuados_como_um():
    assert custo_linha("ç" * 85) == 1
    assert custo_linha("ã" * 86) == 2


def _blocos(texto):
    entrada = preparar(texto)
    return [(b.rotulo, b.tam, [l.texto for l in b.linhas]) for b in delimitar_blocos(entrada.linhas)]


def test_cada_cabecalho_abre_bloco_ate_o_proximo():
    blocos = _blocos("### A\na1\n### B\nb1\nb2\n## C\nc1")
    assert [(r, t) for r, t, _ in blocos] == [("### A", 2), ("### B", 3), ("## C", 2)]


def test_colagem_encadeada_titulo_macrossecao_primeiro_topico():
    texto = "# Doc\n## 1. Seção\n### 1.1 Tópico\ntexto\n### 1.2 Tópico\ntexto"
    blocos = _blocos(texto)
    assert [(r, t) for r, t, _ in blocos] == [("# Doc", 4), ("### 1.2 Tópico", 2)]


def test_colagem_so_quando_o_seguinte_e_mais_profundo():
    blocos = _blocos("## A\n## B\n### B1\n# C\n### C1")
    assert [r for r, _, _ in blocos] == ["## A", "## B", "# C"]


def test_colagem_com_texto_entre_cabecalhos_consecutivos():
    # Decisão D3: o cabeçalho seguinte mais profundo cola mesmo com texto entre eles.
    blocos = _blocos("## Seção\nIntrodução.\n### Tópico\ncorpo")
    assert len(blocos) == 1


def test_colagem_somente_adjacentes_quando_configurado(monkeypatch):
    monkeypatch.setattr(R, "COLAGEM_SOMENTE_ADJACENTES", True)
    assert len(_blocos("## Seção\nIntrodução.\n### Tópico\ncorpo")) == 2
    assert len(_blocos("## Seção\n### Tópico\ncorpo")) == 1


def test_linhas_antes_do_primeiro_cabecalho_pertencem_ao_primeiro_bloco():
    blocos = _blocos("Preâmbulo.\nMais preâmbulo.\n# Título\ntexto\n# Outro\nx")
    assert blocos[0][:2] == ("# Título", 4)
    assert blocos[1][:2] == ("# Outro", 2)


def test_documento_sem_cabecalho_e_um_bloco_so():
    blocos = _blocos("um\ndois\ntrês")
    assert len(blocos) == 1 and blocos[0][1] == 3


@pytest.mark.parametrize("linha", ["#### Subtópico", "##### Cinco", "**Negrito**", "- item", "| a | b |", "---"])
def test_linhas_que_nunca_abrem_bloco(linha):
    blocos = _blocos(f"### A\ntexto\n{linha}\nmais")
    assert len(blocos) == 1 and blocos[0][1] == 4


def test_cabecalho_dentro_de_bloco_de_codigo_nao_abre_bloco():
    blocos = _blocos("### A\n```bash\n# comentário\n## outro\n```\n### B")
    assert [r for r, _, _ in blocos] == ["### A", "### B"]
    assert blocos[0][1] == 5


def test_titulo_exige_espaco_depois_dos_sustenidos():
    assert len(_blocos("### A\n#SemEspaço\n### B")) == 2
