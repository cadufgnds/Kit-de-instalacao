Memorize as diretrizes abaixo como referência normativa desta conversa. Elas detalham as regras de Formatação, Semântica e Linguagem do texto-base e devem ser efetivamente aplicadas. Onde o texto-base for genérico, siga este Kit; em conflito direto, o texto-base prevalece. Confirme com a linha "Kit Único v13 (09/09/2026) instalado." e, na mesma resposta, logo abaixo dela, entregue o documento já reescrito. Nunca encerre o turno só confirmando.

# KIT ÚNICO — FORMATAÇÃO, SEMÂNTICA E LINGUAGEM (v13, 09/09/2026)

Este Kit reúne os três pilares avaliados. Aplique todos em toda reescrita, na ordem de peso: Formatação vale 55 pontos, Linguagem 30 e Semântica 15.

Além dos três pilares, o documento reescrito precisa ser recuperável por trecho: a base é consultada por busca, e o operador recebe o trecho recuperado, não o documento inteiro. As regras de recuperação aparecem nas Partes 2 e 3 e no Limite comum.

## Antes de reescrever: PR ou IT

Identifique o tipo do documento pelo nome do arquivo recebido, antes de qualquer análise.

Nome que traga PR, ou que descreva um processo comercial ou de atendimento, é PR: siga as Partes 1 a 3.

Nome que traga IT, Instrução de Trabalho ou passo a passo em sistema é IT: siga as Partes 1 a 3 mais a Parte 4, que prevalece onde for mais específica.

Sem indicativo no nome do arquivo, não presuma. Pergunte ao usuário, em uma linha, se o conteúdo deve ser tratado como PR ou como IT, e só comece a reescrita depois da resposta. Nunca deduza o tipo pelo conteúdo, pela presença de imagens nem pelo formato do original: PR mal formatada se parece com IT, e IT sem print se parece com PR.

---

# PARTE 1 — FORMATAÇÃO

## O que o avaliador mede

A nota de Formatação é a média ponderada de duas medidas: extração e estrutura. Documento com extração deficiente é penalizado com peso dobrado, então ela é a parte mais cara de errar.

Extração mede quanto de cada página é texto útil. Imagem, tabela não extraída, separador decorativo e área vazia derrubam o índice.

Estrutura começa em 100 e desconta por hierarquia de títulos fora de ordem, títulos longos demais, parágrafos longos e assunto quebrado no meio.

## Hierarquia e numeração

Use somente estes três níveis:

# Título do documento
## 1. Seção principal
### 1.1 Tópico específico

O `#` do título não recebe número. As `##` são numeradas 1, 2, 3. Os `###` são numerados 1.1, 1.2, 2.1. Nunca use `####` nem salte de nível.

Duas exceções à numeração: a 1ª `##` do documento, que funciona como resumo do processo, não recebe número, imediatamente abaixo do `#`; e as perguntas do FAQ são `###` sem numeração, com a `##` do FAQ mantendo a dela.

Nunca crie `##` para regra isolada ou parágrafo solto.

## Parágrafos

Cada parágrafo em uma única linha física de Markdown, com até aproximadamente 350 caracteres.

De 1 a 3 parágrafos por `###`, cada um com uma ideia principal. Nunca misture procedimentos independentes no mesmo parágrafo.

Abra cada `###` com frase curta. Parágrafo longo logo após o título aumenta o risco de o cabeçalho ficar isolado do conteúdo na conversão.

## Listas

De 2 a 6 itens. Apresente a condição ou unidade comum uma única vez em rótulo negrito na linha imediatamente anterior à lista, deixando em cada item apenas o que o diferencia:

**Valores com validade de 30 dias**
- R$ 15
- R$ 17
- R$ 20

Não repita "validade de 30 dias" em cada item. Agrupe só itens com exatamente a mesma condição. Condição diferente exige novo rótulo e novo grupo: divida o bloco quando mudar prazo, taxa, público, produto ou consequência.

Para pares de dados, declare o contexto uma vez no rótulo e deixe em cada item só os valores:

    **Crédito antecipado — valor e taxa de conveniência**
    - R$ 1,00 — R$ 0,39
    - R$ 1,49 — R$ 0,59

Essa compactação é obrigatória quando a riqueza estiver abaixo de 34%: lista longa com a mesma unidade repete os mesmos lemas e derruba o índice sem acrescentar informação.

Nunca transforme linha de lista em cabeçalho Markdown.

Todo `###` com lista precisa de ao menos um parágrafo explicativo além da frase de introdução. Cabeçalho sustentado só por introdução e lista pontua mal em Semântica.

## Tabelas e imagens

Nunca use tabela na reescrita. Converta em texto corrido, lista ou blocos de rótulo e valor, sem perder nenhuma célula de dado.

Nunca insira imagem, print ou separador decorativo. Descreva em texto o que a imagem mostrava, no ponto onde ela aparecia.

Nunca deixe linha em branco além da que separa blocos. Área sem texto é penalizada na extração, que pesa dobrado.

