"""Exercise the real pinned Caddy image's attempt log and open-fetch guard on a Docker host."""
from pathlib import Path
import json
import shutil
import ssl
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'caddy:2.11.2@sha256:25cdc846626b62d05f6b633b9b40c2c9f6ef89b515dc76133cefd920f7dbe562'


def docker(*args):
    return subprocess.check_output(['docker', *args], text=True, stderr=subprocess.STDOUT).strip()


def validate(directory, open_fetch, auth):
    return subprocess.run(['docker', 'run', '--rm', '-e', f'READER_OPEN_FETCH={open_fetch}', '-e', f'READER_AUTH_ENABLED={auth}',
                           '-e', 'READER_PASSWORD_HASH=$2a$14$hashhashhashhashhashhu', '-v', f'{directory}/Caddyfile:/etc/caddy/Caddyfile:ro',
                           IMAGE, 'caddy', 'validate', '--config', '/etc/caddy/Caddyfile'], capture_output=True, text=True).returncode


class AttemptGatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'test-results' if (ROOT / 'test-results').is_dir() else None)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        shutil.copy(ROOT / 'deploy/Caddyfile', self.directory / 'Caddyfile')

    def test_open_fetching_requires_authentication(self):
        results = {(o, a): validate(self.directory, o, a) for o in ('false', 'true', 'yes') for a in ('false', 'true')}
        self.assertEqual({k for k, code in results.items() if code == 0},
                         {('false', 'false'), ('false', 'true'), ('true', 'true')})

    def test_records_only_hostname_and_outcome(self):
        shutil.copytree(ROOT / 'web', self.directory / 'web')
        (self.directory / 'attempts').mkdir()
        container = docker('run', '-d', '--rm', '-p', '127.0.0.1::8446', '-e', 'READER_HOST=localhost',
                           '-v', f'{self.directory}/Caddyfile:/etc/caddy/Caddyfile:ro', '-v', f'{self.directory}/web:/srv:ro',
                           '-v', f'{self.directory}/attempts:/attempts', IMAGE)
        try:
            origin = 'https://localhost:' + docker('port', container, '8446').split(':')[-1]
            context = ssl._create_unverified_context()  # certificate_gateway.py verifies the chain.

            def request(path, method='POST'):
                try:
                    response = urllib.request.urlopen(urllib.request.Request(origin + path, method=method,
                                                      headers={'User-Agent': 'private-agent'}), context=context, timeout=5)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    return response.status

            for _ in range(50):
                try:
                    request('/', 'GET')
                    break
                except OSError:
                    time.sleep(.2)
            self.assertEqual(request('/attempt?host=news.example&outcome=short&chars=12'), 204)
            self.assertEqual(request('/attempt?host=news.example'), 400)
            self.assertEqual(request('/attempt?host=news.example&outcome=ok', 'GET'), 400)
            self.assertEqual(request('/', 'GET'), 200)
            time.sleep(.5)
            log = (self.directory / 'attempts/attempts.log').read_text()
            entries = [json.loads(line) for line in log.splitlines()]
            self.assertEqual([e['request']['uri'] for e in entries], ['/attempt?host=news.example&outcome=short&chars=12'])
            for text in (log, docker('logs', container)):
                self.assertNotIn('private-agent', text)
                self.assertNotIn('remote_ip', text)
                self.assertNotIn('172.17.', text)
            self.assertIn('outcome=short', docker('logs', container))
        finally:
            subprocess.run(['docker', 'stop', container], capture_output=True)


if __name__ == '__main__':
    unittest.main()
