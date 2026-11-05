#!/usr/bin/env python3
"""Check that every <em> quote in an article appears verbatim in the corpus.

The guides now quote owners directly, and the whole editorial claim is that
those quotes are real. A quote that drifted by one word during editing is
indistinguishable from an invented one to a reader, and the failure is silent
-- the page looks fine. So the quotes get checked rather than eyeballed.

Matching is on a normalised form: the corpus stores plain punctuation and the
article writes entities (&mdash;, &ldquo;) and smart quotes, so both sides are
reduced to lowercase words before comparison. That tolerates typography and
not much else, which is the right amount.

  python3 verify_quotes.py                 # every article with review data
  python3 verify_quotes.py brake-pads-rotors-guide
"""
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(ROOT, 'content', 'articles')
REV = os.path.join(ROOT, 'content', 'reviews')


def norm(s):
    s = html.unescape(s)
    s = s.replace('’', "'").replace('‘', "'")
    s = s.replace('“', '"').replace('”', '"')
    s = s.replace('—', ' ').replace('–', ' ')
    s = re.sub(r'[^a-z0-9 ]+', ' ', s.lower())
    return re.sub(r'\s+', ' ', s).strip()


def corpus(slug):
    """Every review body and title for one article, normalised, joined."""
    blob = []
    for f in glob.glob(os.path.join(REV, slug, '*.json')):
        j = json.load(open(f))
        for key in ('visible', 'low', 'low_same_part_other_truck'):
            for r in (j.get(key) or []):
                blob.append(norm(r.get('title') or ''))
                blob.append(norm(r.get('body') or ''))
    return ' || '.join(blob)


def quotes(path):
    body = open(path, encoding='utf-8').read()
    # English section only: the KR and ES blocks carry their own translated
    # quotes, which are not expected to match the English corpus.
    m = re.search(r'^##\s*EN\b', body, re.M)
    if m:
        nxt = re.search(r'^##\s*(KR|ES)\b', body, re.M)
        body = body[m.end():nxt.start()] if nxt else body[m.end():]
    return re.findall(r'<em>(.*?)</em>', body, re.S)


def main():
    want = sys.argv[1:] or sorted(os.path.basename(d) for d in glob.glob(os.path.join(REV, '*')))
    files = {}
    for p in glob.glob(os.path.join(ART, '*.md')):
        t = open(p, encoding='utf-8').read()
        m = re.search(r'^slug:\s*(.+?)\s*$', t, re.M)
        if m:
            files[m.group(1)] = p
    bad = 0
    for slug in want:
        if slug not in files:
            print(f'{slug}: no article'); continue
        blob = corpus(slug)
        if not blob:
            continue
        qs = quotes(files[slug])
        checked = 0
        for q in qs:
            n = norm(q)
            if len(n) < 25:      # an emphasis on a word or two is not a quote
                continue
            checked += 1
            if n not in blob:
                bad += 1
                print(f'\n{slug}: QUOTE NOT IN CORPUS')
                print(f'   {html.unescape(q)[:200]}')
        print(f'{slug}: {checked} quote(s) checked, '
              f'{checked and "ok" or "none"}')
    if bad:
        print(f'\n{bad} quote(s) did not match')
        sys.exit(1)
    print('\nall quotes verbatim')


if __name__ == '__main__':
    main()