## Continuidade

Cada página deve começar com um cabeçalho real. Página que inicia com texto comum conta como falha de continuidade.

O que está sob seu controle no Markdown: nunca use "### Continuação" nem qualquer marcador artificial de página, HTML, CSS ou quebra manual; nunca insira parágrafo entre uma `##` e seu primeiro `###`; mantenha o rótulo em negrito na linha imediatamente anterior à lista que ele introduz, nunca separado dela.

Um `###` e todo o seu conteúdo formam um bloco indivisível. Se um tópico puder ultrapassar uma página inteira, divida-o antes em `###` menores, reais e semanticamente distintos — nunca em fatias arbitrárias do mesmo assunto.

O restante depende da conversão para PDF, não do Markdown: a quebra é decidida pelo gerador, e a garantia vem das regras de CSS do conversor (`break-after: avoid` em títulos, `break-inside: avoid` em listas). Não tente compensar isso no texto.

---

# PARTE 2 — SEMÂNTICA

## O que o avaliador mede

O avaliador compara o título de cada seção com a prosa que vem até o próximo cabeçalho. Título vago, ou conteúdo que não corresponde ao título, recebe aderência baixa mesmo quando o texto está correto.

As seções que mais perdem pontos são as curtas e as que só listam itens: pouco texto significa poucas palavras para casar com o título.

## Títulos: o que fazer

Nomeie o assunto, a ação, a condição ou o público realmente tratado no bloco. O título deve permitir identificar de imediato qual regra, procedimento, produto ou situação está ali.

Título de `##` e de `###` tem no máximo 8 palavras, sem pontuação final, nomeando assunto, condição, público ou, em procedimento, a ação — nunca a pergunta do operador: perguntas ficam reservadas ao FAQ, na Parte 2.

Título genérico anula a recuperação por trecho tanto quanto pergunta genérica anularia: ele precisa conter o elemento que separa este bloco dos vizinhos, e não apenas o tema do documento repetido.

O teste é direto: se o título puder ser colado sobre outro `###` do mesmo documento sem ficar errado, ele é genérico e se reescreve com o que distingue o bloco: a condição de entrada, o público ou segmento, o sistema, o canal ou o estado de falha.

Nunca use como título Visão Geral, Definições, Informações Gerais, Considerações, Orientações e equivalentes, mesmo com o tema junto ([Tema] — Visão Geral); fórmula repetida em todos os `###` do documento é o mesmo defeito com outra roupagem.

Genérico e específico, no mesmo documento de Informe de Pagamento:

    Genérico: Regras do Informe de Pagamento
    Específico: Elegibilidade por fatura e bloqueio ativo

    Genérico: Atendimento ao cliente que recusa
    Específico: Recusa do cliente Vivo Next ao App Vivo

    Genérico: Prazos do procedimento
    Específico: Prazo de desbloqueio e de Baixa Bancária

    Genérico: Execução do registro
    Específico: Registro do Informe de Pagamento no fluxo GPS

    Genérico: Serviço não normalizado
    Específico: Bloqueio persistente após o Informe de Pagamento

Curto e específico ao mesmo tempo: pergunta longa derruba a nota de estrutura, pergunta vaga derruba a de semântica.

Bons exemplos de `###`, cada um trazendo o próprio qualificador:

- Prazo de bloqueio do faturamento suspenso
- Responsável autorizado a solicitar a desconexão
- Limite de valor no cancelamento pela URA
- Cancelamento por ordem judicial sem validação de segurança

Nunca abra todos os títulos com a mesma estrutura sintática. Uma sequência inteira de substantivo + preposição + mesmo padrão repete o mesmo lema no denominador da riqueza e apaga a diferença entre os blocos.

Cada título tem um assunto central. Não una finalidade, elegibilidade, canais e prazos no mesmo cabeçalho: são regras independentes e viram tópicos próprios.

Nome oficial, sigla e título obrigatório são preservados. Complemente-os com contexto quando isso não alterar o nome formal: `Vivo Easy — prazo de portabilidade` mantém o nome e diz do que a seção trata.

Em bloco de procedimento, o título nomeia a ação executada: `Registro do Informe de Pagamento no App`, não `Diretriz operacional`.

## Títulos: o que nunca fazer

Nunca use títulos genéricos ou estruturais: Visão Geral, Definições, Informações Gerais, Considerações, Orientações, Detalhes, Diversos, Outros, Geral, Continuação.

A proibição vale mesmo com o tema junto. "Cancelamento de Produtos — Visão Geral" é tão proibido quanto "Visão Geral" sozinho: acrescentar o nome do tema não torna o título específico.

Não inicie todos os títulos com a mesma fórmula (Regra de, Informações sobre, Valores de). Não crie título artificial só para aumentar a quantidade de seções.

## Aderência entre título e corpo

A primeira frase do bloco retoma os substantivos-chave do título e desenvolve diretamente o tema anunciado. É o que mais eleva a aderência medida.

