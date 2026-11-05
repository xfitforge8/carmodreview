"""Harvest product photographs for the buy blocks.

Two different jobs, and they need two different transports.

Finding the right image needs a browser. The retailer sits behind Cloudflare,
which answers scripted *page* requests with error 1015 / HTTP 429 after a
handful of them -- not after a volume of traffic, and pacing does not help.
A real browser is served normally, because the rate limiting is not aimed at
browsers. So the listing page is read inside a page on the retailer's own
origin and the candidate image URL comes back over the CDP bridge.

Downloading the bytes is better over curl. Cloudflare does not block direct
image fetches with a Referer from the retailer, and pushing a megabyte of
base64 per image through a bridge that caps a call at 30 seconds is what makes
a 40-image batch fail halfway. So the page is browsed and the image is curled.

`find_urls.py` writes the harvested (slug, position, url) triples to
`content/products/urls.json`; `download()` below turns that into files.
`manifest()` is the independent check: it reads the same positions back out of
the article source, so a URL list that has drifted from the articles shows up
as a missing or extra position rather than as a photo on the wrong product.
"""
import base64
import json
import os
import re
import subprocess

URLS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'content', 'products', 'urls.json')

# The image service answers this render size. It ignores the .jpg extension in
# the path and always returns WebP, which is why save() decides the extension
# from the bytes.
RENDER = '?wid=2000&hei=1500&sharpen=1'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

ROOT = os.path.expanduser('~/carmodreview')
OUT = os.path.join(ROOT, 'content', 'products')


def manifest():
    """[(article slug, position, product name, listing url)] for every pick."""
    out = []
    art = os.path.join(ROOT, 'content', 'articles')
    for f in sorted(os.listdir(art)):
        if not f.endswith('.md'):
            continue
        body = open(os.path.join(art, f), encoding='utf-8').read()
        slug = re.search(r'^slug:\s*(.+?)\s*$', body, re.M).group(1)
        for i, block in enumerate(re.split(r'<div class="pick">', body)[1:], 1):
            block = block.split('</div>\n</div>')[0]
            h = re.search(r'<h3>(.+?)</h3>', block, re.S)
            a = re.search(r'class="buy" href="(https://www\.americantrucks\.com/[^"]+)"',
                          block)
            if not (h and a):
                continue
            name = re.sub(r'<[^>]+>', '', h.group(1))
            for k, v in (('&ndash;', '-'), ('&mdash;', '-'), ('&amp;', '&'),
                         ('&nbsp;', ' '), ('&minus;', '-'), ('&middot;', '-')):
                name = name.replace(k, v)
            out.append((slug, i, re.sub(r'\s+', ' ', name).strip(), a.group(1)))
    return out


def already_have(slug, pos):
    d = os.path.join(OUT, slug)
    if not os.path.isdir(d):
        return None
    for f in os.listdir(d):
        if f.startswith(f'{pos:02d}-') and os.path.splitext(f)[1] in (
                '.jpg', '.webp', '.png'):
            return os.path.join(d, f)
    return None


def todo():
    return [m for m in manifest() if not already_have(m[0], m[1])]


def save(slug, pos, name, url, raw):
    """Write one product image plus its provenance sidecar.

    The extension is taken from the bytes, never from the URL. The image
    service names the file .jpg and answers with WebP, so trusting the URL
    would put WebP bytes in a file called .jpg -- tolerated by every browser
    and broken for the first tool that is not a browser.
    """
    ext = ('.webp' if raw[:4] == b'RIFF' else
           '.png' if raw.startswith(b'\x89PNG') else '.jpg')
    m = re.search(r'/([^/]+)\.([A-Za-z0-9_\-]+)\.jpg', url)
    sku = m.group(2) if m else f'p{pos:02d}'
    d = os.path.join(OUT, slug)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f'{pos:02d}-{sku}{ext}')
    with open(path, 'wb') as f:
        f.write(raw)
    with open(os.path.splitext(path)[0] + '.txt', 'w', encoding='utf-8') as f:
        f.write(f'{name}\n'
                f'Product photograph from the listing: {url}\n'
                f'Source image: {url}{RENDER}\n')
    return path, len(raw)


