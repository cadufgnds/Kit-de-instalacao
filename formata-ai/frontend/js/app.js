// Formata.AI Web — interface. Todo o processamento acontece no servidor;
// esta página só envia a entrada, mostra os estados e apresenta o resultado.
// O conteúdo do documento nunca é inserido como HTML na página: tudo entra
// por textContent, e a pré-visualização roda num iframe isolado (sandbox).

const API = (document.querySelector('meta[name="formata-api"]')?.content || "").replace(/\/$/, "");
const EXTENSOES_PADRAO = [".md", ".markdown", ".txt", ".html", ".htm"];

const $ = (id) => document.getElementById(id);
const el = {
  formulario: $("formulario"),
  arquivo: $("arquivo"),
  zona: $("zona-arquivo"),
  escolhido: $("arquivo-escolhido"),
  arquivoNome: $("arquivo-nome"),
  arquivoTamanho: $("arquivo-tamanho"),
  removerArquivo: $("remover-arquivo"),
  texto: $("texto"),
  contador: $("contador"),
  botaoFormatar: $("botao-formatar"),
  botaoLimpar: $("botao-limpar"),
  area: $("area-resultado"),
  tituloResultado: $("t-resultado"),
  status: $("status"),
  statusTitulo: $("status-titulo"),
  statusTexto: $("status-texto"),
  statusErros: $("status-erros"),
  botaoTentar: $("botao-tentar"),
  painel: $("painel-resultado"),
  tabela: $("tabela-corpo"),
  saidaLista: $("saida-lista"),
  saidaHtml: $("saida-html"),
  saidaResposta: $("saida-resposta"),
  previa: $("previa"),
  anuncio: $("anuncio"),
};

const estado = {
  arquivo: null,
  resultado: null,
  processando: false,
  entradaDoResultado: null,
  config: { limite_bytes: 1048576, extensoes_aceitas: EXTENSOES_PADRAO, tempo_limite_segundos: 15 },
};

// ---------- Configuração do servidor ----------

async function carregarConfiguracao() {
  try {
    const [cfg, saude] = await Promise.all([
      fetch(`${API}/api/configuracao`).then((r) => (r.ok ? r.json() : null)),
      fetch(`${API}/api/saude`).then((r) => (r.ok ? r.json() : null)),
    ]);
    if (cfg) estado.config = cfg;
    if (saude) {
      $("versao-diretrizes").textContent = saude.versao_diretrizes;
      $("versao-app").textContent = `v${saude.versao}`;
    }
  } catch {
    // Sem configuração, valem os padrões; o servidor valida de novo de qualquer forma.
  }
  document.querySelectorAll("[data-limite-kb]").forEach((n) => {
    n.textContent = formatarNumero(Math.floor(estado.config.limite_bytes / 1024));
  });
  atualizarContador();
}

// ---------- Entrada ----------

const formatarNumero = (n) => n.toLocaleString("pt-BR");
const bytesUtf8 = (s) => new TextEncoder().encode(s).length;

function formatarTamanho(bytes) {
  if (bytes < 1024) return `${bytes} bytes`;
  return `${formatarNumero(Math.round(bytes / 102.4) / 10)} KB`;
}

function atualizarContador() {
  const n = el.texto.value.length;
  const excedido = bytesUtf8(el.texto.value) > estado.config.limite_bytes;
  el.contador.textContent = `${formatarNumero(n)} caractere${n === 1 ? "" : "s"}${excedido ? " — acima do limite" : ""}`;
  el.contador.classList.toggle("excedido", excedido);
}

function extensaoDe(nome) {
  const i = nome.lastIndexOf(".");
  return i >= 0 ? nome.slice(i).toLowerCase() : "";
}

