# Validation — 2026-09-16

- iOS 26.5 simulator, iPhone 17 Pro: native WKWebView with an ephemeral cookie
  store, iPhone platform, five touch points, 402 CSS-pixel viewport and Safari
  26.5 User-Agent. A test-only content rule reproduced Example publisher A's
  anti-adblock wall after scrolling. The userscript offered its button, tapping
  it reached the deployed reader, and the article rendered without horizontal
  overflow. The screenshot was visually inspected for clipping and overlap.
- The native harness provided the two Userscripts storage APIs. This verifies
  the script in iOS WebKit, not installation through the actual Userscripts app
  or operation on a physical iPhone. Safari's native HTTPS login prompt was also
  observed; saved-bookmark editing was not automated in Simulator Safari.
- Isolated Chromium with a mobile device profile: the generated bookmarklet
  navigated from live Example publisher A and Example publisher B articles, using one cookie jar. The
  reader returned respectively 3,377 and 8,658 characters, with zero script
  elements in its sandbox and no horizontal page overflow.
- Desktop Playwright WebKit's live LAN navigation reported an offline error;
  it was not counted as a passing live test. Its synthetic detector suite passed.
- Backend: Example publisher A fetch returned in roughly 3.5 seconds. FlareSolverr logs confirmed
  an actual request through the outbound proxy. No challenge was present in that
  request, so this does not demonstrate CAPTCHA solving.
- API without authentication returned 401. Nonallowlisted and loopback targets
  returned Ladder's explicit “domain not allowed” error (upstream uses HTTP 500).
  A private-address request through the outbound proxy was denied with HTTP 403.
- Synthetic mobile WebKit tests reject ordinary article pages, cookie dialogs,
  small support banners and hidden walls; accept a persistent large wall; remove
  the button when the wall disappears; and preserve the source URL on navigation.

Site behavior changes with geography, experiments, cookies and article counts.
The three additional configured publishers still need live extraction coverage.
A working fetch is not a claim of full article completeness against a publisher's
subscriber edition. No normal browser profiles were changed for these tests.
