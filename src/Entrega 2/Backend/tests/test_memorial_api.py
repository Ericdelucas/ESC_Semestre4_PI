"""Regressões do memorial dinâmico: filtros, PDF binário e botão do dashboard."""
from io import BytesIO
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from pypdf import PdfReader
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'Frontend'))
from Backend.main import app
from Backend.services.memorial_report import gerar_memorial_pdf


def fixture():
    rows = []
    for scene, factor in [('Cen_A', 1), ('Cen_B', 2)]:
        for year in [1, 2]:
            values = {
                'DRE - Receita': 1000 * factor * year,
                'DRE - Tributos': -100 * factor * year,
                'DRE - Custos': -300 * factor * year,
                'DRE - EBITDA': 500 * factor * year,
                'DRE - Resultado Operacional': 400 * factor * year,
                'DRE - Resultado Financeiro': -20,
                'DRE - Imposto de Renda e Contribuição Social': -50,
                'DRE - Resultado Líquido': 330 * factor * year,
                'DRE - Depreciação e Amortização': -100,
                'DRE - Despesas Financeiras': -20,
                'DRE - Outros Resultados Operacionais': -100,
                'BAL - Ativo Circulante': 1000,
                'BAL - Passivo Circulante': 200,
                'BAL - Realizável a Longo Prazo': 300,
                'BAL - Exigível a Longo Prazo': 100,
                'BAL - Total do Ativo': 2000,
                'FLU - Investimentos': -200,
            }
            for account, value in values.items():
                rows.append([f'Ano {year}', scene, account, value, year])
    df = pd.DataFrame(rows, columns=['ANO','CENA','CONTA','VALOR','ano_num'])
    ranking = pd.DataFrame({'CENA':['Cen_A','Cen_B'], 'caixa_ano12':[100,200], 'liquidez':[5,5], 'selo':['Normal','Normal']})
    return df, pd.DataFrame(), ranking


def pdf_text(data):
    return '\n'.join(p.extract_text() for p in PdfReader(BytesIO(data)).pages)


class MemorialApiTests(unittest.TestCase):
    def test_endpoint_calcula_e_responde_pdf(self):
        with patch('Backend.routers.report_router.prepare_dashboard_data', side_effect=fixture) as pipeline:
            client = TestClient(app)
            a = client.post('/api/v1/relatorio/memorial', json={'scenario':'Cen_A','year':1})
            b = client.post('/api/v1/relatorio/memorial', json={'scenario':'Cen_B','year':2})
            self.assertEqual(pipeline.call_count, 2)
        self.assertEqual(a.status_code, 200)
        self.assertTrue(a.headers['content-type'].startswith('application/pdf'))
        self.assertIn('attachment', a.headers['content-disposition'])
        self.assertEqual(a.headers['cache-control'], 'no-store')
        ta, tb = pdf_text(a.content), pdf_text(b.content)
        self.assertIn('900,00', ta)
        self.assertIn('3.600,00', tb)
        self.assertNotEqual(ta, tb)
        self.assertIn('✓', ta)
        self.assertIn('CAMPO', ta)
        self.assertNotIn('StoreOrder', ta)
        self.assertNotIn('1.2 EBITDA', tb.split('Ano 2')[0])

    def test_todos_media_por_conta_e_anos_separados(self):
        df, _, ranking = fixture()
        text = pdf_text(gerar_memorial_pdf(df, ranking, scenario='Todos'))
        self.assertIn('1.350,00', text)
        self.assertIn('2.700,00', text)
        self.assertIn('Ano 1', text)
        self.assertIn('Ano 2', text)

    def test_filtros_invalidos_e_falha_da_fonte(self):
        with patch('Backend.routers.report_router.prepare_dashboard_data', side_effect=fixture):
            client = TestClient(app)
            for data in [{'scenario':'ausente'}, {'year':12}, {'year':0}]:
                with self.subTest(data=data):
                    self.assertEqual(client.post('/api/v1/relatorio/memorial', json=data).status_code,422)
        with patch('Backend.routers.report_router.prepare_dashboard_data', side_effect=RuntimeError('cache')):
            self.assertEqual(TestClient(app).post('/api/v1/relatorio/memorial',json={}).status_code,503)

    def test_botao_usa_endpoint_e_entrega_os_mesmos_bytes(self):
        from src.views import report
        state = {}
        st = MagicMock()
        st.session_state = state
        st.button.return_value = True
        data = b'%PDF-resultado-do-backend'
        with patch.object(report, 'st', st), patch('src.controllers.data_input.has_custom_data',return_value=False), patch('src.models.api_client.post_pdf',return_value=data) as post:
            report._render_memorial('Cen_B', 2)
            post.assert_called_once_with('/api/v1/relatorio/memorial',{'scenario':'Cen_B','year':2})
            self.assertEqual(st.download_button.call_args.kwargs['data'],data)
            st.button.return_value = False
            report._render_memorial('Cen_A', 1)
            self.assertNotIn('memorial_api_download',state)

    def test_dados_importados_nao_recebem_pdf_da_base_errada(self):
        from src.views import report
        st = MagicMock(); st.session_state = {}
        with patch.object(report,'st',st),patch('src.controllers.data_input.has_custom_data',return_value=True),patch('src.models.api_client.post_pdf') as post:
            report._render_memorial('Cen_A',1)
            post.assert_not_called()
            st.warning.assert_called_once()


if __name__ == '__main__':
    unittest.main()