function escolherArquivo(arquivo) {
  if (!arquivo) return;
  const extensao = extensaoDe(arquivo.name);
  if (extensao === ".docx" || extensao === ".doc") {
    mostrarErro("Formato não aceito", "Arquivos do Word ainda não são aceitos. Exporte o documento como .md ou .txt, ou cole o conteúdo.");
    el.arquivo.value = "";
    return;
  }
  if (!estado.config.extensoes_aceitas.includes(extensao)) {
    mostrarErro("Formato não aceito", `Envie um arquivo ${estado.config.extensoes_aceitas.join(", ")}.`);
    el.arquivo.value = "";
    return;
  }
  if (arquivo.size > estado.config.limite_bytes) {
    mostrarErro("Arquivo grande demais", `O arquivo tem ${formatarTamanho(arquivo.size)}; o limite é ${formatarTamanho(estado.config.limite_bytes)}.`);
    el.arquivo.value = "";
    return;
  }
  if (arquivo.size === 0) {
    mostrarErro("Arquivo vazio", "Envie o documento a ser formatado.");
    el.arquivo.value = "";
    return;
  }
  estado.arquivo = arquivo;
  el.arquivoNome.textContent = arquivo.name;
  el.arquivoTamanho.textContent = `(${formatarTamanho(arquivo.size)})`;
  el.escolhido.hidden = false;
  el.zona.classList.add("com-arquivo");
  el.texto.disabled = true;
  el.texto.setAttribute("aria-label", "Campo de texto desativado enquanto houver arquivo selecionado");
  marcarEntradaAlterada();
  anunciar(`Arquivo ${arquivo.name} selecionado.`);
}

function removerArquivo({ focar = true } = {}) {
  estado.arquivo = null;
  el.arquivo.value = "";
  el.escolhido.hidden = true;
  el.zona.classList.remove("com-arquivo");
  el.texto.disabled = false;
  el.texto.removeAttribute("aria-label");
  marcarEntradaAlterada();
  if (focar) el.arquivo.focus();
}

function assinaturaEntrada() {
  const modo = el.formulario.elements.modo.value;
  if (estado.arquivo) return `arquivo:${estado.arquivo.name}:${estado.arquivo.size}:${estado.arquivo.lastModified}:${modo}`;
  return `texto:${el.texto.value}:${modo}`;
}

function marcarEntradaAlterada() {
  if (estado.resultado && !estado.processando && assinaturaEntrada() !== estado.entradaDoResultado) {
    definirStatus("alerta", "A entrada mudou depois do último processamento",
      "O resultado abaixo corresponde à versão anterior. Selecione “Formatar documento” para processar a nova entrada.");
  } else if (estado.resultado && !estado.processando) {
    mostrarSucesso(estado.resultado);
  }
}

// ---------- Estados ----------

function definirStatus(tipo, titulo, texto, erros = [], podeTentar = false) {
  el.status.className = `status status--${tipo}`;
  el.statusTitulo.textContent = titulo;
  el.statusTexto.textContent = texto;
  el.statusErros.replaceChildren(...erros.map((e) => {
    const li = document.createElement("li");
    li.textContent = e;
    return li;
  }));
  el.statusErros.hidden = erros.length === 0;
  el.botaoTentar.hidden = !podeTentar;
}

function mostrarErro(titulo, texto, erros = [], podeTentar = false) {
  definirStatus("erro", titulo, texto, erros, podeTentar);
}

// Falha de processamento: o resultado anterior sai da tela para não passar por atual.
function descartarResultado() {
  estado.resultado = null;
  estado.entradaDoResultado = null;
  el.painel.hidden = true;
  el.tabela.replaceChildren();
  [el.saidaLista, el.saidaHtml, el.saidaResposta].forEach((n) => { n.textContent = ""; });
  el.previa.srcdoc = "";
}

function mostrarSucesso(r) {
  const quebras = r.itens.filter((i) => i.resultado === "QUEBRA").length + (r.tem_imagens ? 1 : 0);
  definirStatus("sucesso", "Documento formatado",
    `${r.itens.length} bloco${r.itens.length === 1 ? "" : "s"} em ${r.total_paginas_texto} página${r.total_paginas_texto === 1 ? "" : "s"} de texto, ` +
    `${quebras} quebra${quebras === 1 ? "" : "s"} de página. Todas as verificações de integridade foram aprovadas.`);
}

