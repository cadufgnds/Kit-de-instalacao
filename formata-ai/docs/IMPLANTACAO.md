# Implantação do Formata.AI Web

A aplicação é um único serviço HTTP. Ele entrega a landing page (pasta `frontend/`) e a API (`/api/...`). O motor de paginação não depende de banco de dados, de armazenamento nem de serviço externo.

## Requisitos

- Python 3.10 ou superior, ou Docker.
- CPU e memória modestas. Nos testes, um documento de 1 MB, inclusive com conteúdo malformado de propósito, foi processado em até 1,5 s. Cada formatação ocupa um processo Python de curta duração.

## Execução local

```bash
cd formata-ai/backend
python -m pip install -r requirements.txt
python -m servidor                         # http://127.0.0.1:8000
```

Para desenvolvimento e testes:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest                           # suíte completa; os testes de navegador exigem Chromium
python -m playwright install chromium      # só se não houver Chromium disponível
```

## Docker

```bash
cd formata-ai
docker build -t formata-ai .
docker run -d --name formata -p 8000:8000 --env-file .env.example formata-ai
```

O que a imagem traz:
- roda como usuário sem privilégios (UID 10001);
- não grava nada em disco;
- expõe a porta 8000;
- tem `HEALTHCHECK` em `/api/saude`.

## Configuração

Todas as variáveis estão descritas em `.env.example`. As principais:

| Variável | Padrão | Uso |
|---|---|---|
| `FORMATA_LIMITE_BYTES` | 1048576 | Tamanho máximo do documento |
| `FORMATA_LIMITE_LINHAS` | 20000 | Linhas ou parágrafos por documento |
| `FORMATA_TEMPO_LIMITE` | 15 | Segundos por formatação; ao estourar, o processo é encerrado |
| `FORMATA_MAX_PROCESSOS` | nº de CPUs | Formatações simultâneas por worker |
| `FORMATA_WORKERS` | 1 | Workers uvicorn |
| `FORMATA_ORIGENS_CORS` | vazio | Só é preciso quando a interface fica em outro domínio |
| `FORMATA_DOCS_API` | 1 | `0` desativa `/api/docs` |

Se a interface for publicada separada da API, preencha `<meta name="formata-api" content="https://api.exemplo">` em `frontend/index.html` e autorize essa origem em `FORMATA_ORIGENS_CORS`.

## Em produção

1. **HTTPS e proxy reverso.** Coloque o serviço atrás de um proxy (nginx, Apache, balanceador da nuvem) que encerre o TLS. Configure no proxy um limite de corpo coerente com `FORMATA_LIMITE_BYTES`, por exemplo `client_max_body_size 3m` no nginx. Configure também um limite de requisições por IP, se o serviço ficar acessível fora da rede interna.
2. **Controle de acesso.** A aplicação não exige login. Se o ambiente pedir controle de acesso, faça a autenticação no proxy ou no gateway corporativo (SSO, OIDC, VPN), sem mudar o código.
3. **Escala.**
   - Aumente `FORMATA_WORKERS`, ou suba mais réplicas atrás do balanceador. O serviço não tem estado, então qualquer réplica atende qualquer requisição.
   - `FORMATA_MAX_PROCESSOS` limita quantas formatações rodam ao mesmo tempo em cada worker. As demais esperam na fila.
4. **Cabeçalhos de segurança.** O próprio serviço já envia:
   - `Content-Security-Policy` com `script-src 'self'`;
   - `X-Frame-Options: DENY`;
   - `X-Content-Type-Options: nosniff`;
   - `Referrer-Policy: no-referrer`;
   - `Cache-Control: no-store` nas respostas da API.

   Se o proxy também definir esses cabeçalhos, evite duplicar.
5. **Fontes e marca.** Antes de publicar, instale os arquivos licenciados da Vivo Type e confirme as cores em `frontend/marca/marca.css` (veja `frontend/marca/README.md`).

## Privacidade e retenção

- O documento existe só na memória do processo que atende a requisição e do processo filho que o formata. Os dois o descartam ao responder. Não há banco de dados, fila nem cache. Arquivos enviados de até 1 MB ficam em memória. Se `FORMATA_LIMITE_BYTES` for elevado acima disso, o Starlette pode guardar o upload num arquivo temporário do sistema durante a requisição, apagado logo em seguida.
- O log técnico registra para cada requisição: identificador aleatório, origem (texto ou arquivo), tamanho em bytes, código do resultado, duração, número de blocos e de páginas. **Nunca o conteúdo.** Um teste automatizado garante isso (`tests/test_api.py::test_logs_nao_registram_o_conteudo`).
- O log de acesso do uvicorn registra o IP e a rota (sem o corpo). Se a política da organização pedir, desative-o ou anonimize-o no proxy.
- O navegador não guarda o documento: nada vai para `localStorage`, cookies ou serviços de terceiros. A página não carrega nenhum recurso externo.

## Atualização das regras

As regras normativas estão em `backend/formata/regras.py` e documentadas em `docs/REGRAS.md`. Ao publicar uma nova versão das diretrizes:

1. ajuste o código e os testes;
2. rode `python -m pytest`;
3. regrave a saída de referência (`FORMATA_REGRAVAR=1 python -m pytest tests/test_regressao.py`) só depois de revisar a diferença;
4. gere o relatório (`python scripts/gerar_relatorio.py`).