def download(only=None, pause=0.8):
    """Fetch every harvested URL that is not on disk yet.

    Returns (saved, skipped, failed). A failure is named rather than swallowed:
    a 404 here means the URL is wrong, and a silently missing photo is a buy
    block that ships without one and nobody notices.
    """
    import time

    triples = json.load(open(URLS, encoding='utf-8'))
    names = {(s, p): n for s, p, n, _ in manifest()}
    saved, skipped, failed = [], [], []
    for slug, pos, url in triples:
        if only and slug not in only:
            continue
        if already_have(slug, pos):
            skipped.append((slug, pos))
            continue
        name = names.get((slug, pos), '')
        r = subprocess.run(
            ['curl', '-sS', '--max-time', '45', '-w', '%{http_code}',
             '-H', f'Referer: https://www.americantrucks.com/',
             '-H', f'User-Agent: {UA}',
             '-H', 'Accept: image/avif,image/webp,image/*,*/*;q=0.8',
             url + RENDER],
            capture_output=True)
        raw, code = r.stdout[:-3], r.stdout[-3:].decode('ascii', 'replace')
        # A Cloudflare refusal is a 429 with a 17-byte body, and an error page
        # is HTML. Checking the magic bytes rather than the status alone
        # catches both without having to know which one happened.
        ok = (code == '200' and len(raw) > 2000
              and (raw[:4] == b'RIFF' or raw.startswith(b'\x89PNG')
                   or raw[:3] == b'\xff\xd8\xff'))
        if not ok:
            failed.append((slug, pos, code, len(raw)))
            continue
        path, n = save(slug, pos, name, url, raw)
        saved.append((os.path.relpath(path, OUT), n))
        time.sleep(pause)
    return saved, skipped, failed


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--article', action='append')
    ap.add_argument('--pause', type=float, default=0.8)
    a = ap.parse_args()
    saved, skipped, failed = download(a.article, a.pause)
    print(f'saved {len(saved)}  already {len(skipped)}  failed {len(failed)}')
    for p, n in saved:
        print(f'  {p}  {n:,}b')
    for f in failed:
        print(f'  FAILED {f}')


if __name__ == '__main__':
    main()


# Sent into the page. Ranks the candidate images so the main product render
# wins over other angles and over open-box promo art.
PAGE_JS = r"""
async (targets) => {
  const out = [];
  for (const t of targets) {
    try {
      const res = await fetch(t.url, {credentials:'same-origin'});
      const html = await res.text();
      const lslug = t.url.split('/').pop().replace('.html','');
      const esc = lslug.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
      const pat = new RegExp('https://www\\.americantrucks\\.com/image/' + esc +
        '\\.([A-Za-z0-9_-]+)\\.jpg','g');
      // Document order, not a guess at which filename looks plainest. The
      // listing marks its own primary image by putting it first in the markup;
      // suffixes like _Off_01, _alt1, -B and -AL are all main renders under
      // different naming schemes, so any suffix heuristic picks wrong on some
      // product. First occurrence is the one rule that holds across all of them.
      const first = new Map();
      for (const m of html.matchAll(pat)) {
        if (!first.has(m[0])) first.set(m[0], m.index);
      }
      const hits = [...first.entries()].sort((a,b) => a[1]-b[1]).map(([u]) => u);
      out.push({slug: t.slug, pos: t.pos, status: res.status,
                n: hits.length, img: hits[0] || null});
    } catch (e) {
      out.push({slug: t.slug, pos: t.pos, err: String(e).slice(0, 70)});
    }
  }
  return out;
}
"""

IMG_JS = r"""
async (urls) => {
  const out = [];
  for (const u of urls) {
    try {
      const res = await fetch(u, {credentials:'same-origin'});
      const blob = await res.blob();
      const dataUrl = await new Promise(r => {
        const fr = new FileReader();
        fr.onload = () => r(fr.result);
        fr.readAsDataURL(blob);
      });
      out.push({url: u, status: res.status, bytes: blob.size, dataUrl});
    } catch (e) {
      out.push({url: u, err: String(e).slice(0, 70)});
    }
  }
  return out;
}
"""
