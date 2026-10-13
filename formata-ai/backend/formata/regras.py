"""Constantes normativas das Diretrizes Formata.AI v2.6.

Este módulo concentra todos os números, textos e padrões que o motor usa.
Os valores das seções 5.2, 5.3, 5.5 e 5.6 são fixos: alterá-los muda a
paginação e exige nova validação contra as diretrizes.

As constantes marcadas como "Decisão de interpretação" cobrem pontos em que
as diretrizes não descem ao detalhe; cada uma está descrita em
docs/REGRAS.md (seção "Decisões de interpretação") com a regra de origem.
"""

import re

# --- Seção 5.2 — Medida -----------------------------------------------------
LIMITE_PAGINA_1 = 34
LIMITE_DEMAIS_PAGINAS = 40
CARACTERES_POR_LINHA = 85

# --- Seção 5.3 — Decisão ----------------------------------------------------
RESTANTE_MINIMO_SEGUE = 8

FICA = "FICA"
QUEBRA = "QUEBRA"
SEGUE = "SEGUE"

# --- Seções 5.5 e 5.6 — Marcação ---------------------------------------------
ATRIBUTOS_QUEBRA = 'class="quebra-pagina" style="page-break-before: always;"'
P_ABRE = "<p>"
P_ABRE_QUEBRA = f"<p {ATRIBUTOS_QUEBRA}>"
P_FECHA = "</p>"
STRONG_ABRE = "<strong>"
STRONG_FECHA = "</strong>"

TEXTO_LINHA_IMAGENS = "[INSERIR IMAGENS]"
LINHA_IMAGENS = f"{P_ABRE_QUEBRA}{STRONG_ABRE}{TEXTO_LINHA_IMAGENS}{STRONG_FECHA}{P_FECHA}"

# --- Seção 7 — Casos excepcionais --------------------------------------------
MENSAGEM_DOCUMENTO_VAZIO = "Envie o documento a ser formatado."

# --- Seção 3 — Títulos (ATX com 1 a 4 "#", espaço e texto) -------------------
RE_TITULO = re.compile(r"^(#{1,4})[ \t]+\S")
# Cabeçalhos que abrem bloco de paginação (seção 5.1).
NIVEL_MAXIMO_BLOCO = 3

# --- Seção 3 — Negrito -------------------------------------------------------
RE_NEGRITO = re.compile(r"\*\*(.+?)\*\*")

# Decisão de interpretação D4: `**` dentro de código não é negrito.
NEGRITO_EM_CODIGO = False

# Decisão de interpretação D3 (validada): a colagem da seção 5.1 só vale quando
# o cabeçalho mais profundo vem na linha imediatamente seguinte (linhas em
# branco não contam). Com texto entre eles, cada cabeçalho abre o próprio bloco.
COLAGEM_SOMENTE_ADJACENTES = True

# --- Marcação HTML reconhecida no conteúdo ----------------------------------
RE_STRONG_TAG = re.compile(r"</?strong\s*>", re.IGNORECASE)
# Repetições limitadas ({0,N}) evitam tempo quadrático em entradas malformadas.
RE_P_ABERTURA = re.compile(r"<p(\s[^<>]{0,2000})?>", re.IGNORECASE)
RE_P_FECHAMENTO = re.compile(r"</p\s{0,20}>", re.IGNORECASE)
RE_SEM_TEXTO = re.compile(r"&nbsp;|&#160;|&#x0*a0;|<br\s*/?>", re.IGNORECASE)
RE_TAG_QUALQUER = re.compile(r"</?[A-Za-z][^<>]{0,2000}>")

# --- Blocos de código (Markdown) --------------------------------------------
RE_CERCA = re.compile(r"^ {0,3}(`{3,}|~{3,})")
RE_CODIGO_INLINE = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")

# --- Seção 5.6 — Imagens -----------------------------------------------------
# Decisão de interpretação D6: só padrões explícitos ("na dúvida, não acrescentar").
_MARCADOR = (
    r"!\[[^\[\]\n]{0,500}\]\([^()\n]{0,2000}\)"  # imagem Markdown
    r"|<img\b[^<>]{0,2000}>"  # imagem HTML
    r"|\[[ \t]{0,10}(?:imagem|imagens|images?|img|figuras?|fig\.?|prints?|capturas? de tela"
    r"|screenshots?|fotos?|ilustra[çc](?:ão|ões|ao|oes))\b[^\[\]\n]{0,300}\]"
)
RE_MARCADOR_IMAGEM = re.compile(_MARCADOR, re.IGNORECASE)
RE_LINHA_SO_MARCADORES = re.compile(rf"^\s*(?:(?:{_MARCADOR})\s*)+$", re.IGNORECASE)

# --- Seção 4 — Rodapé de confiabilidade --------------------------------------
# Decisão de interpretação D5. A linha só é rodapé quando cita a
# confiabilidade/validade E se refere ao próprio documento, sem traço de
# conteúdo procedimental. Na dúvida, a linha fica (seção 7, "o que menos
# altera o texto").
RODAPE_JANELA = 3
RE_RODAPE_CONFIABILIDADE = re.compile(
    r"confiabilidade|confi[áa]vel|validade|v[áa]lid[oa]s?\b|vig[êe]ncia|vigente"
    r"|desatualizad|n[ãa]o\s+controlad|c[óo]pia\s+controlada|obsolet",
    re.IGNORECASE,
)
RE_RODAPE_DOCUMENTO = re.compile(
    r"documento|material|conte[úu]do|c[óo]pia|vers[ãa]o|impress[oa]|impress[ãa]o|publica[çc][ãa]o",
    re.IGNORECASE,
)
RE_RODAPE_PROCEDIMENTO = re.compile(
    r"\b(?:clientes?|titular|cpf|rg|cnh|fatura|oferta|plano|pedido|protocolo|contrato"
    r"|clique|acesse|selecione|digite|informe|registre|preencha|solicite|oriente|abra)\b",
    re.IGNORECASE,
)
RODAPE_TAMANHO_MAXIMO = 300

# --- Limites operacionais (configuráveis por ambiente na API) ----------------
LIMITE_CARACTERES_PADRAO = 1_000_000
LIMITE_LINHAS_PADRAO = 20_000
