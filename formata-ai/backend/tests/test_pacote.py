"""O pacote para o hub (entrega/formata-ai-php.zip) precisa estar em dia com os fontes."""

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import empacotar_php  # noqa: E402


def test_zip_do_hub_corresponde_aos_fontes():
    esperado = empacotar_php.gerar_zip(empacotar_php.arquivos_do_pacote())
    assert empacotar_php.ZIP_SAIDA.read_bytes() == esperado, (
        "O pacote está desatualizado: rode  python scripts/empacotar_php.py  e faça o commit do .zip."
    )


def test_zip_tem_a_pasta_completa_e_sem_arquivos_de_desenvolvimento():
    nomes = set(zipfile.ZipFile(empacotar_php.ZIP_SAIDA).namelist())
    obrigatorios = {
        "formata-ai/index.php", "formata-ai/config.php", "formata-ai/.htaccess", "formata-ai/LEIA-ME.txt",
        "formata-ai/api/saude.php", "formata-ai/api/configuracao.php", "formata-ai/api/formatar.php",
        "formata-ai/api/formatar/arquivo.php", "formata-ai/nucleo/formata.php", "formata-ai/nucleo/api.php",
        "formata-ai/nucleo/.htaccess", "formata-ai/js/app.js", "formata-ai/css/app.css",
        "formata-ai/marca/marca.css", "formata-ai/favicon.ico",
    }
    assert obrigatorios <= nomes
    assert not [n for n in nomes if "__pycache__" in n or n.endswith((".py", ".pyc"))]
