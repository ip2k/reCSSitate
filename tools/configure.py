#!/usr/bin/env python3
"""Generate local deployment assets from a private site list."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


def configure(origin, sites_file, root):
    u = urlsplit(origin)
    if (u.scheme != 'https' or not u.hostname or u.username or u.password
            or u.query or u.fragment or u.path not in ('', '/')
            or not re.fullmatch(r'[A-Za-z0-9.:-]+', u.netloc)):
        raise ValueError('Use an HTTPS hostname or IPv4 origin without credentials or a path')
    u.port  # Reject malformed or out-of-range ports.
    sites = set()
    for line in sites_file.read_text().splitlines():
        host = line.split('#', 1)[0].strip().lower()
        if not host:
            continue
        labels = host.split('.')
        if (len(host) > 253 or len(labels) < 2 or labels[-1].isdigit()
                or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
                       for label in labels)):
            raise ValueError('The site list must contain DNS hostnames, one per line')
        sites.add(host)
    if not sites:
        raise ValueError('Provide at least one site; unrestricted fetching is not supported')
    rules = []
    allowed = set()
    for site in sorted(sites):
        aliases = [] if site.startswith('www.') else ['www.' + site]
        allowed.update([site, *aliases])
        rules.append({'domain': site, 'domains': aliases, 'useFlareSolverr': True,
                      'headers': {'x-forwarded-for': 'none', 'referer': 'none',
                                  'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36'}})
    # JSON is valid YAML and avoids a YAML dependency in the setup tool.
    (root / 'deploy/rules.yaml').write_text(json.dumps(rules, indent=2) + '\n')
    (root / 'deploy/sites.env').write_text('ALLOWED_DOMAINS=' + ','.join(sorted(allowed)) + '\n')
    script = (root / 'userscript/recssitate.user.js').read_text()
    (root / 'web/recssitate.user.js').write_text(script.replace('__PAGE_RESCUE_ORIGIN__', f'https://{u.netloc}'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', required=True)
    parser.add_argument('--sites', required=True, type=Path)
    args = parser.parse_args()
    try:
        configure(args.origin, args.sites, Path(__file__).resolve().parent.parent)
    except ValueError as error:
        parser.error(str(error))
    print('Generated local rules, allowlist and userscript; these files are excluded from Git.')
