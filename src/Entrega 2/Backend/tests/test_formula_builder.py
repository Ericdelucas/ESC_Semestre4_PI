"""Visual payload to calculation, validation and Streamlit save flow."""
import sys
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'Frontend'))
from src.components.formula_blocks import blocks_expression
from Backend.services.formula_metrics import FormulaError, evaluate_formula
from src.components import formula_blocks
from src.views.persona_tabs import formula_builder

ORIGINAL_COMPONENT = formula_blocks._component
ORIGINAL_VARIABLES = formula_builder._cached_variables

APP = '''
import pandas as pd
import streamlit as st
from src.components import formula_blocks
from src.views.persona_tabs import formula_builder as builder
formula_blocks._component = lambda **kwargs: {'blocks': st.session_state.get('test_blocks', kwargs['initial_blocks'])}
builder._cached_variables = lambda *args, **kwargs: st.session_state.get('test_variables', {'Financeiro::EBITDA': 100., 'Financeiro::Capex': 20.})
builder.render_formula_builder('teste', pd.DataFrame(), pd.DataFrame(), 'Todos', 'Todos')
'''


def metric(name):
    return {'kind': 'metric', 'value': name}


def op(value):
    return {'kind': 'operator', 'value': value}


def number(value):
    return {'kind': 'number', 'value': value}


class BuilderTests(unittest.TestCase):
    def tearDown(self):
        formula_blocks._component = ORIGINAL_COMPONENT
        formula_builder._cached_variables = ORIGINAL_VARIABLES

    def build(self, blocks):
        app = AppTest.from_string(APP).run()
        app.session_state['test_blocks'] = blocks
        return app.run()

    def test_grouped_blocks_preview_and_validation(self):
        blocks = [op('('), metric('Financeiro::EBITDA'), op('-'), metric('Financeiro::Capex'), op(')'), op('/'), number('2')]
        app = self.build(blocks)
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, '40,00')
        self.assertFalse(app.button(key='formula_save_teste').disabled)
        self.assertEqual(app.session_state['formula_blocks_teste'], blocks)
        app.session_state['test_blocks'] = [metric('Financeiro::EBITDA'), op('/'), number('0')]
        app.run()
        self.assertTrue(app.error)
        self.assertTrue(app.button(key='formula_save_teste').disabled)
        self.assertFalse(app.metric)

    def test_empty_incomplete_and_clear(self):
        app = self.build([])
        self.assertEqual(len(app.text_input), 1)  # Only the KPI name remains free text.
        self.assertTrue(app.button(key='formula_save_teste').disabled)
        app.button(key='formula_test_teste').click().run()
        self.assertTrue(app.info)
        app.session_state['test_blocks'] = [number('10'), op('+')]
        app.run()
        self.assertTrue(app.error)
        self.assertTrue(app.button(key='formula_save_teste').disabled)
        app.session_state['test_blocks'] = [number('10'), op('+'), number('20'), op('/'), number('2')]
        app.run()
        self.assertEqual(app.metric[0].value, '20,00')
        app.button(key='formula_test_teste').click().run()
        self.assertEqual(app.metric[0].value, '20,00')
        app.session_state['test_blocks'] = []
        app.run()
        self.assertFalse(app.metric)
        self.assertTrue(app.button(key='formula_save_teste').disabled)

    def test_source_format_and_save(self):
        blocks = [metric('Catalogo::Rentabilidade · ROIC'), op('*'), metric('Financeiro::EBITDA')]
        app = self.build([])
        app.session_state['test_variables'] = {'Financeiro::ROIC': 0.1, 'Catalogo::Rentabilidade · ROIC': 10., 'Financeiro::EBITDA': 100.}
        app.session_state['test_blocks'] = blocks
        app.run()
        self.assertEqual(app.metric[0].value, '1.000,00')
        app.selectbox(key='formula_style_teste').select('Moeda').run()
        self.assertEqual(app.metric[0].value, 'R$ 1.000,00')
        app.selectbox(key='formula_style_teste').select('Percentual').run()
        self.assertEqual(app.metric[0].value, '1.000,00%')
        app.button(key='formula_save_teste').click().run()
        saved = app.session_state['custom_financial_analyses']['teste'][0]
        self.assertEqual(saved['blocks'], blocks)
        self.assertEqual(saved['expression'], '[Catalogo::Rentabilidade · ROIC] * [Financeiro::EBITDA]')
        self.assertEqual(saved['kind'], 'formula')
        self.assertEqual(app.session_state['nav_key'], 'custom::' + saved['id'])
        self.assertFalse(app.session_state['modal_custom_analysis_open_teste'])
        self.assertFalse(app.exception)

    def test_missing_metric_keeps_draft_and_disables_save(self):
        blocks = [metric('CSV::Conta removida')]
        app = self.build(blocks)
        self.assertTrue(app.error)
        self.assertEqual(app.session_state['formula_blocks_teste'], blocks)
        self.assertTrue(app.button(key='formula_save_teste').disabled)
        self.assertFalse(app.exception)

    def test_palette_receives_full_catalog_and_marks_unavailable_values(self):
        script = APP.replace(
            "formula_blocks._component = lambda **kwargs: {'blocks': st.session_state.get('test_blocks', kwargs['initial_blocks'])}",
            "def component(**kwargs):\n    st.session_state['palette_args'] = kwargs\n    return {'blocks': kwargs['initial_blocks']}\nformula_blocks._component = component")
        app = AppTest.from_string(script)
        variables = {f'Fonte nova::Variável {i}': float(i) for i in range(250)}
        variables['Fonte nova::Sem dado'] = float('nan')
        app.session_state['test_variables'] = variables
        app.run()
        args = app.session_state['palette_args']
        self.assertEqual(set(args['metrics']), set(variables))
        self.assertEqual(args['unavailable_metrics'], ['Fonte nova::Sem dado'])
        self.assertFalse(app.exception)

    def test_saved_kpi_is_available_as_operand(self):
        app = self.build([])
        app.session_state['custom_financial_analyses'] = {'teste': [dict(
            id='base', label='Base', kind='formula', expression='[Financeiro::EBITDA] * 2', aggregation='sum')]}
        app.session_state['test_blocks'] = [metric('Personalizado::base · Base'), op('+'), number('1')]
        app.run()
        self.assertEqual(app.metric[0].value, '201,00')
        self.assertFalse(app.button(key='formula_save_teste').disabled)
        self.assertFalse(app.exception)

    def test_payload_validation(self):
        for payload in [None, {}, [number('nan')], [number('1e999')], [op('**')], [metric('unknown')],
                        [number('__import__("os")')], [None], [number('1')] * 121]:
            with self.subTest(payload=payload), self.assertRaises(FormulaError):
                expression = blocks_expression(payload, {})
                evaluate_formula(expression, {})
        self.assertEqual(evaluate_formula(blocks_expression([number('-2'), op('*'), number('0.25')], {}), {}), -.5)


if __name__ == '__main__':
    unittest.main()
