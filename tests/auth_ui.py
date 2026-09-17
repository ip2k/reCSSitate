"""Run with Playwright Python on a Linux test host; no external sites are used."""
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright


class AuthenticationUiTests(unittest.TestCase):
    def test_signin_follows_gateway_setting(self):
        web = Path(__file__).resolve().parents[1] / 'web'
        with sync_playwright() as pw, pw.chromium.launch() as browser:
            for enabled in (False, True):
                with self.subTest(enabled=enabled):
                    page = browser.new_page(viewport={'width': 390, 'height': 844})

                    def route(request):
                        path = request.request.url.split('http://reader.test/', 1)[1]
                        if path == 'auth.json':
                            request.fulfill(json={'enabled': enabled})
                        else:
                            file = web / (path or 'index.html')
                            request.fulfill(path=file) if file.is_file() else request.fulfill(status=404)

                    page.route('http://reader.test/**', route)
                    page.goto('http://reader.test/')
                    page.wait_for_load_state('networkidle')
                    self.assertEqual(page.locator('#signin').is_visible(), enabled)
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                    page.close()


if __name__ == '__main__':
    unittest.main()
