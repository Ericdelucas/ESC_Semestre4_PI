"""Regressões: parecer customizado substitui o automático sem perder conteúdo."""
from pathlib import Path
from io import BytesIO
import sys
import unittest
from unittest.mock import patch
import pandas as pd
from pypdf import PdfReader
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from Backend.services.report_insights import merge_notes_with_insights
from Backend.services.report_generator import insight_card
from Backend.services.custom_report_service import generate_custom_report_pdf


class ReportNotesTests(unittest.TestCase):
    def test_substituicao_por_bloco_sem_concatenar(self):
        auto = {'cover': 'Parecer automático original.', 'financial_dre': 'DRE automática.'}
        result = merge_notes_with_insights({'cover': 'TESTE'}, auto)
        self.assertEqual(result['cover'], 'TESTE')
        self.assertEqual(result['financial_dre'], auto['financial_dre'])
        self.assertEqual(merge_notes_with_insights({'cover': 'Parecer'}, auto)['cover'], 'Parecer')

    def test_vazio_ou_padrao_intacto_usa_automatico(self):
        for text in [None, '', ' \n ', ' Parecer original. ']:
            with self.subTest(text=text):
                self.assertEqual(merge_notes_with_insights({'cover': text}, {'cover': 'Parecer original.'})['cover'], 'Parecer original.')

    def test_parecer_longo_preservado_no_flowable(self):
        text = 'Análise completa. ' * 50 + 'FIM_DO_PARECER'
        self.assertIn('FIM_DO_PARECER', insight_card('', text).getPlainText())

    def test_pdf_substitui_paragrafo_e_preserva_kpis_titulos(self):
        dre = pd.DataFrame({'ano_num': [1], 'Receita Líquida': [900.], 'EBITDA': [500.], 'EBIT': [400.], 'Lucro Líquido': [330.]})
        be = pd.DataFrame({'ano_num': [1], 'Break-Even': [200.], 'Margem de Contribuição (%)': [.6], 'Margem de Segurança (%)': [.7]})
        ltv = pd.DataFrame({'ano_num': [1], 'LTV': [27000.], 'CAC': [100.], 'LTV/CAC': [270.]})
        def generate(notes):
            with patch('Backend.services.custom_report_service.insights_from_tables', return_value={'financial_dre': 'PARECER_AUTOMATICO_IDENTIFICAVEL'}):
                pdf = generate_custom_report_pdf(pd.DataFrame(), scenario='Teste', selected_blocks=['financial_dre'], notes=notes, author='Teste', profile='CEO', dre=dre, be=be, ltv=ltv, skip_charts=True)
            return ' '.join(p.extract_text() for p in PdfReader(BytesIO(pdf)).pages)
        auto = generate({})
        custom_text = 'Texto customizado completo. ' * 30 + 'FIM_DO_TEXTO_CUSTOMIZADO'
        custom = generate({'financial_dre': custom_text})
        self.assertIn('PARECER_AUTOMATICO_IDENTIFICAVEL', auto)
        self.assertNotIn('PARECER_AUTOMATICO_IDENTIFICAVEL', custom)
        self.assertIn('FIM_DO_TEXTO_CUSTOMIZADO', custom)
        for label in ['Análise de EBITDA & DRE', 'Receita Líquida', 'EBITDA', 'EBIT', 'Lucro Líquido']:
            self.assertIn(label, auto)
            self.assertIn(label, custom)
        # Apenas o parágrafo muda: números das métricas permanecem iguais.
        import re
        self.assertEqual(re.findall(r'R\$\s*[\d.,]+', auto), re.findall(r'R\$\s*[\d.,]+', custom))


if __name__ == '__main__':
    unittest.main()
