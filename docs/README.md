# Documentação do SGDI

O SGDI (Sistema de Gestão de Demandas Internas) registra e consulta demandas de uma equipe. Cada demanda guarda título, descrição, solicitante, responsável, status, prioridade e data de criação. Comentários ficam ligados à demanda. A listagem não carrega a tabela inteira: a página é montada no SQLite com `LIMIT` e `OFFSET`.

Stack: Flask 2.3, SQLite e templates Jinja2. Não há autenticação de sessão; os usuários cadastrados servem como solicitantes e responsáveis.

## Como executar

Na raiz do projeto, com Python 3:

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

No Windows:

```bash
py -3 -m pip install -r requirements.txt
py -3 init_db.py
py -3 app.py
```

A aplicação sobe em http://127.0.0.1:5000 e também em `0.0.0.0:5000`, com o depurador do Flask ligado.

`init_db.py` cria `demandas.db` com as tabelas `demandas`, `usuarios` e `comentarios`, índices de filtro e registros de exemplo. Rodar de novo em um banco que já existe reinsere esses exemplos.

Se o banco já foi criado por uma versão anterior, `python app.py` é suficiente. Na abertura da conexão, o sistema adiciona `status` e `responsible_id` quando faltam, preenche status vazio com `aberta`, copia o solicitante para o responsável quando este está vazio e cria os índices `idx_demandas_status`, `idx_demandas_priority` e `idx_demandas_responsible_id`.

Testes, sem alterar `demandas.db`:

```bash
python -m unittest discover -s tests -v
```

## Modelo de dados

### demandas

| Campo | Uso |
| --- | --- |
| `id` | Identificador da demanda |
| `titulo` | Título |
| `descricao` | Texto da demanda |
| `solicitante` | Nome legado do solicitante |
| `usuario_id` | Solicitante em `usuarios` |
| `responsible_id` | Responsável em `usuarios` |
| `data_criacao` | Data e hora de criação |
| `priority` | `0` nenhuma, `1` baixa, `2` média, `3` alta |
| `status` | `aberta`, `em_andamento`, `concluida`, `cancelada` |

### usuarios

`id`, `nome`, `email`, `senha`.

### comentarios

`id`, `demanda_id`, `comentario`, `autor`, `data`.

## Valores de filtro

Status na URL (`status`):

| Valor | Rótulo |
| --- | --- |
| `aberta` | Aberta |
| `em_andamento` | Em Andamento |
| `concluida` | Concluída |
| `cancelada` | Cancelada |

Prioridade na URL (`priority`): `0` nenhuma, `1` baixa, `2` média, `3` alta.

Paginação: `page` começa em 1. `limit` aceita `10`, `20` ou `50`. O padrão é `20`. Valor inválido volta para o padrão. Página menor que 1 vira 1. Página além do fim devolve a última página existente.

Ordenação da listagem: `data_criacao` decrescente e, em empate, `id` decrescente.

## Endpoints

As rotas de página devolvem HTML. A única resposta JSON é `GET /api/demandas`.

### GET /

Lista as demandas da página pedida.

Query params opcionais:

| Param | Efeito |
| --- | --- |
| `page` | Número da página |
| `limit` | `10`, `20` ou `50` |
| `q` | Texto buscado no título ou no ID |
| `status` | Um dos status permitidos |
| `priority` | `0`, `1`, `2` ou `3` |
| `responsibleId` | ID do responsável |
| `usuario_id` | ID do solicitante |

Filtros informados juntos são aplicados com `AND`. Status ou prioridade fora da lista são ignorados. A busca trata `%`, `_` e `\` como texto, remove caracteres de controle e usa no máximo 100 caracteres.

Exemplo: `/?status=em_andamento&priority=3&responsibleId=1&page=1&limit=20`

Sem resultados para esses filtros, a tabela mostra "Nenhuma demanda encontrada com estes filtros".

### GET /buscar

Mesma listagem que `/`, usada pelo campo de busca do cabeçalho. Aceita os mesmos query params. Na listagem, a busca também chama `GET /api/demandas` depois de 400 ms sem digitação, ou na hora ao pressionar Enter.

### GET /api/demandas

Lista paginada em JSON. Aceita os mesmos query params de `GET /`.

Resposta `200`:

```json
{
  "demandas": [
    {
      "id": 1,
      "titulo": "Corrigir bug no login",
      "descricao": "Usuários não conseguem fazer login",
      "solicitante": "João Silva",
      "data_criacao": "2024-01-15 10:30:00",
      "priority": 3,
      "usuario_id": 1,
      "status": "aberta",
      "responsibleId": 1,
      "responsavel": "João Silva"
    }
  ],
  "totalItems": 150,
  "totalPages": 8,
  "currentPage": 1
}
```

`totalItems` é o total que passou pelos filtros, não só a quantidade da página. Sem registros, `demandas` vem vazio, `totalItems` e `totalPages` são `0` e `currentPage` é `1`.

Exemplo: `/api/demandas?q=login&page=1&limit=10`

### GET /nova_demanda

Formulário de nova demanda.

### POST /nova_demanda

Cria a demanda e redireciona para `/`.

Corpo `application/x-www-form-urlencoded`:

| Campo | Obrigatório | Conteúdo |
| --- | --- | --- |
| `titulo` | sim | Título |
| `descricao` | sim | Descrição |
| `usuario_id` | sim | ID do solicitante |
| `priority` | sim | `0`, `1`, `2` ou `3` |
| `status` | não | Status permitido. Fora da lista, grava `aberta` |
| `responsible_id` | não | ID do responsável. Vazio deixa sem responsável |

### GET /editar/\<id\>

Formulário da demanda. Se o ID não existe, redireciona para `/` com aviso.

### POST /editar/\<id\>

Atualiza título, descrição, solicitante, prioridade, status e responsável. Os campos são os mesmos de `POST /nova_demanda`. Redireciona para `/`.

### GET /detalhes/\<id\>

Mostra a demanda e os comentários. ID inexistente redireciona para `/`.

### GET /deletar/\<id\>

Apaga os comentários da demanda e a própria demanda. Redireciona para `/`.

### POST /adicionar_comentario/\<demanda_id\>

Inclui um comentário e volta para `/detalhes/<demanda_id>`.

| Campo | Conteúdo |
| --- | --- |
| `comentario` | Texto |
| `autor` | Nome de quem comentou |

### GET /relatorio/solicitantes

Tabela de usuários com a quantidade de demandas em que cada um é solicitante (`usuario_id`). O nome do solicitante leva à listagem filtrada por `usuario_id`.

## Arquivos principais

| Caminho | Papel |
| --- | --- |
| `app.py` | Rotas, consultas e preparação do banco |
| `init_db.py` | Criação inicial do SQLite |
| `templates/` | Páginas HTML |
| `static/style.css` | Estilo |
| `static/busca.js` | Debounce da busca e atualização da tabela |
| `tests/` | Testes de paginação, busca e filtros |
| `demandas.db` | Banco local, criado na execução |
