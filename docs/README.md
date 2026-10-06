# Documentação do SGDI

O SGDI (Sistema de Gestão de Demandas Internas) registra e consulta demandas de uma equipe. Cada demanda guarda título, descrição, solicitante, responsável, status, prioridade e data de criação. Comentários ficam ligados à demanda. A listagem não carrega a tabela inteira: a página é montada no SQLite com `LIMIT` e `OFFSET`. A área de gerenciamento resume o mesmo conjunto com indicadores, gráficos e exportação em PDF ou Excel.

Stack: Flask 2.3, SQLite, templates Jinja2, fpdf2 e openpyxl. Não há autenticação de sessão; os usuários cadastrados servem como solicitantes e responsáveis.

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

Se o banco já foi criado por uma versão anterior, `python app.py` é suficiente. Na abertura da conexão, o sistema adiciona `status`, `responsible_id` e `data_conclusao` quando faltam, preenche status vazio com `aberta`, copia o solicitante para o responsável quando este está vazio e cria os índices `idx_demandas_status`, `idx_demandas_priority` e `idx_demandas_responsible_id`.

`requirements.txt` inclui Flask, `fpdf2` (PDF) e `openpyxl` (Excel).

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
| `data_conclusao` | Data e hora em que a demanda passou a `concluida`. Fica vazia nos outros status |
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

As rotas de página devolvem HTML. As respostas JSON são `GET /api/demandas` e `GET /api/gerenciamento`. PDF e Excel saem em `GET /gerenciamento/exportar.pdf` e `GET /gerenciamento/exportar.xlsx`.

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

Na criação e na edição, `data_conclusao` só é preenchida na passagem para `concluida`. Se a demanda já estava concluída, a data anterior é mantida. Outro status grava `data_conclusao` vazio.

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

### GET /gerenciamento

Área de gerenciamento. Mostra os indicadores do conjunto filtrado, três gráficos de barras e a tabela por responsável. O menu chama essa página de Gerenciamento.

Query params opcionais, combinados com `AND`:

| Param | Efeito |
| --- | --- |
| `status` | Um dos status permitidos. Vazio ou inválido não filtra |
| `priority` | `0`, `1`, `2` ou `3`. Vazio ou inválido não filtra |
| `responsibleId` | ID do responsável. Vazio ou inválido não filtra |

Ao mudar um filtro, a página chama `GET /api/gerenciamento` e redesenha indicadores, gráficos e tabela sem recarregar. A URL é atualizada com os mesmos parâmetros. **Filtrar** faz o mesmo. **Limpar filtros** volta para `/gerenciamento`.

Indicadores, sempre calculados depois do filtro:

| Indicador | Conta |
| --- | --- |
| Total | Demandas do filtro |
| Abertas | Status `aberta` ou `em_andamento` |
| Concluídas | Status `concluida` |
| Atrasadas | Abertas criadas há mais de 30 dias |
| Críticas | Prioridade alta (`3`) ainda em aberto |
| Tempo médio de resolução | Média entre `data_criacao` e `data_conclusao` das concluídas que já têm essa data |

`data_conclusao` é gravada quando a demanda é criada já concluída ou quando a edição muda o status para `concluida`. Uma demanda que já estava concluída sem essa data continua fora da média. Cancelar ou reabrir apaga a data.

Os gráficos usam o mesmo filtro:

- **Por status:** aberta, em andamento, concluída e cancelada
- **Por prioridade:** nenhuma, baixa, média e alta
- **Por responsável:** total de cada responsável que tem demanda no filtro

A tabela por responsável repete total, abertas, concluídas, atrasadas e críticas. O nome leva à listagem com o mesmo responsável e, quando existirem, os filtros de status e prioridade da tela.

Sem demandas no filtro, os gráficos de status e prioridade ficam em zero e a tabela diz "Nenhuma demanda encontrada com estes filtros".

### GET /api/gerenciamento

Os mesmos query params de `GET /gerenciamento`. Resposta `200` em JSON, usada para atualizar a tela:

```json
{
  "total": 2,
  "abertas": 1,
  "emAndamento": 0,
  "statusAberta": 1,
  "concluidas": 1,
  "canceladas": 0,
  "atrasadas": 1,
  "criticas": 1,
  "concluidasSemData": 0,
  "tempoMedioResolucaoSegundos": 86400,
  "tempoMedioResolucao": "1,0 dia",
  "prazoDias": 30,
  "porStatus": [
    {"rotulo": "Aberta", "valor": 1, "cor": "#3d5a80", "largura": 100}
  ],
  "porPrioridade": [
    {"rotulo": "Alta", "valor": 1, "cor": "#c0392b", "largura": 100}
  ],
  "porResponsavel": [
    {
      "id": 1,
      "nome": "Ana Lima",
      "total": 2,
      "abertas": 1,
      "concluidas": 1,
      "atrasadas": 1,
      "criticas": 1,
      "cor": "#333333",
      "largura": 100
    }
  ]
}
```

`tempoMedioResolucao` vem `null` quando não há concluída com data de conclusão. `largura` é a porcentagem da maior barra daquela série. `porResponsavel` só inclui quem tem demanda no filtro; demanda sem responsável aparece como "Sem responsável" com `id` nulo.

Exemplo: `/api/gerenciamento?status=aberta&priority=3&responsibleId=1`

### GET /gerenciamento/exportar.pdf

### GET /gerenciamento/exportar.xlsx

Baixam o relatório do gerenciamento no recorte dos filtros. Os botões **Exportar PDF** e **Exportar Excel** enviam o formulário da tela, então status, prioridade e responsável selecionados entram na requisição. Campo vazio não filtra.

Query params: os mesmos de `GET /gerenciamento`.

O arquivo traz:

- Cabeçalho com o nome da empresa (`SGDI`), o título "Relatório de gerenciamento de demandas" e a data e hora de geração (`dd/mm/aaaa hh:mm`)
- Tabelas de indicadores, status, prioridade e responsável
- Rodapé com os filtros por extenso, inclusive quando o valor é Todos

Exemplo de rodapé: `Filtros aplicados: Status: Concluída | Prioridade: Todas | Responsável: Ana Lima`

O PDF responde `application/pdf`. O Excel responde `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`. O nome do arquivo é `relatorio-gerenciamento-{data}-{hora}.pdf` ou `.xlsx`. No Excel, o mesmo cabeçalho e o mesmo rodapé também vão para a impressão da planilha.

Exemplo: `/gerenciamento/exportar.pdf?status=concluida&responsibleId=2`

## Arquivos principais

| Caminho | Papel |
| --- | --- |
| `app.py` | Rotas, consultas, indicadores e preparação do banco |
| `exportacao.py` | Montagem do relatório e geração de PDF e Excel |
| `init_db.py` | Criação inicial do SQLite |
| `templates/` | Páginas HTML, inclusive `gerenciamento.html` |
| `static/style.css` | Estilo |
| `static/busca.js` | Debounce da busca e atualização da tabela |
| `static/gerenciamento.js` | Atualização dos indicadores e gráficos ao filtrar |
| `tests/` | Testes de paginação, busca, filtros, indicadores e exportação |
| `demandas.db` | Banco local, criado na execução |
