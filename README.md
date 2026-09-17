# reCSSitate

A small, self-hosted reader for articles obscured by anti-adblock overlays.
Choose a manual bookmarklet or an optional userscript that offers a **Read article**
button after a large anti-adblock wall persists. Both open the same reader.

The button sends only the article URL, after you tap. Ladder fetches a fresh copy,
using FlareSolverr for the configured sites. Mozilla Readability extracts the
article and DOMPurify sanitizes it into a sandboxed, script-free reading view.
It does not forward your publisher cookies or account. It cannot recover text a
publisher never serves, and it is not a universal paywall or CAPTCHA bypass.

## Quick start

The supplied deployment targets Linux x86_64 with Docker Compose. Run it on an
always-on server. Four pinned containers provide Caddy, Ladder, FlareSolverr and
an outbound Squid proxy. Reserve approximately 3 GB RAM for the stack.

1. Clone this repository. Copy `deploy/.env.example` to `deploy/.env`.
2. Set `READER_HOST` to the server's hostname or IPv4 address and `BIND_ADDRESS`
   to its LAN address. The default binds only localhost.
3. Generate a bcrypt hash with `htpasswd -nB reader` (interactive password
   prompt). Copy the hash after `reader:` into `READER_PASSWORD_HASH`, preserving
   the single quotes. Keep `.env` private and save the password in your vault.
4. Run `python3 tools/configure.py --origin https://YOUR-HOST:8446`.
5. Run `docker compose --project-directory deploy config --quiet`, then
   `docker compose --project-directory deploy up -d`.
6. Trust the Caddy local CA on each client. Export its **public certificate** with
   `docker compose --project-directory deploy cp gateway:/data/caddy/pki/authorities/local/root.crt ./reader-ca.crt`.
   Install it using your device's certificate settings; iOS also requires enabling
   full trust in Settings → General → About → Certificate Trust Settings.
7. Open `https://YOUR-HOST:8446`, select **Sign in to the reader**, and sign in as
   `reader` with the password you chose.

Use an existing trusted certificate instead of Caddy's local CA when appropriate.
Never distribute the CA private key. Keep this service on your private network.
The sample deployment does not configure a router or expose itself to the Internet.

## On iPhone and iPad

**Bookmarklet:** open the reader's landing page and tap **Copy bookmarklet**.
Bookmark the page in Safari, then edit the bookmark and replace its address with
that code. Name it “reCSSitate”. When a news page becomes unreadable, select the
bookmark. This requires a tap on each article and cannot automatically watch
future pages.

**Automatic button:** install [Userscripts for Safari](https://github.com/quoid/userscripts),
enable it in Safari's extension settings, and permit it on the news sites you
read. Open **Install reCSSitate userscript** on the reader's landing page, then use
the Userscripts extension menu to install it. The script uses only the manager's
storage APIs. An unconfigured copy asks for your reader server when first tapped.

The detector checks for article text, an anti-adblock message, a large visible
obstruction, and persistence for 2.5 seconds. Small support notices and cookie
consent dialogs are intentionally left alone. It may miss unfamiliar markup or
walls that remove the article entirely; use the bookmarklet then. The × dismisses
the button for that page visit. Navigation uses the same tab, preserving Back.

## Sites and operation

The initial allowlist is Example publisher A, Example publisher B, Example publisher C, Example publisher D,
and Example publisher E (including their `www` hosts). Live article extraction has been
verified on the first two; the other three are configured, not certified.
To add a site, update both `ALLOWED_DOMAINS` in `deploy/compose.yaml` and
`deploy/rules.yaml`, then recreate the stack. Do not allow arbitrary destinations.

Only Caddy publishes a host port. Fetchers use an internal Docker network and
Squid denies private/nonpublic destination addresses and unsafe ports. The API
requires authentication, limits request size, and strips reader credentials
before forwarding requests to Ladder. Article URLs travel in the browser's URL
fragment and POST body. This is not an anonymity service: publishers and image
hosts still observe network requests, and browser history retains source URLs.

The rendered article cannot execute publisher scripts. Images may load from the
publisher; formatting, interactive embeds and some links may be lost. No archive
history or permanent article cache is maintained. FlareSolverr uses a server-side
Chromium identity, even when the reader is opened on an iPhone.

Ladder v0.0.23 uses FlareSolverr's cookies and then performs its own fetch; it does
not render FlareSolverr's returned HTML. The configured User-Agent matches the
pinned solver image. Recheck this pairing when upgrading images. Some challenge
systems bind clearance to additional browser characteristics and will still fail.

## Development and evidence

Run `npm ci`, `npx playwright install webkit`, then `npm test`. Tests use synthetic
articles and cover negative detections, persistent walls, removal and navigation.
See [VALIDATION.md](VALIDATION.md) for live and native iOS results and limitations.
Do not commit credentials, captured articles, deployment addresses or browser profiles.

Own integration code is MIT licensed. Dependencies retain their own licences;
see [THIRD-PARTY.md](THIRD-PARTY.md). This project does not modify or redistribute
Ladder or FlareSolverr binaries; Compose pulls their upstream images.
