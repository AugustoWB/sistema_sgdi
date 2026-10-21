import os
import tempfile
import unittest
from datetime import datetime

from sistema_logs.registro import TIPOS, listar_logs, registrar
from sistema_logs.visualizar import app as app_logs


class TestRegistroDeLogs(unittest.TestCase):

    def setUp(self):
        self.arquivo = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.arquivo.close()
        self.original = os.environ.get('SGDI_LOGS_DB')
        os.environ['SGDI_LOGS_DB'] = self.arquivo.name

    def tearDown(self):
        if self.original is None:
            os.environ.pop('SGDI_LOGS_DB', None)
        else:
            os.environ['SGDI_LOGS_DB'] = self.original
        os.remove(self.arquivo.name)

    def test_grava_e_lista_o_evento_mais_recente(self):
        momento = datetime(2026, 10, 6, 21, 0, 0)
        self.assertTrue(registrar(
            'demanda_criada',
            'Demanda 8 criada: Papo de irimbora',
            demanda_id=8,
            detalhe='Status Aberta, prioridade Alta',
            agora=momento,
        ))

        logs = listar_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['tipo'], 'demanda_criada')
        self.assertEqual(logs[0]['demanda_id'], 8)
        self.assertEqual(logs[0]['data'], '2026-10-06 21:00:00')
        self.assertIn('Papo de irimbora', logs[0]['mensagem'])

    def test_filtra_por_tipo_e_ignora_tipo_desconhecido(self):
        registrar('comentario', 'Comentário de Ana na demanda 3', demanda_id=3)
        registrar('exportacao', 'Relatório PDF exportado', detalhe='Status: Todos')

        so_exportacao = listar_logs('exportacao')
        self.assertEqual(len(so_exportacao), 1)
        self.assertEqual(so_exportacao[0]['tipo'], 'exportacao')
        self.assertFalse(registrar('acesso', 'página aberta'))
        self.assertEqual(len(listar_logs()), 2)

    def test_pagina_mostra_o_evento_e_o_filtro(self):
        registrar(
            'demanda_excluida',
            'Demanda 4 excluída: Adicionar filtros',
            demanda_id=4,
        )

        with app_logs.test_request_context('/?tipo=demanda_excluida'):
            html = app_logs.view_functions['index']()

        self.assertIn('Demanda excluída', html)
        self.assertIn('Adicionar filtros', html)
        self.assertIn('Demanda 4', html)
        self.assertIn(TIPOS['comentario'], html)
