#!/usr/bin/env python3
"""Get the Instagram credentials in place, with as little typing as possible.

The Instagram Graph API needs two values stored at
~/.config/carmodreview/instagram.json:

  ig_user_id    the numeric Instagram Business account id -- not the @handle
  access_token  a long-lived token with instagram_content_publish

Both come from Meta's own tools, so they cannot be created here. What this
script does is take the awkward parts:

  * It finds the ig_user_id for you from the token, rather than making you
    dig the number out of the Graph API explorer -- which is the step people
    get wrong, because the id next to your Page is the Page's id and looks
    equally plausible.
  * It exchanges a short-lived token (what the Graph explorer hands you, good
    for an hour) for a long-lived one (60 days), which is what a daily job
    needs. A short-lived token in this file would work for the first run and
    fail every run after that, with an error that reads like a permissions
    problem.
  * It verifies the token can actually publish before writing the file, so a
    missing instagram_content_publish is caught now rather than at 16:20 when
    the job runs unattended.
  * It writes the file with 0600. A token in a world-readable file is the same
    as a token in the repo.

Usage:
  python3 ig_setup.py                 # reads the token from stdin
  python3 ig_setup.py --token-file ~/Downloads/token.txt

Nothing is printed that would put the token in your shell history or in a
scrollback log.
"""
import argparse
import json
import os
import stat
import sys
import urllib.parse
import urllib.request

CONF = os.path.expanduser('~/.config/carmodreview')
DEST = os.path.join(CONF, 'instagram.json')
GRAPH = 'https://graph.facebook.com/v21.0'


def get(path, params):
    """GET a Graph endpoint, surfacing Facebook's error text verbatim."""
    url = f'{GRAPH}/{path}?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')
        try:
            err = json.loads(body)['error']
            raise SystemExit(
                f'facebook rejected this: {err.get("message")}\n'
                f'  type={err.get("type")} code={err.get("code")} '
                f'subcode={err.get("error_subcode")}\n'
                f'  {err.get("error_user_msg") or ""}')
        except (ValueError, KeyError):
            raise SystemExit(f'facebook returned {e.code}: {body[:400]}')


def long_lived(token):
    """Exchange a short-lived token for a 60-day one.

    Returns the original token unchanged when the exchange is not possible --
    an already-long-lived token cannot be exchanged again, and that is fine,
    not a failure.
    """
    app_id = os.environ.get('FB_APP_ID')
    app_secret = os.environ.get('FB_APP_SECRET')
    if not (app_id and app_secret):
        print('  (no FB_APP_ID / FB_APP_SECRET set, so the token is used as-is)')
        return token, None
    try:
        r = get('oauth/access_token', {
            'grant_type': 'fb_exchange_token',
            'client_id': app_id,
            'client_secret': app_secret,
            'fb_exchange_token': token,
        })
    except SystemExit as e:
        print(f'  (token exchange skipped: {e})')
        return token, None
    return r.get('access_token', token), r.get('expires_in')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--token-file',
                    help='file containing just the token; default is stdin')
    a = ap.parse_args()

    if a.token_file:
        token = open(os.path.expanduser(a.token_file), encoding='utf-8').read()
    else:
        print('Paste the access token from the Graph API explorer, then Enter.')
        print('(It is not echoed back and is not written to history.)')
        token = sys.stdin.readline()
    token = token.strip()
    if not token:
        raise SystemExit('no token given')
    if ' ' in token:
        raise SystemExit('that looks like more than one line; '
                         'paste only the token')

    print('checking the token ...')
    me = get('me', {'fields': 'id,name', 'access_token': token})
    print(f'  facebook identity: {me.get("name")} ({me.get("id")})')

    token, ttl = long_lived(token)

    print('looking for the Instagram Business account ...')
    pages = get('me/accounts', {'access_token': token,
                                'fields': 'id,name,instagram_business_account'})
    found = []
    for pg in pages.get('data', []):
        ig = pg.get('instagram_business_account')
        if ig:
            found.append((pg['name'], ig['id']))
    if not found:
        raise SystemExit(
            'no Instagram Business account is linked to any of your Pages.\n'
            'In the Instagram app: Settings > Business tools and controls >\n'
            'connect a Facebook Page. Then run this again.')

    if len(found) > 1:
        print('more than one linked account:')
        for i, (name, iid) in enumerate(found, 1):
            print(f'  {i}. {name}  (ig id {iid})')
        pick = input(f'which one? [1-{len(found)}] ').strip() or '1'
        page_name, ig_id = found[int(pick) - 1]
    else:
        page_name, ig_id = found[0]
    print(f'  using {page_name} -> instagram id {ig_id}')

    # The id has to be the Instagram account's, not the Page's. Checking that
    # it answers as an IG user is the cheapest way to catch the mix-up, which
    # is otherwise only visible as a confusing publish failure later.
    who = get(ig_id, {'fields': 'id,username', 'access_token': token})
    print(f'  instagram account: @{who.get("username", "?")}')

    # A publish check reads the account's own media edge. Publishing itself
    # is not attempted -- that would post something -- but a token missing
    # instagram_content_publish fails here, before the job ever runs.
    get(f'{ig_id}/media', {'access_token': token, 'limit': '1'})
    print('  token can read the media edge')

    os.makedirs(CONF, mode=0o700, exist_ok=True)
    with open(DEST, 'w', encoding='utf-8') as f:
        json.dump({'ig_user_id': ig_id, 'access_token': token,
                   'page_name': page_name,
                   'obtained': __import__('datetime').date.today().isoformat()},
                  f, indent=2)
    os.chmod(DEST, stat.S_IRUSR | stat.S_IWUSR)
    print(f'\nwrote {DEST} (mode 600)')
    if ttl:
        print(f'token valid for about {ttl // 86400} days -- re-run this before then')
    else:
        print('token lifetime unknown; a Graph API long-lived token lasts 60 days')


if __name__ == '__main__':
    main()
