#!/usr/bin/env python3
"""Pull carmodreview.com traffic from Cloudflare.

Two different numbers live behind two different APIs and they disagree, so this
prints both and says which is which:

  RUM (Web Analytics)  -- from the beacon in every page's <head>. Counts a page
                          view only when a real browser executes JavaScript.
                          Bots and blocked scripts vanish. This is the closest
                          thing to "people who read the site".

  Zone HTTP            -- every request that reached Cloudflare, including
                          crawlers, scanners, and asset fetches. Always larger.

The beacon's site tag is in build.py as CF_BEACON_TOKEN. The zone is found by
name so nothing here hardcodes an account or a zone id.

Token lives outside the repo, per the standing rule that credentials never get
pasted into a chat window or committed:

    ~/.config/carmodreview/cloudflare.env       chmod 600
        CLOUDFLARE_API_TOKEN=...

What the token needs:
    Zone -> Analytics -> Read      (zone HTTP numbers)
    Account -> Account Analytics -> Read   (RUM numbers)
    Zone -> Zone -> Read           (to look up the zone id by name)

Usage:
    python3 tools/cf_traffic.py            # last 7 days
    python3 tools/cf_traffic.py 30         # last 30 days
"""
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.expanduser('~/.config/carmodreview/cloudflare.env')
ZONE_NAME = 'carmodreview.com'
API = 'https://api.cloudflare.com/client/v4'
GRAPHQL = 'https://api.cloudflare.com/client/v4/graphql'


def load_token():
    """Token from the env, else from the config file. Never from argv.

    A token on the command line lands in shell history and in the process list
    where any other account on the machine can read it with `ps`.
    """
    tok = os.environ.get('CLOUDFLARE_API_TOKEN', '').strip()
    if tok:
        return tok
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('CLOUDFLARE_API_TOKEN='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    return ''


def call(path, token, params=None):
    url = API + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())


def gql(query, variables, token):
    body = json.dumps({'query': query, 'variables': variables}).encode()
    req = urllib.request.Request(GRAPHQL, data=body, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def find_zone(token):
    data = call(f'/zones?name={ZONE_NAME}', token)
    for z in data.get('result') or []:
        if z.get('name') == ZONE_NAME:
            return z['id'], z['account']['id']
    return None, None


def beacon_tag():
    """The RUM site tag, read from build.py so there is one source for it."""
    import re
    src = open(os.path.join(ROOT, 'build.py'), encoding='utf-8').read()
    m = re.search(r"CF_BEACON_TOKEN\s*=\s*'([0-9a-f]{32})'", src)
    return m.group(1) if m else ''


def rum_daily(account_id, token, days):
    """Web Analytics pageviews per day, from the beacon."""
    q = """
    query($account: String!, $since: Time!, $until: Time!, $tag: String!) {
      viewer {
        accounts(filter: {accountTag: $account}) {
          rumPageloadEventsAdaptiveGroups(
            limit: 100
            filter: {siteTag: $tag, datetime_geq: $since, datetime_leq: $until}
            orderBy: [date_ASC]
          ) {
            count
            sum { visits }
            dimensions { date }
          }
        }
      }
    }
    """
    import datetime
    until = datetime.datetime.now(datetime.timezone.utc)
    since = until - datetime.timedelta(days=days)
    return gql(q, {
        'account': account_id,
        'since': since.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'until': until.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'tag': beacon_tag(),
    }, token)


def rum_top_paths(account_id, token, days, limit=10):
    q = """
    query($account: String!, $since: Time!, $until: Time!, $tag: String!) {
      viewer {
        accounts(filter: {accountTag: $account}) {
          rumPageloadEventsAdaptiveGroups(
            limit: 10
            filter: {siteTag: $tag, datetime_geq: $since, datetime_leq: $until}
            orderBy: [count_DESC]
          ) {
            count
            dimensions { requestPath }
          }
        }
      }
    }
    """
    import datetime
    until = datetime.datetime.now(datetime.timezone.utc)
    since = until - datetime.timedelta(days=days)
    return gql(q, {
        'account': account_id,
        'since': since.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'until': until.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'tag': beacon_tag(),
    }, token)


def zone_http(zone_id, token, days):
    """Every request that reached the zone, crawlers included."""
    return call(f'/zones/{zone_id}/analytics/dashboard', token,
                {'since': f'-{days}d', 'continuous': 'true'})


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    token = load_token()
    if not token:
        print('No Cloudflare API token found.\n')
        print('Create one (My Profile -> API Tokens -> Create Token, custom token):')
        print('  Zone      -> Analytics            -> Read')
        print('  Zone      -> Zone                 -> Read')
        print('  Account   -> Account Analytics    -> Read')
        print('  Zone Resources: include carmodreview.com\n')
        print('Then save it, never pasting it into a chat window:')
        print(f'  mkdir -p {os.path.dirname(ENV_PATH)}')
        print(f'  echo "CLOUDFLARE_API_TOKEN=paste_it_here" > {ENV_PATH}')
        print(f'  chmod 600 {ENV_PATH}')
        return 1

    zone_id, account_id = find_zone(token)
    if not zone_id:
        print(f'Token works but cannot see a zone named {ZONE_NAME}.')
        print('Check that the token scopes include this zone.')
        return 1
    print(f'zone {ZONE_NAME} = {zone_id[:8]}...  account {account_id[:8]}...\n')

    tag = beacon_tag()
    print(f'beacon site tag: {tag or "(none found in build.py)"}\n')

    print(f'--- Web Analytics (beacon), last {days} days ---')
    try:
        d = rum_daily(account_id, token, days)
        if d.get('errors'):
            print('  query failed:', json.dumps(d['errors'])[:400])
        else:
            groups = (d['data']['viewer']['accounts'][0]
                      ['rumPageloadEventsAdaptiveGroups'])
            if not groups:
                print('  no beacons recorded in this window')
            total = 0
            for g in groups:
                pv, vis = g['count'], (g.get('sum') or {}).get('visits') or 0
                total += pv
                print(f"  {g['dimensions']['date']}  {pv:>6} view  {vis:>6} visit")
            print(f'  {"TOTAL":<10}  {total:>6} view')
    except Exception as e:
        print('  error:', e)

    print(f'\n--- top pages, last {days} days ---')
    try:
        d = rum_top_paths(account_id, token, days)
        if d.get('errors'):
            print('  query failed:', json.dumps(d['errors'])[:400])
        else:
            for g in (d['data']['viewer']['accounts'][0]
                      ['rumPageloadEventsAdaptiveGroups']):
                print(f"  {g['count']:>6}  {g['dimensions']['requestPath']}")
    except Exception as e:
        print('  error:', e)

    print(f'\n--- zone HTTP, last {days} days (includes bots) ---')
    try:
        z = zone_http(zone_id, token, days)
        if not z.get('success'):
            print('  ', json.dumps(z.get('errors'))[:300])
        else:
            t = z['result'].get('totals', {})
            for k in ('requests', 'pageViews', 'uniques', 'bandwidth'):
                v = (t.get(k) or {}).get('all')
                if v is not None:
                    print(f'  {k:<10} {v:,}' if isinstance(v, int) else f'  {k:<10} {v}')
    except Exception as e:
        print('  error:', e)
    return 0


if __name__ == '__main__':
    sys.exit(main())
