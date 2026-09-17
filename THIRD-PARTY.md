# Dependencies and licences

| Component | Pin | Licence / source |
|---|---|---|
| Ladder | v0.0.23 | [GPL-3.0](https://github.com/everywall/ladder) |
| FlareSolverr | v3.5.2 | [MIT](https://github.com/FlareSolverr/FlareSolverr) |
| Caddy | 2.11.2 | [Apache-2.0](https://github.com/caddyserver/caddy) |
| Squid Ubuntu container | image digest in Compose | [GPL-2.0-or-later, plus Ubuntu package licences](https://www.squid-cache.org/) |
| Mozilla Readability | vendored snapshot | [Apache-2.0](https://github.com/mozilla/readability); licence and notice in web/vendor |
| DOMPurify | 3.3.1 | [Apache-2.0 OR MPL-2.0](https://github.com/cure53/DOMPurify); licence in web/vendor |
| Playwright (development only) | 1.62.1 | [Apache-2.0](https://github.com/microsoft/playwright) |

All container images are pinned by digest in Compose. The Squid digest targets
amd64; alternative architectures require a separately verified image pin.
The integration's MIT licence does not replace any dependency's licence.

## Potential upstream improvements

Ladder's FlareSolverr integration transfers cookies but ignores the solver's
returned User-Agent and HTML. Explicitly supporting either output could avoid
identity drift and duplicated fetches. This is a contribution candidate, not a
patch included here. No upstream issue or pull request has been submitted.

Readability has comment-only edits to use a revision-independent source link and
generic wording. Its executable code and licence notice are unchanged.
