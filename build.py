#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — turn ~/carmodreview/content/*.md into a static site in ~/carmodreview/docs/.

No framework, no build step in CI. Run locally, commit the output.

Design contract (matches the existing hand-written pages):
  * English is the primary route at /<category>/<slug>.html
  * Every page: "What we could not verify"
    block before the footer, real publish dates only.
"""
import os
import re, json, html, shutil, datetime, sys, subprocess, hashlib, functools

import markdown
import yaml

ROOT = os.path.expanduser('~/carmodreview')
SRC = os.path.join(ROOT, 'content')
OUT = os.path.join(ROOT, 'docs')
PHOTO_ROOT = os.path.join(SRC, 'photos')
# Product shots are a separate tree from the body photos, because they are a
# different thing: one exact listing's own photograph, placed inside that
# listing's buy box, rather than a component illustration distributed through
# the prose. See product_photos.py.
PRODUCT_ROOT = os.path.join(SRC, 'products')
DOMAIN = 'https://carmodreview.com'


@functools.lru_cache(maxsize=None)
def git_date(path):
    """Date of the last commit that touched this file, or None.

    Used for dateModified and the sitemap's <lastmod>. Both are instructions to
    a search engine about whether a page is worth recrawling, so they have to
    track the file rather than a field someone remembers to bump. Falls back to
    None when git is unavailable or the file is untracked -- the caller then
    keeps whatever the front matter said, so a source tarball still builds.
    """
    try:
        out = subprocess.run(
            ['git', 'log', '-1', '--format=%ad', '--date=short', '--', path],
            cwd=ROOT, capture_output=True, text=True, timeout=10)
        stamp = out.stdout.strip()
        if out.returncode == 0 and re.fullmatch(r'\d{4}-\d{2}-\d{2}', stamp):
            return stamp
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def css_version():
    """Short content hash of style.css, appended to every stylesheet URL.

    The zone's Browser Cache TTL is 4 hours and applies to everything that is
    not HTML, so a plain /style.css is reused from each reader's disk cache for
    four hours after a deploy. That is exactly what happened on 4 November: the
    markup changed, the stylesheet did not reload, and the new .masthead-right
    and .share-icon rules never applied. Fingerprinting the URL makes every CSS
    change a URL the browser has never seen, so no cache -- browser or edge --
    can answer with the old bytes. Cloudflare and GitHub Pages both ignore the
    query string when resolving the file, so this costs nothing at the origin.
    """
    with open(os.path.join(ROOT, 'style.css'), 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()[:10]


def icon_version():
    """Short content hash of the icon set, appended to every icon URL.

    Same failure as the stylesheet, one layer more stubborn. The favicon was
    redrawn three times and the tab kept showing an old mark, because a plain
    /favicon.ico is cached for the zone's 4-hour TTL and browsers cache
    favicons harder still -- Chrome keeps them in a separate store that
    survives a hard reload, and only a URL it has never seen forces a refetch.
    Hashing all five files into one token means any redraw changes every icon
    URL at once, so no reader ever gets the new markup with the old icon.
    """
    h = hashlib.md5()
    for f in ('favicon.ico', 'favicon.svg', 'apple-touch-icon.png',
              'icon-192.png', 'icon-512.png'):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            with open(p, 'rb') as fh:
                h.update(fh.read())
    return h.hexdigest()[:10]

import photos
from photos import (inject_photos, find_photos, photo_html, category_photo,
                    CATEGORY_SOURCE)
import product_photos

# ───────────────────────────────────────────────────── analytics (Cloudflare)
# Cloudflare Web Analytics: cookieless, collects no personal data, no consent
# banner needed.
#
# Deliberately not Google Analytics: GA4 sets cookies, which under CCPA (the
# site is in California) means a consent banner and a cookie policy rewrite.
# This site's whole pitch is being more credible than its competitors, and the
# least-invasive analytics is the consistent choice.
#
# The token is the site tag from the Web Analytics dashboard snippet for
# carmodreview.com. It identifies the site to Cloudflare; it is not a secret,
# which is why it is committed here rather than held in an env var.
#
# The snippet must be type="module", not defer: Cloudflare's own installation
# instructions use a module script, and the docs note that manual installs need
# it set by hand. A deferred classic script still loads, but the module type is
# what the dashboard tells you to ship, so ship that.
CF_BEACON_TOKEN = 'a46f49fdad9f46a49898c4c3899110a0'

CF_BEACON_SNIPPET = (
    '<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" '
    'data-cf-beacon=\'{{"token": "{token}"}}\'></script>'
)


def analytics_tag():
    """The Cloudflare beacon, or '' when no token is configured."""
    if not CF_BEACON_TOKEN:
        return ''
    return CF_BEACON_SNIPPET.format(token=CF_BEACON_TOKEN)


# ──────────────────────────────────────────────────────── contact address
# Read from site.json so there is one place to change it. It used to be written
# literally into three content files plus two contact blocks in this file, which
# is how the site ended up publishing three different domain addresses -- none
# of which existed. Gmail is the honest choice until a real mailbox exists; the
# privacy policy promises a 30-day response, so the address behind it has to be
# one somebody reads.
def _site_config():
    try:
        with open(os.path.join(SRC, 'site.json'), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


CONTACT_EMAIL = _site_config().get('contact_email') or 'contact@carmodreview.com'


def stamp_email(html_text, email=None):
    """Rewrite the contact placeholder in authored markdown.

    Content files carry {email} rather than a literal address, so changing the
    mailbox is a one-line edit to site.json and a rebuild, not a hunt through
    three languages of legal text.
    """
    return html_text.replace('{email}', email or CONTACT_EMAIL)


def inject_analytics(html_text):
    """Add the beacon to a hand-written page that does not go through PAGE.

    The legacy pages are copied forward verbatim, and search.html is a raw
    string, so neither picks up render_page's insertion. Walking them is the
    only way to keep analytics coverage complete -- a page without the beacon
    is invisible in the dashboard, and the gap would not be obvious.
    """
    tag = analytics_tag()
    if not tag or '</head>' not in html_text:
        return html_text
    return html_text.replace('</head>', tag + '\n</head>', 1)


# ─────────────────────────────────────────────────── affiliate configuration
#
# Programs live in content/affiliate.json, not in this file. The site has to be
# able to carry several at once -- RealTruck and Summit Racing both run on
# Impact, Amazon runs its own network, eBay runs a third -- and each builds a
# tracking link a different way. Hardcoding one host here made every other
# program impossible to switch on.
#
# The file ships with every program disabled and empty IDs. Nothing is tagged,
# no disclosure claims a relationship, and the build stays byte-identical until
# an ID is actually pasted in. That is deliberate: rel="sponsored" on a link to
# a merchant that has not approved you is a false statement to Google and to
# the reader, so the default state must be "no relationship".
#
# See content/affiliate.json for the per-network link rules and what to paste
# where. See affiliate-setup.md for the walk-through.
AFFILIATE_CONFIG_PATH = os.path.join(SRC, 'affiliate.json')


def _load_affiliate_config():
    """Programs from content/affiliate.json, or an empty list if absent.

    A missing or malformed file is not fatal: the site simply has no affiliate
    relationships, which is exactly the state it shipped in for its first
    months. Failing the build here would make the file's absence a deploy
    blocker for a site that never had affiliates in the first place.
    """
    try:
        with open(AFFILIATE_CONFIG_PATH, encoding='utf-8') as f:
            data = json.load(f)
        return data.get('programs') or []
    except (OSError, ValueError):
        return []


PROGRAMS = _load_affiliate_config()


def _enabled_programs():
    """Programs with both an enabled flag and a non-empty ID.

    Both conditions matter. 'enabled' alone lets a half-filled row through and
    produces links tagged with an empty string; a non-empty ID alone would let
    a program the site is not actually in start tagging links.
    """
    return [p for p in PROGRAMS if p.get('enabled') and str(p.get('id', '')).strip()]


def active_hosts():
    """Every hostname that belongs to a live affiliate program."""
    return [p['host'].lower() for p in _enabled_programs() if p.get('host')]


def program_for_url(url):
    """The enabled program whose host matches this URL, or None.

    A template-wrapped URL already points at the network's own host (eBay's
    rover hosts), so it must be recognised as already tagged. Without the
    template_host check a second pass would match 'ebay.com' inside the
    encoded destination and wrap the wrapper again, nesting one rover link
    inside another until the destination is unreadable.
    """
    lowered = url.lower()
    for p in _enabled_programs():
        tpl_host = (p.get('template_host') or '').lower()
        if tpl_host and tpl_host in lowered:
            return p
        host = (p.get('host') or '').lower()
        if host and host in lowered:
            return p
    return None


# Legacy single-program names, kept so the rest of this file and any content
# that refers to them keeps working. AFFILIATE_HOST is what the disclosure
# logic keys off: any merchant the site links to commercially.
AFFILIATE_HOST = 'americantrucks.com'

CATEGORIES = {
    'Suspension':      ('suspension',      'Suspension',      '서스펜션',      'Suspensión'),
    'Wheels & Tires':  ('wheels-tires',    'Wheels & Tires',  '휠 & 타이어',   'Llantas y neumáticos'),
    'Engine':          ('engine',          'Engine & Intake', '엔진 & 인테이크', 'Motor y admisión'),
    'Exhaust':         ('exhaust',         'Exhaust',         '배기',          'Escape'),
    'Brakes':          ('brakes',          'Brakes',          '브레이크',      'Frenos'),
    # Bed coverage was the site's largest gap: the truck catalog's highest-volume
    # accessory category had no article at all, so every bed-cover search landed
    # nowhere. HUBLESS is unchanged -- this gets a real hub because there is an
    # article to fill it.
    'Tonneau & Bed':   ('tonneau',          'Tonneau & Bed',   '토노 & 베드',   'Cubiertas y caja'),
    # Windows, locks, lighting and 12V are the most-asked questions on every
    # truck forum and the site had nowhere to file them, so they were being
    # forced into Engine. A distinct hub is honest about what the guides cover.
    'Electrical':      ('electrical',       'Electrical',      '전장',          'Eléctrico'),
    'Tuning':          ('tuning',          'Tuning',          '튜닝',          'Reprogramación'),
}

# English only. The site published machine-translated Korean and Spanish
# tracks alongside every guide, and the translations read badly enough that
# they were worse than no translation at all -- a reader who lands on one
# judges the English guide by it. The UI tables below still carry their kr/es
# strings because the retired pages still need them: see RETIRED_LANGS.
LANGS = [('en', 'EN', '')]

# Language prefixes that are no longer built. Every URL under these prefixes has
# been public and indexed, so each one gets a redirect stub to its English
# counterpart rather than a 404. Generated from what the previous build actually
# wrote, not from a hand-kept list, so nothing is retired and then forgotten.
RETIRED_LANGS = [('kr', '/kr'), ('es', '/es')]

# Categories with no hub page of their own; their nav entry points at the article
# that covers them, so no page ever links to a URL that does not exist.
HUBLESS = {'tuning': 'engine/ecu-tuning-explained.html'}

UI = {
    'en': dict(all_posts='All posts', how='How we pick', home='Home',
               published='Published', updated='Updated', minread='min read', verified='What we could not verify',
               disc_title='Affiliate note',
               disc_body=('We earn commissions from qualifying purchases made through links '
                          'on this page. Commission never decides which products we pick or '
                          'where they rank.'),
               nav_cats='Categories', on='on',
               search='Search', search_label='Search guides', by='By', contact='Contact', about='About', privacy='Privacy',
               terms='Terms', disclosure='Affiliate disclosure',
               foot_tag=('car parts coverage that states its sources and says when it '
                         "doesn't know.")),
    'kr': dict(all_posts='모든 글', how='선정 기준', home='홈',
               published='발행일', updated='수정', minread='분 소요', verified='확인하지 못한 것',
               disc_title='제휴 고지',
               disc_body=('이 페이지의 링크를 통해 구매가 이루어지면 저희는 수수료를 받습니다. '
                          '수수료는 어떤 제품을 고르는지, 순위가 어떻게 되는지를 결정하지 않습니다.'),
               nav_cats='카테고리', on='',
               search='검색', search_label='가이드 검색', by='글쓴이', contact='문의', about='소개', privacy='개인정보처리방침',
               terms='이용약관', disclosure='제휴 고지',
               foot_tag='출처를 밝히고, 모르는 것은 모른다고 말하는 자동차 부품 정보.'),
    'es': dict(all_posts='Todas las guías', how='Cómo elegimos', home='Inicio',
               published='Publicado', updated='Actualizado', minread='min de lectura', verified='Lo que no pudimos verificar',
               disc_title='Nota de afiliación',
               disc_body=('Ganamos comisiones por compras realizadas a través de los enlaces de '
                          'esta página. La comisión nunca decide qué productos elegimos ni en qué '
                          'posición se clasifican.'),
               nav_cats='Categorías', on='',
               search='Buscar', search_label='Buscar guías', by='Por', contact='Contacto', about='Sobre nosotros',
               privacy='Privacidad', terms='Términos', disclosure='Divulgación de afiliados',
               foot_tag=('información de piezas de auto que cita sus fuentes y dice '
                         'cuándo no lo sabe.')),
}

SITE_URLS = {'en': '', 'kr': '/kr', 'es': '/es'}
HTML_LANG = {'en': 'en', 'kr': 'ko', 'es': 'es'}
OG_LOCALE = {'en': 'en_US', 'kr': 'ko_KR', 'es': 'es_ES'}


# ─────────────────────────────────────────────────────────────── helpers
def slugify(s):
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return s


def read_doc(path):
    raw = open(path, encoding='utf-8').read()
    meta, body = {}, raw
    m = re.match(r'^---\n(.*?)\n---\n', raw, re.S)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        body = raw[m.end():]
    return meta, body


def split_langs(body):
    """Split on top-level '## EN' / '## KR — 한국어' / '## ES' headings.

    Returns {lang: markdown}, plus any trailing section with no lang marker
    under key '_after' so we don't silently drop content.
    """
    pattern = re.compile(r'^##[ \t]+(EN|KR|ES)\b[^\n]*$', re.M)
    marks = list(pattern.finditer(body))
    if not marks:
        return {'en': body}, ''
    out, trailing = {}, ''
    for i, mk in enumerate(marks):
        lang = mk.group(1).lower()
        start = mk.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        out[lang] = body[start:end]

    # A shared H1 that sits above the first language marker is the page title
    # for every language; about-us.md is written that way. So is everything
    # else in the preamble -- the privacy policy, affiliate disclosure and
    # terms each carry a "Last updated" line up there, and the privacy policy
    # tells the reader to look at the top of the page for it. Keeping only the
    # H1 silently threw that date away, so the page promised a date it never
    # showed.
    preamble = body[:marks[0].start()]
    h1 = re.search(r'^#[ \t]+[^\n]+', preamble, re.M)
    # Everything that is not the H1: the date line, and the horizontal rule
    # that separates the title block from the body. The rule is dropped rather
    # than carried onto every language section.
    rest = (preamble[:h1.start()] + preamble[h1.end():]) if h1 else preamble
    rest = re.sub(r'^[ \t]*-{3,}[ \t]*$', '', rest, flags=re.M).strip()
    lead = '\n\n'.join(x for x in ((h1.group(0) if h1 else ''), rest) if x)
    if lead:
        for lang, sec in out.items():
            own_h1 = re.search(r'^#[ \t]+[^\n]+', sec, re.M)
            if not own_h1:
                out[lang] = lead + '\n\n' + sec.lstrip('\n')
            elif rest:
                # The section has its own title, so the H1 is redundant but the
                # date is not. Put it straight after their heading.
                out[lang] = (sec[:own_h1.end()] + '\n\n' + rest
                             + '\n' + sec[own_h1.end():].lstrip('\n'))

    # A trailing non-language H2 (e.g. "## Vehicle of Record") is written in
    # English and belongs on the English page, not glued onto the last
    # language block, which may be Korean or Spanish.
    last = marks[-1].group(1).lower()
    sec = out.get(last, '')
    m = re.search(r'^##[ \t]+(?!(?:EN|KR|ES)\b)[^\n]*$', sec, re.M)
    if m:
        tail = sec[m.start():]
        out[last] = sec[:m.start()].rstrip()
        out['en'] = (out.get('en', '').rstrip() + '\n\n' + tail).strip()
    return out, trailing


def clean_md(text):
    """Drop editor notes and normalise whitespace."""
    text = re.sub(r'^> \*\*Editor.s note[^\n]*\n', '', text, flags=re.M)
    return text.strip()


def extract_preamble(md_text):
    """Everything before the first '###' becomes the dek."""
    parts = re.split(r'^###', md_text, maxsplit=1, flags=re.M)
    return parts[0].strip()


def extract_unverified(md_text):
    """Pull a 'what we could not verify' section if the author wrote one."""
    m = re.search(r'^#{2,3}\s*(?:What we could not verify|What we didn.t verify|'
                  r'확인하지 못한 것|Lo que no pudimos verificar)\s*\n(.*?)(?=\n#{2,3}\s|\Z)',
                  md_text, re.M | re.S | re.I)
    return m.group(1).strip() if m else None


def resolve_links(html_text, rel=''):
    """Rewrite internal placeholder links written in markdown.

    `cat:<slug>`  -> the category hub for the current language
    `page:<path>` -> a static page (legal, about, contact, methodology)

    A category with no hub of its own is redirected to the article that covers
    it, so we never emit a link to a page that does not exist. A few pages are
    emitted under a different filename than the content file (about-us.md becomes
    about.html), so those are mapped explicitly.
    """
    page_alias = {'about-us': 'about'}

    def cat_sub(m):
        slug = m.group(1)
        if slug in HUBLESS:
            return f'href="{rel}{HUBLESS[slug]}"'
        return f'href="{rel}{slug}/"'

    def page_sub(m):
        path = m.group(1)
        return f'href="{rel}{page_alias.get(path, path)}.html"'

    html_text = re.sub(r'href="cat:([a-z0-9-]+)"', cat_sub, html_text)
    html_text = re.sub(r'href="page:([a-z0-9/.-]+)"', page_sub, html_text)
    return html_text


def md2html(text, rel=''):
    out = markdown.markdown(
        text,
        extensions=['extra', 'sane_lists', 'smarty'],
        output_format='html5',
    )
    out = resolve_links(out, rel)
    # Articles write their product cards as literal HTML inside the markdown,
    # so those anchors never pass through action() and would otherwise go out
    # untagged even with a live program configured -- the site would look
    # correctly set up while every click earned nothing. Tag here, at the one
    # point every markdown body goes through.
    return tag_affiliate_links(out, rel)


# ───────────────────────────────────────────────── affiliate link handling
# One place decides whether a commercial link carries an affiliate tag, and
# what rel attributes it gets. There are two distinct states and the site was
# previously conflating them:
#
#   AFFILIATE_ID empty   -> we have no affiliate relationship. Links to a
#                           retailer are ordinary outbound links. rel="nofollow"
#                           is correct; rel="sponsored" would be a lie, since
#                           "sponsored" means someone paid for the placement.
#                           The FTC-affiliate / Google-sponsored claim is false
#                           in this state, so we must not emit it.
#
#   a program is enabled -> a real relationship exists. Every link to that
#                           program's host is tagged, carries
#                           rel="sponsored nofollow noopener", and the page must
#                           display a disclosure (enforced by
#                           assert_disclosure(), which fails the build).
#
# With the token filled in, tags appear on the next build with no content edits.


def _affiliate_programs():
    """Programs the site actually participates in, from site.json.

    Kept in the data file rather than hardcoded here so the disclosure page
    cannot claim a relationship the site does not have. Empty list -> the
    disclosure renders an honest "we have no affiliate relationships yet".
    """
    try:
        with open(os.path.join(SRC, 'site.json'), encoding='utf-8') as f:
            return json.load(f).get('affiliate_programs') or []
    except (OSError, ValueError):
        return []


def affiliate_active():
    """True when at least one program is switched on and has a real ID."""
    return bool(_enabled_programs())


def affiliate_url(url):
    """Apply this URL's program tracking, if the site is in that program.

    Each network builds links differently, so the rule comes from the program's
    own 'link_format' in affiliate.json rather than from a guess here. Guessing
    wrong does not fail loudly -- it silently produces untracked links, which
    means every sale earns nothing while the site looks correctly configured.
    """
    program = program_for_url(url)
    if program is None:
        return url

    fmt = program.get('link_format') or 'query_param'
    pid = str(program['id']).strip()

    if fmt == 'query_param':
        # Impact and most in-house programs: append ?param=id, joining with &
        # when the product URL already carries query parameters.
        param = program.get('param') or 'utm_source'
        if f'{param}=' in url:
            return url
        sep = '&' if '?' in url else '?'
        return f'{url}{sep}{param}={pid}'

    if fmt == 'path_segment':
        # Amazon Associates: the tag goes in the path as /dp/ASIN/ref=<tag>.
        # Product URLs on this site are Amazon-format already, so insert the
        # tag before any query string rather than after it.
        tag = program.get('param') or 'tag'
        head, _, query = url.partition('?')
        head = head.rstrip('/')
        if f'{tag}=' in url:
            return url
        out = f'{head}/{tag}={pid}'
        return f'{out}?{query}' if query else out

    if fmt == 'template':
        # Programs that hand you a wrapper URL (eBay's rover links). 'template'
        # holds it with {url} and {id} substituted, and the destination is
        # percent-encoded so its own query string cannot break the wrapper.
        from urllib.parse import quote
        tpl = program.get('template') or ''
        if not tpl:
            # A template program with no template would otherwise emit an
            # empty href. Leave the plain destination instead of a dead link.
            return url
        # Already wrapped: returning the input unchanged keeps repeated builds
        # from nesting rover links inside each other.
        tpl_host = (program.get('template_host') or '').lower()
        if tpl_host and tpl_host in url.lower():
            return url
        return tpl.replace('{url}', quote(url, safe='')).replace('{id}', pid)

    return url


def affiliate_rel(url):
    """rel attributes for an outbound link, depending on whether it is one.

    'sponsored' is decided per host, not globally. If RealTruck approves the
    site but AmericanTrucks has not, an AmericanTrucks link is still an
    ordinary commercial outlink: rel="nofollow", never rel="sponsored".
    Claiming a paid relationship with a merchant that has no agreement is a
    false statement to Google, and it is the kind of error that survives
    review because the page looks correctly marked up.
    """
    if not url_links_to_merchant(url):
        return 'rel="noopener" target="_blank"'
    if program_for_url(url) is not None:
        return 'rel="sponsored nofollow noopener" target="_blank"'
    return 'rel="nofollow noopener" target="_blank"'


def merchant_hosts():
    """Every host the site links to commercially, live program or not.

    The disclosure is owed whenever a page links to a merchant at all -- a
    page full of AmericanTrucks links needs one whether or not that program
    has approved the site yet.
    """
    hosts = set(active_hosts())
    hosts.add(AFFILIATE_HOST.lower())
    for p in PROGRAMS:
        if p.get('host'):
            hosts.add(p['host'].lower())
    return hosts


def url_links_to_merchant(url):
    lowered = url.lower()
    return any(h in lowered for h in merchant_hosts())


def action(url):
    """Render an inline markdown link or a bracketed CTA as an anchor."""
    if not url.startswith('http'):
        return url, ''
    return affiliate_url(url), affiliate_rel(url)


def tag_affiliate_links(html_text, url_prefix):
    """Rewrite the hand-written buy links in a carried-forward page.

    These pages predate the generator and carry their cards as literal HTML, so
    they never pass through action(). Returning the text unchanged when no tag
    is configured keeps the build byte-identical until a relationship is real.
    """
    if not affiliate_active():
        return html_text

    def sub(m):
        open_q, url = m.group(1), m.group(2)
        if not url_links_to_merchant(url):
            return m.group(0)
        return f'href={open_q}{affiliate_url(url)}{open_q}'

    html_text = re.sub(r'href=(["\'])(https?://[^"\']+)\1', sub, html_text)

    # Lift rel on those same anchors to sponsored. Done as one pass over each
    # <a ...> tag: find the href, decide the rel from it, then replace the
    # existing rel attribute or insert one. A link earns rel="sponsored" only
    # when ITS OWN merchant is a live program -- an AmericanTrucks link is not
    # sponsored just because RealTruck approved the site.
    def rel_sub(m):
        tag_html = m.group(0)
        href_m = re.search(r'href=["\'](https?://[^"\']+)["\']', tag_html)
        if not href_m or not url_links_to_merchant(href_m.group(1)):
            return tag_html
        is_sponsored = program_for_url(href_m.group(1)) is not None
        new_rels = 'sponsored nofollow noopener' if is_sponsored else 'nofollow noopener'
        if re.search(r'\brel=["\'][^"\']*["\']', tag_html):
            return re.sub(r'\brel=["\'][^"\']*["\']', f'rel="{new_rels}"', tag_html)
        return tag_html.replace('<a ', f'<a rel="{new_rels}" ', 1)

    return re.sub(r'<a\b[^>]*>', rel_sub, html_text)


def assert_disclosure(html_text, where):
    """A page with affiliate links must carry a visible disclosure.

    Amazon Associates terminates accounts for a missing disclosure, and the FTC
    requires one before the first affiliate link rather than buried in a footer.
    Failing the build is deliberate: a silent miss here is a compliance problem
    that only shows up when a program audits the site, by which point the links
    have been live for months.

    Checked whenever a page links to a merchant at all, not only when a program
    is live: the obligation to disclose comes from having the links.
    """
    if not any(url_links_to_merchant(u) for u in
               re.findall(r'href=["\'](https?://[^"\']+)["\']', html_text)):
        return
    if not affiliate_active():
        return
    if AFFILIATE_HOST not in html_text:
        return
    lowered = html_text.lower()
    if 'affiliate' not in lowered and 'commission' not in lowered:
        raise SystemExit(
            f'build failed: {where} carries merchant links but no '
            f'disclosure. Add the disclosure block before shipping.')


# ───────────────────────────────────────────────────────────── templates
PAGE = """<!DOCTYPE html>
<html lang="{lang_attr}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
{alt_links}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Car Mod Review">
<meta property="og:locale" content="{og_locale}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_image}">
<link rel="alternate" type="application/rss+xml" title="Car Mod Review" href="{domain}/feed.xml">
<!-- Icons are absolute paths on purpose: pages live at /, /es/ and /kr/, so a
     relative href would resolve to /es/favicon.ico and 404 in two languages.
     The ?v= token is the content hash of the icon set; see icon_version(). -->
