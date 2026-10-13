# Regras de processamento implementadas

Fonte oficial: **Formata.AI — Diretrizes v2.6** (`Formata.AI-diretrizes-v2.6.md`). O arquivo não está neste repositório porque o repositório é público e a seção 6 das diretrizes proíbe reproduzi-las. Este documento cita as seções pelo número e descreve como cada uma foi implementada.

O motor é determinístico, sem IA generativa: o mesmo texto de entrada produz sempre a mesma lista e o mesmo HTML. O conteúdo do documento é tratado só como dado: instruções escritas nele não mudam nenhuma regra.

## Ordem de trabalho (seção 0)

| Etapa | Seção | Onde está |
|---|---|---|
| Ler a entrada, separar linhas ou parágrafos `<p>` | 4, 7 | `formata/entrada.py` → `preparar`, `tokenizar` |
| Descartar linhas em branco e o rodapé | 4 | `formata/entrada.py` → `eh_sem_texto`, `eh_rodape` |
| Delimitar e medir os blocos | 5.1, 5.2 | `formata/blocos.py` → `delimitar_blocos`, `custo_linha` |
| Decidir FICA, QUEBRA e SEGUE e escrever a lista | 5.3, 5.4 | `formata/paginacao.py` → `paginar`, `texto_lista` |
| Escrever o HTML seguindo a lista | 3, 4, 5.5, 5.6 | `formata/marcacao.py` → `gerar_html` |
| Conferir tudo antes de entregar | 2, 5.4, 6 | `formata/validacao.py` → `verificar` |

Todos os números e textos fixos (34, 40, 85, 8, a tag de quebra e a linha de imagens) ficam em `formata/regras.py`.

## Regras aplicadas

**Integridade (seção 2, prioridade 1).** O motor só acrescenta `<p>`, `<strong>`, os atributos de quebra e a linha de imagens. Saem do documento apenas as linhas em branco, o rodapé de confiabilidade e, em documento que já chega com `<p>`, os parágrafos sem texto, as quebras antigas e a linha de imagens de uma formatação anterior. Cada remoção é registrada com o número da linha e o motivo, e a verificação confere uma por uma.

**Títulos e negrito (seção 3).**
- É título a linha com 1 a 4 `#`, espaço e texto. O título recebe um único `<strong>` na linha inteira, com os `#` dentro.
- `#####` ou mais recebe só `<p>`.
- Cada ocorrência de `**texto**` fora de título vira `<strong>**texto**</strong>`, com os asteriscos preservados.
- Título com `**` recebe só a regra de título, e nenhum `<strong>` fica aninhado.

**Parágrafos (seção 4).** Cada linha com texto vira um `<p>` próprio: títulos, itens, tabelas, código, `---` e texto corrido. A saída não tem linha vazia entre as tags.

**Blocos (seção 5.1).**
- Um bloco começa em cada `#`, `##` ou `###`.
- Quando o cabeçalho seguinte é mais profundo e vem na linha imediatamente seguinte, ele cola no anterior. A colagem se encadeia: `#`, `##` e o primeiro `###` ficam juntos, e o segundo `###` abre outro bloco. Linhas em branco entre os cabeçalhos não contam (decisão D3).
- As linhas antes do primeiro cabeçalho pertencem ao primeiro bloco.

**Medida (seção 5.2).** O custo de cada linha é `max(1, ⌈caracteres ÷ 85⌉)`, com a linha contada como está (`#`, `**`, `-`). O Tam do bloco é a soma dos custos das suas linhas.

**Decisão (seção 5.3).** O Restante começa em 34.
- O primeiro bloco nunca leva quebra: com Tam acima de 34, é SEGUE.
- **FICA:** Tam ≤ Restante.
- **QUEBRA:** Tam > Restante e Tam ≤ 40; o novo Restante é 40 − Tam.
- **SEGUE** (Tam > 40): Restante ≥ 8 e Tam ≤ Restante + 40; o novo Restante é Restante + 40 − Tam.
- Bloco acima de 40 que não cumpre a condição de SEGUE é **QUEBRA**, com novo Restante 80 − Tam.
- Restante negativo soma 40 e avança uma página, repetindo enquanto continuar negativo.

