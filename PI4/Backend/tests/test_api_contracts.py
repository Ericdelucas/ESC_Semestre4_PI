"""Regressoes dos contratos HTTP e do arranque, usando SQLite temporario.

Executar: python -m unittest discover -s PI4/Backend/tests -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from Backend.main import app
from Backend.db import database, session_scope
from Backend.db.auth import hash_senha
from Backend.db.models import Usuario
from Backend.services import chat_service


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.db_patches = [
            patch.object(database, '_DEFAULT_SQLITE', Path(cls.directory.name) / 'auth.db'),
            patch.object(database, '_engine', None),
            patch.object(database, '_SessionLocal', None),
        ]
        for item in cls.db_patches:
            item.start()
        cls.client = TestClient(app)
        cls.client.__enter__()  # Executa o lifespan real, init_db e seed_usuarios.
        with session_scope() as db:
            db.add(Usuario(email='contract@example.test', senha_hash=hash_senha('test-password'),
                           funcao='CEO', ativo=True, is_super_admin=False))

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        database.get_engine().dispose()
        for item in reversed(cls.db_patches):
            item.stop()
        cls.directory.cleanup()

    def test_existing_paths_and_methods(self):
        expected = {
            '/': {'get', 'head'},
            '/api/health': {'get', 'head'},
            '/json/version': {'get'},
            '/api/v1/health': {'get', 'head'},
            '/api/v1/auth/login': {'post'},
            '/api/v1/auth/logout': {'post'},
            '/api/v1/auth/logs': {'get'},
            '/api/chat': {'post'},
            '/api/v1/users/create': {'post'},
            '/api/v1/users/list': {'get'},
            '/api/v1/email/testar': {'post'},
            '/api/v1/email/status': {'get'},
            '/api/v1/email/riscos': {'get'},
            '/api/v1/email/varrer-risco': {'post'},
            '/api/v1/relatorio/memorial': {'post'},
        }
        paths = app.openapi()['paths']
        self.assertEqual({path: set(operations) for path, operations in paths.items()}, expected)

    def test_health_and_version(self):
        for path in ('/', '/api/health'):
            self.assertEqual(self.client.get(path).json(),
                             {'status': 'online', 'message': 'API CTI Backend Ativa'})
            self.assertEqual(self.client.head(path).status_code, 200)
        self.assertEqual(self.client.get('/json/version').json(),
                         {'version': '1.0.0', 'status': 'ok'})
        response = self.client.get('/api/v1/health')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['database']['ok'])
        self.assertTrue(response.json()['rag']['ok'])
        self.assertEqual(self.client.head('/api/v1/health').status_code, 200)

    def test_login_logout_and_logs(self):
        # Nenhum e-mail ou calculo de risco e disparado pelo teste.
        with patch('Backend.routers.auth_router.disparar_alerta_risco') as alert:
            response = self.client.post('/api/v1/auth/login',
                                        json={'email': 'contract@example.test', 'password': 'test-password'},
                                        headers={'x-forwarded-for': '203.0.113.7, 127.0.0.1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {'ok', 'message', 'user', 'risk_alert'})
        self.assertEqual(response.json()['user']['email'], 'contract@example.test')
        self.assertIsNone(response.json()['risk_alert'])
        alert.assert_called_once_with('contract@example.test', forcar=False,
                                      simular=ANY, origem='login')
        logs = self.client.get('/api/v1/auth/logs', params={'email': 'contract@example.test'})
        self.assertEqual(logs.status_code, 200)
        self.assertEqual(logs.json()['logs'][0]['ip_origem'], '203.0.113.7')
        logout = self.client.post('/api/v1/auth/logout', json={'email': ' CONTRACT@example.test '})
        self.assertEqual(logout.json(), {'ok': True, 'message': 'Logout efetuado'})

    def test_auth_errors_and_validation(self):
        response = self.client.post('/api/v1/auth/login',
                                    json={'email': 'missing@example.test', 'password': 'wrong'})
        self.assertEqual(response.status_code, 401)
        self.assertIn('detail', response.json())
        self.assertEqual(self.client.get('/api/v1/auth/logs',
                                        params={'email': 'missing@example.test'}).status_code, 403)
        self.assertEqual(self.client.post('/api/v1/auth/login', json={}).status_code, 422)
        self.assertEqual(self.client.post('/api/chat', json={}).status_code, 422)

    def test_empty_chat_does_not_initialize_rag(self):
        with patch.object(chat_service, '_rag') as rag:
            response = self.client.post('/api/chat', json={'message': '  '})
        rag.assert_not_called()
        self.assertEqual(response.json(),
                         {'response': 'Escreva uma pergunta sobre os cenários da CTI.', 'sources': []})

    def test_chat_sessions_role_and_history_limit(self):
        engine = Mock()
        engine.responder.return_value = ('Resposta', ['documentos/exemplo.md'])
        with patch.object(chat_service, '_engine', engine), patch.object(chat_service, '_sessoes', {}):
            for _ in range(8):
                response = self.client.post('/api/chat',
                                            json={'message': ' Pergunta ', 'session_id': ' sessao ',
                                                  'user_role': 'CEO'})
                self.assertEqual(response.json(),
                                 {'response': 'Resposta', 'sources': ['documentos/exemplo.md']})
            self.assertEqual(len(chat_service._sessoes['sessao']), 12)
            self.assertEqual(engine.responder.call_args.args[0], 'Pergunta')
            self.assertEqual(engine.responder.call_args.kwargs, {'user_role': 'CEO'})
            self.client.post('/api/chat', json={'message': 'Outra', 'session_id': 'outra'})
            self.assertEqual(len(chat_service._sessoes['outra']), 2)
            self.assertEqual(len(chat_service._sessoes['sessao']), 12)

    def test_cors_preflight(self):
        response = self.client.options('/api/v1/auth/login', headers={
            'origin': 'https://cti-frontend.onrender.com',
            'access-control-request-method': 'POST',
            'access-control-request-headers': 'content-type',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['access-control-allow-origin'],
                         'https://cti-frontend.onrender.com')
        self.assertEqual(response.headers['access-control-allow-credentials'], 'true')

    def test_existing_email_and_users_routers(self):
        self.assertEqual(self.client.get('/api/v1/email/status').status_code, 200)
        for path in ('/api/v1/users/list', '/api/v1/email/riscos'):
            self.assertEqual(self.client.get(path, params={'email': 'missing@example.test'}).status_code, 403)


if __name__ == '__main__':
    unittest.main()
