"""Contratos do pipeline: filtros, KPIs e parquets com cache temporario."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
from pandas.testing import assert_frame_equal

from Backend.data_loader import csv_reader
from Backend.services import dashboard_cache, dashboard_pipeline as pipeline


class DashboardPipelineTests(unittest.TestCase):
    def setUp(self):
        self.ind = pd.DataFrame({
            'CENA': ['B', 'A', 'A'], 'ano_num': [1, 2, 1],
            'ANO': ['Ano 1', 'Ano 2', 'Ano 1'],
            'ebitda': [30.0, 90.0, 10.0], 'dre_receita': [300.0, 900.0, 100.0],
        })
        self.ranking = pd.DataFrame({
            'CENA': ['A', 'B'], 'caixa_ano12': [100.0, -10.0], 'ano_encerramento': [2, 2],
        })
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.cache_dir = Path(self.directory.name)
        for item in (patch.object(pipeline, 'CACHE_DIR', self.cache_dir),
                     patch.object(csv_reader, 'CACHE_DIR', self.cache_dir),
                     patch.dict(os.environ, {'RENDER': ''})):
            item.start()
            self.addCleanup(item.stop)

    def write_cache(self, include_raw=True):
        raw_path, ind_path, rank_path = pipeline.cache_paths()
        self.ind.to_parquet(ind_path, index=False)
        self.ranking.to_parquet(rank_path, index=False)
        raw = pipeline.df_longo_de_indicadores(self.ind)
        if include_raw:
            raw.to_parquet(raw_path, index=False)
        return raw

    def test_scenario_and_year_selection_without_mutating_input(self):
        before = self.ind.copy(deep=True)
        year, risk, focus, selected, kpis = pipeline.build_context_metrics(
            self.ind, self.ranking, cena_sel='A', ano_sel='2')
        self.assertEqual((year, risk), (2, 50.0))
        self.assertEqual(focus['ano_num'].tolist(), [1, 2])
        self.assertEqual(selected['ano_num'].tolist(), [2])
        self.assertEqual(kpis['ebitda'], 90.0)
        assert_frame_equal(self.ind, before)

    def test_all_scenarios_kpis_are_calculated_before_annual_average(self):
        for alias in ('Todos', '__all__', 'All', 'all', 'None', '', None):
            with self.subTest(alias=alias):
                _, _, focus, _, kpis = pipeline.build_context_metrics(
                    self.ind, self.ranking, cena_sel=alias, ano_sel='Todos')
                self.assertEqual(focus['ebitda'].tolist(), [20.0, 90.0])
                self.assertEqual(focus['CENA'].tolist(), ['Todos', 'Todos'])
                self.assertAlmostEqual(kpis['ebitda'], 130.0 / 3)

    def test_missing_year_uses_scenario_kpis(self):
        _, _, focus, selected, kpis = pipeline.build_context_metrics(
            self.ind, self.ranking, cena_sel='A', ano_sel=99)
        self.assertFalse(focus.empty)
        self.assertTrue(selected.empty)
        self.assertEqual(kpis['ebitda'], 50.0)

    def test_empty_indicators_and_missing_scenario(self):
        for indicators, scenario in ((pd.DataFrame(), 'Todos'), (None, 'A'),
                                     (self.ind, 'missing'), (self.ind.drop(columns='CENA'), 'Todos')):
            with self.subTest(scenario=scenario):
                year, risk, focus, selected, kpis = pipeline.build_context_metrics(
                    indicators, pd.DataFrame(), cena_sel=scenario, ano_sel='Todos')
                self.assertEqual((year, risk), (12, 0.0))
                self.assertTrue(focus.empty)
                self.assertTrue(selected.empty)
                self.assertTrue(kpis.isna().all())

    def test_reconstructs_dre_accounts_and_values(self):
        raw = pipeline.df_longo_de_indicadores(self.ind)
        self.assertEqual(set(raw['CONTA']), {'DRE - EBITDA', 'DRE - Receita'})
        ebitda = raw.loc[raw['CONTA'] == 'DRE - EBITDA']
        self.assertEqual(ebitda['VALOR'].tolist(), [30.0, 90.0, 10.0])
        self.assertIsInstance(raw['CONTA'].dtype, pd.CategoricalDtype)

    def test_full_cache_reads_on_render_without_csv(self):
        raw = self.write_cache()
        self.assertTrue(pipeline.cache_disponivel())
        with patch.dict(os.environ, {'RENDER': 'true'}), patch.object(dashboard_cache, 'load_cti_csv') as csv:
            actual, indicators, ranking = pipeline.prepare_dashboard_data('not-needed.csv')
        csv.assert_not_called()
        assert_frame_equal(actual, raw)
        self.assertEqual(indicators['ebitda'].tolist(), [30.0, 90.0, 10.0])
        self.assertEqual(len(ranking), 2)

    def test_partial_cache_reconstructs_raw_when_loaded_directly(self):
        raw = self.write_cache(include_raw=False)
        self.assertFalse(pipeline.cache_disponivel())
        actual, indicators, _ = pipeline.load_cached_dashboard()
        assert_frame_equal(actual, raw)
        self.assertEqual(len(indicators), 3)

    def test_missing_cache_on_render_does_not_read_csv(self):
        with patch.dict(os.environ, {'RENDER': 'true'}), patch.object(dashboard_cache, 'load_cti_csv') as csv:
            with self.assertRaisesRegex(RuntimeError, 'Cti.csv nao e lido em runtime'):
                pipeline.prepare_dashboard_data('blocked.csv')
        csv.assert_not_called()

    def test_local_csv_fallback_builds_reusable_parquets(self):
        source = self.cache_dir / 'sample.csv'
        pd.DataFrame([
            ['Ano 1', 'A', 'DRE - Receita', '100,00'],
            ['Ano 1', 'A', 'DRE - EBITDA', '20,00'],
            ['Ano 2', 'A', 'DRE - Receita', '200,00'],
            ['Ano 2', 'A', 'DRE - EBITDA', '40,00'],
        ]).to_csv(source, index=False, header=False)
        raw, indicators, ranking = pipeline.prepare_dashboard_data(source)
        self.assertEqual(raw['VALOR'].tolist(), [100.0, 20.0, 200.0, 40.0])
        self.assertEqual(indicators['ebitda'].tolist(), [20.0, 40.0])
        self.assertEqual(len(ranking), 1)
        self.assertTrue(pipeline.cache_disponivel())
        with patch.object(dashboard_cache, 'load_cti_csv') as csv:
            cached = pipeline.prepare_dashboard_data(source)
        csv.assert_not_called()
        for actual, expected in zip(cached, (raw, indicators, ranking)):
            assert_frame_equal(actual, expected)

    def test_corrupt_cache_is_blocked_on_render(self):
        self.write_cache()
        pipeline.cache_paths()[1].write_bytes(b'invalid parquet')
        with patch.dict(os.environ, {'RENDER': 'true'}), patch.object(dashboard_cache, 'load_cti_csv') as csv:
            with self.assertRaisesRegex(RuntimeError, 'Cache de indicadores em falta na Render'):
                pipeline.prepare_dashboard_data()
        csv.assert_not_called()


if __name__ == '__main__':
    unittest.main()