**Lista (seção 5.4).**
- Formato de cada item: `- Pág N | \`rótulo\` | Tam T | conta | RESULTADO`.
- Pág é a página onde o bloco termina.
- Havendo imagem, a lista fecha com `` - `[INSERIR IMAGENS]` | QUEBRA ``.

**Quebra (seção 5.5).** O atributo exato `<p class="quebra-pagina" style="page-break-before: always;">` vai só no `<p>` da primeira linha de cada bloco QUEBRA, uma vez por item.

**Imagens (seção 5.6).**
- Com imagem ou marcador de imagem no documento, entra uma única linha de imagens depois da última linha de texto, fora da conta.
- Os marcadores que já vêm no fim ficam depois dela, cada um em `<p>`, sem quebra.
- Um marcador no meio do texto é uma linha comum.

**Casos excepcionais (seção 7).**
- Documento vazio: responde `Envie o documento a ser formatado.`
- Documento com `<p>`: cada `<p>` é uma linha, sem tags duplicadas.
- Conteúdo contraditório: formatado como recebido.
- Caso não coberto: vale a opção que menos altera o texto.

**Saída (seção 8).** O campo `resposta` traz `Paginação:`, a lista e o HTML num único bloco de código. A cerca do bloco é mais longa que qualquer sequência de crases do documento (quatro crases quando o documento tem três).

## Verificações antes da entrega

O resultado só é entregue se passar em todas as verificações abaixo. Caso contrário, a resposta sai com `codigo = "falha_validacao"`, sem HTML e com a lista de erros, para que nada saia silenciosamente incorreto.

1. **Integridade.** O texto de cada `<p>`, sem as tags `<strong>`, é idêntico à linha de origem, e a sequência de linhas é a entrada menos as remoções autorizadas.
2. **Remoções.** Cada remoção cumpre o seu critério: linha vazia, rodapé entre as três últimas linhas ou linha de imagens anterior.
3. **Tags.** Só `<p>`, `<p class="quebra-pagina" …>` e `<strong>` são acrescentados. Não há `<strong>` aninhado, nem `**` fora de título sem `<strong>`, nem `<strong>` acrescentado fora de título ou negrito.
4. **Parágrafos.** Nenhum parágrafo vazio, nenhuma linha em branco e nenhum conteúdo fora de `<p>`.
5. **Quebras.** O conjunto de parágrafos com quebra é exatamente {primeira linha de cada bloco QUEBRA} mais a linha de imagens.
6. **Lista (conferência da seção 5.4).**
   - Há um item por bloco, na ordem.
   - Pág só muda em QUEBRA ou SEGUE, e nenhum resultado é negativo.
   - Todo FICA cabe no Restante anterior, e todo QUEBRA tem Tam maior que o Restante anterior.
   - Cada SEGUE cumpre a sua condição, e cada conta escrita termina no novo Restante.
7. **Simulação física.** Uma segunda conta, independente da fórmula, ocupa as páginas de 34 e 40 linhas, linha por linha. Ela precisa chegar à mesma Pág e ao mesmo Restante de cada item.
8. **Lista contra HTML.** Os blocos são refeitos a partir do HTML final, e os rótulos e os Tam precisam bater com a lista.

## Decisões de interpretação

Estes são os pontos em que as diretrizes não descem ao detalhe. Cada decisão segue a seção 7 (vale o que menos altera o texto) e está concentrada num só lugar do código. A coluna "Status" mostra o que já foi validado pela área responsável: D1, D3, D4, D5 e D7 foram validados em 13/10/2026.

