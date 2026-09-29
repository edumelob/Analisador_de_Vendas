# Analisador de Vendas CSV

Ferramenta de linha de comando em Python que lê um arquivo CSV de vendas e gera um relatório: faturamento, ticket médio, ranking de produtos, totais por categoria e por mês. Usa apenas a biblioteca padrão do Python (sem dependências para rodar).

## Funcionalidades

- Faturamento total, itens vendidos e **ticket médio**
- Produto **mais vendido** (por quantidade) e de **maior faturamento**
- Ranking de produtos com participação percentual e gráfico de barras no terminal
- Totais **por categoria** e **por mês** (quando o CSV tem essas colunas)
- Aceita CSV com vírgula, ponto e vírgula ou tab; números como `50.00`, `50,00` ou `R$ 1.234,56`; datas `AAAA-MM-DD` ou `DD/MM/AAAA`; arquivos UTF-8 ou Windows-1252 (Excel)
- Linhas inválidas são **ignoradas com aviso** (número da linha e motivo); no modo `--strict` o programa falha
- Exporta o resultado em **JSON** e **Markdown**
- Valores monetários calculados com `Decimal` (sem erros de arredondamento de `float`)
- Testes automatizados com `pytest` e CI no GitHub Actions

## Requisitos

- Python 3.10 ou superior
- `pytest` apenas para rodar os testes

## Como usar

# rodar com os dados de exemplo (data/vendas.csv)
python -m sales_analyzer

# rodar com o seu próprio arquivo
python -m sales_analyzer caminho/para/vendas.csv
```

No Windows, use `py -m sales_analyzer` se `python` não for reconhecido.

### Opções

| Opção | Descrição |
|-------|-----------|
| `arquivo.csv` | Arquivo a analisar (padrão: `data/vendas.csv`) |
| `--top N` | Quantidade de produtos no ranking (padrão: 5) |
| `--export-json ARQUIVO` | Salva o resumo em JSON |
| `--export-md ARQUIVO` | Salva o relatório em Markdown |
| `--strict` | Falha se houver qualquer linha inválida |
| `--version`, `--help` | Versão e ajuda |

Exemplo:

```bash
python -m sales_analyzer data/vendas.csv --top 3 --export-json saida/resumo.json --export-md saida/relatorio.md
```

Código de saída: `0` em caso de sucesso e `1` em caso de erro (arquivo inexistente, colunas ausentes, nenhuma venda válida etc.).

## Formato do CSV

Colunas **obrigatórias**: `produto`, `quantidade`, `preco`.
Colunas **opcionais**: `data`, `categoria`.

A ordem das colunas não importa. Também são aceitos os nomes `product`, `quantity`, `qty`, `qtd`, `price`, `preco_unitario`, `date` e `category`, com ou sem acento.

```csv
data,produto,categoria,quantidade,preco
2025-01-03,Mouse,Periféricos,4,50.00
2025-01-08,Monitor,Monitores,1,900.00
```

O arquivo `data/vendas_simples.csv` mostra o formato mínimo, só com as três colunas obrigatórias.

Regras de validação: quantidade inteira maior que zero, preço não negativo, produto preenchido. Em números com vírgula e ponto juntos, o último símbolo é o separador decimal (`1.234,56` e `1,234.56` valem 1234,56); com um símbolo só, ele é tratado como decimal (`50,5` e `50.5` valem 50,5).

## Exemplo de saída

`python -m sales_analyzer data/vendas.csv`

```text
============================================================
 ANÁLISE DE VENDAS
============================================================
Transações (linhas)   : 24
Itens vendidos        : 82
Faturamento total     : R$ 24.370,00
Ticket médio          : R$ 1.015,42
Mais vendido (qtd)    : Cabo HDMI (24 un.)
Maior faturamento     : Notebook (R$ 12.800,00)

TOP 5 PRODUTOS POR FATURAMENTO
Produto   Qtd   Faturamento      %
--------  ---  ------------  -----  --------------------
Notebook    4  R$ 12.800,00  52,5%  ####################
Monitor     6   R$ 5.400,00  22,2%  ########
Webcam      6   R$ 1.320,00   5,4%  ##
Headset     5   R$ 1.250,00   5,1%  ##
Fone       15   R$ 1.200,00   4,9%  ##

POR CATEGORIA
Categoria     Qtd   Faturamento      %
------------  ---  ------------  -----
Computadores    4  R$ 12.800,00  52,5%
Monitores       6   R$ 5.400,00  22,2%
Periféricos    28   R$ 3.120,00  12,8%
Áudio          20   R$ 2.450,00  10,1%
Acessórios     24     R$ 600,00   2,5%

POR MÊS
Mês      Qtd  Faturamento      %
-------  ---  -----------  -----
01/2025   25  R$ 5.690,00  23,3%
02/2025   22  R$ 9.940,00  40,8%
03/2025   35  R$ 8.740,00  35,9%
```

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Os testes cobrem leitura e validação do CSV, os cálculos, a formatação dos relatórios e o comportamento da linha de comando (incluindo erros e exportação).

## Estrutura

```
.
├── sales_analyzer/
│   ├── __main__.py     # permite `python -m sales_analyzer`
│   ├── cli.py          # argumentos e códigos de saída
│   ├── loader.py       # leitura e validação do CSV
│   ├── analysis.py     # cálculos (Decimal)
│   ├── report.py       # relatório em texto, Markdown e JSON
│   └── models.py       # dataclass Sale
├── tests/
├── data/               # CSVs de exemplo
└── .github/workflows/ci.yml
```

## Decisões técnicas

- **`Decimal` em vez de `float`** para dinheiro: `0.1 * 3` em `float` dá `0.30000000000000004`.
- **Cálculo separado da leitura e da apresentação**, o que torna cada parte fácil de testar.
- **Desempates determinísticos**: produtos com o mesmo valor são ordenados por nome, então o resultado não muda entre execuções.
- **Ticket médio** = faturamento total ÷ número de linhas (transações) do CSV.

## Próximos passos

- Gráficos com `matplotlib`
- Filtro por período
- Comparação entre meses

## Licença

[MIT](LICENSE)
