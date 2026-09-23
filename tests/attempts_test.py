import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('attempts', Path(__file__).resolve().parents[1] / 'tools/attempts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def line(host, outcome, ts, logger='http.log.access.attempts-file', status=204, prefix=''):
    uri = f'/attempt?host={host}&outcome={outcome}'
    return prefix + json.dumps({'logger': logger, 'ts': ts, 'status': status, 'request': {'uri': uri}}) + '\n'


class AttemptSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.sites, self.adapters = root / 'sites.txt', root / 'adapters.yaml'
        self.sites.write_text('# Known\nlisted.example\n')
        self.adapters.write_text("- domain: 'ruled.example'\n  useFlareSolverr: false\n")

    def verdicts(self, lines):
        return {r['site']: r['verdict'] for r in module.summarize(lines, self.sites, self.adapters, 2)}

    def test_flags_sites_the_generic_rule_cannot_read(self):
        lines = [
            line('listed.example', 'ok', 1),
            line('www.walled.example', 'challenge', 2), line('walled.example', 'short', 3),
            line('ruled.example', 'short', 4), line('ruled.example', 'fetch-error', 5),
            line('flaky.example', 'ok', 6), line('flaky.example', 'short', 7),
            line('wanted.example', 'not-listed', 8),
            line('slow.example', 'timeout', 9), line('slow.example', 'timeout', 10),
            line('once.example', 'short', 11),
        ]
        self.assertEqual(self.verdicts(lines), {
            'listed.example': 'works', 'walled.example': 'needs adapter', 'ruled.example': 'adapter failing',
            'flaky.example': 'intermittent', 'wanted.example': 'requested',
            'slow.example': 'watch', 'once.example': 'watch',
        })
        rows = module.summarize(lines, self.sites, self.adapters, 2)
        self.assertEqual(rows[0]['site'], 'walled.example')
        self.assertFalse(rows[0]['listed'])

    def test_a_later_success_clears_the_flag(self):
        lines = [line('walled.example', 'short', 1), line('walled.example', 'short', 2), line('walled.example', 'ok', 3)]
        self.assertEqual(self.verdicts(lines), {'walled.example': 'works'})

    def test_ignores_other_log_lines_and_malformed_values(self):
        lines = [
            'gateway-1  | not json\n',
            line('docker.example', 'short', 1, prefix='gateway-1  | '),
            line('other.example', 'short', 1, logger='http.log.access'),
            line('rejected.example', 'short', 1, status=400),
            line('bad host.example', 'short', 1),
            line('odd.example', 'weird', 1),
        ]
        self.assertEqual(self.verdicts(lines), {'docker.example': 'watch'})


if __name__ == '__main__':
    unittest.main()
