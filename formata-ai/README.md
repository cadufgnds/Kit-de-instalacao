# Formata.AI Web — prova de conceito do motor de paginação

Motor determinístico que aplica as **Diretrizes Formata.AI v2.6** a documentos operacionais para a base I.Ajuda. Ele faz cinco coisas:

- descarta as linhas em branco e o rodapé de confiabilidade;
- mede e agrupa os blocos;
- decide FICA, QUEBRA ou SEGUE para cada bloco;
- escreve a lista de paginação;
- gera o HTML com `<p>`, `<strong>`, as quebras e a linha de imagens, sem alterar nenhum caractere do texto.

Esta é a etapa 1 do projeto, pedida antes da interface: o algoritmo e os testes automatizados. A API, a landing page e a implantação vêm depois que as regras e as decisões de interpretação forem validadas.

## Estrutura

```
formata-ai/
├── backend/
│   ├── formata/            motor (Python 3.10+, só biblioteca padrão)
│   │   ├── regras.py       constantes normativas: 34, 40, 85, 8, tag de quebra, padrões
│   │   ├── entrada.py      leitura, linhas em branco, rodapé, imagens, documento com <p>
│   │   ├── blocos.py       delimitação (5.1) e medida (5.2)
│   │   ├── paginacao.py    decisão (5.3) e lista (5.4)
│   │   ├── marcacao.py     <p>, <strong>, quebra (5.5) e imagens (5.6)
│   │   ├── validacao.py    verificações independentes da saída
│   │   ├── motor.py        orquestração e formato da resposta (seção 8)
│   │   └── __main__.py     linha de comando
│   ├── tests/              suíte pytest, saída de referência e documento real
│   └── scripts/gerar_relatorio.py
└── docs/
    ├── REGRAS.md                 regras implementadas e decisões de interpretação
    └── RELATORIO-VALIDACAO.md    resultado da suíte e dos cenários de aceitação
```

## Como executar

```bash
cd formata-ai/backend
python -m pip install pytest          # única dependência, e só para os testes

python -m formata documento.md        # imprime a lista e o HTML (formato da seção 8)
python -m formata documento.md --json # resultado completo: itens, remoções, avisos
python -m formata - < documento.md    # lê da entrada padrão
python -m formata saida.html --modo html   # força o modo de documento com <p>

python -m pytest                      # roda a suíte
python scripts/gerar_relatorio.py     # regrava docs/RELATORIO-VALIDACAO.md
```

Códigos de saída da linha de comando: `0` para formatado, `1` para falha na verificação (nada é entregue) e `2` para entrada vazia ou inválida.

## Uso como biblioteca

```python
from formata import formatar

r = formatar(texto)          # modo "auto", "markdown" ou "html"
if r.ok:
    r.lista_paginacao        # "Paginação:\n- Pág 1 | `# Título` | Tam 27 | 34 − 27 = 7 | FICA ..."
    r.html                   # um <p> por linha
    r.resposta               # lista + HTML num único bloco de código (seção 8)
    r.itens                  # itens estruturados: Tam, Restante anterior/novo, páginas, resultado, conta
    r.removidas, r.avisos    # o que saiu e por quê; pontos para conferência
else:
    r.codigo, r.mensagem, r.erros
```

## Garantias

- **Determinismo.** A mesma entrada produz a mesma saída, sem relógio, aleatoriedade ou dependência de tela.
- **Integridade.** O texto de cada `<p>`, sem as tags `<strong>`, é idêntico à linha de origem, e cada remoção é registrada e conferida.
- **Nada silenciosamente incorreto.** Se qualquer verificação falhar, o resultado sai com `ok = False` e sem HTML.
- **Idempotência.** Reformatar a própria saída, que é um documento com `<p>` (seção 7), produz o mesmo HTML e a mesma lista.
- **Conteúdo como dado.** Instruções escritas no documento não mudam as regras.

Veja `docs/REGRAS.md` para o mapeamento seção → código e as decisões de interpretação D1 a D13 (D1 a D7 validadas).