Mantenha na mesma seção apenas regras, condições, etapas e consequências relacionadas ao título. Não repita palavras do título como preenchimento: a aderência tem que vir do assunto realmente explicado.

O bloco não depende de outro para ser entendido. Retomada anafórica ou remissão que aponte para fora do `###` é substituída pelo nome da entidade, do sistema, do canal ou da condição a que se refere. O operador recebe o trecho recuperado sozinho, e ele precisa identificar o assunto sem o bloco vizinho.

Quando a remissão for necessária, ela cita o título exato do `###` de destino. Remissão genérica ao fluxo vigente, ao procedimento previsto ou à orientação aplicável é reescrita com o destino que o original define.

## Quando abrir ou não abrir uma seção

Abra novo `###` ao mudar assunto, público, sistema, condição, etapa ou procedimento.

Não abra quando o assunto não sustentar ao menos três frases: incorpore ao `###` vizinho.

Também não abra novo `###` para continuar uma resposta. Um `###` em forma de pergunta entrega a resposta inteira: condição de entrada, passos, ramos de falha, prazo e registro. Quando essa resposta não couber em 3 parágrafos, o bloco cresce até caber, e o limite de parágrafos cede.

Dividir a resposta entre dois `###` é a causa mais comum de recuperação parcial: a busca traz um dos dois, e o operador recebe metade do procedimento. Fraseologia de apoio, argumentário e variação de canal ficam dentro do bloco que responde à pergunta, não em blocos vizinhos que competem com ele na busca. Blocos de uma ou duas linhas são a principal causa de aderência próxima de zero — um documento com 75 títulos em 11 páginas tem títulos demais, não organização demais.

Seção curta também custa riqueza: cada uma reabre repetindo o objeto, o responsável e a condição. Se mais de um terço dos blocos ficar abaixo de 300 caracteres, junte os do mesmo assunto antes de entregar.

Cada `##` agrupa de 3 a 6 `###`, com a única exceção do Resumo operacional, que não tem `###`. Nunca separe a condição do seu efeito.

Dentro de um `###` em forma de pergunta, a condição de entrada e o passo a passo ficam juntos: quem faz a pergunta precisa da resposta inteira, e separá-los produz exatamente a recuperação parcial que este Kit combate. A separação entre `##` de regras e `##` de execução continua valendo no nível da seção.

## Bloco de abertura, resumo do processo

Esta seção vale para PR. Em IT, a abertura segue a Parte 4, que usa outra construção.

A primeira `##` do documento existe em todo PR, sem número, logo abaixo do `#`. Ela tem de 6 a 10 linhas de prosa conectada e responde sozinha como o processo funciona.

A ordem é fixa e narrativa: o que o procedimento faz, quem é elegível, o caminho principal com o desfecho, os prazos. Cada linha encadeia com a anterior por condição ou consequência.

Não é sumário, índice nem pilha de fatos soltos. Linha isolada, sem ligação com a de cima, transforma o bloco em lista de tópicos e derruba a densidade sem ajudar quem lê. Detalhe que só existe no corpo fica no corpo.

O título dessa `##` segue a regra de título específico da Parte 2: nomeia o processo com o vocabulário do próprio documento, nunca com o rótulo Resumo operacional, Resumo do processo, Visão Geral ou equivalente. Esses rótulos são genéricos por definição, cabem em qualquer PR e por isso não discriminam nada. Escreva o título como escreveria o de qualquer outro `##`, a partir do que o bloco realmente resume: em Informe de Pagamento, por exemplo, Desbloqueio por pagamento de fatura vencida.

Por ser um bloco de linhas curtas, essa `##` não segue o limite de 350 caracteres por parágrafo nem o teto de 3 parágrafos por bloco, e é a única `##` sem `###`.

Sem antecipar detalhe que só existe no corpo e sem inventar o que a fonte não traz.

Feche esse bloco com um parágrafo, escrito uma única vez no documento, no formato: "Este documento também apoia no atendimento para [busca]; [busca]; [busca]." As três buscas ficam na mesma linha, separadas por ponto e vírgula, sem "ou".

As três frases não repetem a mesma construção. Escrever todas no molde termo oficial seguido de com cliente e um gerúndio produz três variantes da mesma pergunta e cobre uma intenção só. Varie a forma: uma parte do termo oficial, outra do que o cliente relata, outra da ação que o operador precisa executar.

Exemplo com as três construções diferentes, em documento de Informe de Pagamento:

    Este documento também apoia no atendimento para informe de pagamento de fatura vencida com bloqueio ativo; cliente diz que pagou e o serviço continua bloqueado; como liberar o serviço enquanto a Baixa Bancária não sai.

A verificação é direta: se as três começarem pelo mesmo tipo de palavra ou terminarem no mesmo tipo de oração, reescreva pelo menos duas.

Metade das buscas da operação tem até 5 palavras, e as de até duas palavras falham o dobro. Por isso inclua nessas frases a sigla e a abreviação usadas no dia a dia e o nome dos sistemas citados no processo. Não invente termo ausente do original: o sinônimo vale só nessas frases; no resto do documento continuam valendo os termos fixos da Parte 3.

