"""Versão PHP para o hub: API, página, login do hub e fluxo no navegador.

Monta um hub de teste (login em PHP + pasta formata-ai extraída do pacote
entrega/formata-ai-php.zip) e testa contra:
  - o servidor embutido do PHP (padrão), ou
  - um servidor já em execução: FORMATA_HUB_URL=http://host:porta e
    FORMATA_HUB_DIR=<pasta servida como /hub> (ex.: Apache + PHP 7.4 em contêiner).
Pulado quando o executável `php` não está disponível.
"""

import os
import shutil
import socket
import subprocess
import time
import zipfile
from pathlib import Path

import httpx
import pytest

from formata import formatar

PHP = shutil.which("php")
RAIZ = Path(__file__).resolve().parents[2]
ZIP = RAIZ / "entrega" / "formata-ai-php.zip"
FIXTURE = Path(__file__).parent / "fixtures" / "kit_unico_v13.md"

pytestmark = pytest.mark.skipif(PHP is None and not os.environ.get("FORMATA_HUB_URL"), reason="php não instalado")

VERIFICA_LOGIN = """<?php
if (session_status() !== PHP_SESSION_ACTIVE) { session_start(); }
if (empty($_SESSION['usuario'])) { header('Location: /hub/login.php'); exit; }
"""
LOGIN = """<?php
session_start();
if (isset($_GET['entrar'])) { $_SESSION['usuario'] = 'teste'; echo 'logado'; exit; }
echo '<html><body><h1>Login do hub</h1></body></html>';
"""


def _montar_hub(pasta: Path) -> None:
    (pasta / "includes").mkdir(parents=True, exist_ok=True)
    (pasta / "includes" / "verifica-login.php").write_text(VERIFICA_LOGIN, encoding="utf-8")
    (pasta / "login.php").write_text(LOGIN, encoding="utf-8")
    (pasta / "index.php").write_text('<?php echo "dashboard do hub";', encoding="utf-8")
    shutil.rmtree(pasta / "formata-ai", ignore_errors=True)
    with zipfile.ZipFile(ZIP) as zf:
        zf.extractall(pasta)
    for caminho in pasta.rglob("*"):
        caminho.chmod(0o755 if caminho.is_dir() else 0o644)