<link rel="icon" href="/favicon.ico?v={iconv}" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg?v={iconv}">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v={iconv}">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=PT+Sans:ital,wght@0,400;0,700;1,400&display=swap">
<link rel="stylesheet" href="{rel}style.css?v={cssv}">
{jsonld}{analytics}
</head>
<body>

<header class="masthead">
  <div class="wrap masthead-inner">
    <div>
      <a class="brand" href="{rel}index.html">Car Mod<span>.Review</span></a>
      <span class="brand-sub">{tagline}</span>
    </div>
    <div class="masthead-right">
      <nav class="nav">
        <a href="{rel}index.html">{all_posts}</a>
        <a href="{rel}methodology.html">{how}</a>
        <a href="{rel}contact.html">{contact}</a>
      </nav>
      <form class="nav-search" action="{rel}search.html" method="get" role="search">
        <label class="sr-only" for="navq">{search_label}</label>
        <input id="navq" type="search" name="q" placeholder="{search}" autocomplete="off">
        <button type="submit" aria-label="{search_label}">&#8981;</button>
      </form>
    </div>
  </div>
</header>

<main class="wrap">
{disclosure_block}<div class="layout">
<article>
{body}
</article>
<aside class="side">
{sidebar}
</aside>
</div>
</main>

<footer>
  <div class="wrap">
    <p><strong>Car Mod Review</strong> &mdash; {foot_tag}</p>
    <p>
      <a href="{rel}methodology.html">{how}</a> &middot;
      <a href="{rel}contact.html">{contact}</a> &middot;
      <a href="{rel}about.html">{about}</a> &middot;
      <a href="{rel}legal/privacy-policy.html">{privacy}</a> &middot;
      <a href="{rel}legal/affiliate-disclosure.html">{disclosure}</a> &middot;
      <a href="{rel}legal/terms-of-service.html">{terms}</a>
    </p>
    {foot_social}
  </div>
</footer>

