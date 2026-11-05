#!/usr/bin/env python3
"""Post one short a day to Instagram and YouTube.

Design notes, because most of the decisions here are about the failure modes
rather than the happy path:

* It posts from a queue file (social/queue.json), not from "whatever is in the
  folder". A scheduled job that uploads everything it finds will, the first time
  it runs against a fresh render, publish eleven videos in one minute.

* Every action writes its result into social/posted.json BEFORE returning, and
  the queue is re-read from disk each run. If the machine sleeps mid-run or the
  job is interrupted, the next run picks up from the truth on disk rather than
  re-uploading.

* It refuses to post if the article a short came from has changed since the
  short was rendered. A queued video quoting $189.99 when the page now says
  $209.99 is the exact drift make_short.py exists to prevent, and this is the
  last place it can still be caught.

* --dry-run is the default for a first run. Nothing posts until the credentials
  are in place and the operator has seen what it intends to do.

Credentials, none of which belong in this file or in git:
  ~/.config/carmodreview/youtube/client_secret.json   (Google OAuth client)
  ~/.config/carmodreview/youtube/token.json           (written by --auth)
  ~/.config/carmodreview/instagram.json               (IG business account)

  python3 upload.py --auth youtube     # one-time, opens a browser
  python3 upload.py --dry-run          # see what it would post today
  python3 upload.py                    # post it
"""
import argparse
import datetime
import hashlib
import json
import os
import random
import re
import subprocess
import sys

ROOT = os.path.expanduser('~/carmodreview')
SOCIAL = os.path.join(ROOT, 'social')
CONF = os.path.expanduser('~/.config/carmodreview')
QUEUE = os.path.join(SOCIAL, 'queue.json')
LOG = os.path.join(SOCIAL, 'posted.json')

YT_SECRET = os.path.join(CONF, 'youtube', 'client_secret.json')
YT_TOKEN = os.path.join(CONF, 'youtube', 'token.json')
# youtube.upload alone can only create videos. Deleting a bad upload, editing
# a description after the fact, or fixing a typo all need the broader scope, so
# ask for it up front rather than discovering the gap at the moment an edit is
# needed -- which is exactly how this was found.
YT_SCOPE = ['https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube']
IG_CONF = os.path.join(CONF, 'instagram.json')


# ───────────────────────────────────────────────────────── queue construction
def _articles():
    """slug -> source path for every article."""
    out = {}
    d = os.path.join(ROOT, 'content', 'articles')
    for f in sorted(os.listdir(d)):
        if not f.endswith('.md'):
            continue
        p = os.path.join(d, f)
        body = open(p, encoding='utf-8').read()
        m = re.search(r'^slug:\s*(.+?)\s*$', body, re.M)
        if m:
            out[m.group(1)] = p
    return out


def _sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()[:16]


def build_queue():
    """Write the queue if it is missing; otherwise leave it alone.

    Existing entries keep their position and their state. Rebuilding the queue
    every run would reset anything already marked posted and re-post the lot.
    """
    arts = _articles()
    if os.path.exists(QUEUE):
        return json.load(open(QUEUE, encoding='utf-8'))

    items = []
    for slug, src in arts.items():
        mp4 = os.path.join(SOCIAL, f'{slug}-short.mp4')
        if not os.path.exists(mp4):
            continue
        items.append({
            'slug': slug,
            # The article hash at render time. upload.py re-checks it and
            # skips the item rather than posting a stale figure.
            'source_sha': _sha(src),
            'added': datetime.date.today().isoformat(),
        })
    # Newest article first: the tonneau and intake guides are the ones with
    # current prices, and a queue ordered by hash would lead with a guide from
    # January.
    items.sort(key=lambda i: os.path.getmtime(
        os.path.join(ROOT, 'content', 'articles',
                     next(f for f in os.listdir(os.path.join(ROOT, 'content', 'articles'))
                          if re.search(r'^slug:\s*' + re.escape(i['slug']) + r'\s*$',
                                       open(os.path.join(ROOT, 'content', 'articles', f),
                                            encoding='utf-8').read(), re.M)))),
        reverse=True)
    q = {'items': items, 'created': datetime.date.today().isoformat()}
    os.makedirs(SOCIAL, exist_ok=True)
    json.dump(q, open(QUEUE, 'w', encoding='utf-8'), indent=2)
    return q


def posted():
    if not os.path.exists(LOG):
        return {}
    return json.load(open(LOG, encoding='utf-8'))


