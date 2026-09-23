import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('configure', Path(__file__).resolve().parents[1] / 'tools/configure.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('deploy', 'web', 'userscript'):
            (self.root / name).mkdir()
        self.default = (Path(__file__).resolve().parents[1] / 'deploy/rules.default.yaml').read_text()
        (self.root / 'deploy/rules.default.yaml').write_text(self.default)
        (self.root / 'userscript/recssitate.user.js').write_text("const server='__PAGE_RESCUE_ORIGIN__';")
        self.sites = self.root / 'deploy/sites.txt'

    def test_allowlist_is_private_and_deterministic(self):
        self.sites.write_text('# Private selection\nnews.example\nwww.second.example\nnews.example\n')
        module.configure('https://reader.example:8446', self.sites, self.root)
        env = (self.root / 'deploy/sites.env').read_text()
        hosts = set(env.splitlines()[0].split('=', 1)[1].split(','))
        self.assertEqual(hosts, {'news.example', 'www.news.example', 'www.second.example'})
        self.assertIn('READER_OPEN_FETCH=false', env)
        self.assertEqual((self.root / 'deploy/rules.yaml').read_text(), self.default)
        module.configure('https://reader.example:8446', self.sites, self.root)
        self.assertEqual(env, (self.root / 'deploy/sites.env').read_text())

    def test_invalid_or_empty_selection_creates_no_assets(self):
        for value in ('', '# none\n', '*.example', 'https://news.example', 'news.example\nBAD=value', '127.0.0.1'):
            self.sites.write_text(value)
            with self.assertRaises(ValueError):
                module.configure('https://reader.example', self.sites, self.root)
            self.assertFalse((self.root / 'deploy/sites.env').exists())

    def test_open_fetching_requires_authentication(self):
        (self.root / 'deploy/.env').write_text("READER_AUTH_ENABLED=false\n")
        for sites in (None, self.sites):
            self.sites.write_text('news.example\n')
            with self.assertRaises(ValueError):
                module.configure('https://reader.example', sites, self.root, open_fetch=True)
            self.assertFalse((self.root / 'deploy/sites.env').exists())
        (self.root / 'deploy/.env').write_text("READER_AUTH_ENABLED=true\nREADER_PASSWORD_HASH='$2a$14$x'\n")
        module.configure('https://reader.example', None, self.root, open_fetch=True)
        # An empty list is Ladder's allow-all; Squid still blocks private addresses.
        self.assertEqual((self.root / 'deploy/sites.env').read_text(), 'ALLOWED_DOMAINS=\nREADER_OPEN_FETCH=true\n')

    def test_adapters_precede_the_catch_all(self):
        self.sites.write_text('news.example\n')
        adapter = "- domain: news.example\n  paths: ['/amp/']\n  useFlareSolverr: false\n"
        (self.root / 'deploy/adapters.yaml').write_text(adapter)
        module.configure('https://reader.example', self.sites, self.root)
        rules = (self.root / 'deploy/rules.yaml').read_text()
        self.assertLess(rules.index('news.example'), rules.index("domains: ['']"))
        self.assertTrue(rules.endswith(self.default))
        for bad in ("domain: news.example\n", "- domains: ['']\n", '- domain: ""\n'):
            (self.root / 'deploy/adapters.yaml').write_text(bad)
            with self.assertRaises(ValueError):
                module.configure('https://reader.example', self.sites, self.root)


if __name__ == '__main__':
    unittest.main()
