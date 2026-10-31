"""Verifica diagnóstico PDF e separação entre simulação de envio e risco real."""
import copy
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pypdf import PdfReader
from Backend.services import risk_report


class RiskReportTests(unittest.TestCase):
    def payload(self, status='conforme'):
        return {'metrics': {'n_cenarios': 1200, 'limiar_ruina': 15, 'limiar_liquidez': 1},
                'checks': [{'id': 'liquidez', 'label': 'Liquidez média', 'value': '5.11x',
                            'status': status, 'formula': 'AC / PC', 'threshold': '< 1x'}]}

    def text(self, payload):
        pdf = risk_report.gerar_relatorio_riscos(payload)
        return '\n'.join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)

    def test_diagnosticos_e_snapshot_preservado(self):
        for status, expected in [('conforme', 'Favorável:'), ('atencao', 'Atenção:'), ('critico', 'Crítico:')]:
            with self.subTest(status=status):
                payload = self.payload(status)
                original = copy.deepcopy(payload)
                self.assertIn(expected, self.text(payload))
                self.assertEqual(original, payload)

    def test_simulacao_nao_classifica_modelo_como_critico(self):
        payload = self.payload()
        payload['simulated'] = True
        payload['critical'] = True
        payload['checks'].append({'id': 'simulacao', 'status': 'critico'})
        text = self.text(payload)
        self.assertIn('Favorável:', text)
        self.assertIn('selo artificial', text)

    def test_cria_diretorio_ausente(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(risk_report, 'REPORTS_DIR', Path(tmp) / 'relatorios'):
                path = risk_report.salvar_relatorio_riscos(self.payload())
                self.assertTrue(path.read_bytes().startswith(b'%PDF-'))

    def test_recusa_base_vazia(self):
        with self.assertRaises(ValueError):
            risk_report.gerar_relatorio_riscos({'metrics': {}, 'checks': []})


if __name__ == '__main__':
    unittest.main()
