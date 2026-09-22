from flask import Flask, render_template, request, redirect, flash
import sqlite3
from datetime import datetime


app = Flask(__name__)
app.secret_key = '123456'


# ============================================================
# CONEXÃO COM O BANCO DE DADOS
# ============================================================

def get_db():
    conn = sqlite3.connect('demandas.db')
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# PÁGINA INICIAL - LISTA DE DEMANDAS
# ============================================================

@app.route('/')
def index():

    usuario_id = request.args.get('usuario_id')

    conn = get_db()

    # Busca todos os usuários para o filtro
    usuarios = conn.execute(
        '''
        SELECT id, nome, email
        FROM usuarios
        ORDER BY nome
        '''
    ).fetchall()

    # Se foi selecionado um usuário específico
    if usuario_id:

        demandas = conn.execute(
            '''
            SELECT
                demandas.id,
                demandas.titulo,
                demandas.descricao,
                usuarios.nome,
                demandas.data_criacao,
                demandas.priority,
                demandas.usuario_id
            FROM demandas
            LEFT JOIN usuarios
                ON demandas.usuario_id = usuarios.id
            WHERE demandas.usuario_id = ?
            ORDER BY demandas.id DESC
            ''',
            (usuario_id,)
        ).fetchall()

    else:

        # Mostra todas as demandas
        demandas = conn.execute(
            '''
            SELECT
                demandas.id,
                demandas.titulo,
                demandas.descricao,
                usuarios.nome,
                demandas.data_criacao,
                demandas.priority,
                demandas.usuario_id
            FROM demandas
            LEFT JOIN usuarios
                ON demandas.usuario_id = usuarios.id
            ORDER BY demandas.id DESC
            '''
        ).fetchall()

    conn.close()

    return render_template(
        'index.html',
        demandas=demandas,
        usuarios=usuarios,
        usuario_id=usuario_id
    )


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
                priority
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                novo_id,
                titulo,
                descricao,
                usuario_id,
                datetime.now(),
                priority
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

        conn.execute(
            '''
            UPDATE demandas
            SET
                titulo = ?,
                descricao = ?,
                usuario_id = ?,
                priority = ?
            WHERE id = ?
            ''',
            (
                titulo,
                descricao,
                usuario_id,
                priority,
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
            demandas.priority
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

    termo = request.args.get('q', '').strip()

    conn = get_db()

    usuarios = conn.execute(
        '''
        SELECT id, nome, email
        FROM usuarios
        ORDER BY nome
        '''
    ).fetchall()

    if termo:

        demandas = conn.execute(
            '''
            SELECT
                demandas.id,
                demandas.titulo,
                demandas.descricao,
                usuarios.nome,
                demandas.data_criacao,
                demandas.priority,
                demandas.usuario_id
            FROM demandas
            LEFT JOIN usuarios
                ON demandas.usuario_id = usuarios.id
            WHERE demandas.titulo LIKE ?
               OR demandas.descricao LIKE ?
               OR usuarios.nome LIKE ?
            ORDER BY demandas.id DESC
            ''',
            (
                f'%{termo}%',
                f'%{termo}%',
                f'%{termo}%'
            )
        ).fetchall()

    else:

        demandas = conn.execute(
            '''
            SELECT
                demandas.id,
                demandas.titulo,
                demandas.descricao,
                usuarios.nome,
                demandas.data_criacao,
                demandas.priority,
                demandas.usuario_id
            FROM demandas
            LEFT JOIN usuarios
                ON demandas.usuario_id = usuarios.id
            ORDER BY demandas.id DESC
            '''
        ).fetchall()

    conn.close()

    return render_template(
        'index.html',
        demandas=demandas,
        usuarios=usuarios,
        usuario_id=None
    )


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