</body>
</html>
"""

# One copy of the footer social link, shared by the generated pages and the two
# hand-written ones that predate the generator. {rel} is the only variable.
# rel="me" is deliberate: it is the standard way to assert that this site and
# that profile are the same entity, which is what a search engine needs to
# connect them.
FOOT_ICONS = {
    'instagram': '<path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>',
    # YouTube's own mark, drawn as the rounded-rect play button rather than the
    # wordmark, so it reads at 14px next to the Instagram glyph.
    'youtube': '<path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>',
}

# One entry per profile. Order is display order. Adding a network here is the
# only edit needed -- the footer, search.html and the two hand-written pages all
# read from this list.
FOOT_PROFILES = [
    ('instagram', 'Instagram', 'https://www.instagram.com/carmodreview/'),
    ('youtube', 'YouTube', 'https://www.youtube.com/@CarModReview'),
]


def foot_social_html(indent='    '):
    """Social links for a page footer, or '' when no profiles are configured.

    rel="me" is deliberate on each: it is the standard assertion that this site
    and that profile are the same entity, and it is what a search engine reads
    to connect them. Claiming it on a profile we have not confirmed is a real
    cost, which is why FOOT_PROFILES only ever holds URLs someone has checked.
    """
    if not FOOT_PROFILES:
        return ''
    rows = ''.join(
        f'{indent}  <a class="foot-social-link" href="{html.escape(url)}"\n'
        f'{indent}     target="_blank" rel="noopener me" '
        f'aria-label="{html.escape(name)}">\n'
        f'{indent}    <svg class="foot-icon" viewBox="0 0 24 24" '
        f'aria-hidden="true" focusable="false">{FOOT_ICONS[key]}</svg>\n'
        f'{indent}    <span class="foot-social-label">'
        f'{html.escape(name)}</span>\n'
        f'{indent}  </a>\n'
        for key, name, url in FOOT_PROFILES
    )
    return f'{indent}<p class="foot-social">\n{rows}{indent}</p>'

TAGLINE = {
    'en': 'Car parts, checked against the published specs',
    'kr': '공개 스펙과 대조하는 자동차 부품 정보',
    'es': 'Piezas de auto contrastadas con las especificaciones publicadas',
}

# Shown above the article on any page that links to a retailer, and only then.
# The FTC wants the disclosure before the first affiliate link, not in a footer,
# so this sits in the main column above the content. It is conditional because
# putting it on a page with no commercial link would be a false statement about
# that page.
DISCLOSURE = {
    'en': ('<div class="disclosure"><strong>Affiliate note.</strong> CarModReview '
           'may earn a commission from purchases made through links on this page, '
           'at no extra cost to you. It does not decide which parts we pick or '
           'where they rank. '
           '<a href="{rel}legal/affiliate-disclosure.html">Full disclosure</a>.</div>'),
    'kr': ('<div class="disclosure"><strong>제휴 고지.</strong> 이 페이지의 소매점 '
           '링크를 통해 구매하시면 저희가 수수료를 받을 수 있습니다. 구매 가격은 '
           '달라지지 않으며, 어떤 부품을 선택하고 순위를 매기는지에도 영향을 주지 '
           '않습니다. <a href="{rel}legal/affiliate-disclosure.html">전체 고지</a>.</div>'),
    'es': ('<div class="disclosure"><strong>Nota de afiliación.</strong> Los enlaces '
           'a minoristas en esta página pueden generarnos una comisión si compra a '
           'través de ellos. No cambia lo que usted paga ni decide qué piezas '
           'elegimos ni en qué orden las clasificamos. '
           '<a href="{rel}legal/affiliate-disclosure.html">Divulgación completa</a>.</div>'),
}


SHARE_LABEL = {
    'en': 'Share',
    'kr': '공유',
    'es': 'Compartir',
}

# Inline SVG marks for the share row. Drawn inline rather than loaded as files
# or as an icon font: one fewer request, they inherit the link's colour through
# currentColor so hover states need no extra CSS, and they cannot flash a
# fallback glyph the way a webfont does.
#
# No emoji here on purpose. There is no Facebook, X or LinkedIn character in
# Unicode, so an emoji row would be four different-looking pictures on four
# platforms (and, for the ones that do exist, a coloured emoji that fights the
# muted type it sits in). These are the networks' own marks, monochrome, sized
# to the text.
SHARE_ICONS = {
    'facebook': '<path d="M24 12.073C24 5.446 18.627 0 12 0S0 5.446 0 12.073C0 18.063 4.388 23.027 10.125 23.927v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.063 24 12.073z"/>',
    'x': '<path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/>',
    'linkedin': '<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 1 1 0-4.125 2.062 2.062 0 0 1 0 4.125zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>',
    # An envelope, drawn to the same 24-unit grid as the brand marks so the
    # row's optical size stays even.
    'email': '<path d="M2 4h20a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zm10 8.2 8.6-6.2H3.4l8.6 6.2zm0 2.4L2.6 8.4V18h18.8V8.4l-9.4 6.2z"/>',
}

# The byline. Duffy Vance is a pen name, stated as one on the About page, so the
# site never implies a verifiable legal identity it cannot produce. Naming the
# author in the byline and in the Article JSON-LD keeps the page and its
# structured data saying the same thing -- previously the visible page named
# nobody while the markup credited an Organization.
EDITOR = {
    'en': ('Duffy Vance', 'Editor'),
    'kr': ('더피 밴스', '편집자'),
    'es': ('Duffy Vance', 'Editor'),
}


RELATED_LABEL = {
    'en': 'Related guides',
    'kr': '관련 가이드',
    'es': 'Guías relacionadas',
}

TOPICS_LABEL = {
    'en': 'Topics',
    'kr': '주제',
    'es': 'Temas',
}


def build_related(lang, rel, entries, current_slug, current_cat):
    """Links from the foot of an article to the other guides in its category.

    Every article on the site used to link to zero other articles in its own
    body. The only paths between pages were the sidebar's six "recent posts"
    and the category hubs, so a guide that fell out of the recent window was
    reachable only by going Home -> category -> guide. Google reads that as a
    deep, sparsely linked site and crawls it accordingly: it had indexed 3 of
    59 URLs. An explicit related block gives every article a short, stable path
    to its siblings in both directions.

    Same-category first, because that is the link a reader actually wants; the
    list is capped at four so it stays a pointer and not a second navigation.
    Nothing is invented here -- these are the same entries the sidebar uses.
    """
    if not entries:
        return ''
    # How many guides each category has. A category with one guide can never be
    # anyone's same-category sibling, so the related block is its ONLY in-body
    # route and the cross-category filler is its only chance of being linked to
    # at all. Ordering the filler by filename gave every slot to whichever
    # categories happened to sort early, and Brakes, Tonneau and Electrical --
    # one guide each -- sat on three inbound links while ecu-tuning-explained
    # collected eighteen. Feeding the scarcest categories the filler slots is
    # what balances that.
    per_cat = {}
    for _d, _s, cat, *_rest in entries:
        per_cat[cat] = per_cat.get(cat, 0) + 1

    same, other = [], []
    lrel = lang_root(rel, lang)
    for date, slug, cat, cs, cl, ck, ce, meta in entries:
        if slug == current_slug:
            continue
        if lang not in (meta.get('langs_all') or set()):
            continue
        title = (meta.get('title') or {}).get(lang) or \
                (meta.get('title') or {}).get('en') or slug
        title = re.sub(r'^#+\s*', '', title).strip().strip('"')
        catlabel = {'en': cl, 'kr': ck, 'es': ce}[lang]
        row = (f'        <li><a href="{lrel}{cs}/{slug}.html">'
               f'{html.escape(title)}</a>'
               f'<span class="side-cat">{html.escape(catlabel)}</span>'
               f'</li>\n')
        if cat == current_cat:
            same.append(row)
        else:
            other.append(((per_cat.get(cat, 99), slug), row))
    # Every same-category sibling goes in; only the cross-category filler is
    # capped. The old rule capped one flat (same + other) list at four, so in
    # Engine -- six guides -- the fifth and sixth siblings were dropped from
    # every other Engine guide's related block, permanently. That is how
    # listing-install-time and what-owners-complain-about ended up with zero
    # inbound links from any article while four guides they outrank linked past
    # them. A reader on a brakes guide wants the other brakes guide, not four
    # essays about intakes.
    other.sort(key=lambda r: r[0])
    rows = (same + [row for _k, row in other])[:6]
    if not rows:
        return ''
    return (f'\n  <div class="related">\n'
            f'    <h2 class="related-title">{RELATED_LABEL[lang]}</h2>\n'
            f'    <ul class="side-list">\n{"".join(rows)}    </ul>\n'
            f'  </div>\n')


def build_topics(lang, rel, body_html, cat, catlabel, title):
    """The topic row at the foot of an article, as magazines close a piece.

    Every tag comes from something the article already says, never from a
    keyword list. Brands are read off the products the article actually
    recommends (its pick headings) rather than off its prose -- "fuel" appears
    in a paragraph about fuel economy and is not the wheel brand, and a loose
    match on the body would tag an article with a company it never mentions.

    Vehicle tags come from the listing titles too, which carry the fitment.

    Nothing here links anywhere yet: the site has no tag archives, and a row of
    sentences dressed as links would be a dead end for a reader and a crawl
    trap for Google. They render as plain labels until those pages exist.
    """
    import re as _re
    picks = ' '.join(_re.findall(r'<h3>(.*?)</h3>', body_html, _re.S))
    # Articles that write buy links as bare paragraphs have no pick headings,
    # so their recommended products are named only in the link labels. Those
    # are part names too -- "aFe Magnum FLOW Pro DRY S filter" -- so they count
    # as titles rather than prose.
    picks += ' ' + ' '.join(_re.findall(r'class="buy"[^>]*>(.*?)</a>', body_html, _re.S))
    picks = html.unescape(_re.sub(r'<[^>]+>', ' ', picks))

    # Articles that write their buy links as bare paragraphs have no pick
    # headings at all, so fall back to the prose. Only the English article is
    # in body_html -- the KR and ES sections are separate documents here -- so
    # this cannot pick up a translation's wording.
    prose = html.unescape(_re.sub(r'<[^>]+>', ' ', body_html))

    BRANDS = ('K&N', 'aFe', 'AIRAID', 'S&B', 'Corsa', 'MBRP', 'Rough Country',
              'ReadyLIFT', 'Supreme Suspensions', 'Mammoth', 'Fuel Wheels',
              'NITTO', 'Milestar', 'Mickey Thompson', 'BAK', 'Barricade',
              'Proven Ground', 'RedRock', 'PowerStop', 'Hawk', 'EBC',
              'Edge', 'HP Tuners', 'Livernois', 'AutoLöc', 'Roush',
              'SR Performance', 'C&L')
    # Named in prose but never in a pick title, and safe to match there.
    PROSE_BRANDS = ('AutoLöc', 'Proven Ground', 'Barricade', 'Rough Country',
                    'RedRock', 'Roush', 'SR Performance', 'Livernois',
                    'HP Tuners', 'Supreme Suspensions', 'Mickey Thompson',
                    'Milestar', 'NITTO', 'PowerStop')
    tags = []
    picksrc = picks.lower()
    src = (picks + ' ' + prose).lower()

    def names(word, hay=None):
        # Word boundaries, because "GM" sits inside "algorithm" and "Edge"
        # inside "inner edge". The & in S&B and C&L is not a word character,
        # so those two fall back to a plain containment test.
        hay = picksrc if hay is None else hay
        if _re.search(r'[^a-z0-9]', word):
            return word in hay
        return _re.search(r'(?<![a-z0-9])' + _re.escape(word) + r'(?![a-z0-9])',
                          hay) is not None

    # Brands the article recommends are read off its pick titles ONLY. The
    # prose is where "fuel economy" and "the inner edge" live, and matching
    # there tagged an intake article with the wheel brand Fuel and a wheel
    # article with the tuner Edge.
    for b in BRANDS:
        if names(b.lower(), picksrc):
            tags.append(b if b != 'Fuel Wheels' else 'Fuel')

    # A few more are named only in the prose, and are unambiguous there: no
    # ordinary English word collides with "AutoLöc" or "Barricade".
    for b in PROSE_BRANDS:
        if names(b.lower(), src):
            tags.append(b)

    VEHICLES = ('Silverado 1500', 'F-150', 'Duramax', 'TurboMax', '5.3L',
                '6.2L', '2.7L', '3.0L', '4.3L')
    seen = set()
    for v in VEHICLES:
        if names(v.lower(), src) and v not in seen:
            seen.add(v)
            tags.append(v)

    if catlabel and catlabel not in tags:
        tags.insert(0, catlabel)
    # de-dup preserving order, and cap it so it reads as a row, not a list
    out, got = [], set()
    for t in tags:
        if t.lower() not in got:
            got.add(t.lower())
            out.append(t)
    out = out[:8]
    if not out:
        return ''
    items = ''.join(f'      <li>{html.escape(t)}</li>\n' for t in out)
    return (f'\n  <div class="topics">\n'
            f'    <h2 class="topics-title">{TOPICS_LABEL[lang]}</h2>\n'
            f'    <ul class="topics-list">\n{items}    </ul>\n'
            f'  </div>\n')


def build_share(lang, canonical, title):
    """Share links for the foot of an article.

    Plain links, no third-party script and no tracking pixel: each one is just
    the network's own share URL with the article's absolute address in it. That
    keeps the page free of the 200 KB of JavaScript the usual share widgets
    pull in, and it means a share works with JavaScript disabled.

    The email link deliberately opens the reader's own mail client with the
    title and address pre-filled rather than using a mailto: with a body -- a
    subject and link is enough, and a pre-written body would be putting words
    in the reader's mouth.
    """
    from urllib.parse import quote
    u = quote(canonical, safe='')
    t = quote(title, safe='')
    items = (
        ('facebook', 'Facebook',
         f'https://www.facebook.com/sharer/sharer.php?u={u}'),
        ('x', 'X',
         f'https://twitter.com/intent/tweet?url={u}&text={t}'),
        ('linkedin', 'LinkedIn',
         f'https://www.linkedin.com/sharing/share-offsite/?url={u}'),
        ('email', 'Email',
         f'mailto:?subject={t}&body={u}'),
    )
    links = ''.join(
        f'      <li><a class="share-{key}" href="{html.escape(href)}"'
        f'{" target=\"_blank\" rel=\"noopener\"" if key != "email" else ""}>'
        f'<svg class="share-icon" viewBox="0 0 24 24" aria-hidden="true"'
        f' focusable="false">{SHARE_ICONS[key]}</svg>'
        f'<span>{name}</span></a></li>\n'
        for key, name, href in items
    )
    return (f'  <div class="share">\n'
            f'    <span class="share-label">{SHARE_LABEL[lang]}</span>\n'
            f'    <ul class="share-list">\n{links}    </ul>\n'
            f'  </div>\n')


def build_disclosure(lang, rel, body_html):
    """The disclosure block, but only for pages that link to a retailer.

    Keyed on any merchant host, not just one: the disclosure is owed because
    the page has commercial links, regardless of which store they point at or
    whether that store's program has approved the site yet.
    """
    urls = re.findall(r'href=["\'](https?://[^"\']+)["\']', body_html)
    if not any(url_links_to_merchant(u) for u in urls):
        return ''
    return DISCLOSURE[lang].format(rel=rel) + '\n'


def lang_root(rel, lang):
    """Path prefix that stays inside the reader's language.

    `rel` alone is the way back to the site root, so on a localised page it
    climbs straight out of /kr/ or /es/. Every sidebar and related link was
    built as rel+path, which meant a reader on a Korean guide who clicked the
    next guide in the rail landed on the English one -- and, for a crawler, left
    the Korean pages with no internal links pointing at them at all.

    Not used for the masthead or footer nav: about/ exists in all three
    languages but methodology, contact and terms do not, so a language-relative
    prefix there would advertise URLs that are not built. Those links keep
    pointing at the English page, which does exist.
    """
    seg = {'en': '', 'kr': 'kr/', 'es': 'es/'}[lang]
    return rel + seg


def default_sidebar(lang, rel, entries=None):
    """The right-hand panel: recent posts, then categories.

    Order follows CATEGORIES exactly -- the same order the homepage lists the
    categories in. It used to be sorted alphabetically by label, which put
    "Brakes" first in the rail and "Suspension" first in the body: two different
    orders for the same six things on the same page, with no way for a reader to
    reconcile them. Editorial order is a decision; alphabetical by translated
    label is just a property of the words.

    Recent posts come first because that is what a reader arriving from search
    actually wants: something else to read, not a taxonomy. The list is drawn
    from the same index_entries the homepage uses, so the two can never drift
    apart.
    """
    labels = {'en': 1, 'kr': 2, 'es': 3}
    t = {
        'en': ('Recent posts', 'Categories'),
        'kr': ('최근 글', '카테고리'),
        'es': ('Artículos recientes', 'Categorías'),
    }[lang]

    recent = ''
    lrel = lang_root(rel, lang)
    if entries:
        # Newest first. The primary key is published -- what a reader landing on
        # the page means by "latest". date is the revision date and is the
        # tiebreaker, so a genuinely revised guide still floats up among articles
        # published the same day.
        #
        # Both keys are needed. date alone was tried first and broke: it now comes
        # from git_date, so a batch of edits stamps every article with one date
        # and the list collapsed into alphabetical order by slug. published alone
        # would lose the "keeps its figures current" signal the site is built on.
        order = sorted(
            entries,
            key=lambda e: (str(e[7].get('published') or ''), e[0], e[1]),
            reverse=True)
        # The homepage leads with the single newest article above the list, so
        # remove it here rather than showing it twice.
        lead, rest = (order[0], order[1:]) if order else (None, [])
        ordered = ([lead] if lead else []) + rest[:5]
        rows = []
        for date, slug, cat, cs, cl, ck, ce, meta in ordered:
            if lang not in (meta.get('langs_all') or set()):
                continue
            title = (meta.get('title') or {}).get(lang) or \
                    (meta.get('title') or {}).get('en') or slug
            title = re.sub(r'^#+\s*', '', title).strip().strip('"')
            catlabel = {'en': cl, 'kr': ck, 'es': ce}[lang]
            rows.append(
                f'        <li><a href="{lrel}{cs}/{slug}.html">{html.escape(title)}</a>'
                f'<span class="side-cat">{html.escape(catlabel)}</span></li>\n')
        if rows:
            recent = (f'    <div class="side-block">\n'
                      f'      <h2 class="side-title">{t[0]}</h2>\n'
                      f'      <ul class="side-list side-list--posts">\n'
                      f'{"".join(rows)}      </ul>\n'
                      f'    </div>\n')

    items = ''.join(
        f'        <li><a href="{lrel}{HUBLESS.get(slug, slug + "/")}">'
        f'{html.escape(label)}</a></li>\n'
        for slug, label in ((c[0], c[labels[lang]]) for c in CATEGORIES.values())
    )
    cats = (f'    <div class="side-block">\n'
            f'      <h2 class="side-title">{t[1]}</h2>\n'
            f'      <ul class="side-list">\n{items}      </ul>\n'
            f'    </div>\n')

    return recent + cats


def render_page(*, lang, title, desc, canonical, body_html, rel, jsonld='',
                og_type='website', alts=None, og_image=None, robots=None,
                sidebar='', entries=None):
    alts = alts or {}
    # hreflang only means something while more than one language is published.
    # The site is English-only now, so a single self-referential alternate pair
    # would be noise -- and the old pair pointed at 49 URLs that no longer exist.
    alt = ''
    if len(alts) > 1:
        lines = []
        hreflang = {'en': 'en', 'kr': 'ko', 'es': 'es'}
        for code, url in alts.items():
            lines.append(f'<link rel="alternate" hreflang="{hreflang[code]}" href="{url}">')
        lines.append(f'<link rel="alternate" hreflang="x-default" href="{alts.get("en", canonical)}">')
        alt = '\n'.join(lines)
    ui = UI[lang]
    return PAGE.format(
        lang_attr=HTML_LANG[lang], title=html.escape(title), desc=html.escape(desc),
        robots=robots or 'index, follow, max-image-preview:large, max-snippet:-1',
        canonical=canonical, alt_links=alt, og_type=og_type, og_locale=OG_LOCALE[lang],
        og_image=og_image or f'{DOMAIN}/og.png',
        domain=DOMAIN, rel=rel, jsonld=(jsonld + site_jsonld()), body=body_html,
        cssv=css_version(), iconv=icon_version(), foot_social=foot_social_html('    '),
        analytics=('\n' + analytics_tag()) if analytics_tag() else '',
        tagline=TAGLINE[lang], all_posts=ui['all_posts'], how=ui['how'],
        search=ui['search'], search_label=ui['search_label'], by=ui['by'], contact=ui['contact'],
        about=ui['about'],
        privacy=ui['privacy'], terms=ui['terms'], foot_tag=ui['foot_tag'],
        disclosure=ui['disclosure'],
        disclosure_block=build_disclosure(lang, rel, body_html),
        sidebar=sidebar or default_sidebar(lang, rel, entries),
    )


def site_jsonld():
    """Organization + WebSite graph, emitted on every page.

    WebSite carries a SearchAction, which is only declared because search.html
    actually exists and honours the q= parameter.
    """
    return ('<script type="application/ld+json">\n' + json.dumps({
        '@context': 'https://schema.org',
        '@graph': [
            {
                '@type': 'Organization',
                '@id': f'{DOMAIN}/#org',
                'name': 'Car Mod Review',
                'url': f'{DOMAIN}/',
                'logo': {'@type': 'ImageObject', 'url': f'{DOMAIN}/og.png',
                         'width': 1200, 'height': 630},
                'description': ('Car and truck parts guides built from published '
                                'specifications, with every source named.'),
                'foundingDate': '2026',
            },
            {
                '@type': 'WebSite',
                '@id': f'{DOMAIN}/#site',
                'url': f'{DOMAIN}/',
                'name': 'Car Mod Review',
                'publisher': {'@id': f'{DOMAIN}/#org'},
                # English only. This used to list ko and es, left over from the
                # three-language build; those pages are now redirect stubs and
                # announcing them in schema.org tells Google the site has
                # content it cannot crawl.
                'inLanguage': 'en',
                # site search is real (search.html), so declaring it is honest
                'potentialAction': {
                    '@type': 'SearchAction',
                    'target': {'@type': 'EntryPoint',
                               'urlTemplate': f'{DOMAIN}/search.html?q={{search_term_string}}'},
                    'query-input': 'required name=search_term_string',
                },
            },
        ],
    }, ensure_ascii=False, indent=2) + '\n</script>')


def breadcrumb_jsonld(trail):
    """trail: [(name, url), ...] from the homepage down to this page."""
    return ('<script type="application/ld+json">\n' + json.dumps({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': name, 'item': url}
            for i, (name, url) in enumerate(trail)
        ],
    }, ensure_ascii=False, indent=2) + '\n</script>')


def faq_jsonld(pairs):
    return ('<script type="application/ld+json">\n' + json.dumps({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {'@type': 'Question', 'name': q,
             'acceptedAnswer': {'@type': 'Answer', 'text': a}}
            for q, a in pairs
        ],
    }, ensure_ascii=False, indent=2) + '\n</script>')


def disclosure_html(lang):
    ui = UI[lang]
    return (f'  <div class="disclosure">\n'
            f'    <strong>{ui["disc_title"]}:</strong> {ui["disc_body"]}\n'
            f'  </div>\n')


def article_jsonld(title, desc, canonical, published, modified, section, lang, image=None):
    return ('<script type="application/ld+json">\n' + json.dumps({
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': title,
        'description': desc,
        'datePublished': published,
        'dateModified': modified,
        'inLanguage': HTML_LANG[lang],
        'articleSection': section,
        'image': [image or f'{DOMAIN}/og.png'],
        'author': {'@type': 'Person', 'name': EDITOR['en'][0],
                   'url': f'{DOMAIN}/about.html'},
        'publisher': {'@type': 'Organization', 'name': 'Car Mod Review', '@id': f'{DOMAIN}/#org'},
        'isAccessibleForFree': True,
        'mainEntityOfPage': {'@type': 'WebPage', '@id': canonical},
    }, ensure_ascii=False, indent=2) + '\n</script>')


# ─────────────────────────────────────────────────────────────── build
def build():
    # Before the rmtree: this reads the previous build to learn which retired
    # language URLs need a stub. Afterwards there is nothing left to read.
    inventory_retired_langs()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    # Shorts published for the Instagram Graph API. It fetches video from a URL
    # rather than accepting an upload, so the renders have to be served from the
    # site. They live at social/public/ in the repo root because rmtree above
    # takes docs/ with it -- parked under docs/ they would vanish on the next
    # build and every already-queued Reel would 404 at post time.
    social_pub = os.path.join(ROOT, 'social', 'public')
    if os.path.isdir(social_pub):
        shutil.copytree(social_pub, os.path.join(OUT, 'social'))
    # photo width/height must describe the resized file the browser fetches
    photos.configure(PHOTO_ROOT, os.path.join(OUT, 'img', 'photos'))

    # keep the hand-written assets that aren't generated
    shutil.copy(os.path.join(SRC, '..', 'docs', 'CNAME'), os.path.join(OUT, 'CNAME')) \
        if os.path.exists(os.path.join(SRC, '..', 'docs', 'CNAME')) else open(
            os.path.join(OUT, 'CNAME'), 'w').write('carmodreview.com\n')

    # GitHub Pages runs Jekyll over every deploy unless this file is present.
    # The site is already-rendered HTML, so Jekyll is pure overhead: it added
    # minutes to each build and, worse, would silently mangle a page containing
    # Liquid-looking braces. An empty file is the whole fix, but rmtree above
    # deletes it each time -- so it is written here, on every build.
    open(os.path.join(OUT, '.nojekyll'), 'w').close()

    arts = []
    for fn in sorted(os.listdir(os.path.join(SRC, 'articles'))):
        if not fn.endswith('.md'):
            continue
        meta, body = read_doc(os.path.join(SRC, 'articles', fn))
        langs_md, _ = split_langs(body)
        arts.append(dict(meta=meta, langs=langs_md, file=fn,
                         path=os.path.join(SRC, 'articles', fn)))

    print(f'  parsed {len(arts)} articles')
    for a in arts:
        # Only the built languages are checked. The content files still carry
        # their KR and ES sections; reporting those as missing would cry wolf on
        # every article forever, which is how a real missing translation gets
        # missed. What matters now is that nothing is missing from English.
        miss = [l for l, _, _ in LANGS if l not in a['langs']]
        if miss:
            print(f'    ! {a["file"]}: missing {",".join(miss)}')

    # grab the assets we want to preserve from the existing site
    prev = os.path.join(ROOT, '_prev_docs')
    if os.path.isdir(prev):
        for asset in ('og.png',):
            p = os.path.join(prev, asset)
            if os.path.exists(p):
                shutil.copy(p, os.path.join(OUT, asset))
    # style.css is tracked in the repo root now, not carried from _prev_docs
    shutil.copy(os.path.join(ROOT, 'style.css'), os.path.join(OUT, 'style.css'))

    # The editor avatar, referenced from about-us.md. It lives in the repo root
    # next to style.css for the same reason: rmtree above takes docs/ with it,
    # and a missing avatar would leave a broken image on the about page.
    for f in ('avatar.svg',):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(OUT, f))

    # IndexNow key file. Bing, Yandex and Naver fetch /<key>.txt to prove the
    # submitter controls the domain; without it their submissions are rejected.
    # It must sit at the site root and be reachable, so it is copied every build
    # for the same reason as the icons: rmtree takes docs/ with it.
    for f in os.listdir(ROOT):
        if f.endswith('.txt') and len(f) == 36 and re.fullmatch(r'[0-9a-f]{32}\.txt', f):
            shutil.copy(os.path.join(ROOT, f), os.path.join(OUT, f))

    # Browser-tab icon set. All of these live in the repo root and are copied
    # here because rmtree wiped them from docs/. Missing icons are silent --
    # the tab just shows a blank page glyph -- so they are easy to lose without
    # noticing. favicon.ico is what older browsers and Safari pinned tabs
    # fetch; the SVG is what modern browsers prefer; the PNGs cover iOS home
    # screens and Android. Regenerated from favicon.svg with:
    #   sips -s format png favicon.svg --out out.png --resampleWidth N
    for f in ('favicon.ico', 'favicon.svg', 'apple-touch-icon.png',
              'icon-192.png', 'icon-512.png'):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(OUT, f))
        else:
            print(f'    ! icon missing from repo root: {f}')

    # Web app manifest. Android Chrome uses these icons when a reader adds the
    # site to a home screen; without a manifest it falls back to a screenshot.
    # Written rather than copied because it is five lines and lives nowhere else.
    iconv = icon_version()
    with open(os.path.join(OUT, 'site.webmanifest'), 'w', encoding='utf-8') as fh:
        json.dump({
            'name': 'Car Mod Review',
            'short_name': 'Car Mod Review',
            'description': 'Car and truck parts guides built from published '
                           'specifications, with every source named.',
            'start_url': '/',
            'display': 'browser',
            'background_color': '#fbfaf7',
            'theme_color': '#14161a',
            # Same token as the <link> tags in the page head. A home-screen
            # shortcut reads its icon from here, not from the head, so a
            # redraw that only changed the head would update the tab and
            # leave the installed icon stale indefinitely.
            'icons': [
                {'src': f'/icon-192.png?v={iconv}', 'sizes': '192x192',
                 'type': 'image/png'},
                {'src': f'/icon-512.png?v={iconv}', 'sizes': '512x512',
                 'type': 'image/png'},
            ],
        }, fh, indent=2)

    # Google Search Console proves ownership by fetching this exact file at the
    # site root. It has to survive every rebuild -- rmtree at the top of build()
    # takes docs/ with it -- or verification lapses and Search Console drops the
    # property. Tracked in the repo root next to style.css for that reason.
    for f in os.listdir(ROOT):
        if f.startswith('google') and f.endswith('.html'):
            shutil.copy(os.path.join(ROOT, f), os.path.join(OUT, f))

    # real photographs, copied from content/photos/. Only image files are
    # published — the sidecar captions and the README stay out of the build.
    if os.path.isdir(PHOTO_ROOT):
        for dirpath, _, files in os.walk(PHOTO_ROOT):
            for f in files:
                if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.avif')):
                    continue
                srcp = os.path.join(dirpath, f)
                relp = os.path.relpath(srcp, PHOTO_ROOT)
                dst = os.path.join(OUT, 'img', 'photos', relp)
                photos.publish_image(srcp, dst)

    # Product photographs, published to img/products/. Sidecars stay out for
    # the same reason the photo captions do: they record where an image came
    # from and are not part of the site.
    n_prod = product_photos.publish(PRODUCT_ROOT, os.path.join(OUT, 'img', 'products'))
    if n_prod:
        print(f'  product photos: {n_prod}')

    index_entries = []
    feed_items = []
    search_items = []
    # Built from the same source as index_entries below, but before the render
    # loop: the sidebar on every page lists recent posts, and a page cannot wait
    # for a list that is only finished after it has been written.
    sidebar_entries = []
    for a in arts:
        m = a['meta']
        cslug, clabel, ckr, ces = CATEGORIES.get(m.get('category', 'Engine'),
                                                 ('engine', 'Engine', '엔진', 'Motor'))
        sidebar_entries.append((
            git_date(a['path']) or str(m.get('last_updated', '2026-11-01')),
            m.get('slug') or slugify(a['file']),
            m.get('category', 'Engine'), cslug, clabel, ckr, ces,
            # published has to travel with the entry: default_sidebar sorts on
            # it first, and an entry without it sorts as '' -- which put the
            # newest guide first only because "what-owners-..." happened to beat
            # "tonneau-..." alphabetically. The next guide whose slug starts with
            # an early letter would have dropped down the rail.
            {'title': m.get('title') or {}, 'langs_all': set(a['langs']),
             'published': str(m.get('published') or '')},
        ))
    for a in arts:
        meta = a['meta']
        meta['langs_all'] = set(a['langs'])
        cat = meta.get('category', 'Engine')
        catslug, catlabel, catkr, cates = CATEGORIES.get(cat, ('engine', cat, cat, cat))
        slug = meta.get('slug') or slugify(a['file'])
        # dateModified has to describe the file, not a hand-maintained field.
        # last_updated: was written by hand and had drifted: nine guides still
        # claimed May-July 2026 after every one of them had been rewritten with
        # quoted owner reviews and corrected prices this week. A search engine
        # reads dateModified and the sitemap's <lastmod> to decide whether to
        # recrawl; both were reporting these pages as untouched, so the edits
        # were invisible to the one audience they were meant for. The commit
        # date of the article file is the honest answer and cannot drift.
        date = git_date(a['path']) or str(meta.get('last_updated', '2026-11-01'))
        # datePublished must not move -- it is when the page first existed, and
        # rewriting last_updated: must never be able to restate it.
        published = str(meta.get('published', date))
        index_entries.append((date, slug, cat, catslug, catlabel, catkr, cates, meta))

        en_path = f'{catslug}/{slug}.html'
        altmap = {'en': f'{DOMAIN}/{en_path}'}
        for code, _, prefix in LANGS[1:]:
            if code in a['langs']:
                altmap[code] = f'{DOMAIN}{prefix}/{catslug}/{slug}.html'

        for code, label, prefix in LANGS:
            if code not in a['langs']:
                continue
            raw = clean_md(a['langs'][code])
            title = (meta.get('title') or {}).get(code) or (meta.get('title') or {}).get('en') or slug
            title = re.sub(r'^#+\s*', '', title).strip().strip('"')
            # seo_title keeps the full headline as the H1 while giving the <title>
            # tag something that fits a search result. Falls back to the headline.
            seo_title = ((meta.get('seo_title') or {}).get(code)
                         or (meta.get('seo_title') or {}).get('en') or title)
            seo_title = re.sub(r'^#+\s*', '', str(seo_title)).strip().strip('"')
            # the site name is appended by the template, so budget for it here
            page_title = (seo_title if len(seo_title) + 18 > 60
                          else f'{seo_title} | Car Mod Review')
            # the dek is the opening prose trimmed mid-sentence, which makes a
            # 300-character meta description. Use the written one when present.
            seo_desc = ((meta.get('seo_desc') or {}).get(code)
                        or (meta.get('seo_desc') or {}).get('en') or dek or title)
            seo_desc = re.sub(r'\s+', ' ', str(seo_desc)).strip()
            body_md = re.sub(r'^#[^\n]*\n', '', raw, count=1).lstrip()
            pre_md = extract_preamble(body_md)
            dek = re.sub(r'\s+', ' ', re.sub(r'[#*_>`]', '', pre_md))[:300].strip()
            unver = extract_unverified(body_md)
            words = len(re.findall(r'\w+', body_md))
            mins = max(1, round(words / 220))
            inner = re.sub(r'^#{2,3}\s*(?:What we could not verify|확인하지 못한 것|Lo que no pudimos verificar)[\s\S]*?(?=\n#{2,3}\s|\Z)', '',
                           body_md, flags=re.M | re.I)
            inner = re.sub(r'^\s*###.*?(?=\n)', '', inner, count=1, flags=re.M) if False else inner

            body_html = []
            body_html.append(f'  <div class="kicker">{html.escape(catlabel if code=="en" else (catkr if code=="kr" else cates))}</div>\n')
            body_html.append(f'  <h1>{html.escape(title)}</h1>\n')
            if dek:
                body_html.append(f'  <p class="dek">{html.escape(dek)}</p>\n')
            revised = (f' &middot; {UI[code]["updated"]} {date}'
                       if published != date else '')
            rel = '../' if not prefix else '../../'
            editor_name, editor_role = EDITOR[code]
            body_html.append(f'  <div class="byline">\n'
                             f'    <span class="byline-author">{UI[code]["by"]} '
                             f'<a href="{lang_root(rel, code)}about.html">'
                             f'{html.escape(editor_name)}</a>, '
                             f'{html.escape(editor_role)}</span>\n'
                             f'    <span>{UI[code]["published"]} {published}{revised}</span>\n'
                             f'  </div>\n')
            art_html = md2html(inner, rel)
            art_html = inject_photos(art_html, slug, code, rel,
                                     find_photos(PHOTO_ROOT, slug))
            # Product shots go into the buy boxes, after the body photographs.
            # Order matters only in that both split the same html; running the
            # product pass second means it sees the body html already settled.
            if code == 'en':
                art_html = product_photos.inject_product_photos(
                    art_html, slug, rel, PRODUCT_ROOT)
            body_html.append(art_html)
            if unver:
                body_html.append(
                    f'\n  <div class="unverified">\n'
                    f'    <h3>{UI[code]["verified"]}</h3>\n'
                    f'    {md2html(unver, rel)}\n'
                    f'  </div>\n')

            body_html.append(build_topics(code, rel, art_html, cat, catlabel, title))
            body_html.append(build_related(code, rel, sidebar_entries, slug, cat))
            body_html.append(build_share(code, altmap[code], title))

            canon = altmap[code]
            shots = find_photos(PHOTO_ROOT, slug)
            hero_img = (f'{DOMAIN}/img/photos/{slug}/{os.path.basename(shots[0])}'
                        if shots else None)
            trail = [('Home', f'{DOMAIN}{prefix}/' if prefix else f'{DOMAIN}/'),
                     (catlabel if code == 'en' else cat,
                      f'{DOMAIN}{prefix}/{catslug}/'),
                     (title, canon)]
            jsonld = (article_jsonld(title, seo_desc, canon, published, date,
                                     catlabel if code == 'en' else cat, code, hero_img)
                      + breadcrumb_jsonld(trail))
            search_items.append({
                'u': canon.replace(DOMAIN, '') or '/',
                't': title,
                'd': seo_desc,
                'c': (catlabel if code == 'en' else (catkr if code == 'kr' else cates)),
                'l': code,
            })
            if code == 'en':
                feed_items.append({'title': title, 'desc': seo_desc,
                                   'url': canon, 'published': published,
                                   'modified': date, 'section': catlabel})
            page = render_page(
                lang=code, title=page_title, desc=seo_desc, canonical=canon,
                body_html='\n'.join(body_html), rel=rel,
                jsonld=jsonld, og_type='article', alts=altmap, og_image=hero_img,
                entries=sidebar_entries,
            )
            outdir = os.path.join(OUT, *( ([prefix.strip('/')] if prefix else []) + [catslug] ))
            os.makedirs(outdir, exist_ok=True)
            with open(os.path.join(outdir, f'{slug}.html'), 'w', encoding='utf-8') as f:
                f.write(page)
    print(f'  wrote {len(arts)} articles x {len(LANGS)} langs')

    build_static_pages(index_entries, sidebar_entries)
    build_category_pages(arts, sidebar_entries)
    build_legacy_pages(sidebar_entries)
    build_redirects()
    build_sitemap(arts)
    build_feed(feed_items)
    build_search(search_items)


# Pages that moved. GitHub Pages is static and cannot issue a 301, so a page
# that changes its URL would simply 404 for anyone holding the old link. A stub
# at the old path forward to the new one instead.
REDIRECTS = {
    'suspension/silverado-rst-leveling-kit.html': 'leveling-kit-guide.html',
    'kr/suspension/silverado-rst-leveling-kit.html': 'leveling-kit-guide.html',
    # The guides themselves stopped being about one truck. Each of these three
    # is a URL that has been public and indexed, so it gets a stub rather than
    # a 404. The targets carry the new slug; the category path is unchanged.
    'suspension/silverado-leveling-kit.html': 'leveling-kit-guide.html',
    'kr/suspension/silverado-leveling-kit.html': 'leveling-kit-guide.html',
    'es/suspension/silverado-leveling-kit.html': 'leveling-kit-guide.html',
    'engine/silverado-27-turbomax-cold-air-intake.html':
        'turbo-four-cold-air-intake.html',
    'kr/engine/silverado-27-turbomax-cold-air-intake.html':
        'turbo-four-cold-air-intake.html',
    'es/engine/silverado-27-turbomax-cold-air-intake.html':
        'turbo-four-cold-air-intake.html',
    'wheels-tires/silverado-4x4-tire-buying-guide.html':
        '4x4-tire-buying-guide.html',
    'kr/wheels-tires/silverado-4x4-tire-buying-guide.html':
        '4x4-tire-buying-guide.html',
    'es/wheels-tires/silverado-4x4-tire-buying-guide.html':
        '4x4-tire-buying-guide.html',
}


def build_redirects():
    """Emit meta-refresh stubs for URLs that have moved.

    Two sources, both resolved to a path relative to the site root before
    anything is written:

      * REDIRECTS            -- slugs that were renamed, same directory
      * retired_lang_redirects -- every URL the previous build published under a
                                 retired language prefix, mapped to its English
                                 twin. Generated, so retiring a language cannot
                                 strand a URL somebody forgot to list.

    The first version of this wrote the refresh target verbatim, which was fine
    while every target was a bare filename in the same directory. Retired
    language targets are not: /kr/exhaust/index.html has to point at
    /exhaust/index.html, two levels up, and writing "exhaust/index.html" asked
    the browser for /kr/exhaust/exhaust/index.html -- a 404 that looked like a
    working stub in the markup. Both the link and the canonical are now computed
    from the stub's own depth.
    """
    # old site path -> new site path, both relative to the output root
    moves = {old: os.path.join(os.path.dirname(old), new)
             for old, new in REDIRECTS.items()}
    moves.update(retired_lang_redirects)

    for old, new in moves.items():
        dst = os.path.join(OUT, old)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        href = os.path.relpath(new, os.path.dirname(old) or '.')
        full = f'{DOMAIN}/{new}'
        open(dst, 'w', encoding='utf-8').write(
            f'<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            f'<meta charset="UTF-8">\n'
            f'<title>Moved</title>\n'
            f'<meta name="robots" content="noindex, follow">\n'
            f'<link rel="canonical" href="{full}">\n'
            f'<meta http-equiv="refresh" content="0; url={href}">\n'
            f'</head>\n<body>\n'
            f'<p>This guide moved to <a href="{full}">{full}</a>.</p>\n'
            f'</body>\n</html>\n'
        )
    n = len(moves)
    print(f'  redirects: {n} stub(s)'
          + (f' ({len(retired_lang_redirects)} retired language)'
             if retired_lang_redirects else ''))


# Filled by inventory_retired_langs() before build_redirects() runs.
retired_lang_redirects = {}


def _follow_stub(path):
    """Resolve a stub to the real page it points at, or None if it is real.

    Retiring a language happens in one build, but the hand-kept REDIRECTS above
    means some of the previous build's pages were already stubs. Copying those
    as targets would give /kr/x -> /y -> /z: two hops, and a canonical that
    names a redirect. Follow the chain to whatever actually has content.
    """
    seen = set()
    while path not in seen:
        seen.add(path)
        p = os.path.join(OUT, path)
        if not os.path.exists(p):
            return None
        m = re.search(r'http-equiv="refresh" content="0; url=([^"]+)"',
                      open(p, encoding='utf-8').read())
        if not m:
            return path
        path = os.path.normpath(
            os.path.join(os.path.dirname(path), m.group(1))).replace(os.sep, '/')
    return None


def inventory_retired_langs():
    """Stub every page under a retired language prefix to its English twin.

    Read from the previous build's output rather than from a list, because a
    list is exactly what goes stale. Every page under /kr/ and /es/ has an
    English counterpart at the same path minus the prefix; that is checked
    rather than assumed, so a page with no twin is reported instead of being
    redirected into a 404.

    Runs before the rmtree, because it reads docs/. A clean clone has no docs/
    and so nothing already indexed to preserve -- an empty dict is correct
    there, not a failure.
    """
    retired_lang_redirects.clear()
    missing = []
    for _, prefix in RETIRED_LANGS:
        lang = prefix.strip('/')
        root = os.path.join(OUT, lang)
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for f in files:
                if not f.endswith('.html'):
                    continue
                stem = os.path.relpath(os.path.join(dirpath, f), root)
                target = _follow_stub(stem.replace(os.sep, '/'))
                # Only a genuinely unresolvable target is a problem. The English
                # twin's path is normally identical to the stem minus the
                # language prefix -- /kr/about.html -> about.html -- so an
                # earlier version that compared target to stem flagged every
                # correct redirect as missing and stubbed only the handful that
                # chained through REDIRECTS.
                if not target:
                    missing.append(f'{prefix}/{stem}')
                    continue
                retired_lang_redirects[f'{lang}/{stem}'.replace(os.sep, '/')] = target
    if retired_lang_redirects:
        print(f'  retired languages: {len(retired_lang_redirects)} url(s) stubbed')
    if missing:
        print(f'  ! retired url(s) with no English twin: {len(missing)}')
        for m in missing[:5]:
            print(f'      {m}')


def build_legacy_pages(sidebar_entries=None):
    """Carry the hand-written pages that predate this generator forward verbatim.

    These are real published articles, not generated output; rmtree at the top
    of build() would otherwise delete them. The F-150 guide also gets the intake
    diagram spliced in, since it predates the figure pipeline.
    """
    prev = os.path.join(ROOT, '_prev_docs')
    legacy = ['cold-air-intakes/best-cold-air-intake-f150-50l.html',
              'cold-air-intakes/index.html']
    n = 0
    for relp in legacy:
        src = os.path.join(prev, relp)
        if not os.path.exists(src):
            continue
        dst = os.path.join(OUT, relp)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        txt = open(src, encoding='utf-8').read()
        if relp.endswith('best-cold-air-intake-f150-50l.html'):
            shots = find_photos(PHOTO_ROOT, 'cold-air-intake-guide')
            if shots:
                fig = photo_html(shots[:1], 'cold-air-intake-guide', 'en', '../')
                txt = txt.replace('  <h2>The short answer</h2>',
                                  fig + '  <h2>The short answer</h2>', 1)
            # The same rule the generated articles follow: the photograph next
            # to a price is a photograph of that product. This page bypasses
            # render_article, so without this it is the one page on the site
            # whose buy boxes carry no picture.
            txt = product_photos.inject_product_photos(
                txt, 'legacy-f150-intake', '../', PRODUCT_ROOT)
        else:
            # The legacy hub had no photograph and no way to get one, since it
            # is carried across verbatim rather than generated. It is the only
            # remaining page above the post list that was pure text, so it gets
            # the same listing shot its own guide uses for its first pick.
            fig = hub_product_photo(['legacy-f150-intake'], '../')
            if fig:
                txt = txt.replace('  <ul class="post-list">',
                                  fig + '  <ul class="post-list">', 1)
        # these pages predate the generator and carry their own stale affiliate
        # note and reading-time byline. Strip them, then re-add a disclosure
        # below only if the page actually links to a retailer -- the old text
        # made claims about commission that were not true.
        txt = re.sub(r'\s*<div class="disclosure">.*?</div>\s*', '\n', txt, flags=re.S)
        txt = re.sub(r'\s*<p[^>]*>\s*<strong>Affiliate note:</strong>.*?</p>\s*', '\n', txt, flags=re.S)
        txt = re.sub(r'\s*<p[^>]*>\s*We earn commissions?[^<]*</p>\s*', '\n', txt, flags=re.S)
        txt = re.sub(r'\s*<span>\d+\s+min read</span>', '', txt)
        # These pages hard-code ../style.css; they were written before the
        # generator fingerprinted the URL. Left alone, the two legacy pages --
        # one of which is the F-150 guide Google actually indexed -- would keep
        # loading whatever CSS the reader cached hours ago.
        txt = txt.replace('href="../style.css"',
                          f'href="../style.css?v={css_version()}"')
        # These two carry a hand-written footer, so they miss every footer
        # change the generator makes. They are also the pages Google has
        # actually indexed, so leaving them without the social link puts it
        # everywhere except where the traffic is.
        # The commission-claim strip above runs first and leaves this line
        # unindented, so match it without a leading-whitespace prefix.
        txt = txt.replace(
            '<p><a href="../methodology.html">How we pick products</a></p>',
            '<p><a href="../methodology.html">How we pick products</a></p>\n'
            + foot_social_html(''), 1)

        # The legacy pages were written before there was a named editor, so the
        # byline says only "Published <date>" and the JSON-LD credits the
        # Organization as author. Every generated article credits the Person.
        # Two different authors on one site is a contradiction a search engine
        # has to resolve by trusting neither, so bring the old page in line.
        if relp.endswith('best-cold-air-intake-f150-50l.html'):
            name, role = EDITOR['en']
            txt = txt.replace(
                '  <div class="byline">\n'
                '    <span>Published 30 October 2026</span>\n'
                '    <span>14 products compared</span>\n'
                '  </div>',
                '  <div class="byline">\n'
                f'    <span class="byline-author">{UI["en"]["by"]} '
                f'<a href="../about.html">{html.escape(name)}</a>, '
                f'{html.escape(role)}</span>\n'
                '    <span>Published 30 October 2026</span>\n'
                '    <span>14 products compared</span>\n'
                '  </div>', 1)
            txt = txt.replace(
                '"author": {\n        "@id": "https://carmodreview.com/#org"\n      },',
                '"author": {\n        "@type": "Person",\n'
                f'        "name": "{name}",\n'
                '        "url": "https://carmodreview.com/about.html"\n      },', 1)
            # and give it the same related block the generated articles get, or
            # it stays the one page with no route to its siblings
            rel_html = build_related('en', '../', sidebar_entries,
                                     'cold-air-intake', 'Engine')
            if rel_html:
                art = re.search(r'<article[^>]*>.*?</article>', txt, re.S)
                topics = build_topics('en', '../',
                                      art.group(0) if art else txt,
                                      'cold-air-intake', 'Engine & Intake', '')
                txt = txt.replace('</article>', topics + rel_html + '</article>', 1)

        # affiliate tagging and the matching disclosure, for pages that bypass
        # render_page and so never pass through action()
        txt = tag_affiliate_links(txt, relp)
        disc = build_disclosure('en', '../', txt)
        if disc:
            txt = txt.replace('<main class="wrap">',
                              f'<main class="wrap">\n{disc}', 1)
        assert_disclosure(txt, relp)

        open(dst, 'w', encoding='utf-8').write(inject_analytics(txt))
        n += 1
    if n:
        print(f'  carried forward {n} legacy page(s)')


def build_static_pages(index_entries, sidebar_entries=None):
    """homepage, about, methodology, contact, legal x3, 404"""
    meta_about, body_about = read_doc(os.path.join(SRC, 'about-us.md'))
    langs_about, _ = split_langs(body_about)
    meta_home, body_home = read_doc(os.path.join(SRC, 'homepage.md'))
    langs_home, _ = split_langs(body_home)

    for code, label, prefix in LANGS:
        rel = '../' if prefix else ''
        # The canonical is the bare root, not /index.html. GitHub Pages serves
        # identical bytes from both, which makes them duplicates, and Google
        # reports the pair as "Duplicate, Google chose different canonical"
        # rather than merging cleanly. Pointing every signal at "/" makes the
        # choice unambiguous. The og:url and sitemap follow the same URL.
        alts = {'en': f'{DOMAIN}/'}
        for c, _, p in LANGS[1:]:
            alts[c] = f'{DOMAIN}{p}/index.html'
        if code in langs_home:
            md = clean_md(langs_home[code])
            # the dek is the first blockquote-ish bold line
            title = 'Car Mod Review'
            body = md2html(md, rel)
            # No homepage photography. The three stock shots that used to sit
            # here were generic pickups on dirt roads -- a reference vehicle in
            # everything but name, captioned with a description of the stock
            # photo rather than anything about a part. On a site whose whole
            # claim is that every picture shows the actual component, a
            # decorative truck was the thing working against it. The call stays
            # so that dropping real photos into content/photos/home/ still
            # places them; with nothing on disk it is a no-op.
            body = inject_photos(body, 'home', code, rel,
                                 find_photos(PHOTO_ROOT, 'home'))
            # The .home-hero scoping that used to be here capped the homepage
            # photograph so it did not push the lead block off screen. That
            # photograph is gone; if one is ever added back it will need the cap
            # again, and the measurement to check it against was 798px on an
            # 807px viewport.
            # The newest guide goes above the fold. It sits directly after the
            # site's one-line description and before the "Browse guides" links,
            # which is the first place it can go without pushing the h1 down:
            # putting it after the <hr> worked but landed at 798px on an 807px
            # screen, so the title cleared the fold by nine pixels and nothing
            # else did. Anchor on the dek paragraph, falling back to the first
            # <hr> and then the end of the body, so the guide stays on the page
            # if the homepage copy is rewritten.
            lead = featured_html(index_entries, code, rel)
            if lead:
                dek = re.search(r'<p><a href="#guides">[^<]*(?:<[^>]+>[^<]*)*?</p>\s*', body)
                if dek:
                    body = body[:dek.start()] + lead + body[dek.start():]
                elif '<hr>' in body:
                    body = body.replace('<hr>', '<hr>\n' + lead, 1)
                else:
                    body = body + lead
            # The product rail goes between the newest-guide block and the
            # "Browse guides" line: high enough to be seen, low enough not to
            # push the h1 or the lead below the fold.
            strip = homepage_strip_html(index_entries, rel)
            if strip:
                if '<hr>' in body:
                    body = body.replace('<hr>', strip + '<hr>', 1)
                else:
                    body = strip + body
            body_with_lead = body + '\n' + index_list_html(index_entries, code, rel)
            page = render_page(
                lang=code, title=title if code != 'en' else
                # 50 characters. The old wording ran to 63, and Google cuts the
                # tail around 60 -- which threw away "Against the Specs", the one
                # phrase that says what this site does differently from every
                # other parts blog. "Spec-Checked" keeps that claim inside the
                # limit instead of shortening it away.
                'Car Mod Review — Car and Truck Parts, Spec-Checked',
                desc='Car and truck parts guides built from published specifications, '
                     'with every source named. No invented numbers and no unverified claims.',
                canonical=alts[code], body_html=body_with_lead,
                rel=rel, alts=alts, entries=index_entries)
            d = os.path.join(OUT, prefix.strip('/')) if prefix else OUT
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page)

        if code in langs_about:
            md = clean_md(langs_about[code])
            page = render_page(
                lang=code, title=('About CarModReview' if code == 'en'
                                  else '소개 | Car Mod Review' if code == 'kr'
                                  else 'Sobre CarModReview'),
                desc={'en': 'Who writes CarModReview, how a guide gets written, and what '
                             'this site will not do.',
                      'kr': 'CarModReview를 누가 쓰는지, 가이드가 어떻게 만들어지는지, '
                            '그리고 이 사이트가 하지 않는 것.',
                      'es': 'Quién escribe CarModReview, cómo se escribe una guía y lo que '
                            'este sitio no hace.'}[code],
                canonical=f'{DOMAIN}{prefix}/about.html',
                body_html=md2html(md, rel), rel=rel, entries=sidebar_entries,
                # English only. These pointed at /kr/ and /es/ pages that are
                # no longer built, which is a hreflang pair advertising a 404.
                alts={'en': f'{DOMAIN}/about.html'})
            d = os.path.join(OUT, prefix.strip('/')) if prefix else OUT
            open(os.path.join(d, 'about.html'), 'w', encoding='utf-8').write(page)

    # methodology (existing hand-written page, re-emitted with new nav)
    old = os.path.join(ROOT, '_prev_docs', 'methodology.html')
    if os.path.exists(old):
        txt = open(old, encoding='utf-8').read()
        m = re.search(r'<article>(.*?)</article>', txt, re.S)
        if m:
            inner = m.group(1)
            inner = re.sub(r'</?article>', '', inner)
            # the money section belongs on a page about funding, and there is no
            # longer one; how products get picked is the whole subject here
            inner = re.sub(r'\s*<h2>How we make money.*?(?=<h2)', '\n\n  ', inner,
                           flags=re.S)
            # Photographs, because this is six screens of unbroken prose about
            # method -- the driest page on the site and the one that most needs
            # something to stop the eye. They are borrowed from the guides,
            # not new: each is a real component photograph already licensed and
            # captioned, shown beside the section it illustrates (a laptop
            # reading data next to how reviews are collected, a torque
            # measurement next to how claims get checked). The caption always
            # describes what is actually in frame, so none of them is standing
            # in as proof of work we did not do.
            photo_blocks = {
                'What we actually do':
                    ('ecu-tuning-explained', '02-10490631'),
                'The three rankings':
                    ('wheels-buying-guide', '03-5504082'),
                "What we won't do":
                    ('brake-pads-rotors-guide', '04-6870299'),
                'Corrections':
                    ('cold-air-intake-guide', '04-11074558'),
            }
            for heading, (ph_slug, stem) in photo_blocks.items():
                src = os.path.join(PHOTO_ROOT, ph_slug, stem + '.jpg')
                if not os.path.exists(src):
                    continue
                fig = photos.photo_html([src], ph_slug, 'en', '')
                # Place the figure just before the heading it belongs to, so it
                # closes the previous section rather than opening the next one.
                pat = re.compile(r'(\s*<h2>' + re.escape(heading) + r'</h2>)')
                if pat.search(inner):
                    inner = pat.sub(fig + r'\1', inner, count=1)
            # The first entry lands directly after the dek, because "What we
            # actually do" is the first heading on the page. A photograph
            # wedged between the standfirst and the opening section reads as a
            # mistake -- the dek belongs to the title. Pull that one out and
            # make it a hero above the dek instead, which is where every article
            # on the site puts its lead photo.
            lead_fig = ''
            m_lead = re.search(r'\n\s*<figure class="fig fig--photo">.*?</figure>', inner, re.S)
            if m_lead and m_lead.start() < inner.find('<h2>'):
                lead_fig = m_lead.group(0)
                inner = inner[:m_lead.start()] + inner[m_lead.end():]
                lead_fig = lead_fig.replace('class="fig fig--photo"',
                                            'class="fig fig--photo fig--hero"', 1)
            if lead_fig:
                inner = re.sub(r'(<p class="dek">.*?</p>)',
                               r'\1' + lead_fig, inner, count=1, flags=re.S)
            page = render_page(
                lang='en', title='How we pick products | Car Mod Review',
                desc='Our selection method: how products are compared, ranked and sourced.',
                canonical=f'{DOMAIN}/methodology.html', body_html=inner, rel='',
                entries=sidebar_entries)
            open(os.path.join(OUT, 'methodology.html'), 'w', encoding='utf-8').write(page)

    # legal pages x3 languages. The affiliate disclosure is published now that
    # the footer links to it; its body states the true current status (no paid
    # relationships yet) rather than the participation list it used to claim.
    for fn, slug in (('privacy-policy.md', 'privacy-policy'),
                     ('affiliate-disclosure.md', 'affiliate-disclosure'),
                     ('terms-of-service.md', 'terms-of-service')):
        meta, body = read_doc(os.path.join(SRC, 'legal', fn))
        langs, _ = split_langs(body)
        os.makedirs(os.path.join(OUT, 'legal'), exist_ok=True)
        for code, label, prefix in LANGS:
            if code not in langs:
                continue
            md = clean_md(langs[code])
            # these pages get their own <h1> below; drop any heading the
            # source carries (the shared trilingual one, or a per-language one),
            # but leave the "Last updated" line that follows it in place
            md = re.sub(r'^#[ \t]+[^\n]*\n?', '', md, count=1).strip()
            title = {('privacy-policy', 'en'): 'Privacy Policy',
                     ('privacy-policy', 'kr'): '개인정보 처리방침',
                     ('privacy-policy', 'es'): 'Política de privacidad',
                     ('affiliate-disclosure', 'en'): 'Affiliate Disclosure',
                     ('affiliate-disclosure', 'kr'): '제휴 고지',
                     ('affiliate-disclosure', 'es'): 'Divulgación de afiliados',
                     ('terms-of-service', 'en'): 'Terms of Service',
                     ('terms-of-service', 'kr'): '이용약관',
                     ('terms-of-service', 'es'): 'Términos del servicio'}[(slug, code)]
            # English only; see the note on the about page above.
            alts = {'en': f'{DOMAIN}/legal/{slug}.html'}
            legal_desc = {
                ('privacy-policy', 'en'): 'What data Car Mod Review collects, how analytics are '
                    'handled, and how to request deletion.',
                ('privacy-policy', 'kr'): 'Car Mod Review가 수집하는 데이터, 분석 도구와 제휴 링크 처리 방식, 삭제 요청 방법.',
                ('privacy-policy', 'es'): 'Qué datos recoge Car Mod Review, cómo se manejan las '
                    'analíticas y los enlaces de afiliado, y cómo solicitar su eliminación.',
                ('affiliate-disclosure', 'en'): 'How Car Mod Review handles affiliate links, '
                    'commission, and editorial independence — including our current status.',
                ('affiliate-disclosure', 'kr'): 'Car Mod Review의 제휴 링크, 수수료, 편집 독립성 '
                    '방침과 현재 제휴 관계 여부를 안내합니다.',
                ('affiliate-disclosure', 'es'): 'Cómo trata Car Mod Review los enlaces de '
                    'afiliación, las comisiones y la independencia editorial, incluido nuestro '
                    'estado actual.',
                ('terms-of-service', 'en'): 'The terms that govern use of Car Mod Review: '
                    'accuracy, liability, external links and third-party platforms.',
                ('terms-of-service', 'kr'): 'Car Mod Review 이용에 적용되는 정확성, 책임의 한계, '
                    '외부 링크 및 제3자 플랫폼 관련 약관입니다.',
                ('terms-of-service', 'es'): 'Los términos que rigen el uso de Car Mod Review: '
                    'exactitud, responsabilidad, enlaces externos y plataformas de terceros.',
            }.get((slug, code), title)
            page = render_page(
                lang=code, title=f'{title} | Car Mod Review',
                desc=legal_desc, canonical=alts[code],
                body_html=stamp_email(f'  <h1>{html.escape(title)}</h1>\n'
                                      + md2html(md, '../../' if prefix else '../')),
                rel='../../' if prefix else '../', alts=alts, og_type='article',
                entries=sidebar_entries)
            d = os.path.join(OUT, *( ([prefix.strip('/')] if prefix else []) + ['legal'] ))
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, f'{slug}.html'), 'w', encoding='utf-8').write(page)

    # contact. The terms page used to be hardcoded right here; it lives in
    # content/legal/terms-of-service.md now, beside the other two legal pages,
    # because it grew the same trilingual body they have and a second copy in
    # this function is exactly how the two drift apart.
    contact_inner = """
  <h1>Contact</h1>
  <p class="dek">One person reads this inbox. Expect a reply within a few days,
  sooner if you are correcting something we got wrong.</p>
  <div class="callout">
    <div class="callout-title">Corrections first</div>
    <p>If a spec on this site is wrong, tell us which page and what the correct
    number is. Corrections get priority over everything else, and we will publish
    the fix with a note.</p>
  </div>
  <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
  <p><strong>Products / PR:</strong> we do not accept paid placement. If you want a part
  considered for a guide, send the published specs and the manufacturer documentation,
  not a press release.</p>
  <p><strong>Partnerships:</strong> same address, subject line "partnership".</p>
