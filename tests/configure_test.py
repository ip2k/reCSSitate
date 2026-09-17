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
        (self.root / 'userscript/recssitate.user.js').write_text("const server='__PAGE_RESCUE_ORIGIN__';")
        self.sites = self.root / 'deploy/sites.txt'

    def test_allowlist_is_private_and_deterministic(self):
        self.sites.write_text('# Private selection\nnews.example\nwww.second.example\nnews.example\n')
        module.configure('https://reader.example:8446', self.sites, self.root)
        env = (self.root / 'deploy/sites.env').read_text()
        hosts = set(env.strip().split('=', 1)[1].split(','))
        self.assertEqual(hosts, {'news.example', 'www.news.example', 'www.second.example'})
        self.assertFalse((self.root / 'deploy/rules.yaml').exists())
        module.configure('https://reader.example:8446', self.sites, self.root)
        self.assertEqual(env, (self.root / 'deploy/sites.env').read_text())

    def test_invalid_or_empty_selection_creates_no_assets(self):
        for value in ('', '# none\n', '*.example', 'https://news.example', 'news.example\nBAD=value', '127.0.0.1'):
            self.sites.write_text(value)
            with self.assertRaises(ValueError):
                module.configure('https://reader.example', self.sites, self.root)
            self.assertFalse((self.root / 'deploy/sites.env').exists())


if __name__ == '__main__':
    unittest.main()
