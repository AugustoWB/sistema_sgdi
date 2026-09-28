import os
import sqlite3
import tempfile
import unittest

from app import (
    api_demandas,
    app,
    consultar_demandas_paginadas,
    escapar_curinga_like,
    index,
    normalizar_termo_busca,
)
from test_paginacao import criar_conexao, popular_demandas, salvar_banco


class TestNormalizacaoDaBusca(unittest.TestCase):

    def test_termo_vazio(self):
        self.assertIsNone(normalizar_termo_busca(None))
        self.assertIsNone(normalizar_termo_busca('   '))

    def test_remove_controle_e_espacos(self):
        self.assertEqual(normalizar_termo_busca(' \x00 login \n '), 'login')

    def test_limita_tamanho(self):
        self.assertEqual(len(normalizar_termo_busca('a' * 150)), 100)

    def test_escapa_curingas_do_like(self):
        self.assertEqual(escapar_curinga_like('%'), '\\%')
        self.assertEqual(escapar_curinga_like('_'), '\\_')
        self.assertEqual(escapar_curinga_like('\\'), '\\\\')


class TestBuscaNoBanco(unittest.TestCase):

    def setUp(self):
        self.conn = criar_conexao()
        popular_demandas(self.conn, 25)
        self.conn.execute(
            '''
            INSERT INTO demandas (
                id, titulo, descricao, solicitante,
                data_criacao, priority, usuario_id
            ) VALUES (99, '100%_ok', 'texto interno', 'Ana Lima', '2026-06-01 10:00:00', 1, 1)
            '''
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_encontra_por_titulo(self):
        resultado = consultar_demandas_paginadas(self.conn, 1, 10, termo='especial')

        self.assertEqual(resultado['total_items'], 1)
        self.assertEqual(resultado['demandas'][0]['titulo'], 'Relatorio especial')

    def test_encontra_por_id(self):
        resultado = consultar_demandas_paginadas(self.conn, 1, 10, termo='99')
        ids = [item['id'] for item in resultado['demandas']]

        self.assertIn(99, ids)

    def test_nao_busca_descricao_nem_solicitante(self):
        por_descricao = consultar_demandas_paginadas(
            self.conn, 1, 10, termo='texto interno'
        )
        por_nome = consultar_demandas_paginadas(self.conn, 1, 10, termo='Bruno Souza')

        self.assertEqual(por_descricao['total_items'], 0)
        self.assertEqual(por_nome['total_items'], 0)

    def test_percentual_e_underscore_sao_literais(self):
        por_percentual = consultar_demandas_paginadas(self.conn, 1, 50, termo='%')
        por_underscore = consultar_demandas_paginadas(self.conn, 1, 50, termo='_')

        self.assertEqual(
            [item['titulo'] for item in por_percentual['demandas']],
            ['100%_ok'],
        )
        self.assertEqual(
            [item['titulo'] for item in por_underscore['demandas']],
            ['100%_ok'],
        )

    def test_aspas_nao_alteram_a_consulta(self):
        resultado = consultar_demandas_paginadas(
            self.conn, 1, 10, termo="' OR 1=1 --"
        )

        self.assertEqual(resultado['total_items'], 0)


class TestApiDeBusca(unittest.TestCase):

    def setUp(self):
        self.arquivo = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.arquivo.close()
        self.database_original = app.config.get('DATABASE')
        app.config['DATABASE'] = self.arquivo.name
        salvar_banco(self.arquivo.name, 25)

        conn = sqlite3.connect(self.arquivo.name)
        conn.execute(
            '''
            INSERT INTO demandas (
                id, titulo, descricao, solicitante,
                data_criacao, priority, usuario_id
            ) VALUES (99, '100%_ok', 'texto interno', 'Ana Lima', '2026-06-01 10:00:00', 1, 1)
            '''
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        if self.database_original is None:
            app.config.pop('DATABASE', None)
        else:
            app.config['DATABASE'] = self.database_original
        os.remove(self.arquivo.name)

    def test_api_busca_titulo(self):
        with app.test_request_context('/api/demandas?q=especial&limit=10'):
            dados = api_demandas().get_json()

        self.assertEqual(dados['totalItems'], 1)
        self.assertEqual(dados['demandas'][0]['id'], 1)

    def test_api_busca_id(self):
        with app.test_request_context('/api/demandas?q=99&limit=10'):
            dados = api_demandas().get_json()

        ids = [item['id'] for item in dados['demandas']]
        self.assertEqual(ids, [99])

    def test_api_percentual_nao_retorna_todos(self):
        with app.test_request_context('/api/demandas?q=%25&limit=50'):
            dados = api_demandas().get_json()

        self.assertEqual(dados['totalItems'], 1)
        self.assertEqual(dados['demandas'][0]['titulo'], '100%_ok')

    def test_listagem_mostra_busca_por_titulo(self):
        with app.test_request_context('/?q=especial&limit=10'):
            html = index()

        self.assertIn('Exibindo 1-1 de 1', html)
        self.assertIn('Relatorio especial', html)
        self.assertIn('value="especial"', html)
