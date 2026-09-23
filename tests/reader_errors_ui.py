"""Run with Playwright Python on a Linux test host; no external sites are used."""
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright

ARTICLE = 'https://news.example/story'
CASES = [
    (500, 'domain not allowed. news.example not in [other.example private.example]',
     'news.example is not on this reader’s site list.'),
    (500, 'Get "https://news.example/story": context deadline exceeded (Client.Timeout exceeded while awaiting headers)',
     'news.example did not respond in time.'),
    (502, '', 'The reader server did not respond.'),
    (500, 'connection reset by peer', 'This site could not be fetched.'),
    (401, '', 'Sign in, then try again.'),
]


class ReaderErrorTests(unittest.TestCase):
    def test_fetch_failures_explain_the_cause(self):
        web = Path(__file__).resolve().parents[1] / 'web'
        with sync_playwright() as pw, pw.chromium.launch() as browser:
            for status, detail, expected in CASES:
                with self.subTest(status=status, detail=detail):
                    page = browser.new_page(viewport={'width': 390, 'height': 844})

                    def route(request):
                        path = request.request.url.split('http://reader.test/', 1)[1].split('#', 1)[0]
                        if path == 'auth.json':
                            request.fulfill(json={'enabled': False})
                        elif path == 'api/':
                            request.fulfill(status=status, body=detail, content_type='text/plain')
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
                    page.close()


if __name__ == '__main__':
    unittest.main()
