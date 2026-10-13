"""Testes de ponta a ponta da landing page num navegador real (Playwright + Chromium).

São pulados quando o Playwright ou o Chromium não estão disponíveis.
Variáveis opcionais:
    FORMATA_CHROMIUM   caminho do executável do Chromium
    FORMATA_AXE_JS     caminho do axe.min.js (axe-core) para a auditoria de acessibilidade
    FORMATA_CAPTURAS   pasta onde gravar capturas de tela do fluxo
"""

import glob
import os
import socket
import threading
import time
from pathlib import Path

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
uvicorn = pytest.importorskip("uvicorn")

from formata import formatar  # noqa: E402
from servidor.app import criar_app  # noqa: E402
from servidor.config import Configuracao  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "kit_unico_v13.md"
CAPTURAS = os.environ.get("FORMATA_CAPTURAS")


def _chromium():
    if os.environ.get("FORMATA_CHROMIUM"):
        return os.environ["FORMATA_CHROMIUM"]
    candidatos = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
    return candidatos[-1] if candidatos else None


@pytest.fixture(scope="module")
def url_base():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    app = criar_app(Configuracao(isolamento="processo", limite_bytes=200_000))
    servidor = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=porta, log_level="warning"))
    thread = threading.Thread(target=servidor.run, daemon=True)
    thread.start()
    for _ in range(100):
        if servidor.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{porta}/"
    servidor.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(scope="module")
def navegador():
    with playwright_api.sync_playwright() as p:
        try:
            nav = p.chromium.launch(executable_path=_chromium())
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"Chromium indisponível: {exc}")
        yield nav
        nav.close()


@pytest.fixture
def pagina(navegador, url_base):
    contexto = navegador.new_context(viewport={"width": 1366, "height": 900})
    contexto.grant_permissions(["clipboard-read", "clipboard-write"], origin=url_base.rstrip("/"))
    pg = contexto.new_page()
    pg.erros_console = []
    pg.on("console", lambda m: pg.erros_console.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: pg.erros_console.append(str(e)))
    pg.goto(url_base)
    pg.wait_for_load_state("networkidle")
    yield pg
    contexto.close()


def _capturar(pg, nome, pagina_inteira=True):
    # Iframes isolados (sandbox) saem distorcidos na captura de página inteira do Chromium;
    # para a pré-visualização, use a captura da área visível.
    if CAPTURAS:
        Path(CAPTURAS).mkdir(parents=True, exist_ok=True)
        pg.screenshot(path=str(Path(CAPTURAS) / f"{nome}.jpg"), full_page=pagina_inteira, type="jpeg", quality=70)


def _formatar(pg, texto):
    pg.fill("#texto", texto)
    pg.click("#botao-formatar")
    pg.wait_for_selector(".status--sucesso, .status--erro", timeout=20_000)


def test_estado_inicial_deixa_claro_que_nada_foi_processado(pagina):
    assert pagina.inner_text("#status-titulo") == "Documento ainda não processado"
    assert pagina.is_hidden("#painel-resultado")
    assert pagina.is_hidden("#botao-tentar")
    assert pagina.inner_text("#versao-diretrizes") == "2.6"
    assert pagina.erros_console == []
    _capturar(pagina, "01-inicio")


