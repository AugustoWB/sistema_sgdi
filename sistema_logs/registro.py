import os
import sqlite3
from datetime import datetime


PASTA = os.path.dirname(os.path.abspath(__file__))

TIPOS = {
    'demanda_criada': 'Demanda criada',
    'demanda_atualizada': 'Demanda atualizada',
    'demanda_excluida': 'Demanda excluída',
    'comentario': 'Comentário',
    'exportacao': 'Relatório exportado',
}


def caminho_banco():
    return os.environ.get(
        'SGDI_LOGS_DB',
        os.path.join(PASTA, 'logs.db'),
    )


def conectar():
    conn = sqlite3.connect(caminho_banco())
    conn.row_factory = sqlite3.Row
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            tipo TEXT NOT NULL,
            demanda_id INTEGER,
            mensagem TEXT NOT NULL,
            detalhe TEXT
        )
        '''
    )
    conn.execute(
        'CREATE INDEX IF NOT EXISTS idx_logs_data ON logs (data)'
    )
    conn.execute(
        'CREATE INDEX IF NOT EXISTS idx_logs_tipo ON logs (tipo)'
    )
    return conn


def registrar(tipo, mensagem, demanda_id=None, detalhe=None, agora=None):
    """Grava um evento importante. Falha de log não interrompe o SGDI."""

    if tipo not in TIPOS:
        return False

    momento = agora or datetime.now()
    texto_data = momento.strftime('%Y-%m-%d %H:%M:%S')

    try:
        conn = conectar()
        conn.execute(
            '''
            INSERT INTO logs (data, tipo, demanda_id, mensagem, detalhe)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (texto_data, tipo, demanda_id, mensagem, detalhe),
        )
        conn.commit()
        conn.close()
    except sqlite3.Error:
        return False

    return True


def listar_logs(tipo=None, limite=150):
    conn = conectar()
    if tipo in TIPOS:
        linhas = conn.execute(
            '''
            SELECT id, data, tipo, demanda_id, mensagem, detalhe
            FROM logs
            WHERE tipo = ?
            ORDER BY id DESC
            LIMIT ?
            ''',
            (tipo, limite),
        ).fetchall()
    else:
        linhas = conn.execute(
            '''
            SELECT id, data, tipo, demanda_id, mensagem, detalhe
            FROM logs
            ORDER BY id DESC
            LIMIT ?
            ''',
            (limite,),
        ).fetchall()
    conn.close()
    return linhas
