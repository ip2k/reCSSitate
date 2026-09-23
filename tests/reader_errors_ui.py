"""Run with Playwright Python on a Linux test host; no external sites are used."""
from pathlib import Path
import json
import unittest
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright

ARTICLE = 'https://news.example/story/private-path'
TEXT = '<p>' + 'A readable paragraph of synthetic article text. ' * 20 + '</p>'
PAGE = lambda title, body: json.dumps({'body': f'<html><head><title>{title}</title></head><body><article><h1>{title}</h1>{body}</article></body></html>'})
# status, response body, expected message, recorded outcome (None: not the site's fault)
CASES = [
    (500, 'domain not allowed. news.example not in [other.example private.example]',
     'news.example is not on this reader’s site list.', 'not-listed'),
    (500, 'Get "https://news.example/story": context deadline exceeded (Client.Timeout exceeded while awaiting headers)',
     'news.example did not respond in time.', 'timeout'),
    (502, '', 'The reader server did not respond.', None),
    (500, 'connection reset by peer', 'This site could not be fetched.', 'fetch-error'),
    (401, '', 'Sign in, then try again.', None),
    (200, PAGE('Just a moment...', TEXT), 'challenge page', 'challenge'),
    (200, PAGE('Subscribe', '<p>Short teaser.</p>'), 'No readable article was returned.', 'short'),
    (200, PAGE('A synthetic story', TEXT), 'Article ready.', 'ok'),
]


class ReaderErrorTests(unittest.TestCase):
    def test_fetch_failures_explain_the_cause_and_record_the_outcome(self):
        web = Path(__file__).resolve().parents[1] / 'web'
        with sync_playwright() as pw, pw.chromium.launch() as browser:
            for status, detail, expected, outcome in CASES:
                with self.subTest(status=status, outcome=outcome):
                    page = browser.new_page(viewport={'width': 390, 'height': 844})
                    recorded = []

                    def route(request):
                        path = request.request.url.split('http://reader.test/', 1)[1].split('#', 1)[0]
                        if path == 'auth.json':
                            request.fulfill(json={'enabled': False})
                        elif path == 'api/':
                            request.fulfill(status=status, body=detail, content_type='application/json' if status == 200 else 'text/plain')
                        elif path.startswith('attempt?'):
                            recorded.append((request.request.method, request.request.url))
                            request.fulfill(status=204)
                        else:
                            file = web / (path or 'index.html')
                            request.fulfill(path=file) if file.is_file() else request.fulfill(status=404)

                    page.route('http://reader.test/**', route)
                    page.goto('http://reader.test/#url=' + ARTICLE)
                    page.wait_for_function('!document.querySelector("#open button").disabled')
                    text = page.locator('#status').text_content()
                    self.assertIn(expected, text)
                    # Ladder's allowlist error names every configured site; never display it.
                    self.assertNotIn('private.example', text)
                    if outcome:
                        page.wait_for_timeout(200)
                    self.assertEqual(len(recorded), 1 if outcome else 0, recorded)
                    if outcome:
                        method, url = recorded[0]
                        query = parse_qs(urlsplit(url).query)
                        self.assertEqual(method, 'POST')
                        self.assertEqual((query['host'], query['outcome']), (['news.example'], [outcome]))
                        # Only the hostname leaves the browser, never the article path.
                        self.assertNotIn('private-path', url)
                    page.close()


if __name__ == '__main__':
    unittest.main()