"""
    page = render_page(lang='en', title='Contact | Car Mod Review',
                       desc='How to reach Car Mod Review, how corrections are handled, '
                            'and why we do not accept paid placement.',
                       canonical=f'{DOMAIN}/contact.html',
                       body_html=stamp_email(contact_inner), rel='',
                       entries=sidebar_entries)
    open(os.path.join(OUT, 'contact.html'), 'w', encoding='utf-8').write(page)

    # a 404 has nothing to index and nothing to rank; letting it be indexed
    # puts a dead URL in the results for the brand name
    nf = render_page(lang='en', title='Page not found | Car Mod Review',
                     desc='That page does not exist. Browse the guides index instead.',
                     canonical=f'{DOMAIN}/404.html', robots='noindex, follow',
                     body_html='  <h1>Not found</h1>\n  <p>That page does not exist. '
                               '<a href="index.html">Start from the homepage</a>.</p>', rel='',
                     entries=sidebar_entries)
    open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8').write(nf)
    print('  wrote static pages')


def featured_html(index_entries, code, rel):
    """The newest guide, as a lead block at the top of the homepage.

    Sorting the lists correctly was only half of the job. The newest guide still
    sat below the hero photograph and four paragraphs about how the site works,
    so a reader who came to see what is new had to scroll past the site's own
    introduction to find it. This puts it directly under the site title.

    Uses the same key as the sidebar and the index, so the three can never
    disagree about which guide is newest.
    """
    field = {'en': 1, 'kr': 2, 'es': 3}[code]
    rows = [e for e in index_entries
            if code in (e[7].get('langs_all') or set())]
    if not rows:
        return ''
    date, slug, cat, cs, cl, ck, ce, meta = sorted(
        rows,
        key=lambda e: (str(e[7].get('published') or ''), e[0], e[1]),
        reverse=True)[0]
    title = ((meta.get('title') or {}).get(code)
             or (meta.get('title') or {}).get('en') or slug)
    title = re.sub(r'^#+\s*', '', title).strip().strip('"')
    desc = ((meta.get('seo_desc') or {}).get(code)
            or (meta.get('seo_desc') or {}).get('en') or '')
    desc = re.sub(r'\s+', ' ', str(desc)).strip()
    catlabel = (cl, ck, ce)[field - 1]
    pub = str(meta.get('published') or date)
    try:
        pretty = datetime.datetime.strptime(pub, '%Y-%m-%d').strftime('%d %B %Y').lstrip('0')
    except ValueError:
        pretty = pub
    kicker = {'en': 'Latest guide', 'kr': '최신 가이드', 'es': 'Última guía'}[code]
    out = ['\n  <section class="lead">\n',
           f'    <p class="lead-kicker">{html.escape(kicker)}</p>\n',
           f'    <h2 class="lead-title"><a href="{rel}{cs}/{slug}.html">'
           f'{html.escape(title)}</a></h2>\n']
    if desc:
        out.append(f'    <p class="lead-desc">{html.escape(desc)}</p>\n')
    out.append(f'    <p class="lead-meta"><time datetime="{html.escape(pub)}">'
               f'{html.escape(pretty)}</time> · {html.escape(catlabel)}</p>\n')
    out.append('  </section>\n')
    return ''.join(out)


def _strip_label(name):
    """Product name with its trailing fitment removed, for a tile caption.

    The fitment is the most useful half of these names on a product page and
    the least useful half on a 168px tile, where "…(19-26 2.7L Silverado
    1500)" would take three lines and push the guide label out of the card.
    It stays in the alt text, which is where a search engine and a screen
    reader look for it.
    """
    return re.sub(r'\s*\([^()]*\)\s*$', '', name).strip() or name


def hub_product_photo(slugs, rel):
    """A listing photograph for a hub that has no body photography of its own.

    Only used when category_photo() found nothing. Two hubs were bare -- no
    image at all above the post list -- because their articles' photography is
    of the products themselves rather than of a car. The tonneau guide is the
    clearest case: the entire subject is four specific covers, so the honest
    picture of it is one of those covers, exactly as the buy box on the guide
    shows it.
    """
    for slug in slugs:
        for finder in (product_photos._shots, product_photos._sku_shots):
            found = finder(PRODUCT_ROOT, slug)
            if not found:
                continue
            img = (found[min(found)] if isinstance(next(iter(found)), int)
                   else found[sorted(found)[0]])
            alt = product_photos._alt_for(img, slug)
            return (f'  <div class="pick-photo">'
                    f'<img src="{rel}img/products/{slug}/{os.path.basename(img)}" '
                    f'alt="{html.escape(alt)}" loading="lazy" decoding="async">'
                    f'</div>\n')
    return ''


def homepage_strip_html(index_entries, rel, limit=8):
    """A rail of real product photographs across the top of the homepage.

    The homepage carried no images at all after the three stock pickup shots
    were removed in 6ef8528: they were generic trucks on dirt roads, captioned
    with a description of the photograph rather than of any part, and on a site
    whose whole claim is that every picture shows the actual component they
    worked against it. Rather than reintroduce a reference vehicle, this uses
    the photography that already exists and is already verified -- the listing
    shots fetched for the buy boxes, each one tied to the exact product its
    guide recommends.

    One tile per category, from each category's newest guide that has a photo,
    so the rail shows an intake box beside wheels, a levelling spacer and a
    brake kit instead of eight variations on one part. Every tile links to the
    guide it came from.
    """
    rows = [e for e in index_entries
            if 'en' in (e[7].get('langs_all') or set())]
    by_cat = {}
    for e in sorted(rows,
                    key=lambda e: (str(e[7].get('published') or ''), e[0], e[1]),
                    reverse=True):
        by_cat.setdefault(e[3], []).append(e)

    tiles = []
    for catslug, catlabel, _kr, _es in CATEGORIES.values():
        for _date, slug, _cat, cs, cl, _ck, _ce, meta in by_cat.get(catslug, []):
            # Two keying conventions exist and both have to be tried: most
            # guides number their photos by pick-block position (01-<sku>),
            # but the tonneau and electrical guides write bare buy links and
            # key theirs by listing sku (sku-<sku>). Reading only the first
            # dropped both of those categories out of the rail.
            shots = product_photos._shots(PRODUCT_ROOT, slug)
            if shots:
                img = shots[min(shots)]
            else:
                by_sku = product_photos._sku_shots(PRODUCT_ROOT, slug)
                if not by_sku:
                    continue
                img = by_sku[sorted(by_sku)[0]]
            name = product_photos._alt_for(img, cl)
            title = ((meta.get('title') or {}).get('en') or slug)
            title = re.sub(r'^#+\s*', '', title).strip().strip('"')
            size = photos._dimensions(photos._published_path(img))
            dims = (f' width="{size[0]}" height="{size[1]}"' if size else '')
            tiles.append(
                f'\n    <li class="home-strip-item">'
                f'<a href="{rel}{cs}/{slug}.html" title="{html.escape(title)}">'
                f'<img src="{rel}img/products/{slug}/{os.path.basename(img)}" '
                f'alt="{html.escape(name)}" loading="lazy" decoding="async"{dims}>'
                f'<span class="home-strip-name">{html.escape(_strip_label(name))}</span>'
                f'<span class="home-strip-cat">{html.escape(catlabel)}</span>'
                f'</a></li>')
            break
        if len(tiles) >= limit:
            break

    if not tiles:
        return ''
    return ('\n  <section class="home-strip" aria-label="Parts covered in the guides">\n'
            '    <p class="home-strip-kicker">Parts in these guides</p>\n'
            '    <p class="home-strip-note">Every photograph below is the listing&rsquo;s '
            'own product shot, matched to the exact part the guide recommends.</p>\n'
            '    <ul class="home-strip-rail">' + ''.join(tiles) + '\n    </ul>\n'
            '  </section>\n')


def index_list_html(index_entries, code, rel):
    """The guides index on the homepage, in the same order as the left rail.

    The order comes from CATEGORIES, not from the order the article files happen to be
    read in and not from the alphabet. A reader who sees the rail on the left and the
    index in the middle is looking at one page; two orders for the same six categories
    reads as a bug, because it is one.
    """
    label_i = {'en': 1, 'kr': 2, 'es': 3}[code]
    by_cat = {}
    for e in index_entries:
        if code not in (e[7].get('langs_all') or set()):
            continue
        by_cat.setdefault(e[3], []).append(e)

    # Tuning has no hub, so its guide is filed under Engine. The rail still shows
    # Tuning as its own line, so the index has to as well or the two lists disagree
    # again. Move that one guide under its own heading and drop it from Engine, so it
    # appears once and in the same place the rail puts it.
    for hslug, target in HUBLESS.items():
        tdir, _, tfile = target.rpartition('/')
        stem = tfile[:-5] if tfile.endswith('.html') else tfile
        for e in index_entries:
            if e[3] == tdir and e[1] == stem:
                by_cat[hslug] = [e]
                by_cat[tdir] = [x for x in by_cat.get(tdir, []) if x is not e]
                break

    out = [f'\n  <h2 id="guides">{UI[code]["nav_cats"]}</h2>\n']
    for catslug, *labels in CATEGORIES.values():
        items = by_cat.get(catslug)
        if not items:
            continue
        # Newest first inside each category, by the same rule the sidebar uses.
        # Without this the list ran in article-filename order, so a new guide
        # appeared wherever its number happened to fall rather than at the top
        # of its section.
        items = sorted(
            items,
            key=lambda e: (str(e[7].get('published') or ''), e[0], e[1]),
            reverse=True)
        out.append(f'  <h3><a href="{rel}{HUBLESS.get(catslug, catslug + "/")}">'
                   f'{html.escape(labels[label_i - 1])}</a></h3>\n')
        out.append('  <ul class="post-list">\n')
        for e in items:
            date, slug, cat, cs, cl, ck, ce, meta = e
            t = (meta.get('title') or {}).get(code) or (meta.get('title') or {}).get('en')
            t = re.sub(r'^#+\s*', '', t or slug).strip().strip('"')
            out.append(f'    <li><a href="{rel}{cs}/{slug}.html">{html.escape(t)}</a>'
                       f'<div class="meta">{date}</div></li>\n')
        out.append('  </ul>\n')

    if code == 'en' and os.path.exists(os.path.join(ROOT, '_prev_docs', 'cold-air-intakes', 'index.html')):
        out.append('  <h2>Also published</h2>\n  <ul class="post-list">\n')
        out.append('    <li><a href="cold-air-intakes/index.html">Cold air intakes</a>'
                   '<div class="meta">F-150 5.0L buying guide</div></li>\n')
        out.append('  </ul>\n')
    return ''.join(out)


def build_category_pages(arts, sidebar_entries=None):
    by_cat = {}
    for a in arts:
        by_cat.setdefault(a['meta'].get('category', 'Engine'), []).append(a)
    # Newest first, matching the homepage and the sidebar. Left unsorted, a hub
    # listed its guides in article-filename order, so the one guide that had just
    # been published sat in the middle of the page.
    for lst in by_cat.values():
        lst.sort(key=lambda a: (str(a['meta'].get('published') or ''),
                                str(a['meta'].get('last_updated') or ''),
                                str(a['meta'].get('slug') or '')),
                 reverse=True)
    for cat, items in by_cat.items():
        cs, cl, ck, ce = CATEGORIES.get(cat, ('engine', cat, cat, cat))
        for code, label, prefix in LANGS:
            rel = '../../' if prefix else '../'
            rows = []
            for a in items:
                if code not in a['langs']:
                    continue
                meta = a['meta']
                slug = meta.get('slug') or slugify(a['file'])
                t = (meta.get('title') or {}).get(code) or (meta.get('title') or {}).get('en')
                t = re.sub(r'^#+\s*', '', t or slug).strip().strip('"')
                d = str(meta.get('last_updated', ''))
                rows.append(f'    <li><a href="{slug}.html">{html.escape(t)}</a>'
                            f'<div class="meta">{d}</div></li>\n')
            if not rows:
                continue
            name = cl if code == 'en' else (ck if code == 'kr' else ce)
            hub_fig = category_photo(cs, code, rel, PHOTO_ROOT)
            if not hub_fig:
                # Only when the hub has no photograph of its own: two figures
                # above the post list is one too many.
                hub_fig = hub_product_photo(
                    [a['meta'].get('slug') or slugify(a['file']) for a in items], rel)
            inner = (f'  <div class="kicker">Car Mod Review</div>\n'
                     f'  <h1>{html.escape(name)}</h1>\n'
                     + hub_fig
                     + f'  <ul class="post-list">\n{"".join(rows)}  </ul>\n')
            # English only; see the note on the about page above.
            # "/engine/" not "/engine/index.html". GitHub Pages serves identical
            # bytes from both, and two URLs for one hub is the duplicate the
            # sitemap and every inbound link now avoid.
            alts = {'en': f'{DOMAIN}/{cs}/'}
            trail = [('Home', f'{DOMAIN}{prefix}/' if prefix else f'{DOMAIN}/'),
                     (name, alts[code])]
            hub_jsonld = breadcrumb_jsonld(trail) + (
                '<script type="application/ld+json">\n' + json.dumps({
                    '@context': 'https://schema.org',
                    '@type': 'CollectionPage',
                    'name': f'{name} guides',
                    'description': f'{name} buying and fitment guides, each built from '
                                   'published specifications with sources named.',
                    'url': alts[code],
                    'isPartOf': {'@id': f'{DOMAIN}/#site'},
                    'inLanguage': HTML_LANG[code],
                }, ensure_ascii=False, indent=2) + '\n</script>')
            hub_shots = find_photos(PHOTO_ROOT, (CATEGORY_SOURCE.get(cs) or [''])[0])
            hub_img = (f'{DOMAIN}/img/photos/{(CATEGORY_SOURCE.get(cs) or [""])[0]}/'
                       f'{os.path.basename(hub_shots[0])}' if hub_shots else None)
            page = render_page(lang=code, title=f'{name} | Car Mod Review',
                               desc=(f'{name} guides built from published specifications — '
                                     'fitment, sizing and what the numbers actually mean.'),
                               canonical=alts[code], body_html=inner, rel=rel, alts=alts,
                               jsonld=hub_jsonld, og_image=hub_img,
                               entries=sidebar_entries)
            d = os.path.join(OUT, *( ([prefix.strip('/')] if prefix else []) + [cs] ))
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page)
    print(f'  wrote {len(by_cat)} category hubs x{len(LANGS)} langs')


SEARCH_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Search | Car Mod Review</title>
<meta name="description" content="Search every Car Mod Review guide by part, system or problem.">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{domain}/search.html">
<link rel="stylesheet" href="style.css">
</head>
<body>

<header class="masthead">
  <div class="wrap masthead-inner">
    <div>
      <a class="brand" href="index.html">Car Mod<span>.Review</span></a>
      <span class="brand-sub">Car parts, checked against the published specs</span>
    </div>
    <div class="masthead-right">
      <nav class="nav">
        <a href="index.html">All posts</a>
        <a href="methodology.html">How we pick</a>
        <a href="contact.html">Contact</a>
      </nav>
      <form class="nav-search" action="search.html" method="get" role="search">
        <label class="sr-only" for="navq">Search guides</label>
        <input id="navq" type="search" name="q" placeholder="Search" autocomplete="off"
               value="">
        <button type="submit" aria-label="Search guides">&#8981;</button>
      </form>
    </div>
  </div>
</header>

<main class="wrap">
  <h1>Search</h1>
  <p class="dek">Every guide on the site, searched by title, summary and category.</p>
  <form class="search-form" role="search" onsubmit="return false;">
    <label class="sr-only" for="q">Search guides</label>
    <input id="q" type="search" name="q" placeholder="offset, exhaust drone, brake bedding&hellip;"
           autocomplete="off" autofocus>
  </form>
  <p class="search-status" id="status">Type to search.</p>
  <ul class="search-results" id="results"></ul>
  <noscript><p>Search needs JavaScript. Browse the <a href="index.html">full guide index</a> instead.</p></noscript>
</main>

<footer>
  <div class="wrap">
    <p><strong>Car Mod Review</strong> &mdash; car parts coverage that states its
    sources and says when it doesn't know.</p>
    {foot_social}
  </div>
</footer>

<script>
(function () {
  var INDEX = null, box = document.getElementById('q'),
      out = document.getElementById('results'), status = document.getElementById('status');

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
    });
  }

  function render(items, q) {
    if (!q) { out.innerHTML = ''; status.textContent = 'Type to search.'; return; }
    if (!items.length) {
      status.textContent = 'No guides match “' + q + '”.';
      out.innerHTML = '';
      return;
    }
    status.textContent = items.length + (items.length === 1 ? ' guide' : ' guides');
    out.innerHTML = items.map(function (it) {
      return '<li><a href="' + esc(it.u) + '">' + esc(it.t) + '</a>'
           + '<p>' + esc(it.d) + '</p>'
           + '<span class="meta">' + esc(it.c) + '</span></li>';
    }).join('');
  }

  function score(it, terms) {
    // title matches outrank summary matches, and every term must appear
    // somewhere, so a two-word query cannot return a page that hits only one.
    var t = it.t.toLowerCase(), d = it.d.toLowerCase(), c = it.c.toLowerCase();
    var n = 0;
    for (var i = 0; i < terms.length; i++) {
      var term = terms[i], hit = false;
      if (t.indexOf(term) >= 0) { n += 10; hit = true; }
      if (c.indexOf(term) >= 0) { n += 4; hit = true; }
      if (d.indexOf(term) >= 0) { n += 2; hit = true; }
      if (!hit) return 0;
    }
    return n;
  }

  function run(q) {
    if (!INDEX) return;
    var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) { render([], ''); return; }
    var scored = [];
    for (var i = 0; i < INDEX.length; i++) {
      var s = score(INDEX[i], terms);
      if (s > 0) scored.push([s, INDEX[i]]);
    }
    scored.sort(function (a, b) { return b[0] - a[0]; });
    render(scored.slice(0, 30).map(function (x) { return x[1]; }), q);
  }

  // Read ?q= so a search can be linked and shared.
  var initial = new URLSearchParams(location.search).get('q') || '';
  box.value = initial;

  fetch('search-index.json')
    .then(function (r) { return r.json(); })
    .then(function (data) { INDEX = data; run(box.value); })
    .catch(function () { status.textContent = 'Search is unavailable right now.'; });

  box.addEventListener('input', function () { run(box.value); });
})();
</script>

</body>
</html>
"""