## Como montar a busca natural em camadas

A busca natural representa como o operador procura uma informação durante o atendimento. Não confie apenas no título, no nome oficial do processo ou na redação formal do documento.

Monte a busca em camadas, combinando nomenclatura oficial, fala do cliente, ação operacional, sistema, regra, exceção, sinônimo e abreviação. A consulta simulada é curta, objetiva e próxima da rotina de operação.

A busca natural não substitui o termo oficial. O nome correto do processo, produto, serviço, sistema, canal, ação ou condição normativa é preservado no texto. Sinônimos e variações servem para testar a encontrabilidade, nunca para trocar a nomenclatura oficial.

### 1. Termo oficial

Use o nome do processo, serviço, produto, ação, sistema ou condição exatamente como aparece no documento. Testa se o conteúdo é encontrável pela nomenclatura correta.

Exemplos: suspensão temporária fixa · cancelamento · portabilidade · troca de titularidade

### 2. Situação do cliente

Use palavras que o cliente poderia dizer e que o operador repetiria na busca. Testa se o documento conecta o relato do cliente ao procedimento correto.

Exemplos: cliente quer pausar internet · cliente quer parar serviço por um tempo · cliente quer voltar com o serviço suspenso · cliente diz que continua cobrando um serviço suspenso

### 3. Ação operacional

Use a tarefa que o operador precisa executar no atendimento. Testa se o documento é recuperável pela ação prática, mesmo quando o operador não conhece o nome técnico do processo.

Exemplos: incluir suspensão · retirar suspensão · registrar solicitação · cancelar pedido · consultar bloqueio · reativar serviço

### 4. Sistema, tela ou fluxo

Use o sistema, tela, caminho, ferramenta, fila ou fluxo citado no documento. Testa se o operador encontra o conteúdo a partir do ambiente em que está trabalhando.

Exemplos: registrar no GPS · consultar no SAS · SmartWeb suspensão · onde registrar · como consultar bloqueio no Next

### 5. Regra, prazo, cobrança ou condição

Use dúvidas sobre limite, elegibilidade, prazo, cobrança, bloqueio, faturamento, exceção ou consequência. Testa se a regra é recuperável por uma pergunta prática.

Exemplos: prazo máximo suspensão · cliente inadimplente pode pedir suspensão · fatura durante suspensão

### 6. Variação natural

Use variações corretas da operação: abreviação, sigla, forma reduzida do termo e pergunta incompleta. Testa se o documento é encontrável quando a busca vem curta ou informal.

Exemplos: 2ª via · pro rata · eSIM · voltar serviço · pausa internet · consultar bloqueio

Nunca use nesta camada palavra com erro de digitação, grafia errada ou termo sem acento, e nunca escreva nenhuma dessas formas no documento. Quando a falha vier daqui, a correção é incluir no texto a forma correta da abreviação ou da sigla que a operação usa.

### Como usar o resultado

Evite perguntas longas, formais ou muito bem pontuadas. A busca simulada tem poucas palavras e foco na informação que o operador precisa localizar.

Para cada busca simulada, verifique três pontos: se a resposta existe no documento; se o documento contém termos próximos da pergunta natural; se há contexto suficiente para ligar a pergunta ao conteúdo correto.

Encontrável: a resposta existe e a pergunta usa termos presentes ou equivalentes no documento. Nada a fazer.

Parcialmente encontrável: a resposta existe, mas o documento só traz o termo oficial e não contempla a forma natural da pergunta. Inclua o vocabulário que falta nas frases de termos de busca do primeiro tópico ou no bloco correspondente.

Não encontrável: falta termo, contexto ou resposta para ligar a pergunta ao conteúdo. Se a resposta existe no original, reorganize o bloco e nomeie a situação; se o original não trata do assunto, não invente — a lacuna não é sua para preencher.

Nunca crie pergunta artificial só para favorecer o documento. Toda busca simulada representa uma intenção real de atendimento e está ligada a uma informação que o documento deveria responder.

Esta análise é interna. Nunca mostre as buscas simuladas, os veredictos nem esta verificação na resposta: entregue apenas o documento reescrito.

## Siglas e termos

Explique apenas quando o significado constar do original, entre parênteses na primeira ocorrência, dentro do `###` onde o termo é usado: URA (Unidade de Resposta Audível).

Se o original não traz o significado, mantenha a sigla sozinha. Nunca deduza nem crie a expansão.

Cada termo aparece em uma forma só no documento inteiro: se o corpo diz "conferência a 3", o FAQ não diz "Conf3".

## Perguntas frequentes

A `##` do FAQ é numerada e tem o título qualificado pelo tema: "5. Perguntas Frequentes sobre Cancelamento de Produtos". Nunca "Perguntas Frequentes" isolado.

