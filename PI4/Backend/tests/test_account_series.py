"""Regressoes de contas ausentes e colunas com encoding divergente."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_series_equal

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'Frontend'))

from Backend.metrics.financial_kpis import _conta


class AccountSeriesTests(unittest.TestCase):
    def test_missing_account_preserves_index(self):
        frame = pd.DataFrame({'outra': [1, 2]}, index=[4, 9])
        assert_series_equal(_conta(frame, 'ausente'), pd.Series(0., index=frame.index))
        assert_series_equal(_conta(frame.iloc[:0], 'ausente'), pd.Series(0., index=frame.index[:0]))

    def test_encoding_alias_uses_existing_value(self):
        frame = pd.DataFrame({'BAL - RealizÃ¡vel a Longo Prazo': ['50', None]}, index=[4, 9])
        result = _conta(frame, 'BAL - Realizável a Longo Prazo')
        self.assertEqual(result.tolist(), [50., 0.])
        self.assertEqual(result.index.tolist(), [4, 9])

    def test_exact_column_takes_precedence(self):
        frame = pd.DataFrame({'BAL - Disponível': [10], 'BAL - DisponÃ­vel': [0]})
        self.assertEqual(_conta(frame, 'BAL - Disponível').iloc[0], 10)

    def test_concession_views_and_comparison_use_financial_accounts(self):
        from src.views.persona_tabs import concession
        from src.views.persona_tabs.comparison_concession import _concedente_cmp
        amounts = {
            'BAL - Ativo Circulante': 100,
            'BAL - Realizável a Longo Prazo': 50,
            'BAL - Passivo Circulante': 30,
            'BAL - Exigível a Longo Prazo': 20,
            'BAL - Investimentos - Imobilizado': 80,
            'BAL - Investimentos - Intangível': 40,
            'BAL - Depreciação Acumulada': -10,
            'BAL - Amortização Acumulada': -5,
            'DRE - Receita': 200,
        }
        raw = pd.DataFrame([{'CENA': 'A', 'ano_num': 1, 'CONTA': key, 'VALOR': value}
                            for key, value in amounts.items()])
        for scene in ['A', 'Todos']:
            with self.subTest(scene=scene), patch.object(concession, 'st') as st, patch.object(concession, 'render_table') as table:
                concession.render_concedente_solvencia(raw, scene, 'Todos')
                self.assertEqual(table.call_args.args[0].iloc[0, 1], 3.)
                concession.render_concedente_ativos(raw, scene, 'Todos')
                self.assertEqual(st.plotly_chart.call_count, 2)
                comparison = _concedente_cmp(raw, scene)
                self.assertEqual(comparison['Liquidez Geral'].iloc[0], 3.)
                self.assertEqual(comparison['Base Final'].iloc[0], 120.)


if __name__ == '__main__':
    unittest.main()
