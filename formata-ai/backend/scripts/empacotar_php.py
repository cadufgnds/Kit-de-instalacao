"""Monta a versão PHP do Formata.AI para o hub: pasta pronta e arquivo .zip.

Uso (a partir de formata-ai/backend):  python scripts/empacotar_php.py
Saída:  formata-ai/entrega/formata-ai-php.zip  (contém a pasta formata-ai/)

A pasta junta a interface (frontend/) com a API e o motor em PHP (php/). O
.zip é determinístico: mesmos fontes, mesmo arquivo, byte a byte.
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FRONTEND = RAIZ / "frontend"
PHP = RAIZ / "php"
ZIP_SAIDA = RAIZ / "entrega" / "formata-ai-php.zip"
PASTA = "formata-ai"
DATA_FIXA = (2026, 1, 1, 0, 0, 0)

CABECALHO_INDEX = """<?php
// Formata.AI — página da ferramenta no hub. Gerado por backend/scripts/empacotar_php.py
// a partir de frontend/index.html; edite o original e gere o pacote de novo.
declare(strict_types=1);
require __DIR__ . '/nucleo/api.php';
FormataApi\\exigir_autenticacao();
header('Content-Type: text/html; charset=utf-8');
FormataApi\\cabecalhos_seguranca();
?>
"""

META_ORIGINAL = '<meta name="formata-api-extensao" content="">'
META_PHP = '<meta name="formata-api-extensao" content=".php">'


def arquivos_do_pacote() -> dict[str, bytes]:
    arquivos: dict[str, bytes] = {}
    for origem, pastas in ((FRONTEND, ("css", "js", "marca")), (PHP, ("api", "nucleo", "ferramentas"))):
        for pasta in pastas:
            for caminho in sorted((origem / pasta).rglob("*")):
                if caminho.is_file() and "__pycache__" not in caminho.parts:
                    arquivos[caminho.relative_to(origem).as_posix()] = caminho.read_bytes()
    arquivos["favicon.ico"] = (FRONTEND / "favicon.ico").read_bytes()
    for nome in ("config.php", ".htaccess", "LEIA-ME.txt"):
        arquivos[nome] = (PHP / nome).read_bytes()

    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    if META_ORIGINAL not in html:
        raise SystemExit("frontend/index.html não tem a meta formata-api-extensao esperada.")
    arquivos["index.php"] = (CABECALHO_INDEX + html.replace(META_ORIGINAL, META_PHP)).encode("utf-8")
    return dict(sorted(arquivos.items()))


def gerar_zip(arquivos: dict[str, bytes]) -> bytes:
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for nome, conteudo in arquivos.items():
            info = zipfile.ZipInfo(f"{PASTA}/{nome}", date_time=DATA_FIXA)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, conteudo)
    return memoria.getvalue()


def main() -> int:
    conteudo = gerar_zip(arquivos_do_pacote())
    ZIP_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    ZIP_SAIDA.write_bytes(conteudo)
    print(f"Pacote gravado em {ZIP_SAIDA} ({len(conteudo) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