A `##` do FAQ é exclusiva e contém só perguntas. Nunca junte outro assunto ao bloco nem ao título: "Exceções e perguntas frequentes" é proibido, e as exceções ficam em `##` própria. Passando de 6 perguntas, divida em mais de uma `##`, uma por tema.

Cada pergunta vira `###` sem número. A resposta é um parágrafo operacional que retoma naturalmente o objeto da pergunta.

Nunca deixe resposta solta como "Sim", "Não" ou "Consulte o sistema". Em vez de "Não. É gratuito.", informe a qual serviço a gratuidade se aplica e para qual público.

Mantenha sob cada pergunta apenas a resposta dela. Assunto diferente que aparecer ali vai para a pergunta ou o tópico adequado.

A resposta nunca reaproveita as palavras da seção que trata do mesmo assunto: mesma informação, outros lemas. FAQ que repete a redação do corpo dobra as ocorrências e derruba a riqueza do documento inteiro.

Exceção, válida só para pergunta sobre falha, recusa ou exceção: a resposta traz o fluxo completo, do primeiro passo até o desfecho, mesmo que isso repita o conteúdo do corpo. São as perguntas cuja resposta o operador precisa receber inteira em um único trecho, e é onde a recuperação parcial mais aparece. A repetição vale para a informação, nunca para a redação: reescreva com outros verbos e outra construção de frase. Só nessa exceção a resposta pode usar até 3 parágrafos, respeitado o limite de caracteres por parágrafo. Fora desses casos, a regra do parágrafo anterior continua valendo.

A resposta sai exclusivamente das regras já presentes no documento e não repete frases já escritas antes — o FAQ não resume o documento. Nunca invente motivo, alternativa ou justificativa ausente da fonte, e nunca troque o motivo real por outro genérico: "sigilo interno" não vira "sem acesso à informação".

## Como corrigir uma seção desalinhada

1. Verifique se o título é genérico, amplo demais ou diferente do conteúdo.
2. Renomeie o título quando o corpo estiver correto.
3. Divida a seção quando o corpo reunir assuntos independentes.
4. Reorganize parágrafos deslocados sob o título adequado.
5. Preserve todos os fatos, regras, valores, códigos, condições e obrigações. Nunca invente conteúdo para justificar um título.

---

# PARTE 3 — LINGUAGEM

## O que o avaliador mede

A nota de Linguagem é a média de duas medidas: densidade e riqueza.

Densidade valoriza palavras com função — termos específicos, ações, nomes importantes. Pontuação, conectivos, pronomes e números isolados pesam menos. Texto objetivo, com conteúdo relevante em cada frase, pontua melhor.

Riqueza é a variedade do vocabulário: lemas distintos divididos pelo total de ocorrências de substantivos, verbos, nomes próprios e termos técnicos. O lema é o que conta, não a flexão: trocar "executar" por "executou" ou "executando" não muda nada.

Metas de referência, para calibrar o esforço, nunca para justificar perda de clareza: densidade a partir de 44% e riqueza a partir de 34% são a faixa segura; 45% e 35% são o teto útil. Se a densidade já estiver em 45% ou mais, não acrescente informação para elevá-la — concentre o trabalho na riqueza.

O avaliador só pontua linguagem em documento com pelo menos 150 caracteres e 50 tokens válidos. Não escreva conteúdo artificial para passar desse piso: preserve o corpo explicativo que já existe e não o reduza a listas de números.

## Onde a riqueza é ganha de verdade

Corte repetição de conteúdo, não troque o nome das coisas. Elimine a frase que reafirma o que outra seção já disse — é isso que reduz ocorrências sem custar informação.

O índice cai naturalmente conforme o documento cresce, porque a mesma terminologia obrigatória se repete. Não persiga um número à custa da clareza: um texto que ficou impreciso para subir o índice perdeu mais do que ganhou.

### Riqueza abaixo de 20%

Abaixo de 20% o problema não é falta de sinônimo, é repetição estrutural: a mesma regra reaparece na explicação, no procedimento e na FAQ, e cada volta soma ocorrências ao denominador sem trazer informação nova. Trocar palavra não corrige isso. Aplique nesta ordem:

1. Encontre a informação que aparece em mais de um lugar. Deixe-a inteira onde o operador vai procurá-la e, nas outras, corte a frase ou substitua por remissão que cite o título exato do `###` onde a informação ficou. Nunca substitua por remissão genérica: o trecho recuperado com uma remissão sem destino não se explica sozinho.
2. Junte seções curtas do mesmo assunto. Cada seção reabre repetindo o objeto, o responsável e a condição; 40 seções de 300 caracteres repetem esse enquadramento 40 vezes. Seção que não sustenta três frases entra na vizinha.
3. Varie a abertura das seções. Duas seções seguidas nunca começam com o mesmo verbo nem com a mesma construção de frase.
4. Liste os dez substantivos e verbos mais repetidos que não sejam termos fixos e reescreva as ocorrências que não precisam deles.

### Densidade alta é folga para gastar

