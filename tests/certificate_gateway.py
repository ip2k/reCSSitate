"""Exercise the real pinned Caddy image on an isolated Linux Docker host."""
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
    return subprocess.check_output(['docker', *args], text=True).strip()


class CertificateGatewayTests(unittest.TestCase):
    def test_setup_with_authentication_off_and_on(self):
        for enabled in ('false', 'true'):
            with self.subTest(authentication=enabled), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                shutil.copytree(ROOT / 'web', directory / 'web')
                shutil.copy(ROOT / 'deploy/Caddyfile', directory / 'Caddyfile')
                password_hash = docker('run', '--rm', IMAGE, 'caddy', 'hash-password', '--plaintext', 'disposable-test-password')
                container = docker('run', '-d', '--rm', '-p', '127.0.0.1::8086', '-p', '127.0.0.1::8446',
                    '-e', 'READER_HOST=localhost', '-e', 'READER_SETUP_PORT=8086',
                    '-e', f'READER_AUTH_ENABLED={enabled}', '-e', f'READER_PASSWORD_HASH={password_hash}',
                    '-v', f'{directory}/Caddyfile:/etc/caddy/Caddyfile:ro',
                    '-v', f'{directory}/web:/srv:ro', IMAGE)
                try:
                    http = 'http://localhost:' + docker('port', container, '8086').split(':')[-1]
                    https_port = docker('port', container, '8446').split(':')[-1]
                    https = f'https://localhost:{https_port}'

                    def get(path, origin=http, context=None, method='GET'):
                        try:
                            response = urllib.request.urlopen(urllib.request.Request(origin + path, method=method), context=context, timeout=5)
                        except urllib.error.HTTPError as error:
                            response = error
                        with response:
                            return response.status, response.headers, response.read()

                    for _ in range(50):
                        try:
                            status, headers, cert = get('/reader-ca.crt')
                            if status == 200:
                                break
                        except OSError:
                            pass
                        time.sleep(.2)
                    else:
                        self.fail('Caddy did not start and generate its public CA')
                    self.assertEqual(headers.get_content_type(), 'application/x-x509-ca-cert')
                    self.assertIn(b'BEGIN CERTIFICATE', cert)
                    self.assertNotIn(b'PRIVATE KEY', cert)
                    # The downloaded CA must verify the HTTPS server's real leaf.
                    context = ssl.create_default_context(cadata=cert.decode())
                    for _ in range(50):
                        try:
                            secured = get('/reader-ca.crt', https, context)
                            break
                        except OSError:
                            time.sleep(.2)  # Caddy issues its first leaf asynchronously.
                    else:
                        self.fail('HTTPS did not become ready with the downloaded CA')
                    self.assertEqual(secured[2], cert)
                    self.assertIn(b'Trust your reader', get('/')[2])
                    for path in ('/certificate.html', '/certificate.js', '/style.css', '/assets/ios-certificate/01-download.png'):
                        self.assertEqual(get(path)[0], 200, path)
                        self.assertEqual(get(path, https, context)[0], 200, path)
                    config = json.loads(get('/certificate.json')[2])
                    self.assertEqual(config, {'reader_url': 'https://localhost:8446/', 'bootstrap_url': 'http://localhost:8086/'})
                    for path in ('/root.key', '/root.crt', '/reader-ca.crt/root.key', '/ca/root.key', '/data/caddy/pki/authorities/local/root.key', '/assets/ios-certificate/../../../root.key', '/api/', '/signin', '/reader.js', '/recssitate.user.js'):
                        self.assertEqual(get(path)[0], 404, path)
                    self.assertEqual(get('/api/', method='POST')[0], 404)
                    self.assertEqual(json.loads(get('/auth.json', https, context)[2])['enabled'], enabled == 'true')
                    self.assertEqual(get('/api/unsupported', https, context)[0], 401 if enabled == 'true' else 405)
                finally:
                    docker('stop', container)


if __name__ == '__main__':
    unittest.main()
