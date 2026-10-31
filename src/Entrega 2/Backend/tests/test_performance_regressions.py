"""Preserva resultados financeiros, filtros e inicializacao lazy do chat."""
from __future__ import annotations

import subprocess
import sys
import time
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

PI4_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PI4_ROOT))
sys.path.insert(0, str(PI4_ROOT / 'Frontend'))

import pandas as pd
from pandas.testing import assert_frame_equal

from Backend.metrics.column_resolver import normalize_label, resolve_account_name
from Backend.services import chat_service
from src.controllers.sidebar import _valores_unicos


class PerformanceRegressionTests(unittest.TestCase):
    def test_normalization_accepts_non_hashable_values_and_mojibake(self):
        for source, expected in [(' BAL - Patrimônio Líquido ', 'bal patrimonio liquido'),
                                 ('BAL - DisponÃ­vel', 'bal disponivel'),
                                 (None, 'none'), ([], ''), (123, '123')]:
            with self.subTest(source=source):
                self.assertEqual(normalize_label(source), expected)
                self.assertEqual(normalize_label(source), expected)

    def test_official_names_keep_precedence_and_iterator_support(self):
        self.assertEqual(resolve_account_name('Receita', ['RECEITA']), 'RECEITA')
        self.assertEqual(resolve_account_name('Receita Bruta R$'), 'DRE - Receita')
        self.assertEqual(resolve_account_name(' EBITDA ', iter(['DRE - EBITDA'])), 'DRE - EBITDA')
        self.assertEqual(resolve_account_name('Não reconhecida'), 'Não reconhecida')
        self.assertEqual(resolve_account_name('a', ['A', 'a']), 'a')
        self.assertEqual(resolve_account_name('a', ['a', 'A']), 'A')

    def test_sidebar_options_are_unique_and_do_not_mutate_data(self):
        frame = pd.DataFrame({'CENA': ['B', 'A', 'B', None, '', 'None', 'nan', 'A'],
                              'ano_num': [2, 1, 2, None, 3, 3, 1, 2]})
        original = frame.copy(deep=True)
        self.assertEqual(_valores_unicos(frame, 'CENA'), ['B', 'A'])
        self.assertEqual(_valores_unicos(frame, 'ano_num'), [2.0, 1.0, 3.0])
        assert_frame_equal(frame, original)
        self.assertEqual(_valores_unicos(None, 'CENA'), [])
        self.assertEqual(_valores_unicos(frame, 'missing'), [])

    def test_sidebar_handles_categorical_values(self):
        frame = pd.DataFrame({'CENA': pd.Categorical(['B', 'A', 'B', None], categories=['A', 'B', 'C'])})
        self.assertEqual(_valores_unicos(frame, 'CENA'), ['B', 'A'])

    def test_backend_import_does_not_load_rag_or_streamlit(self):
        code = (f'import sys; sys.path.insert(0, {str(PI4_ROOT)!r}); '
                'import Backend.main; '
                'assert "Backend.rag_engine" not in sys.modules; '
                'assert "streamlit" not in sys.modules')
        subprocess.run([sys.executable, '-c', code], check=True, capture_output=True, timeout=30)

    def test_concurrent_first_requests_initialize_only_one_rag(self):
        fake_module = types.ModuleType('Backend.rag_engine')
        instance = object()

        def initialize():
            time.sleep(0.02)
            return instance

        fake_module.CTIRag = Mock(side_effect=initialize)
        with patch.dict(sys.modules, {'Backend.rag_engine': fake_module}), patch.object(chat_service, '_engine', None):
            with ThreadPoolExecutor(max_workers=8) as executor:
                engines = list(executor.map(lambda _: chat_service._rag(), range(8)))
            fake_module.CTIRag.assert_called_once_with()
            self.assertTrue(all(engine is instance for engine in engines))

    def test_failed_initialization_can_be_retried(self):
        fake_module = types.ModuleType('Backend.rag_engine')
        instance = object()
        fake_module.CTIRag = Mock(side_effect=[RuntimeError('not ready'), instance])
        with patch.dict(sys.modules, {'Backend.rag_engine': fake_module}), patch.object(chat_service, '_engine', None):
            with self.assertRaisesRegex(RuntimeError, 'not ready'):
                chat_service._rag()
            self.assertIs(chat_service._rag(), instance)
            self.assertEqual(fake_module.CTIRag.call_count, 2)


if __name__ == '__main__':
    unittest.main()
