from flask import Flask, jsonify, render_template, request, redirect, flash
import sqlite3
from datetime import datetime


app = Flask(__name__)
app.secret_key = '123456'


# ============================================================
# CONEXÃO COM O BANCO DE DADOS
# ============================================================

STATUS_PERMITIDOS = ('aberta', 'em_andamento', 'concluida', 'cancelada')
STATUS_ROTULOS = {
    'aberta': 'Aberta',
    'em_andamento': 'Em Andamento',
    'concluida': 'Concluída',
    'cancelada': 'Cancelada',
}
PRIORIDADES_PERMITIDAS = (0, 1, 2, 3)


def get_db():
    caminho = app.config.get('DATABASE', 'demandas.db')
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    preparar_banco(conn)
    return conn


def preparar_banco(conn):
    """Garante colunas e índices usados pelos filtros da listagem."""

    colunas = {
        linha[1]
        for linha in conn.execute('PRAGMA table_info(demandas)')
    }

    if not colunas:
        return

    if 'status' not in colunas:
        conn.execute(
            "ALTER TABLE demandas ADD COLUMN status TEXT DEFAULT 'aberta'"
        )

    if 'responsible_id' not in colunas:
        conn.execute(
            'ALTER TABLE demandas ADD COLUMN responsible_id INTEGER'
        )

    conn.execute(
        '''
        UPDATE demandas
        SET status = 'aberta'
        WHERE status IS NULL OR TRIM(status) = ''
        '''
    )
    conn.execute(
        '''
        UPDATE demandas
        SET responsible_id = usuario_id
        WHERE responsible_id IS NULL
          AND usuario_id IS NOT NULL
        '''
    )
    conn.execute(
        'CREATE INDEX IF NOT EXISTS idx_demandas_status ON demandas (status)'
    )
    conn.execute(
        'CREATE INDEX IF NOT EXISTS idx_demandas_priority ON demandas (priority)'
    )
    conn.execute(
        '''
        CREATE INDEX IF NOT EXISTS idx_demandas_responsible_id
        ON demandas (responsible_id)
        '''
    )
    conn.commit()


# Itens por página aceitos na listagem e na API.
LIMITES_PERMITIDOS = (10, 20, 50)
LIMITE_PADRAO = 20


def obter_parametros_paginacao():
    """Lê page e limit da query string e aplica os valores permitidos."""

    try:
        pagina = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        pagina = 1

    if pagina < 1:
        pagina = 1

    try:
        limite = int(request.args.get('limit', LIMITE_PADRAO))
    except (TypeError, ValueError):
        limite = LIMITE_PADRAO

    if limite not in LIMITES_PERMITIDOS:
        limite = LIMITE_PADRAO

    return pagina, limite


def janela_de_paginas(pagina_atual, total_paginas, tamanho=5):
    """Números de página exibidos ao redor da página atual."""

    if total_paginas <= 0:
        return []

    if total_paginas <= tamanho:
        return list(range(1, total_paginas + 1))

    metade = tamanho // 2
    inicio = max(1, pagina_atual - metade)
    fim = min(total_paginas, inicio + tamanho - 1)
    inicio = max(1, fim - tamanho + 1)

    return list(range(inicio, fim + 1))


def normalizar_termo_busca(termo):
    """Remove caracteres de controle e limita o tamanho do texto buscado."""

    if termo is None:
        return None

    texto = ''.join(caractere for caractere in str(termo) if caractere.isprintable())
    texto = texto.strip()

    if not texto:
        return None

    return texto[:100]


def escapar_curinga_like(termo):
    """Escapa \\, % e _ para que não funcionem como curinga do LIKE."""

    return (
        termo.replace('\\', '\\\\')
        .replace('%', '\\%')
        .replace('_', '\\_')
    )


def ler_status():
    status = request.args.get('status', '').strip()
    if status in STATUS_PERMITIDOS:
        return status
    return None


def ler_priority():
    bruto = request.args.get('priority', '').strip()
    if bruto == '':
        return None

    try:
        priority = int(bruto)
    except (TypeError, ValueError):
        return None

    if priority not in PRIORIDADES_PERMITIDAS:
        return None

    return priority


def ler_responsible_id():
    bruto = request.args.get('responsibleId', '').strip()
    if not bruto:
        return None

    try:
        responsible_id = int(bruto)
    except (TypeError, ValueError):
        return None

    if responsible_id < 1:
        return None

    return responsible_id


