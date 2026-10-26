import os
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
import server


class RecallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(self.temp.name) / 'test.sqlite3'
        self.client = TestClient(server.app)

    def tearDown(self):
        for (path, key), future in list(server.jobs.items()):
            if path == str(server.DB_PATH):
                future.result(timeout=30)
        self.client.close()
        self.temp.cleanup()

    def test_capture_retrieve_search_and_delete(self):
        item = {'id': 'test-capture', 'title': 'Special pricing table', 'text': 'A unique quasar subscription costs $42.', 'date': '2026-10-23T10:00:00Z'}
        self.assertEqual(self.client.post('/api/memories', json=item).status_code, 200)
        found = self.client.get('/api/search', params={'q': 'the quasar subscription'}).json()
        self.assertIn('test-capture', found['ids'])
        item['saved'] = True
        self.client.post('/api/memories', json=item)
        matching = [m for m in self.client.get('/api/memories').json() if m['id'] == 'test-capture']
        self.assertEqual(len(matching), 1)
        self.assertTrue(matching[0]['saved'])
        self.client.delete('/api/memories/test-capture')
        self.assertNotIn('test-capture', self.client.get('/api/search', params={'q': 'quasar'}).json()['ids'])

    def test_cross_origin_and_private_files_are_blocked(self):
        self.assertEqual(self.client.get('/api/memories', headers={'Origin': 'https://example.com'}).status_code, 403)
        self.assertEqual(self.client.get('/api/memories', headers={'Host': 'evil.test'}).status_code, 403)
        self.assertEqual(self.client.get('/seeds.json').status_code, 404)
        self.assertEqual(self.client.get('/server.py').status_code, 404)

    def test_deleted_samples_do_not_reappear(self):
        self.client.get('/api/memories')
        self.client.delete('/api/memories/sample-1')
        self.assertNotIn('sample-1', [m['id'] for m in self.client.get('/api/memories').json()])


if __name__ == '__main__':
    unittest.main()
