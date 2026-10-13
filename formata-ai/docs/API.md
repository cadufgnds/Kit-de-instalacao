# API do Formata.AI Web

As duas versões, PHP (hub) e Python, têm o mesmo contrato. No hub, as rotas terminam em `.php`: `api/saude.php`, `api/configuracao.php`, `api/formatar.php` e `api/formatar/arquivo.php`, a partir da pasta da ferramenta (por exemplo, `https://hub/formata-ai/api/formatar.php`). No hub também existem os códigos `metodo_nao_permitido` (405) e, em `saude.php`, `requisito_ausente` (500, quando falta PHP 7.4 ou mbstring).

Base: o mesmo endereço que entrega a landing page. A documentação interativa (OpenAPI) fica em `/api/docs`, e o esquema em `/api/openapi.json`; as duas podem ser desativadas com `FORMATA_DOCS_API=0`.

Todas as respostas são JSON em UTF-8, com `Cache-Control: no-store`. Nenhum documento é gravado em disco ou em log.

## `POST /api/formatar`

Formata um texto enviado em JSON.

```json
{ "texto": "# Título\nTexto do procedimento.", "modo": "auto" }
```

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `texto` | string | sim | Conteúdo do documento: Markdown, texto ou HTML que já chega com `<p>` |
| `modo` | `auto`, `markdown` ou `html` | não (padrão `auto`) | Em `auto`, a presença de `<p>` ativa o tratamento de documento já formatado (seção 7 das diretrizes) |

## `POST /api/formatar/arquivo`

Formata um arquivo enviado em `multipart/form-data`.

| Campo | Descrição |
|---|---|
| `arquivo` | Arquivo `.md`, `.markdown`, `.txt`, `.html` ou `.htm`, em UTF-8 (o BOM é aceito) |
| `modo` | Opcional: `auto`, `markdown` ou `html` |

O servidor recusa:
- arquivos do Word ou ZIP (assinatura `PK`);
- outras extensões;
- conteúdo binário (byte nulo);
- texto que não esteja em UTF-8.

Nenhuma conversão de codificação é feita, porque converter alteraria caracteres.

## Resposta de sucesso (200)

```json
{
  "ok": true,
  "codigo": "ok",
  "mensagem": "Documento formatado.",
  "modo": "markdown",
  "lista_paginacao": "Paginação:\n- Pág 1 | `# Título` | Tam 2 | 34 − 2 = 32 | FICA",
  "itens": [
    {
      "bloco": 1, "rotulo": "# Título", "tam": 2,
      "restante_anterior": 34, "restante_novo": 32,
      "pagina_inicio": 1, "pagina": 1,
      "resultado": "FICA", "conta": "34 − 2 = 32"
    }
  ],
  "html": "<p><strong># Título</strong></p>\n<p>Texto do procedimento.</p>",
  "resposta": "Paginação:\n...\n\n```\n<p>...</p>\n```",
  "total_paginas_texto": 1,
  "tem_imagens": false,
  "removidas": [ { "numero": 3, "motivo": "rodape_confiabilidade", "texto": "..." } ],
  "avisos": [],
  "erros": [],
  "versao_diretrizes": "2.6"
}
```

| Campo | Conteúdo |
|---|---|
| `lista_paginacao` | Lista no formato da seção 5.4, começando por `Paginação:` |
| `itens` | A mesma lista em formato estruturado. `pagina` é a página onde o bloco termina. |
| `html` | Documento final, um `<p>` por linha, sem linhas vazias |
| `resposta` | Lista mais o HTML num único bloco de código (seção 8) |
| `removidas` | Linhas que saíram, com número e motivo: `linha_em_branco`, `paragrafo_sem_texto`, `rodape_confiabilidade` ou `linha_imagens_anterior` |
| `avisos` | Pontos para conferência humana. Não impedem a entrega. |

## Erros

Os erros mantêm o mesmo formato: `ok: false`, `codigo`, `mensagem` e `erros`.

| HTTP | `codigo` | Quando |
|---|---|---|
| 400 | `documento_vazio` | Sem texto depois de descartar as linhas em branco. A mensagem é `Envie o documento a ser formatado.` |
| 400 | `entrada_invalida` | Conteúdo binário, arquivo fora de UTF-8 ou caracteres inválidos |
| 400 | `requisicao_invalida` | JSON malformado, campo ausente ou de tipo errado, multipart sem `arquivo` |
| 400 | `modo_invalido` | Modo diferente de `auto`, `markdown` ou `html` |
| 411 | `tamanho_desconhecido` | Requisição de formatação sem `Content-Length` |
| 413 | `documento_muito_extenso` | Documento acima de `FORMATA_LIMITE_BYTES` ou de `FORMATA_LIMITE_LINHAS` |
| 415 | `tipo_nao_suportado` | Extensão não aceita ou arquivo do Word |
| 422 | `falha_validacao` | O resultado não passou nas verificações de integridade. A resposta vem **sem HTML**, com os erros listados. |
| 500 | `erro_interno` | Falha técnica no processamento. Pode-se tentar de novo. |
| 504 | `tempo_esgotado` | A formatação passou de `FORMATA_TEMPO_LIMITE`, e o processo foi encerrado |

## Outras rotas

- `GET /api/saude` → `{"status": "ok", "versao": "0.3.0", "versao_diretrizes": "2.6"}`
- `GET /api/configuracao` → limites e formatos aceitos, que a interface usa para validar antes de enviar

## Exemplos

```bash
curl -s http://localhost:8000/api/formatar \
  -H 'Content-Type: application/json' \
  -d '{"texto": "# Título\nTexto com **negrito**."}'

curl -s http://localhost:8000/api/formatar/arquivo -F arquivo=@procedimento.md
```

## Garantias do processamento

- **Determinismo.** A mesma entrada e o mesmo modo produzem a mesma resposta.
- **Isolamento.** Cada formatação roda num processo próprio, encerrado ao fim da requisição ou quando estoura o tempo-limite.
- **Nenhum resultado silenciosamente incorreto.** Se qualquer verificação falhar, a resposta é 422, sem HTML.
- **Conteúdo é dado.** Instruções escritas no documento não alteram o processamento.