def ler_filtros_da_requisicao():
    usuario_id = request.args.get('usuario_id', '').strip() or None
    termo = normalizar_termo_busca(request.args.get('q', ''))

    return {
        'usuario_id': usuario_id,
        'termo': termo,
        'status': ler_status(),
        'priority': ler_priority(),
        'responsible_id': ler_responsible_id(),
    }


def consultar_demandas_paginadas(
    conn,
    pagina,
    limite,
    usuario_id=None,
    termo=None,
    status=None,
    priority=None,
    responsible_id=None,
):
    """
    Busca demandas já paginadas no SQLite (COUNT + LIMIT/OFFSET).
    Ordenação padrão: data de criação decrescente.
    """

    filtros = []
    parametros = []

    if usuario_id:
        filtros.append('demandas.usuario_id = ?')
        parametros.append(usuario_id)

    if status in STATUS_PERMITIDOS:
        filtros.append('demandas.status = ?')
        parametros.append(status)

    if priority in PRIORIDADES_PERMITIDAS:
        filtros.append('demandas.priority = ?')
        parametros.append(priority)

    if responsible_id:
        filtros.append('demandas.responsible_id = ?')
        parametros.append(responsible_id)

    termo = normalizar_termo_busca(termo)

    if termo:
        padrao = f'%{escapar_curinga_like(termo)}%'
        filtros.append(
            '''(
                demandas.titulo LIKE ? ESCAPE '\\'
                OR CAST(demandas.id AS TEXT) LIKE ? ESCAPE '\\'
            )'''
        )
        parametros.extend([padrao, padrao])

    where_sql = ''
    if filtros:
        where_sql = 'WHERE ' + ' AND '.join(filtros)

    total_items = conn.execute(
        f'''
        SELECT COUNT(*)
        FROM demandas
        LEFT JOIN usuarios
            ON demandas.usuario_id = usuarios.id
        LEFT JOIN usuarios AS responsavel
            ON demandas.responsible_id = responsavel.id
        {where_sql}
        ''',
        parametros
    ).fetchone()[0]

    if total_items == 0:
        total_pages = 0
        current_page = 1
        offset = 0
    else:
        total_pages = (total_items + limite - 1) // limite
        current_page = min(pagina, total_pages)
        offset = (current_page - 1) * limite

    demandas = conn.execute(
        f'''
        SELECT
            demandas.id,
            demandas.titulo,
            demandas.descricao,
            usuarios.nome,
            demandas.data_criacao,
            demandas.priority,
            demandas.usuario_id,
            demandas.status,
            demandas.responsible_id,
            responsavel.nome AS responsavel_nome
        FROM demandas
        LEFT JOIN usuarios
            ON demandas.usuario_id = usuarios.id
        LEFT JOIN usuarios AS responsavel
            ON demandas.responsible_id = responsavel.id
        {where_sql}
        ORDER BY demandas.data_criacao DESC, demandas.id DESC
        LIMIT ? OFFSET ?
        ''',
        parametros + [limite, offset]
    ).fetchall()

    if total_items == 0:
        inicio = 0
        fim = 0
    else:
        inicio = offset + 1
        fim = offset + len(demandas)

    return {
        'demandas': demandas,
        'total_items': total_items,
        'total_pages': total_pages,
        'current_page': current_page,
        'inicio': inicio,
        'fim': fim,
        'paginas': janela_de_paginas(current_page, total_pages),
    }


def listar_usuarios(conn):
    return conn.execute(
        '''
        SELECT id, nome, email
        FROM usuarios
        ORDER BY nome
        '''
    ).fetchall()


def demanda_para_json(demanda):
    return {
        'id': demanda['id'],
        'titulo': demanda['titulo'],
        'descricao': demanda['descricao'],
        'solicitante': demanda['nome'],
        'data_criacao': demanda['data_criacao'],
        'priority': demanda['priority'],
        'usuario_id': demanda['usuario_id'],
        'status': demanda['status'],
        'responsibleId': demanda['responsible_id'],
        'responsavel': demanda['responsavel_nome'],
    }