def test_fluxo_completo_texto_colado(pagina):
    texto = FIXTURE.read_text(encoding="utf-8")[:8000] + "\n[Imagem 1]"
    esperado = formatar(texto)
    pagina.fill("#texto", texto)
    pagina.click("#botao-formatar")
    # O estado de processamento aparece antes do resultado.
    pagina.wait_for_selector(".status--carregando, .status--sucesso")
    pagina.wait_for_selector(".status--sucesso", timeout=20_000)

    assert pagina.is_visible("#painel-resultado")
    linhas = pagina.locator("#tabela-corpo tr")
    assert linhas.count() == len(esperado.itens) + 1  # + linha [INSERIR IMAGENS]
    assert pagina.inner_text("#saida-lista") == esperado.lista_paginacao
    assert pagina.locator("#saida-html").text_content() == esperado.html
    assert pagina.locator("#saida-resposta").text_content() == esperado.resposta
    assert pagina.inner_text("#r-blocos") == str(len(esperado.itens))
    primeira = linhas.nth(0).locator("td")
    assert [primeira.nth(i).inner_text() for i in (0, 2, 4)] == [
        str(esperado.itens[0].pagina), str(esperado.itens[0].tam), esperado.itens[0].resultado
    ]
    _capturar(pagina, "02-resultado")

    pagina.click("#aba-previa")
    quadro = pagina.frame_locator("#previa")
    assert quadro.locator("p.quebra-pagina").count() == pagina.locator("#saida-html").text_content().count("quebra-pagina")
    pagina.evaluate("window.scrollTo({top: document.querySelector('.abas').getBoundingClientRect().top + scrollY - 160, behavior: 'instant'})")
    _capturar(pagina, "03-previa", pagina_inteira=False)
    assert pagina.erros_console == []


def test_copiar_html_para_a_area_de_transferencia(pagina):
    _formatar(pagina, "# T\ntexto **b**")
    pagina.click("#botao-copiar-html")
    assert pagina.evaluate("navigator.clipboard.readText()") == formatar("# T\ntexto **b**").html
    playwright_api.expect(pagina.locator("#anuncio")).to_contain_text("copiado")


def test_envio_de_arquivo(pagina, tmp_path):
    arquivo = tmp_path / "procedimento.md"
    arquivo.write_text("# Procedimento\n## Passo\nTexto do passo.", encoding="utf-8")
    pagina.set_input_files("#arquivo", str(arquivo))
    assert pagina.inner_text("#arquivo-nome") == "procedimento.md"
    assert pagina.is_disabled("#texto")
    pagina.click("#botao-formatar")
    pagina.wait_for_selector(".status--sucesso", timeout=20_000)
    assert pagina.locator("#saida-html").text_content() == formatar(arquivo.read_text(encoding="utf-8")).html
    pagina.click("#remover-arquivo")
    assert pagina.is_enabled("#texto")


def test_arquivo_de_formato_nao_aceito_e_recusado_no_navegador(pagina, tmp_path):
    arquivo = tmp_path / "documento.docx"
    arquivo.write_bytes(b"PK\x03\x04")
    pagina.set_input_files("#arquivo", str(arquivo))
    assert "status--erro" in pagina.get_attribute("#status", "class")
    assert "Word" in pagina.inner_text("#status-texto")
    assert pagina.is_hidden("#arquivo-escolhido")


def test_erro_do_servidor_e_exibido_com_opcao_de_tentar_de_novo(pagina, tmp_path):
    arquivo = tmp_path / "latin1.md"
    arquivo.write_bytes("ação".encode("latin-1"))
    pagina.set_input_files("#arquivo", str(arquivo))
    pagina.click("#botao-formatar")
    pagina.wait_for_selector(".status--erro", timeout=20_000)
    assert "UTF-8" in pagina.inner_text("#status-texto")
    assert pagina.is_hidden("#painel-resultado")


def test_documento_vazio_nao_e_enviado(pagina):
    requisicoes = []
    pagina.on("request", lambda r: requisicoes.append(r.url) if "/api/formatar" in r.url else None)
    pagina.fill("#texto", "   \n  ")
    pagina.click("#botao-formatar")
    assert pagina.inner_text("#status-texto") == "Envie o documento a ser formatado."
    assert requisicoes == []


def test_erro_depois_de_resultado_nao_deixa_resultado_antigo_na_tela(pagina):
    _formatar(pagina, "# T\ntexto")
    assert pagina.is_visible("#painel-resultado")
    pagina.fill("#texto", "")
    pagina.click("#botao-formatar")
    assert pagina.is_hidden("#painel-resultado")