function definirProcessando(ativo) {
  estado.processando = ativo;
  el.botaoFormatar.disabled = ativo;
  el.botaoFormatar.textContent = ativo ? "Formatando…" : "Formatar documento";
  el.area.setAttribute("aria-busy", ativo ? "true" : "false");
  document.querySelectorAll("#botao-reprocessar, #botao-tentar").forEach((b) => { b.disabled = ativo; });
}

function anunciar(mensagem) {
  el.anuncio.textContent = "";
  window.setTimeout(() => { el.anuncio.textContent = mensagem; }, 50);
}

// ---------- Envio ----------

const MENSAGENS_HTTP = {
  413: "O documento passa do limite de tamanho aceito pelo servidor.",
  415: "Formato de arquivo não aceito.",
  429: "Muitas requisições em sequência. Aguarde alguns segundos e tente novamente.",
  502: "O servidor está indisponível no momento.",
  503: "O servidor está indisponível no momento.",
};

async function formatar() {
  if (estado.processando) return;
  const modo = el.formulario.elements.modo.value;
  if (!estado.arquivo) {
    if (!el.texto.value.trim()) {
      descartarResultado();
      mostrarErro("Nada para formatar", "Envie o documento a ser formatado.");
      el.texto.focus();
      return;
    }
    if (bytesUtf8(el.texto.value) > estado.config.limite_bytes) {
      descartarResultado();
      mostrarErro("Documento grande demais", `O limite é ${formatarTamanho(estado.config.limite_bytes)}.`);
      return;
    }
  }

  const assinatura = assinaturaEntrada();
  definirProcessando(true);
  definirStatus("carregando", "Processando no servidor…", "Calculando blocos, paginação e marcação HTML. O resultado aparece quando o servidor terminar.");
  el.tituloResultado.scrollIntoView({ behavior: "smooth", block: "start" });

  const controle = new AbortController();
  const prazo = window.setTimeout(() => controle.abort(), (estado.config.tempo_limite_segundos + 20) * 1000);
  try {
    let resposta;
    if (estado.arquivo) {
      const dados = new FormData();
      dados.append("arquivo", estado.arquivo);
      dados.append("modo", modo);
      resposta = await fetch(`${API}/api/formatar/arquivo`, { method: "POST", body: dados, signal: controle.signal });
    } else {
      resposta = await fetch(`${API}/api/formatar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: el.texto.value, modo }),
        signal: controle.signal,
      });
    }
    let corpo = null;
    try { corpo = await resposta.json(); } catch { /* resposta sem JSON */ }

    if (resposta.ok && corpo && corpo.ok === true) {
      estado.resultado = corpo;
      estado.entradaDoResultado = assinatura;
      apresentarResultado(corpo);
      mostrarSucesso(corpo);
      anunciar("Documento formatado. O resultado está disponível.");
      return;
    }
    descartarResultado();
    const mensagem = corpo?.mensagem || MENSAGENS_HTTP[resposta.status] || "O servidor não conseguiu processar o documento.";
    const titulo = corpo?.codigo === "falha_validacao" ? "Resultado não entregue: falhou nas verificações"
      : corpo?.codigo === "tempo_esgotado" ? "Tempo de processamento esgotado"
      : resposta.status >= 500 ? "Falha no processamento" : "Não foi possível formatar";
    mostrarErro(titulo, mensagem, corpo?.erros || [], resposta.status >= 500 || corpo?.codigo === "tempo_esgotado");
    anunciar(`${titulo}. ${mensagem}`);
  } catch (erro) {
    descartarResultado();
    const tempo = erro?.name === "AbortError";
    mostrarErro(tempo ? "Sem resposta do servidor" : "Não foi possível falar com o servidor",
      tempo ? "O servidor demorou demais para responder. Tente novamente."
        : "Verifique a conexão e tente novamente.", [], true);
    anunciar("Falha de comunicação com o servidor.");
  } finally {
    window.clearTimeout(prazo);
    definirProcessando(false);
  }
}

// ---------- Resultado ----------

function celula(texto, classe) {
  const td = document.createElement("td");
  td.textContent = texto;
  if (classe) td.className = classe;
  return td;
}

function selo(resultado) {
  const span = document.createElement("span");
  span.className = `selo selo--${resultado.toLowerCase()}`;
  span.textContent = resultado;
  return span;
}

const MOTIVOS = {
  linha_em_branco: "linha em branco",
  paragrafo_sem_texto: "parágrafo sem texto",
  rodape_confiabilidade: "rodapé de confiabilidade",
  linha_imagens_anterior: "linha de imagens de formatação anterior",
};

function preencherLista(id, itens) {
  const lista = $(id);
  lista.replaceChildren(...itens.map((t) => {
    const li = document.createElement("li");
    li.textContent = t;
    return li;
  }));
}

function apresentarResultado(r) {
  const linhas = r.itens.map((item) => {
    const tr = document.createElement("tr");
    tr.append(celula(String(item.pagina), "num"), celula(item.rotulo, "rotulo-bloco"), celula(String(item.tam), "num"), celula(item.conta, "conta"));
    const td = document.createElement("td");
    td.append(selo(item.resultado));
    tr.append(td);
    return tr;
  });
  if (r.tem_imagens) {
    const tr = document.createElement("tr");
    tr.className = "linha-imagens";
    tr.append(celula(String(r.total_paginas_texto + 1), "num"), celula("[INSERIR IMAGENS]", "rotulo-bloco"), celula("—", "num"), celula("abre a página de imagens, fora da conta", ""));
    const td = document.createElement("td");
    td.append(selo("QUEBRA"));
    tr.append(td);
    linhas.push(tr);
  }
  el.tabela.replaceChildren(...linhas);

  el.saidaLista.textContent = r.lista_paginacao;
  el.saidaHtml.textContent = r.html;
  el.saidaResposta.textContent = r.resposta;

  const quebras = r.itens.filter((i) => i.resultado === "QUEBRA").length + (r.tem_imagens ? 1 : 0);
  $("r-blocos").textContent = formatarNumero(r.itens.length);
  $("r-paginas").textContent = formatarNumero(r.total_paginas_texto);
  $("r-quebras").textContent = formatarNumero(quebras);
  $("r-imagens").textContent = r.tem_imagens ? "Sim" : "Não";
  $("r-removidas").textContent = formatarNumero(r.removidas.length);

  $("detalhes-avisos").hidden = r.avisos.length === 0;
  $("n-avisos").textContent = r.avisos.length;
  preencherLista("lista-avisos", r.avisos);

  $("detalhes-removidas").hidden = r.removidas.length === 0;
  $("n-removidas").textContent = r.removidas.length;
  preencherLista("lista-removidas", r.removidas.map((x) => {
    const motivo = MOTIVOS[x.motivo] || x.motivo;
    return x.texto.trim() ? `Linha ${x.numero} — ${motivo}: ${x.texto}` : `Linha ${x.numero} — ${motivo}`;
  }));

  montarPrevia(r.html);
  el.painel.hidden = false;
  selecionarAba($("aba-lista"), false);
}

const CSS_PREVIA = `
  body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; font-size: 15px; line-height: 1.5; color: #1c1424; margin: 0; padding: 24px 28px; }
  p { margin: 0 0 6px; white-space: pre-wrap; overflow-wrap: anywhere; }
  p.quebra-pagina { margin-top: 28px; padding-top: 30px; position: relative; }
  p.quebra-pagina::before { content: "Nova página"; position: absolute; left: -28px; right: -28px; top: 0; padding: 4px 28px;
    font: 700 11px/1.4 system-ui, sans-serif; letter-spacing: .08em; text-transform: uppercase; color: #fff; background: #660099; }
  img { display: none; }
`;

function montarPrevia(html) {
  // Iframe com sandbox vazio: sem scripts, sem formulários, origem isolada.
  // A CSP abaixo bloqueia também imagens e qualquer recurso externo citado no documento.
  el.previa.srcdoc = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">` +
    `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">` +
    `<style>${CSS_PREVIA}</style></head><body>${html}</body></html>`;
}

// ---------- Abas ----------

const abas = Array.from(document.querySelectorAll('[role="tab"]'));

function selecionarAba(aba, focar = true) {
  abas.forEach((a) => {
    const ativa = a === aba;
    a.setAttribute("aria-selected", String(ativa));
    a.tabIndex = ativa ? 0 : -1;
    $(a.getAttribute("aria-controls")).hidden = !ativa;
  });
  if (focar) aba.focus();
}

abas.forEach((aba, i) => {
  aba.addEventListener("click", () => selecionarAba(aba));
  aba.addEventListener("keydown", (e) => {
    const destino = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: abas.length - 1 }[e.key];
    if (destino === undefined) return;
    e.preventDefault();
    selecionarAba(abas[(destino + abas.length) % abas.length]);
  });
});

// ---------- Cópia ----------

async function copiarTexto(texto) {
  try {
    await navigator.clipboard.writeText(texto);
    return true;
  } catch {
    const area = document.createElement("textarea");
    area.value = texto;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.append(area);
    area.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch { ok = false; }
    area.remove();
    return ok;
  }
}

const ROTULOS_COPIA = { html: "HTML", lista: "Lista de paginação", resposta: "Resposta completa" };

document.addEventListener("click", async (e) => {
  const botao = e.target.closest("[data-copiar]");
  if (!botao || !estado.resultado) return;
  const tipo = botao.dataset.copiar;
  const texto = { html: estado.resultado.html, lista: estado.resultado.lista_paginacao, resposta: estado.resultado.resposta }[tipo];
  const ok = await copiarTexto(texto);
  const original = botao.dataset.rotulo || botao.textContent;
  botao.dataset.rotulo = original;
  botao.textContent = ok ? "Copiado!" : "Não foi possível copiar";
  botao.classList.toggle("copiado", ok);
  anunciar(ok ? `${ROTULOS_COPIA[tipo]} copiado para a área de transferência.` : "Não foi possível copiar. Selecione o texto e copie manualmente.");
  window.setTimeout(() => { botao.textContent = original; botao.classList.remove("copiado"); }, 2000);
});

// ---------- Limpar ----------

function limpar() {
  removerArquivo({ focar: false });
  el.texto.value = "";
  el.formulario.elements.modo.value = "auto";
  descartarResultado();
  atualizarContador();
  definirStatus("vazio", "Documento ainda não processado", "Envie um arquivo ou cole o conteúdo e selecione “Formatar documento”.");
  el.texto.focus();
  anunciar("Entrada e resultado limpos.");
}

// ---------- Eventos ----------

el.formulario.addEventListener("submit", (e) => { e.preventDefault(); formatar(); });
el.botaoTentar.addEventListener("click", formatar);
$("botao-reprocessar").addEventListener("click", formatar);
el.botaoLimpar.addEventListener("click", limpar);
$("botao-limpar-resultado").addEventListener("click", limpar);
el.texto.addEventListener("input", () => { atualizarContador(); marcarEntradaAlterada(); });
el.formulario.addEventListener("change", (e) => { if (e.target.name === "modo") marcarEntradaAlterada(); });
el.arquivo.addEventListener("change", () => escolherArquivo(el.arquivo.files[0]));
el.removerArquivo.addEventListener("click", () => removerArquivo());

["dragenter", "dragover"].forEach((tipo) => el.zona.addEventListener(tipo, (e) => {
  e.preventDefault();
  el.zona.classList.add("arrastando");
}));
["dragleave", "drop"].forEach((tipo) => el.zona.addEventListener(tipo, () => el.zona.classList.remove("arrastando")));
el.zona.addEventListener("drop", (e) => {
  e.preventDefault();
  const arquivo = e.dataTransfer?.files?.[0];
  if (arquivo) escolherArquivo(arquivo);
});
// Arquivo solto fora da área não deve abrir no navegador e descartar o que foi digitado.
["dragover", "drop"].forEach((tipo) => window.addEventListener(tipo, (e) => {
  if (!el.zona.contains(e.target)) e.preventDefault();
}));

carregarConfiguracao();
