import os
import sqlite3
import tempfile
import unittest

from werkzeug.security import generate_password_hash

from app import app, autenticar_usuario, registrar_novo_usuario


class TestLogin(unittest.TestCase):
    def test_autentica_senha_hashada(self):
        usuario = {"senha": generate_password_hash("admin123")}

        self.assertTrue(autenticar_usuario(usuario, "admin123"))

    def test_autentica_senha_em_texto_legacy(self):
        usuario = {"senha": "admin123"}

        self.assertTrue(autenticar_usuario(usuario, "admin123"))

    def test_cadastra_usuario_com_senha_hashada(self):
        arquivo = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        arquivo.close()
        database_anterior = app.config.get('DATABASE')
        app.config['DATABASE'] = arquivo.name

        try:
            conn = sqlite3.connect(arquivo.name)
            conn.execute(
                'CREATE TABLE IF NOT EXISTS usuarios ('
                'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'nome TEXT, '
                'email TEXT, '
                'senha TEXT'
                ')'
            )
            conn.commit()
            conn.close()

            self.assertTrue(registrar_novo_usuario('Maria', 'maria@teste.com', 'senha123'))

            conn = sqlite3.connect(arquivo.name)
            linha = conn.execute(
                "SELECT nome, email, senha FROM usuarios WHERE email = 'maria@teste.com'"
            ).fetchone()
            conn.close()

            self.assertEqual(linha[0], 'Maria')
            self.assertNotEqual(linha[2], 'senha123')
            self.assertIn(':', linha[2])
        finally:
            if database_anterior is None:
                app.config.pop('DATABASE', None)
            else:
                app.config['DATABASE'] = database_anterior
            os.remove(arquivo.name)