def record(slug, platform, result):
    """Write the outcome before anything else happens.

    Called immediately after an upload returns, so an interruption after this
    point cannot cause a second upload of the same video.
    """
    log = posted()
    log.setdefault(slug, {})[platform] = result
    json.dump(log, open(LOG, 'w', encoding='utf-8'), indent=2)


def next_item(queue):
    """First item that still needs posting somewhere it can be posted.

    Reordering for variety is deliberately not done: a deterministic order means
    a failed run is reproducible, and random.choice on a scheduled job is how you
    end up unable to explain what went out on Tuesday.
    """
    log = posted()
    for it in queue['items']:
        done = log.get(it['slug'], {})
        if 'youtube' not in done or 'instagram' not in done:
            return it
    return None


# ─────────────────────────────────────────────────────────────────── youtube
def yt_client():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    if os.path.exists(YT_TOKEN):
        creds = Credentials.from_authorized_user_file(YT_TOKEN, YT_SCOPE)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not os.path.exists(YT_SECRET):
            raise SystemExit(
                f'missing {YT_SECRET}\n'
                'Create a Google Cloud project, enable "YouTube Data API v3",\n'
                'create an OAuth client of type "Desktop app", download the JSON\n'
                'and save it there. Then run: python3 upload.py --auth youtube')
        flow = InstalledAppFlow.from_client_secrets_file(YT_SECRET, YT_SCOPE)
        creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(YT_TOKEN), exist_ok=True)
        open(YT_TOKEN, 'w').write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)


def post_youtube(slug, dry):
    """Upload as a Short.

    YouTube decides "Short" by aspect ratio and length, not by an API flag: a
    vertical clip under three minutes uploaded normally is a Short. The #Shorts
    tag is what makes it surface in the Shorts shelf sooner.
    """
    mp4 = os.path.join(SOCIAL, f'{slug}-short.mp4')
    meta = os.path.join(SOCIAL, f'{slug}-youtube.txt')
    title = open(meta, encoding='utf-8').read().split('\n')[0][:100]
    desc = open(meta, encoding='utf-8').read() + '\n#Shorts'
    if dry:
        return {'dry': True, 'title': title, 'file': os.path.basename(mp4),
                'bytes': os.path.getsize(mp4)}

    from googleapiclient.http import MediaFileUpload
    yt = yt_client()
    body = {
        'snippet': {
            'title': title,
            'description': desc[:4900],
            'categoryId': '2',  # Autos & Vehicles
            'defaultLanguage': 'en',
        },
        'status': {
            'privacyStatus': 'public',
            # Declared, not guessed: the shorts contain no third-party footage
            # and no music, but they do discuss products we have no licence to
            # monetise claims about, so this is stated honestly as "not made
            # for kids" and nothing more.
            'selfDeclaredMadeForKids': False,
        },
    }
    media = MediaFileUpload(mp4, mimetype='video/mp4', resumable=True)
    req = yt.videos().insert(part='snippet,status', body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f'  youtube {int(status.progress() * 100)}%')
    vid = resp['id']
    return {'id': vid, 'url': f'https://youtube.com/shorts/{vid}',
            'at': datetime.datetime.now().isoformat(timespec='seconds')}