def render_listagem(filtros):
    pagina, limite = obter_parametros_paginacao()

    conn = get_db()
    usuarios = listar_usuarios(conn)
    resultado = consultar_demandas_paginadas(
        conn,
        pagina,
        limite,
        usuario_id=filtros['usuario_id'],
        termo=filtros['termo'],
        status=filtros['status'],
        priority=filtros['priority'],
        responsible_id=filtros['responsible_id'],
    )
    conn.close()

    filtros_ativos = any((
        filtros['status'],
        filtros['priority'] is not None,
        filtros['responsible_id'],
    ))

    return render_template(
        'index.html',
        demandas=resultado['demandas'],
        usuarios=usuarios,
        usuario_selecionado=filtros['usuario_id'],
        termo=filtros['termo'],
        status=filtros['status'],
        priority=filtros['priority'],
        responsible_id=filtros['responsible_id'],
        status_rotulos=STATUS_ROTULOS,
        filtros_ativos=filtros_ativos,
        limit=limite,
        current_page=resultado['current_page'],
        total_pages=resultado['total_pages'],
        total_items=resultado['total_items'],
        inicio=resultado['inicio'],
        fim=resultado['fim'],
        paginas=resultado['paginas'],
    )


# ============================================================
# PÁGINA INICIAL - LISTA DE DEMANDAS
# ============================================================

@app.route('/')
def index():

    return render_listagem(ler_filtros_da_requisicao())


# ============================================================
# API - LISTAGEM PAGINADA DE DEMANDAS
# ============================================================

@app.route('/api/demandas')
def api_demandas():

    filtros = ler_filtros_da_requisicao()
    pagina, limite = obter_parametros_paginacao()

    conn = get_db()
    resultado = consultar_demandas_paginadas(
        conn,
        pagina,
        limite,
        usuario_id=filtros['usuario_id'],
        termo=filtros['termo'],
        status=filtros['status'],
        priority=filtros['priority'],
        responsible_id=filtros['responsible_id'],
    )
    conn.close()

    return jsonify({
        'demandas': [
            demanda_para_json(demanda)
            for demanda in resultado['demandas']
        ],
        'totalItems': resultado['total_items'],
        'totalPages': resultado['total_pages'],
        'currentPage': resultado['current_page'],
    })


# ============================================================
# NOVA DEMANDA
# ============================================================