def test_entrada_alterada_depois_do_resultado_e_sinalizada(pagina):
    _formatar(pagina, "# T\ntexto")
    pagina.fill("#texto", "# T\ntexto alterado")
    assert "status--alerta" in pagina.get_attribute("#status", "class")
    pagina.fill("#texto", "# T\ntexto")
    assert "status--sucesso" in pagina.get_attribute("#status", "class")


def test_conteudo_malicioso_nao_executa_nem_entra_no_dom(pagina):
    texto = '# T\n<script>window.__invadido = 1</script>\n<img src=x onerror="window.__invadido = 2">\n**b**'
    _formatar(pagina, texto)
    pagina.click("#aba-previa")
    pagina.wait_for_timeout(300)
    assert pagina.evaluate("window.__invadido") is None
    assert pagina.evaluate("document.querySelectorAll('body img, body script:not([type=module])').length") == 0
    assert "<script>" in pagina.locator("#saida-html").text_content()  # exibido como texto
    # Os únicos erros de console permitidos são os próprios bloqueios (sandbox ou CSP).
    assert all("Blocked" in e or "Content Security Policy" in e for e in pagina.erros_console)


def test_navegacao_so_por_teclado(pagina):
    pagina.focus("#texto")
    pagina.keyboard.type("# Título\ntexto")
    for _ in range(12):
        pagina.keyboard.press("Tab")
        if pagina.evaluate("document.activeElement.id") == "botao-formatar":
            break
    assert pagina.evaluate("document.activeElement.id") == "botao-formatar"
    pagina.keyboard.press("Enter")
    pagina.wait_for_selector(".status--sucesso", timeout=20_000)
    pagina.focus("#aba-lista")
    pagina.keyboard.press("ArrowRight")
    assert pagina.evaluate("document.activeElement.id") == "aba-html"
    assert pagina.is_visible("#painel-html") and pagina.is_hidden("#painel-lista")


def test_limpar_volta_ao_estado_inicial(pagina):
    _formatar(pagina, "# T\ntexto")
    pagina.click("#botao-limpar-resultado")
    assert pagina.input_value("#texto") == ""
    assert pagina.is_hidden("#painel-resultado")
    assert pagina.inner_text("#status-titulo") == "Documento ainda não processado"


@pytest.mark.parametrize("largura", [390, 768, 1366])
def test_sem_rolagem_horizontal(navegador, url_base, largura):
    pg = navegador.new_page(viewport={"width": largura, "height": 900})
    pg.goto(url_base)
    _formatar(pg, FIXTURE.read_text(encoding="utf-8")[:6000])
    assert pg.evaluate("document.documentElement.scrollWidth") <= largura
    if largura == 390:
        _capturar(pg, "04-celular")
    pg.close()


@pytest.mark.skipif(not os.environ.get("FORMATA_AXE_JS"), reason="FORMATA_AXE_JS não definido")
@pytest.mark.parametrize("largura", [390, 1366])
def test_acessibilidade_axe_sem_violacoes(navegador, url_base, largura):
    axe = Path(os.environ["FORMATA_AXE_JS"]).read_text(encoding="utf-8")
    contexto = navegador.new_context(viewport={"width": largura, "height": 900}, bypass_csp=True)
    pg = contexto.new_page()
    pg.goto(url_base)
    regras = "{runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']}}"

    def violacoes():
        pg.evaluate(axe)
        return pg.evaluate(f"axe.run(document, {regras}).then(r => r.violations.map(v => v.id + ': ' + v.nodes.length))")

    assert violacoes() == []
    _formatar(pg, "# T\ntexto\n## A\n**b**\n[Imagem 1]")
    assert violacoes() == []
    pg.click("#aba-html")
    assert violacoes() == []
    pg.fill("#texto", "")
    pg.click("#botao-formatar")
    assert violacoes() == []
    contexto.close()
