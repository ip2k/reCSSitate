#!/usr/bin/env python3
"""Summarize reader attempts and flag sites the generic rule cannot read.

Reads the gateway's attempt log (deploy/attempts/attempts.log by default), or
`docker compose logs gateway` output on standard input with `-`.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
OUTCOMES = ('ok', 'short', 'challenge', 'fetch-error', 'timeout', 'not-listed')
# Outcomes that point at the site's markup or defences rather than the network.
UNREADABLE = ('short', 'challenge', 'fetch-error')
HOST = re.compile(r'[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?')


def records(lines):
    for line in lines:
        start = line.find('{')
        if start < 0:
            continue
        try:
            entry = json.loads(line[start:])
        except ValueError:
            continue
        if not str(entry.get('logger', '')).startswith('http.log.access.attempts') or entry.get('status') != 204:
            continue
        query = parse_qs(urlsplit(entry.get('request', {}).get('uri', '')).query)
        host = query.get('host', [''])[0].lower()
        outcome = query.get('outcome', [''])[0]
        if HOST.fullmatch(host) and outcome in OUTCOMES:
            yield entry.get('ts', 0), host, outcome


def site(host):
    return host[4:] if host.startswith('www.') else host


def named_sites(path, pattern):
    if not path.exists():
        return set()
    return {site(match.lower()) for match in re.findall(pattern, path.read_text())}


def covered(host, names):
    return any(host == name or host.endswith('.' + name) for name in names)


def verdict(counts, last, listed, adapter, threshold):
    unreadable = sum(counts[o] for o in UNREADABLE)
    if counts['ok'] and last == 'ok':
        return 'works'
    if counts['ok']:
        return 'intermittent'
    if unreadable >= threshold:
        return 'adapter failing' if adapter else 'needs adapter'
    if counts['not-listed'] and not listed and set(counts) == {'not-listed'}:
        return 'requested'
    return 'watch'


ORDER = ('needs adapter', 'adapter failing', 'intermittent', 'requested', 'watch', 'works')


def summarize(lines, sites_file, adapters_file, threshold):
    known = named_sites(sites_file, r'(?m)^\s*([A-Za-z0-9.-]+)')
    adapters = named_sites(adapters_file, r'''['"]([A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,})['"]''')
    hosts = {}
    for ts, host, outcome in records(lines):
        entry = hosts.setdefault(site(host), {'counts': Counter(), 'last': None, 'ts': 0})
        entry['counts'][outcome] += 1
        if ts >= entry['ts']:
            entry['ts'], entry['last'] = ts, outcome
    rows = []
    for host, entry in hosts.items():
        listed, adapter = covered(host, known), covered(host, adapters)
        rows.append({
            'site': host, 'verdict': verdict(entry['counts'], entry['last'], listed, adapter, threshold),
            'attempts': sum(entry['counts'].values()), 'outcomes': dict(entry['counts']),
            'last': entry['last'], 'last_seen': datetime.fromtimestamp(entry['ts'], timezone.utc).strftime('%Y-%m-%d'),
            'listed': listed, 'adapter': adapter,
        })
    return sorted(rows, key=lambda r: (ORDER.index(r['verdict']), -r['attempts'], r['site']))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('log', nargs='*', default=[str(ROOT / 'deploy/attempts/attempts.log')],
                        help="attempt log files, or - for standard input")
    parser.add_argument('--sites', type=Path, default=ROOT / 'deploy/sites.txt')
    parser.add_argument('--adapters', type=Path, default=ROOT / 'deploy/adapters.yaml')
    parser.add_argument('--threshold', type=int, default=2,
                        help='unreadable attempts, with none readable, before a site is flagged (default 2)')
    parser.add_argument('--flagged', action='store_true', help='show only sites that need an adapter')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    lines = []
    for name in args.log:
        if name == '-':
            lines.extend(sys.stdin)
        else:
            # Rolled files (attempts-<time>.log) hold older entries.
            path = Path(name)
            parts = sorted(path.parent.glob(path.stem + '*' + path.suffix)) or ([path] if path.exists() else [])
            if not parts:
                parser.error(f'no attempt log at {path}')
            for part in parts:
                with open(part, errors='replace') as handle:
                    lines.extend(handle)
    rows = summarize(lines, args.sites, args.adapters, args.threshold)
    if args.flagged:
        rows = [r for r in rows if r['verdict'] in ('needs adapter', 'adapter failing')]
    if args.json:
        json.dump(rows, sys.stdout, indent=2)
        print()
        return
    if not rows:
        print('No attempts recorded.' if not args.flagged else 'No site needs an adapter.')
        return
    width = max(len(r['site']) for r in rows)
    print(f"{'site':<{width}}  {'verdict':<15}  {'tries':>5}  {'last':<11}  {'seen':<10}  outcomes")
    for r in rows:
        outcomes = ' '.join(f'{k}={v}' for k, v in sorted(r['outcomes'].items()))
        marks = ('' if r['listed'] else ' unlisted') + (' adapter' if r['adapter'] else '')
        print(f"{r['site']:<{width}}  {r['verdict']:<15}  {r['attempts']:>5}  {r['last']:<11}  {r['last_seen']:<10}  {outcomes}{marks}")


if __name__ == '__main__':
    main()