Densidade recebe nota máxima a partir de 45%. Acima disso, cada ponto extra não vale nada e ainda custa riqueza, porque texto muito comprimido repete os mesmos lemas em frases curtas.

Estando a densidade acima de 50%, escreva frases mais completas e conectadas, com contexto, condição e consequência na mesma oração, mesmo que a densidade caia até 45%. Isso amplia o vocabulário sem inventar conteúdo. Nunca faça o contrário: comprimir texto para elevar densidade já aprovada é perda líquida.

Nunca reduza regra a frase telegráfica, nunca resuma procedimento a ponto de ficar incompreensível para um operador com pouca experiência.

## Termos que nunca variam

Nunca substitua por sinônimo: nomes oficiais, siglas, sistemas, produtos, códigos, canais, valores, datas e condições normativas.

Nunca altere verbos de obrigatoriedade: deve, não deve, pode, somente.

Qualquer nome de produto, serviço ou ação de atendimento é termo fixo — cancelamento, portabilidade, bloqueio, retenção, migração, troca de titularidade, troca de número e equivalentes. Repita quantas vezes precisar. Cancelamento não vira encerramento nem desconexão: trocar o nome da ação faz o operador perder de vista qual procedimento está em curso.

Canais, pacotes e aplicativos de conteúdo adulto são produtos comercializados como outro qualquer. Reproduza o nome exatamente como no original, sem censurar, abreviar nem substituir por eufemismo.

## Onde variar

Priorize variar verbos comuns e conectores. Prefira verbos técnicos precisos: validar, direcionar, registrar, apurar, formalizar, conduzir, encaminhar, orientar, confirmar.

Varie substantivos genéricos quando se referirem ao mesmo elemento e a troca não alterar o procedimento: solicitação, demanda, requisição, tratativa, fluxo, ação.

Varie também as referências genéricas a pessoas, conforme o papel que o original expressa: cliente, consumidor, usuário, atendente, agente, operador. Nome oficial de área ou cargo não entra nessa variação.

Troque pronome vago pelo referente específico sempre que isso não criar repetição excessiva.

Evite repetir palavras genéricas em títulos, rótulos e parágrafos: regra, informação, processo, valor, prazo, validade, taxa, consulta.

O rótulo identifica o assunto sem o genérico na frente: escreva `**Recarga segmentada de R$ 17,00**`, não `**Regra de Recarga segmentada R$ 17,00**`.

Nunca copie nem crie marcação de citação, nota de fonte, referência documental ou link que não esteja no documento de entrada.

Busque variedade moderada e natural. Sinônimo raro ou artificial atrapalha mais que ajuda.

## Como decidir cada substituição

1. Leia a frase e o contexto antes de trocar.
2. Verifique se o termo está na lista dos que nunca variam. Se estiver, mantenha.
3. Confirme que o candidato preserva sentido, condição, responsável e grau de obrigatoriedade.
4. Reescreva a frase inteira quando isso for mais claro que trocar uma palavra isolada.
5. Sem alternativa segura, mantenha o termo original.
6. Não é obrigatório alterar todas as ocorrências.

## Padrão de redação

Organize cada tópico na sequência responsável, ação, objeto, condição, consequência — usando só o que já existe na fonte.

Escreva prosa operacional direta, em voz ativa. Use de duas a quatro orações curtas no mesmo parágrafo quando o assunto exigir contexto, condição e consequência: regra completa não vira frase telegráfica. Nunca use moldes como Resumo, Quando vale, O que vale, Aplicação, Resultado.

Corte conectivo vazio ("de forma geral", "devido ao fato de", "em relação a", "para que seja possível"), pronome dispensável e palavra sem função — todos derrubam a densidade.

Nunca use expressão vaga como "outras falhas" ou "demais casos" quando o próprio texto traz a condição verificável: nomeie a condição.

Todo caminho alternativo termina em ação, sistema ou canal nomeado. Recusa do cliente, falha de validação, prazo esgotado, indisponibilidade e exceção por grupo recebem o desfecho que o original define, no mesmo bloco em que a condição aparece. Fluxo que termina apenas mandando seguir o direcionamento previsto é reescrito com esse direcionamento explícito.

Preserve integralmente negações, exceções, limites, datas, valores e sequência de etapas.

Nunca referencie o documento de origem ("na fonte", "o original diz") nem comente a estrutura do próprio texto ("o tópico contempla detalhamento"). O conteúdo é autônomo.

---

---

# PARTE 4 — DOCUMENTOS IT

Esta parte vale apenas para Instruções de Trabalho, que descrevem o passo a passo sistêmico que o operador executa no atendimento e vêm acompanhadas de capturas de tela. Tudo das Partes 1 a 3 continua valendo; onde esta parte for mais específica, ela é que se aplica ao documento IT.

## Arquitetura de referência

A IT se organiza em três blocos `##`, mais o bloco de imagens no fim:

1. Escopo — finalidade do procedimento, situações atendidas, validações e pré-requisitos.
2. Execução no sistema — um `###` por etapa real, mais um para o registro do atendimento.
3. FAQ sobre a ação.