def build_search(items):
    """Emit search-index.json and search.html.

    A static site has no server to query, so the index is a flat JSON file the
    page filters in the browser. It covers English only: the captions and
    summaries are English, and mixing three languages into one result list
    returns near-duplicates for every query.
    """
    en = [i for i in items if i['l'] == 'en']
    payload = [{'u': i['u'], 't': i['t'], 'd': i['d'], 'c': i['c']} for i in en]
    with open(os.path.join(OUT, 'search-index.json'), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=0)
    open(os.path.join(OUT, 'search.html'), 'w', encoding='utf-8').write(
        inject_analytics(SEARCH_PAGE.replace("{domain}", DOMAIN)
                         .replace('style.css', f'style.css?v={css_version()}')
                         .replace('{foot_social}', foot_social_html('    '))))
    print(f'  search: {len(payload)} guides indexed')


def build_feed(items):
    """RSS 2.0 feed of the English guides, newest first.

    Every page links to this at /feed.xml, so it has to exist — a rel=alternate
    pointing at a 404 is worse than no link at all. Dates are the real
    datePublished values, not the build date.
    """
    def rfc822(d):
        return datetime.datetime.strptime(d, '%Y-%m-%d').strftime('%a, %d %b %Y 00:00:00 +0000')

    # published first, then modified, then url. The middle key matters: both of
    # the two newest guides carry published 2026-11-05, so without it the tie
    # fell through to the URL and listed them alphabetically -- putting the
    # older tonneau guide above the one published after it.
    items = sorted(items, key=lambda i: (i['published'], i.get('modified') or '',
                                         i['url']), reverse=True)
    last = items[0]['modified'] if items else datetime.date.today().isoformat()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
           '  <channel>',
           '    <title>Car Mod Review</title>',
           f'    <link>{DOMAIN}/</link>',
           '    <description>Car and truck parts guides built from published '
           'specifications, with every source named.</description>',
           '    <language>en</language>',
           f'    <lastBuildDate>{rfc822(last)}</lastBuildDate>',
           f'    <atom:link href="{DOMAIN}/feed.xml" rel="self" type="application/rss+xml"/>']
    for i in items:
        out.append('    <item>')
        out.append(f"      <title>{html.escape(i['title'], quote=False)}</title>")
        out.append(f"      <link>{i['url']}</link>")
        out.append(f'      <guid isPermaLink="true">{i["url"]}</guid>')
        out.append(f'      <category>{html.escape(i["section"], quote=False)}</category>')
        out.append(f'      <pubDate>{rfc822(i["published"])}</pubDate>')
        out.append(f"      <description>{html.escape(i['desc'], quote=False)}</description>")
        out.append('    </item>')
    out += ['  </channel>', '</rss>']
    open(os.path.join(OUT, 'feed.xml'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(f'  feed: {len(items)} items')


def build_sitemap(arts):
    """Write sitemap.xml and robots.txt.

    lastmod has to be true or it is worse than absent. Google only honours the
    field while it stays consistent, and this file used to stamp
    datetime.date.today() on the 30 static and hub URLs -- so every single
    deploy announced that a third of the site had just changed, on a site whose
    articles were last revised in May. That is the classic signal that trains a
    crawler to ignore lastmod entirely.

      * articles  -> the real last_updated from the frontmatter
      * hubs      -> the newest last_updated among the guides they list
      * static    -> no lastmod at all; a page rendered from a shared template
                     has no honest per-page date to report
    """
    urls = []
    today = datetime.date.today().isoformat()
    newest_by_cat = {}
    for a in arts:
        cs = CATEGORIES.get(a['meta'].get('category'), ('engine',))[0]
        slug = a['meta'].get('slug') or slugify(a['file'])
        # Same source as the Article's dateModified. These two disagreeing is
        # worse than either being stale: dateModified says the page changed
        # while a not-newer lastmod tells the crawler not to bother coming
        # back, and Google resolves that conflict by distrusting lastmod for
        # the whole file.
        d = (git_date(a['path'])
             or str(a['meta'].get('last_updated', today)))
        for code, _, prefix in LANGS:
            if code in a['langs']:
                urls.append((f'{DOMAIN}{prefix}/{cs}/{slug}.html', d))
                if d > newest_by_cat.get(cs, ''):
                    newest_by_cat[cs] = d
    # Static pages do not all exist in every language — about, methodology,
    # contact and terms are per-language authored, not generated. List a URL only
    # when build_static_pages actually writes it, or the sitemap advertises 404s.
    # The homepage goes in as "/" rather than "/index.html": both return the
    # same bytes, so listing the second form invites the duplicate.
    static_paths = ('about.html', 'methodology.html', 'contact.html',
                    'legal/privacy-policy.html',
                    'legal/affiliate-disclosure.html',
                    'legal/terms-of-service.html')
    for code, _, prefix in LANGS:
        if (prefix or '/') == '/':
            urls.append((f'{DOMAIN}/', None))
    for path in static_paths:
        for code, _, prefix in LANGS:
            if os.path.exists(os.path.join(OUT, *(prefix.strip('/').split('/')
                                                 if prefix else []), path)):
                urls.append((f'{DOMAIN}{prefix}/{path}', None))
    for c in sorted(newest_by_cat):
        for code, _, prefix in LANGS:
            urls.append((f'{DOMAIN}{prefix}/{c}/', newest_by_cat[c]))

    # hand-written pages carried forward from the pre-generator site
    urls.append((f'{DOMAIN}/cold-air-intakes/', '2026-10-30'))
    urls.append((f'{DOMAIN}/cold-air-intakes/best-cold-air-intake-f150-50l.html', '2026-10-30'))

    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, d in urls:
        sm.append(f'  <url><loc>{u}</loc></url>' if d is None
                  else f'  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>')
    sm.append('</urlset>')
    open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(sm) + '\n')

    open(os.path.join(OUT, 'robots.txt'), 'w', encoding='utf-8').write(
        'User-agent: *\nAllow: /\n\n'
        f'Sitemap: {DOMAIN}/sitemap.xml\n')
    print(f'  sitemap: {len(urls)} urls')


if __name__ == '__main__':
    print('building site ->', OUT)
    build()
    print('done')