@pytest.fixture(scope="module")
def hub(tmp_path_factory):
    """(url base do hub, pasta do hub)."""
    if os.environ.get("FORMATA_HUB_URL"):
        pasta = Path(os.environ["FORMATA_HUB_DIR"])
        _montar_hub(pasta)
        yield os.environ["FORMATA_HUB_URL"].rstrip("/") + "/hub", pasta
        return
    raiz = tmp_path_factory.mktemp("servidor")
    pasta = raiz / "hub"
    _montar_hub(pasta)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    proc = subprocess.Popen(
        # Sem opcache: os testes reescrevem config.php com o servidor no ar.
        [PHP, "-d", "memory_limit=256M", "-d", "opcache.enable=0", "-S", f"127.0.0.1:{porta}", "-t", str(raiz)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{porta}"
    for _ in range(100):
        try:
            httpx.get(url + "/hub/index.php", timeout=0.5)
            break
        except httpx.HTTPError:
            time.sleep(0.05)
    yield url + "/hub", pasta
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture
def api(hub):
    url, _ = hub
    with httpx.Client(base_url=url + "/formata-ai/", timeout=30) as cliente:
        yield cliente


def _configurar(pasta: Path, **valores) -> None:
    config = pasta / "formata-ai" / "config.php"
    linhas = ["<?php", "return ["]
    for chave, valor in valores.items():
        linhas.append(f"    '{chave}' => {valor!r},".replace("True", "true").replace("False", "false"))
    linhas.append("];")
    config.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def _esperar_opcache():
    # Num servidor externo, o opcache pode levar até 2 s para reler config.php.
    if os.environ.get("FORMATA_HUB_URL"):
        time.sleep(3)


@pytest.fixture
def com_login(hub):
    _, pasta = hub
    _configurar(pasta, arquivo_autenticacao="../includes/verifica-login.php")
    _esperar_opcache()
    yield
    _configurar(pasta, arquivo_autenticacao="")
    _esperar_opcache()


def test_saude_e_configuracao(api):
    assert api.get("api/saude.php").json() == {"status": "ok", "versao": "0.3.0", "versao_diretrizes": "2.6"}
    cfg = api.get("api/configuracao.php").json()
    assert cfg["limite_bytes"] == 1048576 and ".md" in cfg["extensoes_aceitas"]


@pytest.mark.parametrize(
    "texto",
    [
        "# Título\nTexto com **negrito**.\n[Imagem 1]",
        "# T\ntexto\nDocumento válido somente na versão eletrônica.",
        "<p><strong>Atenção:</strong> use **isto**.</p>",
        "## Doc\n" + "\n".join(f"linha {i}" for i in range(60)) + "\n## B\n" + "\n".join(f"b {i}" for i in range(30)),
    ],
)
def test_formatar_igual_ao_motor_de_referencia(api, texto):
    r = api.post("api/formatar.php", json={"texto": texto})
    assert r.status_code == 200
    assert r.json() == formatar(texto).como_dict() | {"versao_diretrizes": "2.6"}
    assert r.headers["cache-control"] == "no-store"


def test_documento_real(api):
    texto = FIXTURE.read_text(encoding="utf-8")
    corpo = api.post("api/formatar.php", json={"texto": texto, "modo": "auto"}).json()
    assert corpo["html"] == formatar(texto).html


@pytest.mark.parametrize("texto", ["", "  \n", "<p></p>"])
def test_documento_vazio(api, texto):
    r = api.post("api/formatar.php", json={"texto": texto})
    assert r.status_code == 400 and r.json()["mensagem"] == "Envie o documento a ser formatado."


@pytest.mark.parametrize("corpo", [b"{texto", b'{"outro": 1}', b'{"texto": 5}', b'{"texto": "x", "modo": "word"}', b"[]"])
def test_requisicao_invalida(api, corpo):
    r = api.post("api/formatar.php", content=corpo, headers={"content-type": "application/json"})
    assert r.status_code == 400 and r.json()["codigo"] == "requisicao_invalida"


def test_metodo_errado_405(api):
    r = api.get("api/formatar.php")
    assert r.status_code == 405 and r.json()["codigo"] == "metodo_nao_permitido"


def test_corpo_grande_demais_413(api):
    r = api.post("api/formatar.php", content=b"x" * (2 * 1048576 + 70000), headers={"content-type": "application/json"})
    assert r.status_code == 413


def test_arquivo_markdown(api):
    texto = "# A\n**b**\n[Imagem 1]"
    r = api.post("api/formatar/arquivo.php", files={"arquivo": ("doc.md", texto.encode(), "text/markdown")})
    assert r.status_code == 200 and r.json()["html"] == formatar(texto).html


@pytest.mark.parametrize(
    "nome, conteudo, status, codigo",
    [
        ("doc.docx", b"PK\x03\x04conteudo", 415, "tipo_nao_suportado"),
        ("doc.pdf", b"%PDF-1.7", 415, "tipo_nao_suportado"),
        ("doc.md", "ação".encode("latin-1"), 400, "entrada_invalida"),
        ("doc.txt", b"abc\x00def", 400, "entrada_invalida"),
        ("doc.md", b"   ", 400, "documento_vazio"),
    ],
)
def test_arquivos_invalidos(api, nome, conteudo, status, codigo):
    r = api.post("api/formatar/arquivo.php", files={"arquivo": (nome, conteudo, "application/octet-stream")})
    assert r.status_code == status and r.json()["codigo"] == codigo


def test_multipart_sem_arquivo_e_modo_invalido(api):
    assert api.post("api/formatar/arquivo.php", data={"modo": "auto"}).json()["codigo"] == "requisicao_invalida"
    r = api.post("api/formatar/arquivo.php", files={"arquivo": ("d.md", b"x", "text/plain")}, data={"modo": "x"})
    assert r.json()["codigo"] == "modo_invalido"


def test_pagina_do_hub(api):
    r = api.get("")
    assert r.status_code == 200 and "Seu documento pronto para publicação." in r.text
    assert '<meta name="formata-api-extensao" content=".php">' in r.text
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert not r.text.startswith("<?php")


def test_login_do_hub_e_exigido_quando_configurado(hub, com_login):
    url, _ = hub
    with httpx.Client(base_url=url, timeout=30) as cliente:
        sem_login = cliente.post("/formata-ai/api/formatar.php", json={"texto": "# T"})
        assert sem_login.status_code == 302 and sem_login.headers["location"] == "/hub/login.php"
        assert cliente.get("/formata-ai/").status_code == 302
        cliente.get("/login.php", params={"entrar": 1})
        com_sessao = cliente.post("/formata-ai/api/formatar.php", json={"texto": "# T\ntexto"})
        assert com_sessao.status_code == 200 and com_sessao.json()["ok"] is True


# --- Navegador -----------------------------------------------------------------------------

playwright_api = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def navegador():
    import glob

    caminho = os.environ.get("FORMATA_CHROMIUM") or (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")) or [None])[-1]
    with playwright_api.sync_playwright() as p:
        try:
            nav = p.chromium.launch(executable_path=caminho)
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"Chromium indisponível: {exc}")
        yield nav
        nav.close()


def test_fluxo_completo_no_navegador(hub, navegador):
    url, _ = hub
    pg = navegador.new_page()
    erros = []
    pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
    pg.goto(url + "/formata-ai/")
    playwright_api.expect(pg.locator("#versao-app")).to_have_text("v0.3.0")
    texto = FIXTURE.read_text(encoding="utf-8")[:6000] + "\n[Imagem 1]"
    pg.fill("#texto", texto)
    pg.click("#botao-formatar")
    pg.wait_for_selector(".status--sucesso, .status--erro", timeout=20_000)
    assert "status--sucesso" in pg.get_attribute("#status", "class"), pg.inner_text("#status")
    assert pg.locator("#saida-html").text_content() == formatar(texto).html
    assert erros == []
    pg.close()


def test_sessao_expirada_e_explicada_no_navegador(hub, navegador, com_login):
    url, _ = hub
    contexto = navegador.new_context()
    pg = contexto.new_page()
    pg.goto(url + "/login.php?entrar=1")
    pg.goto(url + "/formata-ai/")
    pg.wait_for_load_state("networkidle")
    contexto.clear_cookies()  # sessão expira com a página aberta
    pg.fill("#texto", "# T\ntexto")
    pg.click("#botao-formatar")
    playwright_api.expect(pg.locator("#status-titulo")).to_have_text("Sessão do hub encerrada")
    contexto.close()