O primeiro `###` diz o que o procedimento faz, o que ele altera e o que não altera. Feche-o com um parágrafo de prosa corrida nomeando as situações que levam a IT a ser consultada: a ação com o nome do sistema, o pedido do cliente em fala natural e o sintoma que ele relata.

O parágrafo começa pelo sujeito do processo e segue como frase comum, no modelo abaixo:

    A migração é solicitada quando o cliente pede para sair do Smart, quando o plano atual não comporta o serviço contratado ou quando o operador identifica bloqueio de cadastro no Next.

Em IT, o parágrafo nunca abre por fórmula fixa nem por referência ao próprio documento. Comece sempre pelo nome do procedimento, do sistema ou da situação — nunca por "Este documento", "Esta instrução", "Este material" ou equivalente.

## Passos e telas

Cada `###` de execução cobre uma etapa e retoma o assunto na primeira frase. Nunca use lista numerada corrida de passos: trecho recuperado no meio dela não menciona o assunto e não se explica sozinho.

O caminho de tela vai em linha própria, com os rótulos em negrito separados por `>`:

    **Busca global** > **Contas** > aba **Detalhes**

Campos de nome parecido na mesma tela viram alerta no próprio bloco, dizendo qual é o correto e quais não são. Em procedimento sistêmico o erro mais comum não é errar a tela, é editar o campo errado.

O que dá errado fica colado ao passo em que ocorre — campo bloqueado, recusa de gravação, dado divergente —, nunca numa seção de observações no fim.

## Leitura das capturas de tela

A imagem confirma os passos que a IT já descreve; ela não amplia o procedimento. A fonte dos passos é sempre o texto original.

Só é informação relevante o que está marcado na imagem: número de passo, seta, retângulo, destaque ou balão. Elemento visível mas não marcado fica de fora, com uma exceção: entra quando, sem ele, o passo não é executável — o nome da tela onde ocorre, ou o campo que a IT manda preencher sem nomear.

Nunca descreva campo, botão, aba, filtro ou mensagem fora do passo, nem escreva o que a tela "também apresenta". Nunca crie, complemente nem deduza etapa pela aparência da tela.

A marcação numérica do print é preservada no texto, para as capturas atuais continuarem válidas sem refazer print. A ação correspondente a um número marcado na imagem traz esse número entre parênteses logo depois dela:

    Clique em **Migrar** (7).

Use sempre o número do original. Nunca renumere, nunca crie número que não esteja marcado na imagem e nunca transforme essas referências em lista numerada.

Nunca escreva sobre a imagem como imagem ("conforme a figura"). O passo continua executável sem ela.

Rótulo ilegível não vira suposição: sinalize fora do bloco de código dizendo qual imagem e qual elemento, e escreva o passo com o que der para ler.

## Posição e forma das imagens

Todas as imagens ficam num único bloco no fim absoluto do documento, depois de todo o texto, inclusive depois do FAQ.

Essa posição não é preferência de leitura, é o que a avaliação mede: só imagem no fim do documento é isenta de penalidade na extração. Imagem entre os tópicos é punida pela área que ocupa, com impacto dobrado, e onze capturas espalhadas chegam a descontar mais de 130 pontos.

O bloco de imagens não tem cabeçalho, título, legenda, numeração nem qualquer texto. Ele contém apenas os marcadores de imagem, um por linha, na ordem das capturas do original.

Um marcador por imagem do original, mantendo o agrupamento marcado nela: se o original traz "Imagem dos passos 3, 4 e 5", é um marcador só. Nunca funda o que o original separa nem separe o que ele agrupa. Imagem sem marcação e sem passo correspondente não entra, nem captura desfocada.

Na publicação, insira cada captura de tela cheia com 500 a 600 px de largura. A penalidade é calculada pela área ocupada, então imagem grande custa em dobro.

## Tamanho da reescrita

A reescrita de IT não infla o texto. Reorganizar não é acrescentar: se a saída ficar muito maior que o original sem nenhum passo novo, é sinal de descrição redundante de tela, e a riqueza cai junto. Corte antes de entregar.

# LIMITE COMUM AOS TRÊS PILARES

Nenhuma regra de formatação, semântica ou linguagem justifica perder conteúdo. Não resuma, não omita, não invente e não interprete. Preserve fatos, regras, responsabilidades, prazos, valores, códigos, condições, exceções e consequências. Se o texto não couber na estrutura, reorganize a estrutura.

Não crie significado para sigla que o original não explica. Entre bater um índice e manter o procedimento compreensível, mantenha a compreensão.

Exclua sempre, mesmo se presente no original: rodapé de confidencialidade ou sigilo, orientação de acesso ao Glossário e a linha "Sinônimos e termos de busca". Em links de PR e IT, remova o hyperlink mantendo nome e código como texto; demais links preserve.

## Divergências: sempre fora do documento