@app.route('/nova_demanda', methods=['GET', 'POST'])
def nova_demanda():

    conn = get_db()

    # Busca usuários cadastrados
    usuarios = conn.execute(
        '''
        SELECT id, nome, email
        FROM usuarios
        ORDER BY nome
        '''
    ).fetchall()

    if request.method == 'POST':

        titulo = request.form['titulo']
        descricao = request.form['descricao']
        usuario_id = request.form['usuario_id']
        priority = request.form['priority']
        status = request.form.get('status', 'aberta')
        responsible_id = request.form.get('responsible_id', '').strip() or None

        if status not in STATUS_PERMITIDOS:
            status = 'aberta'

        # Descobre o próximo ID
        resultado = conn.execute(
            'SELECT MAX(id) FROM demandas'
        ).fetchone()

        novo_id = (resultado[0] or 0) + 1

        # Insere a nova demanda
        conn.execute(
            '''
            INSERT INTO demandas
            (
                id,
                titulo,
                descricao,
                usuario_id,
                data_criacao,
                priority,
                status,
                responsible_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                novo_id,
                titulo,
                descricao,
                usuario_id,
                datetime.now(),
                priority,
                status,
                responsible_id
            )
        )

        conn.commit()
        conn.close()

        flash('Demanda salva com sucesso!')

        return redirect('/')

    conn.close()

    return render_template(
        'nova_demanda.html',
        usuarios=usuarios
    )


# ============================================================
# EDITAR DEMANDA
# ============================================================

@app.route('/editar/<id>', methods=['GET', 'POST'])
def editar(id):

    conn = get_db()

    # Busca os usuários para o dropdown
    usuarios = conn.execute(
        '''
        SELECT id, nome, email
        FROM usuarios
        ORDER BY nome
        '''
    ).fetchall()

    if request.method == 'POST':

        titulo = request.form['titulo']
        descricao = request.form['descricao']
        usuario_id = request.form['usuario_id']
        priority = request.form['priority']
        status = request.form.get('status', 'aberta')
        responsible_id = request.form.get('responsible_id', '').strip() or None

        if status not in STATUS_PERMITIDOS:
            status = 'aberta'

        conn.execute(
            '''
            UPDATE demandas
            SET
                titulo = ?,
                descricao = ?,
                usuario_id = ?,
                priority = ?,
                status = ?,
                responsible_id = ?
            WHERE id = ?
            ''',
            (
                titulo,
                descricao,
                usuario_id,
                priority,
                status,
                responsible_id,
                id
            )
        )

        conn.commit()
        conn.close()

        flash('Demanda atualizada com sucesso!')

        return redirect('/')

    # Busca a demanda que será editada
    demanda = conn.execute(
        '''
        SELECT
            demandas.id,
            demandas.titulo,
            demandas.descricao,
            demandas.usuario_id,
            demandas.data_criacao,
            demandas.priority,
            demandas.status,
            demandas.responsible_id
        FROM demandas
        WHERE demandas.id = ?
        ''',
        (id,)
    ).fetchone()

    conn.close()

    if demanda is None:
        flash('Demanda não encontrada!')
        return redirect('/')

    return render_template(
        'editar.html',
        demanda=demanda,
        usuarios=usuarios
    )


# ============================================================
# DELETAR DEMANDA
# ============================================================

@app.route('/deletar/<id>')
def deletar(id):

    conn = get_db()

    # Primeiro remove os comentários relacionados
    conn.execute(
        '''
        DELETE FROM comentarios
        WHERE demanda_id = ?
        ''',
        (id,)
    )

    # Depois remove a demanda
    conn.execute(
        '''
        DELETE FROM demandas
        WHERE id = ?
        ''',
        (id,)
    )

    conn.commit()
    conn.close()

    flash('Demanda deletada com sucesso!')

    return redirect('/')


# ============================================================
# BUSCAR DEMANDA
# ============================================================

@app.route('/buscar')
def buscar():

    return render_listagem(ler_filtros_da_requisicao())


# ============================================================
# DETALHES DA DEMANDA
# ============================================================

@app.route('/detalhes/<id>')
def detalhes(id):

    conn = get_db()

    # Busca a demanda junto com o nome do usuário
    demanda = conn.execute(
        '''
        SELECT
            demandas.id,
            demandas.titulo,
            demandas.descricao,
            usuarios.nome,
            demandas.data_criacao,
            demandas.priority
        FROM demandas
        LEFT JOIN usuarios
            ON demandas.usuario_id = usuarios.id
        WHERE demandas.id = ?
        ''',
        (id,)
    ).fetchone()

    if demanda is None:
        conn.close()
        flash('Demanda não encontrada!')
        return redirect('/')

    # Busca os comentários
    comentarios = conn.execute(
        '''
        SELECT
            id,
            demanda_id,
            comentario,
            autor,
            data
        FROM comentarios
        WHERE demanda_id = ?
        ORDER BY id
        ''',
        (id,)
    ).fetchall()

    conn.close()

    return render_template(
        'detalhes.html',
        demanda=demanda,
        comentarios=comentarios
    )


# ============================================================
# ADICIONAR COMENTÁRIO
# ============================================================

@app.route(
    '/adicionar_comentario/<demanda_id>',
    methods=['POST']
)
def adicionar_comentario(demanda_id):

    comentario = request.form['comentario']
    autor = request.form['autor']

    conn = get_db()

    # Descobre o próximo ID do comentário
    resultado = conn.execute(
        'SELECT MAX(id) FROM comentarios'
    ).fetchone()

    novo_id = (resultado[0] or 0) + 1

    conn.execute(
        '''
        INSERT INTO comentarios
        (
            id,
            demanda_id,
            comentario,
            autor,
            data
        )
        VALUES (?, ?, ?, ?, ?)
        ''',
        (
            novo_id,
            demanda_id,
            comentario,
            autor,
            datetime.now()
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        f'/detalhes/{demanda_id}'
    )


# ============================================================
# RELATÓRIO POR SOLICITANTE
# ============================================================

@app.route('/relatorio/solicitantes')
def relatorio_solicitantes():

    conn = get_db()

    relatorio = conn.execute(
        '''
        SELECT
            usuarios.id,
            usuarios.nome,
            usuarios.email,
            COUNT(demandas.id) AS total_demandas
        FROM usuarios

        LEFT JOIN demandas
            ON usuarios.id = demandas.usuario_id

        GROUP BY
            usuarios.id,
            usuarios.nome,
            usuarios.email

        ORDER BY usuarios.nome
        '''
    ).fetchall()

    conn.close()

    return render_template(
        'relatorio_solicitantes.html',
        relatorio=relatorio
    )


# ============================================================
# FUNÇÃO AUXILIAR
# ============================================================

def calcular_prazo(data_inicio):
    return "30 dias"


# ============================================================
# EXECUÇÃO DO SISTEMA
# ============================================================

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0'
    )