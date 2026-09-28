import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta

from app import (
    app,
    api_demandas,
    buscar,
    consultar_demandas_paginadas,
    index,
    janela_de_paginas,
    obter_parametros_paginacao,
)


def criar_conexao():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript(
        '''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            email TEXT,
            senha TEXT
        );

        CREATE TABLE demandas (
            id INTEGER,
            titulo TEXT,
            descricao TEXT,
            solicitante TEXT,
            data_criacao TEXT,
            priority INTEGER,
            usuario_id INTEGER,
            status TEXT DEFAULT 'aberta',
            responsible_id INTEGER
        );

        INSERT INTO usuarios VALUES (1, 'Ana Lima', 'ana@example.com', 'x');
        INSERT INTO usuarios VALUES (2, 'Bruno Souza', 'bruno@example.com', 'x');
        '''
    )
    return conn


def popular_demandas(conn, quantidade=25):
    """
    O menor id recebe a data mais recente, para distinguir
    ordenação por data de criação da ordenação por id.
    """
    base = datetime(2026, 1, 1, 8, 0, 0)

    for i in range(quantidade):
        data = (base + timedelta(days=quantidade - 1 - i)).strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        usuario_id = 1 if i % 2 == 0 else 2
        nome = 'Ana Lima' if usuario_id == 1 else 'Bruno Souza'
        titulo = 'Relatorio especial' if i == 0 else f'Demanda {i + 1:02d}'

        conn.execute(
            '''
            INSERT INTO demandas (
                id, titulo, descricao, solicitante,
                data_criacao, priority, usuario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                i + 1,
                titulo,
                'Descricao de teste',
                nome,
                data,
                (i % 3) + 1,
                usuario_id,
            ),
        )

    conn.commit()


def salvar_banco(caminho, quantidade=25):
    conn = sqlite3.connect(caminho)
    conn.executescript(
        '''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            email TEXT,
            senha TEXT
        );

        CREATE TABLE demandas (
            id INTEGER,
            titulo TEXT,
            descricao TEXT,
            solicitante TEXT,
            data_criacao TEXT,
            priority INTEGER,
            usuario_id INTEGER,
            status TEXT DEFAULT 'aberta',
            responsible_id INTEGER
        );

        INSERT INTO usuarios VALUES (1, 'Ana Lima', 'ana@example.com', 'x');
        INSERT INTO usuarios VALUES (2, 'Bruno Souza', 'bruno@example.com', 'x');
        '''
    )
    if quantidade:
        popular_demandas(conn, quantidade)
    else:
        conn.commit()
    conn.close()


class TestJanelaDePaginas(unittest.TestCase):

    def test_sem_paginas(self):
        self.assertEqual(janela_de_paginas(1, 0), [])

    def test_poucas_paginas_mostra_todas(self):
        self.assertEqual(janela_de_paginas(2, 4), [1, 2, 3, 4])

    def test_inicio_da_listagem(self):
        self.assertEqual(janela_de_paginas(1, 10), [1, 2, 3, 4, 5])

    def test_meio_da_listagem(self):
        self.assertEqual(janela_de_paginas(6, 10), [4, 5, 6, 7, 8])

    def test_fim_da_listagem(self):
        self.assertEqual(janela_de_paginas(10, 10), [6, 7, 8, 9, 10])


class TestParametrosPaginacao(unittest.TestCase):

    def test_valores_padrao(self):
        with app.test_request_context('/api/demandas'):
            self.assertEqual(obter_parametros_paginacao(), (1, 20))

    def test_page_e_limit_validos(self):
        with app.test_request_context('/api/demandas?page=2&limit=50'):
            self.assertEqual(obter_parametros_paginacao(), (2, 50))

    def test_page_invalida_volta_para_primeira(self):
        for pagina in ('0', '-4', 'abc'):
            with self.subTest(pagina=pagina):
                with app.test_request_context(f'/api/demandas?page={pagina}'):
                    page, _ = obter_parametros_paginacao()
                    self.assertEqual(page, 1)

    def test_limit_fora_da_lista_usa_padrao(self):
        for limite in ('7', '0', 'abc'):
            with self.subTest(limite=limite):
                with app.test_request_context(f'/api/demandas?limit={limite}'):
                    _, limit = obter_parametros_paginacao()
                    self.assertEqual(limit, 20)


class TestConsultaPaginada(unittest.TestCase):

    def setUp(self):
        self.conn = criar_conexao()
        popular_demandas(self.conn, 25)

    def tearDown(self):
        self.conn.close()

    def test_primeira_pagina_limita_quantidade_e_metadados(self):
        resultado = consultar_demandas_paginadas(self.conn, 1, 10)

        self.assertEqual(len(resultado['demandas']), 10)
        self.assertEqual(resultado['total_items'], 25)
        self.assertEqual(resultado['total_pages'], 3)
        self.assertEqual(resultado['current_page'], 1)
        self.assertEqual(resultado['inicio'], 1)
        self.assertEqual(resultado['fim'], 10)

    def test_ordenacao_por_data_de_criacao_decrescente(self):
        resultado = consultar_demandas_paginadas(self.conn, 1, 10)
        datas = [item['data_criacao'] for item in resultado['demandas']]

        self.assertEqual(datas, sorted(datas, reverse=True))
        self.assertEqual(resultado['demandas'][0]['id'], 1)
        self.assertEqual(resultado['demandas'][-1]['id'], 10)

    def test_segunda_pagina_usa_offset(self):
        resultado = consultar_demandas_paginadas(self.conn, 2, 10)
        ids = [item['id'] for item in resultado['demandas']]

        self.assertEqual(ids, list(range(11, 21)))
        self.assertEqual(resultado['inicio'], 11)
        self.assertEqual(resultado['fim'], 20)
        self.assertEqual(resultado['current_page'], 2)

    def test_ultima_pagina_parcial(self):
        resultado = consultar_demandas_paginadas(self.conn, 3, 10)

        self.assertEqual(len(resultado['demandas']), 5)
        self.assertEqual(resultado['inicio'], 21)
        self.assertEqual(resultado['fim'], 25)

    def test_pagina_alem_do_fim_volta_para_a_ultima(self):
        resultado = consultar_demandas_paginadas(self.conn, 99, 10)

        self.assertEqual(resultado['current_page'], 3)
        self.assertEqual(resultado['fim'], 25)

    def test_limite_de_20_e_50(self):
        vinte = consultar_demandas_paginadas(self.conn, 1, 20)
        cinquenta = consultar_demandas_paginadas(self.conn, 1, 50)

        self.assertEqual(len(vinte['demandas']), 20)
        self.assertEqual(vinte['total_pages'], 2)
        self.assertEqual(len(cinquenta['demandas']), 25)
        self.assertEqual(cinquenta['total_pages'], 1)

    def test_filtro_por_solicitante(self):
        resultado = consultar_demandas_paginadas(
            self.conn, 1, 10, usuario_id=1
        )

        self.assertEqual(resultado['total_items'], 13)
        self.assertTrue(
            all(item['usuario_id'] == 1 for item in resultado['demandas'])
        )

    def test_busca_por_termo(self):
        resultado = consultar_demandas_paginadas(
            self.conn, 1, 10, termo='especial'
        )

        self.assertEqual(resultado['total_items'], 1)
        self.assertEqual(resultado['demandas'][0]['titulo'], 'Relatorio especial')

    def test_banco_vazio(self):
        conn = criar_conexao()
        resultado = consultar_demandas_paginadas(conn, 1, 10)
        conn.close()

        self.assertEqual(resultado['demandas'], [])
        self.assertEqual(resultado['total_items'], 0)
        self.assertEqual(resultado['total_pages'], 0)
        self.assertEqual(resultado['current_page'], 1)
        self.assertEqual(resultado['inicio'], 0)
        self.assertEqual(resultado['fim'], 0)
        self.assertEqual(resultado['paginas'], [])


class BancoTemporario(unittest.TestCase):

    quantidade = 25

    def setUp(self):
        self.arquivo = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.arquivo.close()
        self.database_original = app.config.get('DATABASE')
        app.config['DATABASE'] = self.arquivo.name
        salvar_banco(self.arquivo.name, self.quantidade)

    def tearDown(self):
        if self.database_original is None:
            app.config.pop('DATABASE', None)
        else:
            app.config['DATABASE'] = self.database_original
        os.remove(self.arquivo.name)


class TestApiDemandas(BancoTemporario):

    def test_resposta_traz_lista_e_metadados(self):
        with app.test_request_context('/api/demandas?page=1&limit=10'):
            resposta = api_demandas()
            dados = resposta.get_json()

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(set(dados), {
            'demandas',
            'totalItems',
            'totalPages',
            'currentPage',
        })
        self.assertEqual(dados['totalItems'], 25)
        self.assertEqual(dados['totalPages'], 3)
        self.assertEqual(dados['currentPage'], 1)
        self.assertEqual(len(dados['demandas']), 10)

    def test_segunda_pagina_nao_repete_a_primeira(self):
        with app.test_request_context('/api/demandas?page=1&limit=10'):
            primeira = api_demandas().get_json()
        with app.test_request_context('/api/demandas?page=2&limit=10'):
            segunda = api_demandas().get_json()

        ids_primeira = {item['id'] for item in primeira['demandas']}
        ids_segunda = {item['id'] for item in segunda['demandas']}

        self.assertEqual(len(ids_segunda), 10)
        self.assertTrue(ids_primeira.isdisjoint(ids_segunda))
        self.assertEqual(segunda['currentPage'], 2)

    def test_mais_recentes_primeiro(self):
        with app.test_request_context('/api/demandas?limit=10'):
            dados = api_demandas().get_json()

        datas = [item['data_criacao'] for item in dados['demandas']]
        self.assertEqual(datas, sorted(datas, reverse=True))
        self.assertEqual(dados['demandas'][0]['titulo'], 'Relatorio especial')

    def test_limit_invalido_usa_vinte(self):
        with app.test_request_context('/api/demandas?limit=15'):
            dados = api_demandas().get_json()

        self.assertEqual(len(dados['demandas']), 20)
        self.assertEqual(dados['totalPages'], 2)


class TestApiSemRegistros(BancoTemporario):

    quantidade = 0

    def test_metadados_de_lista_vazia(self):
        with app.test_request_context('/api/demandas'):
            dados = api_demandas().get_json()

        self.assertEqual(dados['demandas'], [])
        self.assertEqual(dados['totalItems'], 0)
        self.assertEqual(dados['totalPages'], 0)
        self.assertEqual(dados['currentPage'], 1)


class TestListagemHtml(BancoTemporario):

    def test_indicador_e_controles_na_primeira_pagina(self):
        with app.test_request_context('/?limit=10'):
            html = index()

        self.assertIn('Exibindo 1-10 de 25', html)
        self.assertIn('Itens por página', html)
        self.assertIn('Anterior', html)
        self.assertIn('Próxima', html)
        self.assertIn('href="/?page=2&limit=10"', html)
        self.assertIn('href="/?page=3&limit=10"', html)
        self.assertIn('class="desabilitado"', html)
        self.assertIn('value="10"', html)
        self.assertIn('value="20"', html)
        self.assertIn('value="50"', html)

    def test_ultima_pagina_desabilita_proxima(self):
        with app.test_request_context('/?page=3&limit=10'):
            html = index()

        self.assertIn('Exibindo 21-25 de 25', html)
        self.assertIn('href="/?page=2&limit=10"', html)
        self.assertNotIn('href="/?page=4&limit=10"', html)

    def test_filtro_preserva_solicitante_na_paginacao(self):
        with app.test_request_context('/?usuario_id=1&limit=10'):
            html = index()

        self.assertIn('Exibindo 1-10 de 13', html)
        self.assertIn('href="/?page=2&limit=10&usuario_id=1"', html)

    def test_busca_paginada(self):
        with app.test_request_context('/buscar?q=especial&limit=10'):
            html = buscar()

        self.assertIn('Exibindo 1-1 de 1', html)
        self.assertIn('Relatorio especial', html)
        self.assertIn('id="q-paginacao" value="especial"', html)


if __name__ == '__main__':
    unittest.main()
