"""Coverage contracts for every loaded/formula source, including new columns."""
import math
import unittest
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_frame_equal

from Backend.data_loader.upload_normalizer import normalizar_upload
from Backend.metrics.custom_catalog import FINANCIAL_METRICS_DICT
from Backend.services.formula_metrics import (
    FORMULA_SOURCES, custom_formula_variables, formula_variables, evaluate_formula,
)


def sample():
    rows = []
    for scenario, multiplier in [('A', 1), ('B', 3)]:
        for year in [1, 2]:
            for account, value in [('DRE - Receita', 100), ('DRE - EBITDA', 30),
                                   ('DRE - Custos', -50), ('DRE - Resultado Operacional', 20),
                                   ('FLU - Investimentos', -5), ('Conta sem mapeamento', 7)]:
                rows.append((scenario, year, account, value * multiplier * year))
    return pd.DataFrame(rows, columns=['CENA', 'ano_num', 'CONTA', 'VALOR'])


class FormulaCatalogTests(unittest.TestCase):
    def test_all_accounts_columns_indicators_and_provider_outputs_are_exported(self):
        raw = sample()
        raw['Premissa nova'] = '1.234,50'
        ind = pd.DataFrame({'CENA': ['A', 'B'], 'ano_num': [1, 1],
                            'Indicador novo': ['2,5', '7,5'],
                            'Indefinido': [None, None], 'Texto': ['base', 'stress']})
        ranks = pd.DataFrame({'CENA': ['A', 'B'], 'Risco novo': [2., 4.]})
        before = raw.copy(deep=True)
        # New source and new formula must appear without changing formula_variables.
        def provider(batch, scenario):
            return batch[['ano_num']].drop_duplicates().assign(**{'Métrica futura': 42})
        with patch.dict(FORMULA_SOURCES, {'Fonte futura': provider}), patch.dict(
            FINANCIAL_METRICS_DICT, {'Fórmula futura': {'formula': lambda wide: wide['DRE - Receita'] / 2}}):
            values = formula_variables(raw, ind, ano=1, ranking=ranks)
            self.assertTrue({f'CSV::{account}' for account in raw['CONTA'].unique()} <= values.keys())
            self.assertTrue({f'Catalogo::{name}' for name in FINANCIAL_METRICS_DICT} <= values.keys())
            for prefix, builder in FORMULA_SOURCES.items():
                frame = builder(raw.loc[raw.CENA == 'A'], 'A')
                self.assertTrue({f'{prefix}::{col}' for col in frame if col != 'ano_num'} <= values.keys(), prefix)
        self.assertEqual(values['Fonte futura::Métrica futura'], 42)
        self.assertEqual(values['Catalogo::Fórmula futura'], 100)
        self.assertEqual(values['Coluna CSV::Premissa nova'], 1234.5)
        self.assertEqual(values['Indicador::Indicador novo'], 5)
        self.assertTrue(math.isnan(values['Indicador::Indefinido']))
        self.assertTrue(math.isnan(values['Indicador::Texto']))
        self.assertEqual(values['Ranking::Risco novo'], 3)
        self.assertTrue({'Comercial::LTV', 'Comercial::CAC', 'Comercial::LTV/CAC',
                         'Financeiro::CAPEX Acumulado', 'Financeiro::Margem EBIT (%)',
                         'Financeiro::YoY OPEX (%)', 'Financeiro::Base Líquida de Ativos'} <= values.keys())
        assert_frame_equal(raw, before)

    def test_cumulative_and_yoy_use_history_before_selected_year_per_scenario(self):
        values = formula_variables(sample(), pd.DataFrame(), 'Todos', 2)
        self.assertEqual(values['Financeiro::CAPEX Acumulado'], 30)  # A=15, B=45
        self.assertEqual(values['Financeiro::YoY OPEX (%)'], 1)
        self.assertEqual(values['Comercial::CAC'], 100)
        self.assertEqual(values['Comercial::LTV/CAC'], 225)
        single = formula_variables(sample(), pd.DataFrame(), 'A', 2)
        self.assertEqual(single['Financeiro::CAPEX Acumulado'], 15)
        self.assertEqual(single['CSV::DRE - Receita'], 200)

    def test_long_and_wide_uploads_keep_unmapped_columns(self):
        long = sample().assign(ANO=lambda frame: 'Ano ' + frame.ano_num.astype(str), **{'Premissa extra': '12,5'})
        normalized, errors = normalizar_upload(long)
        self.assertFalse(errors)
        self.assertIn('Premissa extra', normalized.columns)
        self.assertEqual(formula_variables(normalized, pd.DataFrame())['Coluna CSV::Premissa extra'], 12.5)
        wide = pd.DataFrame({'CENA': ['A'], 'ANO': ['Ano 1'], 'DRE - Receita': [100],
                             'Métrica inventada': [9], 'Valor de Mercado': [500]})
        normalized, errors = normalizar_upload(wide)
        self.assertFalse(errors)
        self.assertEqual(formula_variables(normalized, pd.DataFrame())['CSV::Métrica inventada'], 9)
        self.assertEqual(formula_variables(normalized, pd.DataFrame())['CSV::Valor de Mercado'], 500)

    def test_missing_numeric_columns_and_missing_year_stay_visible(self):
        raw = sample()
        raw['Sem dado'] = pd.NA
        raw.loc[(raw.CENA == 'A') & (raw.ano_num == 1) & (raw.CONTA == 'Conta sem mapeamento'), 'VALOR'] = math.nan
        values = formula_variables(raw, pd.DataFrame(), 'A', 1)
        self.assertTrue(math.isnan(values['Coluna CSV::Sem dado']))
        self.assertTrue(math.isnan(values['CSV::Conta sem mapeamento']))
        missing = formula_variables(raw, pd.DataFrame(), 'A', 99)
        self.assertIn('CSV::DRE - Receita', missing)
        self.assertTrue(math.isnan(missing['CSV::DRE - Receita']))

    def test_custom_formulas_dependencies_aggregations_and_cycles(self):
        analyses = [dict(id='a', label='Primeiro', kind='formula', expression='[CSV::Receita] * 2', aggregation='sum'),
                    dict(id='b', label='Segundo', kind='formula', expression='[Personalizado::a · Primeiro] + 1'),
                    dict(id='c', label='Circular', kind='formula', expression='[Personalizado::c · Circular]')]
        values = custom_formula_variables({'CSV::Receita': 10}, list(reversed(analyses)),
                                           {'sum': {'CSV::Receita': 100}})
        self.assertEqual(values['Personalizado::a · Primeiro'], 200)
        self.assertEqual(values['Personalizado::b · Segundo'], 201)
        self.assertTrue(math.isnan(values['Personalizado::c · Circular']))
        self.assertEqual(evaluate_formula('[Personalizado::b · Segundo] / 3', values), 67)

    def test_indicators_only_still_populate_catalog(self):
        raw = pd.DataFrame(columns=['CENA', 'ano_num', 'CONTA', 'VALOR'])
        ind = pd.DataFrame({'CENA': ['A'], 'ano_num': [1], 'Nova': [3.]})
        values = formula_variables(raw, ind)
        self.assertEqual(values['Indicador::Nova'], 3)
        self.assertTrue({f'Catalogo::{name}' for name in FINANCIAL_METRICS_DICT} <= values.keys())


if __name__ == '__main__':
    unittest.main()
