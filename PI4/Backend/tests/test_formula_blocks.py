"""Conversao blocos <-> texto, gramatica dos blocos e rota /api/v1/formulas."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from Backend.routers import formula_router
from Backend.services.formula_blocks import (
    BlockError, block_palette, blocks_to_expression, check_structure, expression_to_blocks,
)
from Backend.services.formula_metrics import FormulaError, evaluate_formula

VALUES = {'Financeiro::EBITDA': 100., 'Financeiro::Capex': 20., 'CSV::DRE - Receita': 200.,
          'Indicador::ebitda': 999., 'Catalogo::Rentabilidade · ROIC': 10., 'Indicador::NCG': float('nan')}


def var(key):
    return {'type': 'var', 'value': key}


def op(value):
    return {'type': 'op', 'value': value}


def num(value):
    return {'type': 'num', 'value': value}


def paren(value):
    return {'type': 'paren', 'value': value}


class BlockConversionTests(unittest.TestCase):
    def test_blocks_round_trip_and_evaluate(self):
        blocks = [paren('('), var('Financeiro::EBITDA'), op('-'), var('Financeiro::Capex'), paren(')'),
                  op('/'), num('2'), op('*'), op('-'), num('1.5')]
        expression = blocks_to_expression(blocks, VALUES)
        self.assertEqual(expression, '([Financeiro::EBITDA] - [Financeiro::Capex]) / 2 * -1.5')
        self.assertEqual(evaluate_formula(expression, VALUES), -60)
        self.assertEqual(expression_to_blocks(expression, VALUES), blocks)

    def test_free_text_becomes_resolved_blocks(self):
        self.assertEqual(expression_to_blocks('(EBITDA - Capex) / 2', VALUES),
                         [paren('('), var('Financeiro::EBITDA'), op('-'), var('Financeiro::Capex'),
                          paren(')'), op('/'), num('2')])
        self.assertEqual(expression_to_blocks('ebitda', VALUES, choices={'ebitda': 'Indicador::ebitda'}),
                         [var('Indicador::ebitda')])
        self.assertEqual(expression_to_blocks('[Catalogo::Rentabilidade · ROIC] % 3.', VALUES),
                         [var('Catalogo::Rentabilidade · ROIC'), op('%'), num('3')])

    def test_structure_errors_point_to_block(self):
        cases = [
            ([var('Financeiro::EBITDA'), var('Financeiro::Capex')], 1),
            ([op('*'), num('2')], 0),
            ([num('2'), op('+')], 1),
            ([paren('('), num('2')], 0),
            ([num('2'), paren(')')], 1),
            ([paren('('), paren(')')], 1),
            ([num('2'), paren('(')], 1),
        ]
        for blocks, index in cases:
            with self.subTest(blocks=blocks), self.assertRaises(BlockError) as caught:
                check_structure(blocks)
            self.assertEqual(caught.exception.index, index)
        check_structure([op('-'), paren('('), op('+'), num('2'), paren(')')])

    def test_rejects_unsafe_or_unknown_blocks(self):
        for blocks in ([var('__import__("os")')], [var('Inexistente')], [num('1e999')], [num('2;3')],
                       [{'type': 'call', 'value': 'print'}], [num('2'), op('**'), num('3')],
                       [var('Financeiro::EBITDA]+[Financeiro::Capex')]):
            with self.subTest(blocks=blocks), self.assertRaises(FormulaError):
                blocks_to_expression(blocks, VALUES)
        for expression in ('__import__("os")', '2 ** 3 ', 'a + 1', '1e5', '[x]'):
            with self.subTest(expression=expression), self.assertRaises(FormulaError):
                check_structure(expression_to_blocks(expression, VALUES))

    def test_palette_groups_and_missing_values(self):
        palette = {item['key']: item for item in block_palette(VALUES)}
        self.assertEqual(list(palette)[0], 'Financeiro::Capex')
        self.assertEqual(palette['CSV::DRE - Receita']['group'], 'Contas do Cti.csv · DRE')
        self.assertEqual(palette['Catalogo::Rentabilidade · ROIC']['label'], 'ROIC')
        self.assertIsNone(palette['Indicador::NCG']['value'])


class FormulaRouteTests(unittest.TestCase):
    def setUp(self):
        api = FastAPI()
        api.include_router(formula_router.router)
        self.client = TestClient(api)
        patcher = patch.object(formula_router, '_variables', return_value=VALUES)
        self.variables = patcher.start()
        self.addCleanup(patcher.stop)

    def test_validate_blocks_and_expression(self):
        body = {'blocks': [var('Financeiro::EBITDA'), op('-'), var('Financeiro::Capex')], 'year': 3}
        data = self.client.post('/api/v1/formulas/validate', json=body).json()
        self.assertTrue(data['valid'])
        self.assertEqual((data['expression'], data['value']), ('[Financeiro::EBITDA] - [Financeiro::Capex]', 80))
        self.variables.assert_called_with('Todos', 3, 'mean')
        data = self.client.post('/api/v1/formulas/validate', json={'expression': 'EBITDA / 4'}).json()
        self.assertEqual((data['value'], data['blocks'][0]), (25, var('Financeiro::EBITDA')))

    def test_invalid_formula_reports_block(self):
        body = {'blocks': [num('1'), op('/'), op('*'), num('0')]}
        data = self.client.post('/api/v1/formulas/validate', json=body).json()
        self.assertEqual((data['valid'], data['error_index']), (False, 2))
        data = self.client.post('/api/v1/formulas/validate', json={'expression': '1 / 0'}).json()
        self.assertFalse(data['valid'])
        self.assertIn('divisao por zero', data['error'])

    def test_rejects_malformed_payloads(self):
        for body in ({}, {'expression': '1', 'blocks': []}, {'blocks': [{'type': 'call', 'value': 'x'}]},
                     {'expression': 'x' * 4001}, {'expression': '1', 'aggregation': 'median'}):
            with self.subTest(body=str(body)[:40]):
                self.assertEqual(self.client.post('/api/v1/formulas/validate', json=body).status_code, 422)

    def test_variables_palette_and_unavailable_data(self):
        data = self.client.get('/api/v1/formulas/variables', params={'scenario': 'A'}).json()
        self.assertEqual(len(data['variables']), len(VALUES))
        self.variables.side_effect = RuntimeError('cache')
        self.assertEqual(self.client.get('/api/v1/formulas/variables').status_code, 503)


if __name__ == '__main__':
    unittest.main()
