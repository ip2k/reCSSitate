#!/usr/bin/env python3
"""Generate an installable userscript without putting a deployment URL in source."""
import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit
p=argparse.ArgumentParser();p.add_argument('--origin',required=True);args=p.parse_args()
u=urlsplit(args.origin)
if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in ('','/'):
    p.error('Use an HTTPS origin without credentials, a path, query or fragment')
if not re.fullmatch(r'[A-Za-z0-9.:-]+', u.netloc):
    p.error('Use a DNS hostname or IPv4 address, with an optional port')
try:
    u.port
except ValueError:
    p.error('Invalid port')
root=Path(__file__).resolve().parent.parent
origin=f'https://{u.netloc}'
(root/'web/recssitate.user.js').write_text((root/'userscript/recssitate.user.js').read_text().replace('__PAGE_RESCUE_ORIGIN__',origin))
print('Generated web/recssitate.user.js')
