import math
import unittest

import pandas as pd

from Backend.services.formula_metrics import FormulaError, evaluate_formula, formula_variables, format_formula_value, variable_reference


class FormulaTests(unittest.TestCase):
    def test_user_expression_with_duplicate_ebitda_sources(self):
        values = {'Indicador::ebitda': 999, 'Financeiro::EBITDA': 100,
                  'Financeiro::Capex': 20, 'Financeiro::EBIT': 60, 'CSV::DRE - Receita': 200}
        expression = '((EBITDA * 1.15) - (Capex / 2)) / ((DRE_Ebit + 50000) * (1 - 0.34))'
        expected = ((100 * 1.15) - (20 / 2)) / ((60 + 50000) * (1 - 0.34))
        for variables in (values, dict(reversed(list(values.items())))):
            self.assertAlmostEqual(evaluate_formula(expression, variables), expected)
            self.assertEqual(evaluate_formula('ebitda', variables), 100)
            self.assertEqual(evaluate_formula('[Indicador::ebitda]', variables), 999)
            for key, value in variables.items():
                self.assertEqual(evaluate_formula(variable_reference(key, variables), variables), value)

    def test_arithmetic(self):
        self.assertEqual(evaluate_formula('([CSV::Receita] - 20) / 2', {'CSV::Receita': 100}), 40)
        self.assertEqual(format_formula_value(1234.5, 'Moeda'), 'R$ 1.234,50')

    def test_free_metric_names_and_qualified_names(self):
        values = {'Financeiro::EBITDA': 100, 'Financeiro::Capex': 20,
                  'CSV::DRE - Receita': 200, 'Financeiro::EBIT': 60}
        self.assertEqual(evaluate_formula('(EBITDA - Capex) / 2', values), 40)
        self.assertEqual(evaluate_formula('DRE - Ebit / DRE - Receita * 100', values), 30)
        self.assertEqual(evaluate_formula('ebitda + Financeiro::Capex', values), 120)
        self.assertEqual(evaluate_formula('[CSV::DRE - Receita] / 2', values), 100)

    def test_ambiguous_and_overlapping_names(self):
        values = {'CSV::Receita': 100, 'CSV::Receita Líquida': 80,
                  'Financeiro::ROIC': 0.1, 'Indicador::ROIC': 10,
                  'Catalogo::Taxa (anual)': 5}
        self.assertEqual(evaluate_formula('Receita Líquida / Receita', values), 0.8)
        self.assertEqual(evaluate_formula('[Taxa (anual)] + 1', values), 6)
        self.assertEqual(evaluate_formula('Financeiro::ROIC * 100', values), 10)
        self.assertEqual(evaluate_formula('ROIC + 1', values), 1.1)
        with self.assertRaises(FormulaError):
            evaluate_formula('ReceitaExtra + 1', values)

    def test_dynamic_names_without_metric_specific_shortcuts(self):
        values = {'CSV::BAL - Provisões Especiais': 40,
                  'Financeiro::Índice Novo': 2, 'Indicador::Índice Novo': 200,
                  'Financeiro::Despesas Financeiras': 8}
        self.assertEqual(evaluate_formula('Provisoes_Especiais / Indice_Novo - Despesa_Financeira', values), 12)
        resolved = {}
        self.assertEqual(evaluate_formula('Indice_Novo', values, resolved=resolved), 2)
        self.assertEqual(resolved['indice_novo'], 'Financeiro::Índice Novo')
        self.assertEqual(evaluate_formula('Indice_Novo', values,
                         choices={'indice novo': 'Indicador::Índice Novo'}), 200)
        self.assertEqual(evaluate_formula('[CSV::BAL - Provisões Especiais]', values), 40)

    def test_rejects_code_and_invalid_numbers(self):
        for expression in ['__import__("os")', '(1).__class__', '2 ** 100', 'True', '1 / 0',
                           '[ausente]', '[x]', '1e999', 'a + 1', '[x][0]']:
            with self.subTest(expression=expression), self.assertRaises(FormulaError):
                evaluate_formula(expression, {'x': math.nan})

    def test_real_accounts_filters_and_monte_carlo(self):
        rows = []
        for scene, multiplier in [('A', 1), ('B', 3)]:
            for year in [1, 2]:
                for account, amount in [('Conta fora do mapeamento', 10), ('DRE - Receita', 100),
                                        ('DRE - Resultado Operacional', 20), ('DRE - EBITDA', 30),
                                        ('FLU - Investimentos', -5)]:
                    rows.append((scene, year, account, amount * multiplier * year))
        raw = pd.DataFrame(rows, columns=['CENA', 'ano_num', 'CONTA', 'VALOR'])
        ind = pd.DataFrame({'CENA': ['A', 'B'], 'ano_num': [1, 1], 'NCG': [2., 6.]})
        values = formula_variables(raw, ind, 'Todos', 1)
        self.assertEqual(values['CSV::Conta fora do mapeamento'], 20)
        self.assertEqual(values['Indicador::NCG'], 4)
        self.assertEqual(values['Financeiro::EBIT'], 40)
        self.assertEqual(values['Financeiro::Capex'], 10)
        self.assertEqual(formula_variables(raw, ind, 'A', 'Todos', 'sum')['CSV::DRE - Receita'], 300)
        with self.assertRaises(FormulaError):
            formula_variables(raw, ind, 'inexistente')


if __name__ == '__main__':
    unittest.main()
