"""Interacao real dos widgets Streamlit, sem depender do CSV de producao."""
import sys
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'Frontend'))

APP = '''
import pandas as pd
from src.views.persona_tabs import formula_builder as builder
builder._cached_variables = lambda *args: {'Financeiro::EBITDA': 100., 'Financeiro::Capex': 20.}
builder.render_formula_builder('teste', pd.DataFrame(), pd.DataFrame(), 'Todos', 'Todos')
'''


class BuilderTests(unittest.TestCase):
    def test_free_text_preview_insertion_and_validation(self):
        app = AppTest.from_string(APP).run()
        self.assertFalse(app.exception)
        app.text_input(key='formula_expression_teste').set_value('(EBITDA - Capex) / 2').run()
        self.assertEqual(app.metric[0].value, '40,00')
        self.assertFalse(app.button(key='formula_save_teste').disabled)
        app.selectbox(key='formula_var_teste').select('Financeiro::Capex').run()
        self.assertTrue(app.text_input(key='formula_expression_teste').value.endswith(' [Financeiro::Capex]'))
        app.text_input(key='formula_expression_teste').set_value('EBITDA / 0').run()
        self.assertTrue(app.error)
        self.assertTrue(app.button(key='formula_save_teste').disabled)
        self.assertFalse(app.metric)
        self.assertFalse(app.exception)

    def test_creation_and_test_controls_visible_before_metric_loading(self):
        app = AppTest.from_string(APP).run()
        self.assertEqual(app.button(key='formula_test_teste').label, 'Testar Fórmula')
        self.assertEqual(app.button(key='formula_save_teste').label, 'Criar fórmula / Salvar KPI')
        self.assertTrue(app.button(key='formula_save_teste').disabled)
        app.button(key='formula_test_teste').click().run()
        self.assertTrue(app.info)
        app.text_input(key='formula_expression_teste').set_value('10 + 20 / 2').run()
        self.assertEqual(app.metric[0].value, '20,00')
        self.assertFalse(app.exception)

    def test_general_resolution_and_source_selection(self):
        script = APP.replace("'Financeiro::Capex': 20.", "'Financeiro::Capex': 20., 'Financeiro::ROIC': 0.1, 'Catalogo::Rentabilidade · ROIC': 10., 'CSV::DRE - Despesas Financeiras': 8.")
        app = AppTest.from_string(script).run()
        expression = '(ROIC * EBITDA) / (Capex + 1) - (Despesa_Financeira * 0.25)'
        app.text_input(key='formula_expression_teste').set_value(expression).run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertEqual(app.metric[0].value, '-1,52')
        app.selectbox(key='formula_source_teste_roic').select('Catalogo::Rentabilidade · ROIC').run()
        self.assertEqual(app.metric[0].value, '45,62')
        app.button(key='formula_save_teste').click().run()
        saved = app.session_state['custom_financial_analyses']['teste'][0]
        self.assertEqual(saved['choices']['roic'], 'Catalogo::Rentabilidade · ROIC')
        self.assertFalse(app.exception)

    def test_format_and_save_after_preview(self):
        app = AppTest.from_string(APP).run()
        app.text_input(key='formula_expression_teste').set_value('EBITDA - Capex').run()
        app.selectbox(key='formula_style_teste').select('Moeda').run()
        self.assertEqual(app.metric[0].value, 'R$ 80,00')
        app.selectbox(key='formula_style_teste').select('Percentual').run()
        self.assertEqual(app.metric[0].value, '80,00%')
        app.button(key='formula_save_teste').click().run()
        saved = app.session_state['custom_financial_analyses']['teste'][0]
        self.assertEqual(saved['expression'], 'EBITDA - Capex')
        self.assertEqual(saved['kind'], 'formula')
        self.assertFalse(app.exception)


if __name__ == '__main__':
    unittest.main()
