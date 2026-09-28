import os
import sqlite3
import tempfile
import unittest

from app import (
    api_demandas,
    app,
    consultar_demandas_paginadas,
    get_db,
    index,
)
from test_paginacao import criar_conexao, popular_demandas, salvar_banco


class TestFiltrosCombinados(unittest.TestCase):

    def setUp(self):
        self.conn = criar_conexao()
        popular_demandas(self.conn, 25)
        self.conn.execute(
            '''
            UPDATE demandas
            SET status = 'em_andamento', priority = 3, responsible_id = 1
            WHERE id = 1
            '''
        )
        self.conn.execute(
            '''
            UPDATE demandas
            SET status = 'em_andamento', priority = 1, responsible_id = 1
            WHERE id = 2
            '''
        )
        self.conn.execute(
            '''
            UPDATE demandas
            SET status = 'aberta', priority = 3, responsible_id = 2
            WHERE id = 3
            '''
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_status_prioridade_e_responsavel_juntos(self):
        resultado = consultar_demandas_paginadas(
            self.conn,
            1,
            10,
            status='em_andamento',
            priority=3,
            responsible_id=1,
        )

        self.assertEqual(resultado['total_items'], 1)
        self.assertEqual(resultado['demandas'][0]['id'], 1)
        self.assertEqual(resultado['demandas'][0]['status'], 'em_andamento')

    def test_status_sozinho(self):
        resultado = consultar_demandas_paginadas(
            self.conn, 1, 50, status='em_andamento'
        )

        ids = {item['id'] for item in resultado['demandas']}
        self.assertEqual(ids, {1, 2})

    def test_status_invalido_nao_filtra(self):
        resultado = consultar_demandas_paginadas(
            self.conn, 1, 50, status='inexistente'
        )

        self.assertEqual(resultado['total_items'], 25)


class TestFiltrosNaListagem(unittest.TestCase):

    def setUp(self):
        self.arquivo = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.arquivo.close()
        self.database_original = app.config.get('DATABASE')
        app.config['DATABASE'] = self.arquivo.name
        salvar_banco(self.arquivo.name, 25)

    def tearDown(self):
        if self.database_original is None:
            app.config.pop('DATABASE', None)
        else:
            app.config['DATABASE'] = self.database_original
        os.remove(self.arquivo.name)

    def test_cria_indices_de_filtro(self):
        conn = get_db()
        nomes = {
            linha[1]
            for linha in conn.execute('PRAGMA index_list(demandas)')
        }
        conn.close()

        self.assertIn('idx_demandas_status', nomes)
        self.assertIn('idx_demandas_priority', nomes)
        self.assertIn('idx_demandas_responsible_id', nomes)

    def test_url_guarda_os_filtros_na_paginacao(self):
        with app.test_request_context('/?status=aberta&limit=10'):
            html = index()

        self.assertIn('href="/?page=2&limit=10&status=aberta"', html)
        self.assertIn('Limpar Filtros', html)

        with app.test_request_context('/?status=aberta&priority=3&responsibleId=1&limit=10'):
            html = index()

        self.assertIn('name="status" value="aberta"', html)
        self.assertIn('name="priority" value="3"', html)
        self.assertIn('name="responsibleId" value="1"', html)

    def test_empty_state_quando_filtros_nao_encontram_nada(self):
        with app.test_request_context('/?status=cancelada&priority=3&limit=10'):
            html = index()

        self.assertIn('Nenhuma demanda encontrada com estes filtros', html)
        self.assertIn('Exibindo 0 de 0', html)

    def test_api_aceita_query_params(self):
        conn = sqlite3.connect(self.arquivo.name)
        conn.execute(
            '''
            UPDATE demandas
            SET status = 'em_andamento', priority = 3, responsible_id = 1
            WHERE id = 1
            '''
        )
        conn.commit()
        conn.close()

        with app.test_request_context(
            '/api/demandas?status=em_andamento&priority=3&responsibleId=1&limit=10'
        ):
            dados = api_demandas().get_json()

        self.assertEqual(dados['totalItems'], 1)
        self.assertEqual(dados['demandas'][0]['id'], 1)
        self.assertEqual(dados['demandas'][0]['responsibleId'], 1)
        self.assertEqual(dados['currentPage'], 1)