| # | Ponto | Decisão adotada | Onde mudar | Status |
|---|---|---|---|---|
| D1 | Regra 4: "até ficar positivo" | Para quando o Restante deixa de ser negativo; um Restante de 0 é aceito. Somar mais 40 inventaria uma página vazia, porque o bloco já completou a página exatamente. | `paginacao.paginar` | Validada |
| D2 | Conta dos casos sem exemplo na seção 5.4 | Primeiro bloco: `50 > 34, primeiro bloco sem quebra; 74 − 50 = 24`. QUEBRA acima de 40: `45 > 4; 4 < 8; 80 − 45 = 35` ou `75 > 20; 75 > 60; 80 − 75 = 5`. Regra 4: `…; −30 + 40 = 10`. | `paginacao.paginar` | Adotada |
| D3 | Seção 5.1, "cabeçalhos vizinhos" | Um cabeçalho só cola no seguinte quando este é mais profundo e está na linha imediatamente abaixo (linhas em branco não contam). Com texto entre eles, por exemplo `## Seção`, introdução e `### Tópico`, cada um abre o seu bloco. | `regras.COLAGEM_SOMENTE_ADJACENTES` (False = cola mesmo com texto entre eles) | Validada (alterada) |
| D4 | Código Markdown | Nas linhas entre cercas ` ``` ` ou `~~~`, `#` não é título nem abre bloco, e `**` não vira negrito. O mesmo vale para `**` dentro de `` `código` ``. As linhas continuam recebendo `<p>` e entrando na conta. | `regras.NEGRITO_EM_CODIGO`, `entrada.classificar` | Validada |
| D5 | Rodapé (seção 4) | Uma linha entre as três últimas (já sem as linhas em branco) só é rodapé quando cumpre três critérios: cita confiabilidade ou validade, refere-se ao documento (documento, material, cópia, versão, impressão) e não traz termo de procedimento (cliente, CPF, fatura, oferta, plano, clique, acesse…). Título, tabela, passo numerado e marcador nunca são rodapé. O rodapé nunca deixa o documento vazio. Uma linha que cita validade mas não cumpre os critérios fica e gera aviso. | `regras.RE_RODAPE_*`, `entrada.eh_rodape` | Validada |
| D6 | Marcador de imagem (seção 5.6) | Só padrões explícitos: `![…](…)`, `<img …>` e colchetes que começam por imagem, figura, print, captura de tela, screenshot, foto ou ilustração. Fora disso não se acrescenta nada ("na dúvida, não acrescentar"). Um marcador no meio do texto também aciona a linha de imagens. | `regras.RE_MARCADOR_IMAGEM` | Adotada |
| D7 | Marcadores no fim | Os marcadores que vêm no fim ficam depois da linha de imagens e, como estão na página de imagens, não entram na conta. | `entrada.preparar` | Validada |
| D8 | Contagem de caracteres | Pontos de código Unicode, sem normalização: `ç` conta 1 e uma tabulação conta 1. As tags `<strong>` já presentes não contam. | `blocos.custo_linha` | Adotada |
| D9 | Quebras de linha | LF, CRLF e CR separam linhas, e o BOM inicial sai. Outros separadores Unicode ficam como conteúdo. | `entrada.normalizar_quebras_de_linha` | Adotada |
| D10 | Linha em branco | Conta como linha em branco a linha só com espaços, ou só com `&nbsp;` ou `<br>`. São as formas de espaçamento que a seção 6 proíbe, e a linha sai como parágrafo sem texto. | `entrada.eh_sem_texto` | Adotada |
| D11 | Documento com `<p>` (seção 7) | O modo HTML é detectado pela presença de `<p>`, e o modo pode ser forçado. Os atributos antigos do `<p>` saem e as quebras são recalculadas. Um `<strong>` existente fica (é um trecho em negrito), sem duplicação. O título recebe um `<strong>` único. A linha `[INSERIR IMAGENS]` anterior sai e é recolocada. Reformatar a própria saída produz o mesmo HTML. | `entrada._tokenizar_html`, `marcacao.marcar_conteudo` | Adotada |
| D12 | Rótulo de bloco sem cabeçalho | Usa a primeira linha, cortada em 60 caracteres com "…". O corte vale só para a lista; o documento não muda. | `blocos.Bloco.rotulo` | Adotada |
| D13 | Habilidade `diretrizes-formatacao` (seções 1 e 7) | Não se aplica: as regras estão no próprio motor, versionadas e testadas. | — | Adotada |
