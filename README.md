# SGDI — Sistema de Gestão de Demandas Internas

O SGDI é uma aplicação web para registrar, acompanhar e consultar demandas internas. Cada demanda tem título, descrição, solicitante, responsável, status, prioridade e data de criação. A listagem pagina os registros no servidor, permite busca por título ou ID e combina filtros de status, prioridade e responsável.

A interface é servida pelo Flask. Os dados ficam em um banco SQLite (`demandas.db`).

## Funcionalidades

- Criar, editar, visualizar e excluir demandas
- Comentários em cada demanda
- Listagem paginada (10, 20 ou 50 itens), com as mais recentes primeiro
- Busca por título ou ID, com debounce de 400 ms
- Filtros combinados de status, prioridade e responsável, preservados na URL
- Relatório de demandas por solicitante
- Área de gerenciamento com indicadores, gráficos e filtro que atualiza números e gráficos juntos
- Exportação do gerenciamento em PDF e Excel, com data de geração, nome da empresa e filtros no rodapé
- Registro e exibição dos eventos importantes em um visualizador separado (`sistema_logs`)

A descrição de cada rota, dos parâmetros e do formato da API está em [docs/README.md](docs/README.md).

## Guia rápido

Requisitos: Python 3 e pip.

Na pasta do projeto:

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

No Windows, se `python` não for o interpretador desejado:

```bash
py -3 -m pip install -r requirements.txt
py -3 init_db.py
py -3 app.py
```

Abra http://127.0.0.1:5000.

O visualizador de logs sobe em outro terminal, na mesma pasta do projeto. Ele usa a porta 5001 e lê o banco `sistema_logs/logs.db`, que o SGDI preenche ao criar, editar, excluir, comentar ou exportar um relatório. Os dois ficam no ar ao mesmo tempo.

```bash
py -3 sistema_logs\visualizar.py
```

No Linux ou no macOS:

```bash
python sistema_logs/visualizar.py
```

Abra http://127.0.0.1:5001. No menu do SGDI, o link **Logs** aponta para esse endereço. Para encerrar um dos dois, use Ctrl+C no terminal correspondente. O SGDI precisa estar em execução para gravar eventos novos.

`init_db.py` cria o banco e dados de exemplo. Se `demandas.db` já existir, basta `python app.py`: na primeira conexão o sistema completa colunas e índices que ainda faltarem.

Para rodar os testes:

```bash
python -m unittest discover -s tests -v
```