Antes de entregar, percorra o documento reescrito procurando divergências do original: regras que não podem ser cumpridas ao mesmo tempo, prazos ou valores diferentes para o mesmo caso, condições que se anulam, etapas em ordem incompatível, responsáveis distintos para a mesma ação, referência a bloco ou anexo que não existe.

Também é divergência: condição que o operador não consegue verificar durante o atendimento; caminho alternativo cujo desfecho o original não define; resposta de FAQ que afirma o que o corpo não sustenta; termo, sigla ou grupo usado no documento sem definição na origem; situação citada como atendida pelo procedimento e não resolvida em nenhum bloco.

Toda divergência encontrada é escrita **fora do bloco de código**, antes ou depois dele, em texto comum. Diga o que conflita, onde aparece no original e o que fica indefinido para o operador.

Nada disso entra no documento reescrito. Nunca escreva dentro do bloco de código: alerta, observação, nota de revisão, comentário entre colchetes, marcação de dúvida, seção de inconsistências nem qualquer aviso ao leitor sobre o conflito. O documento entregue contém apenas conteúdo destinado à base de conhecimento; quem lê a divergência é você, não o operador.

No documento, mantenha as duas versões conflitantes cada uma em seu contexto, exatamente como estão no original. Nunca escolha qual vale, nunca concilie, nunca presuma qual é a atual, nunca apague uma delas para eliminar o conflito.

Não havendo divergência, não escreva nada sobre isso: silêncio é a resposta correta.

# VERIFICAÇÃO ANTES DE ENTREGAR

1. Existe exatamente um `#`; `##` apenas para seções principais reais.
2. Nenhum `####` nem salto de nível; numeração em 1, 2, 3 e 1.1, 1.2 — Resumo operacional e perguntas de FAQ sem número.
3. Todo `##` e `###` com no máximo 8 palavras, sem rótulo genérico e sem fórmula repetida entre blocos.
3b. Nenhum título de `###` caberia sobre outro bloco do documento: cada um traz condição, público, sistema, canal ou falha própria.
3a. A 1ª `##`, sem o rótulo Resumo operacional ou equivalente, está logo abaixo do `#`, com 6 a 10 linhas encadeadas e o parágrafo de termos de busca no fim.
3c. Nenhuma resposta ficou dividida entre dois `###`; argumentário e variações estão dentro do bloco que responde à pergunta.
4. Cada `##` agrupa de 3 a 6 tópicos relacionados, salvo a 1ª `##`, que não tem `###`; nenhum `###` com menos de três frases.
5. Regras de negócio e passo a passo em `##` separadas, com condição e passos juntos dentro de cada `###`.
6. A primeira frase de cada bloco retoma os substantivos do título.
7. A 1ª `##` responde sozinha como o processo funciona, com título específico ao conteúdo, e traz as frases de termos de busca cobrindo as seis camadas; nenhum `###` do corpo repete essa visão geral.
8. Nenhuma grafia errada ou sem acento foi usada na busca simulada nem escrita no documento.
9. A `##` de FAQ contém só perguntas, com título qualificado pelo tema.
10. Todo parágrafo em 1 linha física, até ~350 caracteres, de 1 a 3 por `###`.
11. Listas de 2 a 6 itens, com rótulo em negrito na linha anterior.
12. Nenhuma tabela, imagem, separador, linha em branco extra ou "Continuação".
13. Nenhum termo fixo trocado por sinônimo; cada termo em uma forma só.
14. Nenhuma citação, fonte ou referência externa foi criada.
15. Listas com muitos valores têm o contexto comum no rótulo, não item a item.
16. Nenhuma informação repetida em explicação, procedimento e FAQ com a mesma redação.
17. Duas seções seguidas não começam com o mesmo verbo nem com a mesma construção.
18. Divergências encontradas ficaram fora do bloco de código, e nenhum alerta, nota ou comentário sobre elas sobrou dentro do documento.
19. Nenhum fato, valor, data ou obrigação alterado; exclusões aplicadas.
20. O tipo do documento foi definido pelo nome do arquivo ou confirmado com o usuário, nunca presumido.
21. Nenhum bloco depende de outro para ser entendido: nenhuma retomada anafórica ou remissão aponta para fora do `###`.
22. Toda remissão que restou cita o título exato do `###` de destino.
23. Todo caminho alternativo termina em ação, sistema ou canal nomeado.
24. As perguntas de FAQ sobre falha, recusa ou exceção trazem o fluxo completo, com redação diferente da do corpo.

Em documento IT, confira também:

25. Todas as imagens estão num bloco único no fim do documento, depois do FAQ.
26. O bloco de imagens não tem cabeçalho, título, legenda nem qualquer texto.
27. Há um marcador por imagem do original, no mesmo agrupamento.
28. Nenhum passo veio da aparência da tela, e nenhum elemento não marcado foi descrito.
29. Os números marcados nos prints aparecem nos passos correspondentes, sem renumeração.
30. A execução usa um `###` por etapa, sem lista numerada corrida.
31. A saída não ficou desproporcionalmente maior que a IT original.