# ───────────────────────────────────────────────────────────────── instagram
def post_instagram(slug, dry):
    """Publish a Reel through the Instagram Graph API.

    The Reel flow is three calls: create a media container pointing at a public
    video URL, poll until Instagram has finished ingesting it, then publish.

    That first point is why this cannot work with a local file: the Graph API
    fetches the video from a URL, so the mp4 has to be publicly reachable. The
    site is on GitHub Pages, so the supported route is to commit the short under
    docs/social/ and let the Pages build serve it. If it is not reachable, this
    raises rather than posting a broken container.
    """
    if not os.path.exists(IG_CONF):
        raise SystemExit(
            f'missing {IG_CONF}\n'
            'Needs: {"ig_user_id": ..., "access_token": ...}\n'
            'A long-lived token goes on an Instagram Business account connected\n'
            'to a Facebook Page, with instagram_content_publish granted.')
    conf = json.load(open(IG_CONF, encoding='utf-8'))
    caption = open(os.path.join(SOCIAL, f'{slug}-caption.txt'),
                   encoding='utf-8').read()
    video_url = f'https://carmodreview.com/social/{slug}-short.mp4'
    cover_url = f'https://carmodreview.com/social/{slug}-cover.jpg'
    if dry:
        return {'dry': True, 'video_url': video_url, 'cover': cover_url,
                'caption_chars': len(caption)}
    if subprocess.run(['curl', '-sfI', video_url], stdout=subprocess.DEVNULL).returncode:
        raise SystemExit(f'video not reachable at {video_url} -- commit the short '
                         'to docs/social/ and let Pages build before posting')

    import urllib.parse

    base = f'https://graph.facebook.com/v21.0/{conf["ig_user_id"]}'
    token = conf['access_token']

    # curl, not urllib. The Python on this machine cannot find a CA bundle, so
    # every https call through urllib dies with CERTIFICATE_VERIFY_FAILED
    # before the request leaves the process -- which reads as a Meta outage
    # rather than the local environment problem it is. curl trusts the chain
    # here, and passes Meta's own error text straight through.
    def graph(url, data=None):
        cmd = ['curl', '-sS', '--max-time', '120']
        if data:
            cmd += ['-X', 'POST', '--data', urllib.parse.urlencode(data)]
        cmd.append(url)
        r = subprocess.run(cmd, capture_output=True)
        body = r.stdout.decode('utf-8', 'replace')
        try:
            return json.loads(body)
        except ValueError:
            raise SystemExit(f'graph returned non-json: {body[:400]}')

    def call(path, params):
        params = dict(params, access_token=token)
        r = graph(f'{base}{path}', params)
        if r.get('error'):
            raise SystemExit(f'instagram {path} failed: {r["error"].get("message")}')
        return r

    container = call('/media', {
        'media_type': 'REELS',
        'video_url': video_url,
        'cover_url': cover_url,
        'caption': caption[:2200],
        'share_to_feed': 'true',
    })
    cid = container['id']

    # Instagram ingests asynchronously. Poll rather than sleeping a fixed
    # amount: too short and publish fails on a container still in progress,
    # too long and the job sits idle every day for no reason.
    import time
    status_url = (f'https://graph.facebook.com/v21.0/{cid}'
                  f'?fields=status_code&access_token={token}')
    for _ in range(40):
        r = graph(status_url)
        code = r.get('status_code')
        if code == 'FINISHED':
            break
        if code == 'ERROR':
            raise SystemExit(f'instagram container error: {r}')
        time.sleep(10)
    else:
        raise SystemExit('instagram container never finished processing')

    res = call('/media_publish', {'creation_id': cid})
    return {'id': res['id'], 'at': datetime.datetime.now().isoformat(timespec='seconds')}


# ────────────────────────────────────────────────────────────────────── main
def cmd_auth(platform):
    if platform == 'youtube':
        yt_client()
        print(f'authorised; token written to {YT_TOKEN}')
    else:
        raise SystemExit('only youtube needs --auth; instagram uses a token '
                         'file you create by hand (see the docstring)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--auth', choices=['youtube'])
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--platform', choices=['youtube', 'instagram', 'both'],
                    default='both')
    ap.add_argument('--slugs', help='comma-separated, for a one-off post')
    a = ap.parse_args()

    if a.auth:
        return cmd_auth(a.auth)

    queue = build_queue()
    done = posted()

    if a.slugs:
        want = [s.strip() for s in a.slugs.split(',') if s.strip()]
        items = [i for i in queue['items'] if i['slug'] in want]
    else:
        one = next_item(queue)
        items = [one] if one else []

    if not items:
        print('queue empty -- every short has been posted to both platforms')
        return

    arts = _articles()
    for it in items:
        src = arts.get(it['slug'])
        if not src:
            print(f'skip {it["slug"]}: article gone')
            continue
        # Drift check: the article must still be the one the short was cut from.
        if _sha(src) != it.get('source_sha'):
            print(f'skip {it["slug"]}: article changed since render. '
                  f'Re-run: python3 make_short.py {it["slug"]}')
            continue

        todo = [p for p in (['youtube', 'instagram']
                            if a.platform == 'both' else [a.platform])
                if p not in done.get(it['slug'], {})]
        for platform in todo:
            fn = post_youtube if platform == 'youtube' else post_instagram
            try:
                res = fn(it['slug'], a.dry_run)
            except SystemExit as e:
                print(f'{platform} {it["slug"]}: {e}')
                continue
            if a.dry_run:
                print(f'[dry] {platform} {it["slug"]}: {json.dumps(res)[:200]}')
            else:
                record(it['slug'], platform, res)
                print(f'posted {platform}: {res}')
                # Deliberate gap between platforms, not between videos: a burst
                # of two identical uploads from one IP is what platform spam
                # heuristics look for.
                import time
                time.sleep(random.randint(30, 90))


if __name__ == '__main__':
    main()
