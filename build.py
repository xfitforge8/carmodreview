#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — turn ~/carmodreview/content/*.md into a static site in ~/carmodreview/docs/.

No framework, no build step in CI. Run locally, commit the output.

Design contract (matches the existing hand-written pages):
  * English is the primary route at /<category>/<slug>.html
  * Korean and Spanish are alternates at /kr/... and /es/...
  * Every page: "What we could not verify"
    block before the footer, real publish dates only.
"""
import os, re, json, html, shutil, datetime, sys, subprocess

import markdown
import yaml

ROOT = os.path.expanduser('~/carmodreview')
SRC = os.path.join(ROOT, 'content')
OUT = os.path.join(ROOT, 'docs')
PHOTO_ROOT = os.path.join(SRC, 'photos')
DOMAIN = 'https://carmodreview.com'

import photos
from photos import (inject_photos, find_photos, photo_html, category_photo,
                    CATEGORY_SOURCE)

# ───────────────────────────────────────────────────── analytics (Cloudflare)
# Cloudflare Web Analytics: cookieless, collects no personal data, no consent
# banner needed. The beacon is inert until a token is set here -- with the token
# empty, every page renders byte-identical to before. To switch on: add
# carmodreview.com as a site in the Cloudflare dashboard, copy the token out of
# the JS snippet it gives you, paste it below, rebuild.
#
# Deliberately not Google Analytics: GA4 sets cookies, which under CCPA (the
# site is in California) means a consent banner and a cookie policy rewrite.
# This site's whole pitch is being more credible than its competitors, and the
# least-invasive analytics is the consistent choice.
CF_BEACON_TOKEN = ''

CF_BEACON_SNIPPET = (
    '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
    'data-cf-beacon=\'{{"token": "{token}"}}\'></script>'
)


def analytics_tag():
    """The Cloudflare beacon, or '' when no token is configured."""
    if not CF_BEACON_TOKEN:
        return ''
    return CF_BEACON_SNIPPET.format(token=CF_BEACON_TOKEN)


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

CATEGORIES = {
    'Suspension':      ('suspension',      'Suspension',      '서스펜션',      'Suspensión'),
    'Wheels & Tires':  ('wheels-tires',    'Wheels & Tires',  '휠 & 타이어',   'Llantas y neumáticos'),
    'Engine':          ('engine',          'Engine & Intake', '엔진 & 인테이크', 'Motor y admisión'),
    'Exhaust':         ('exhaust',         'Exhaust',         '배기',          'Escape'),
    'Brakes':          ('brakes',          'Brakes',          '브레이크',      'Frenos'),
    'Tuning':          ('tuning',          'Tuning',          '튜닝',          'Reprogramación'),
}

LANGS = [('en', 'EN', ''), ('kr', 'KR', '/kr'), ('es', 'ES', '/es')]

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
               nav_cats='Categories', other='Read this in', on='on',
               search='Search', contact='Contact', about='About', privacy='Privacy',
               terms='Terms',
               foot_tag=('car parts coverage that states its sources and says when it '
                         "doesn't know.")),
    'kr': dict(all_posts='모든 글', how='선정 기준', home='홈',
               published='발행일', updated='수정', minread='분 소요', verified='확인하지 못한 것',
               disc_title='제휴 고지',
               disc_body=('이 페이지의 링크를 통해 구매가 이루어지면 저희는 수수료를 받습니다. '
                          '수수료는 어떤 제품을 고르는지, 순위가 어떻게 되는지를 결정하지 않습니다.'),
               nav_cats='카테고리', other='다른 언어', on='',
               search='검색', contact='문의', about='소개', privacy='개인정보처리방침',
               terms='이용약관',
               foot_tag='출처를 밝히고, 모르는 것은 모른다고 말하는 자동차 부품 정보.'),
    'es': dict(all_posts='Todas las guías', how='Cómo elegimos', home='Inicio',
               published='Publicado', updated='Actualizado', minread='min de lectura', verified='Lo que no pudimos verificar',
               disc_title='Nota de afiliación',
               disc_body=('Ganamos comisiones por compras realizadas a través de los enlaces de '
                          'esta página. La comisión nunca decide qué productos elegimos ni en qué '
                          'posición se clasifican.'),
               nav_cats='Categorías', other='Leer en', on='',
               search='Buscar', contact='Contacto', about='Sobre nosotros',
               privacy='Privacidad', terms='Términos',
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
    # for every language; about-us.md is written that way. Prepend it to any
    # section that does not open with its own H1 so no page renders headless.
    preamble = body[:marks[0].start()]
    h1 = re.search(r'^#[ \t]+[^\n]+', preamble, re.M)
    if h1:
        for lang, sec in out.items():
            if not re.search(r'^#[ \t]+[^\n]+', sec, re.M):
                out[lang] = h1.group(0) + '\n\n' + sec.lstrip('\n')

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
        return f'href="{rel}{slug}/index.html"'

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
    return resolve_links(out, rel)


def action(url):
    """Render an inline markdown link or a bracketed CTA as an anchor."""
    if url.startswith('http') and 'americantrucks' in url:
        return url, 'rel="sponsored nofollow noopener" target="_blank"'
    if url.startswith('http'):
        return url, 'rel="noopener" target="_blank"'
    return url, ''


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
<link rel="stylesheet" href="{rel}style.css">
{jsonld}{analytics}
</head>
<body>

<header class="masthead">
  <div class="wrap masthead-inner">
    <div>
      <a class="brand" href="{rel}index.html">Car Mod<span>.Review</span></a>
      <span class="brand-sub">{tagline}</span>
    </div>
    <nav class="nav">
      <a href="{rel}index.html">{all_posts}</a>
      <a href="{rel}methodology.html">{how}</a>
      <a href="{rel}search.html">{search}</a>
      <a href="{rel}contact.html">{contact}</a>
    </nav>
  </div>
</header>

<main class="wrap">
<div class="layout">
<aside class="side">
{sidebar}
</aside>
<article>
{body}
</article>
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
      <a href="{rel}legal/terms-of-service.html">{terms}</a>
    </p>
    <p class="lang-switch">{other}: <a href="{alt_en}">English</a> &middot;
      <a href="{alt_kr}">한국어</a> &middot; <a href="{alt_es}">Español</a></p>
  </div>
</footer>

</body>
</html>
"""

TAGLINE = {
    'en': 'Car parts, checked against the published specs',
    'kr': '공개 스펙과 대조하는 자동차 부품 정보',
    'es': 'Piezas de auto contrastadas con las especificaciones publicadas',
}


def default_sidebar(lang, rel):
    """Category list for the left rail, the way a blog sidebar conventionally works.

    Order follows CATEGORIES exactly — the same order the homepage lists the
    categories in. It used to be sorted alphabetically by label, which put
    "Brakes" first in the rail and "Suspension" first in the body: two different
    orders for the same six things on the same page, with no way for a reader to
    reconcile them. Editorial order is a decision; alphabetical by translated
    label is just a property of the words.
    """
    labels = {'en': 1, 'kr': 2, 'es': 3}
    head = {'en': 'Categories', 'kr': '카테고리', 'es': 'Categorías'}[lang]
    items = ''.join(
        f'        <li><a href="{rel}{HUBLESS.get(slug, slug + "/index.html")}">'
        f'{html.escape(label)}</a></li>\n'
        for slug, label in ((c[0], c[labels[lang]]) for c in CATEGORIES.values())
    )
    return (f'    <div class="side-block">\n'
            f'      <h2 class="side-title">{head}</h2>\n'
            f'      <ul class="side-list">\n{items}      </ul>\n'
            f'    </div>\n')


def render_page(*, lang, title, desc, canonical, body_html, rel, jsonld='',
                og_type='website', alts=None, og_image=None, robots=None,
                sidebar=''):
    alts = alts or {}
    alt = ''
    if alts:
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
        analytics=('\n' + analytics_tag()) if analytics_tag() else '',
        tagline=TAGLINE[lang], all_posts=ui['all_posts'], how=ui['how'], other=ui['other'],
        search=ui['search'], contact=ui['contact'], about=ui['about'],
        privacy=ui['privacy'], terms=ui['terms'], foot_tag=ui['foot_tag'],
        alt_en=alts.get('en', canonical), alt_kr=alts.get('kr', canonical),
        alt_es=alts.get('es', canonical),
        sidebar=sidebar or default_sidebar(lang, rel),
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
                'inLanguage': ['en', 'ko', 'es'],
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
        'author': {'@type': 'Organization', 'name': 'Car Mod Review', '@id': f'{DOMAIN}/#org'},
        'publisher': {'@type': 'Organization', 'name': 'Car Mod Review', '@id': f'{DOMAIN}/#org'},
        'isAccessibleForFree': True,
        'mainEntityOfPage': {'@type': 'WebPage', '@id': canonical},
    }, ensure_ascii=False, indent=2) + '\n</script>')


# ─────────────────────────────────────────────────────────────── build
def build():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    # photo width/height must describe the resized file the browser fetches
    photos.configure(PHOTO_ROOT, os.path.join(OUT, 'img', 'photos'))

    # keep the hand-written assets that aren't generated
    shutil.copy(os.path.join(SRC, '..', 'docs', 'CNAME'), os.path.join(OUT, 'CNAME')) \
        if os.path.exists(os.path.join(SRC, '..', 'docs', 'CNAME')) else open(
            os.path.join(OUT, 'CNAME'), 'w').write('carmodreview.com\n')

    arts = []
    for fn in sorted(os.listdir(os.path.join(SRC, 'articles'))):
        if not fn.endswith('.md'):
            continue
        meta, body = read_doc(os.path.join(SRC, 'articles', fn))
        langs_md, _ = split_langs(body)
        arts.append(dict(meta=meta, langs=langs_md, file=fn))

    print(f'  parsed {len(arts)} articles')
    for a in arts:
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

    index_entries = []
    feed_items = []
    search_items = []
    for a in arts:
        meta = a['meta']
        meta['langs_all'] = set(a['langs'])
        cat = meta.get('category', 'Engine')
        catslug, catlabel, catkr, cates = CATEGORIES.get(cat, ('engine', cat, cat, cat))
        slug = meta.get('slug') or slugify(a['file'])
        date = str(meta.get('last_updated', '2026-11-01'))
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
            body_html.append(f'  <div class="byline">\n'
                             f'    <span>{UI[code]["published"]} {published}{revised}</span>\n'
                             f'  </div>\n')
            rel = '../' if not prefix else '../../'
            art_html = md2html(inner, rel)
            art_html = inject_photos(art_html, slug, code, rel,
                                     find_photos(PHOTO_ROOT, slug))
            body_html.append(art_html)
            if unver:
                body_html.append(
                    f'\n  <div class="unverified">\n'
                    f'    <h3>{UI[code]["verified"]}</h3>\n'
                    f'    {md2html(unver, rel)}\n'
                    f'  </div>\n')

            canon = altmap[code]
            shots = find_photos(PHOTO_ROOT, slug)
            hero_img = (f'{DOMAIN}/img/photos/{slug}/{os.path.basename(shots[0])}'
                        if shots else None)
            trail = [('Home', f'{DOMAIN}/{prefix}/index.html' if prefix else f'{DOMAIN}/'),
                     (catlabel if code == 'en' else cat,
                      f'{DOMAIN}{prefix}/{catslug}/index.html'),
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
            )
            outdir = os.path.join(OUT, *( ([prefix.strip('/')] if prefix else []) + [catslug] ))
            os.makedirs(outdir, exist_ok=True)
            with open(os.path.join(outdir, f'{slug}.html'), 'w', encoding='utf-8') as f:
                f.write(page)
    print(f'  wrote {len(arts)} articles x {len(LANGS)} langs')

    build_static_pages(index_entries)
    build_category_pages(arts)
    build_legacy_pages()
    build_redirects()
    build_sitemap(arts)
    build_feed(feed_items)
    build_search(search_items)


# Pages that moved. GitHub Pages is static and cannot issue a 301, so a page
# that changes its URL would simply 404 for anyone holding the old link. A stub
# at the old path forward to the new one instead.
REDIRECTS = {
    'suspension/silverado-rst-leveling-kit.html': 'silverado-leveling-kit.html',
    'kr/suspension/silverado-rst-leveling-kit.html': 'silverado-leveling-kit.html',
}


def build_redirects():
    """Emit meta-refresh stubs for URLs that have moved."""
    for old, new in REDIRECTS.items():
        dst = os.path.join(OUT, old)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        full = f'{DOMAIN}/{old.rsplit("/", 1)[0]}/{new}'
        # relative, so the stub works whether it is served from the domain root
        # or from a project subpath
        open(dst, 'w', encoding='utf-8').write(
            f'<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            f'<meta charset="UTF-8">\n'
            f'<title>Moved</title>\n'
            f'<meta name="robots" content="noindex, follow">\n'
            f'<link rel="canonical" href="{full}">\n'
            f'<meta http-equiv="refresh" content="0; url={new}">\n'
            f'</head>\n<body>\n'
            f'<p>This guide moved to <a href="{new}">{full}</a>.</p>\n'
            f'</body>\n</html>\n'
        )
    print(f'  redirects: {len(REDIRECTS)} stub(s)')


def build_legacy_pages():
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
        # these pages predate the generator and carry their own affiliate note
        # and reading-time byline; strip them so no page contradicts the
        # site-wide removal of both
        txt = re.sub(r'\s*<div class="disclosure">.*?</div>\s*', '\n', txt, flags=re.S)
        txt = re.sub(r'\s*<p[^>]*>\s*<strong>Affiliate note:</strong>.*?</p>\s*', '\n', txt, flags=re.S)
        txt = re.sub(r'\s*<p[^>]*>\s*We earn commissions?[^<]*</p>\s*', '\n', txt, flags=re.S)
        txt = re.sub(r'\s*<span>\d+\s+min read</span>', '', txt)
        open(dst, 'w', encoding='utf-8').write(inject_analytics(txt))
        n += 1
    if n:
        print(f'  carried forward {n} legacy page(s)')


def build_static_pages(index_entries):
    """homepage, about, methodology, contact, legal x3, 404"""
    meta_about, body_about = read_doc(os.path.join(SRC, 'about-us.md'))
    langs_about, _ = split_langs(body_about)
    meta_home, body_home = read_doc(os.path.join(SRC, 'homepage.md'))
    langs_home, _ = split_langs(body_home)

    for code, label, prefix in LANGS:
        rel = '../' if prefix else ''
        alts = {'en': f'{DOMAIN}/index.html'}
        for c, _, p in LANGS[1:]:
            alts[c] = f'{DOMAIN}{p}/index.html'
        if code in langs_home:
            md = clean_md(langs_home[code])
            # the dek is the first blockquote-ish bold line
            title = 'Car Mod Review'
            body = md2html(md, rel)
            body = inject_photos(body, 'home', code, rel,
                                 find_photos(PHOTO_ROOT, 'home'))
            page = render_page(
                lang=code, title=title if code != 'en' else
                'Car Mod Review — Car and Truck Parts, Checked Against the Specs',
                desc='Car and truck parts guides built from published specifications, '
                     'with every source named. No invented numbers and no unverified claims.',
                canonical=alts[code], body_html=body + '\n' + index_list_html(index_entries, code, rel),
                rel=rel, alts=alts)
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
                body_html=md2html(md, rel), rel=rel,
                alts={'en': f'{DOMAIN}/about.html', 'kr': f'{DOMAIN}/kr/about.html',
                      'es': f'{DOMAIN}/es/about.html'})
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
            page = render_page(
                lang='en', title='How we pick products | Car Mod Review',
                desc='Our selection method: how products are compared, ranked and sourced.',
                canonical=f'{DOMAIN}/methodology.html', body_html=inner, rel='')
            open(os.path.join(OUT, 'methodology.html'), 'w', encoding='utf-8').write(page)

    # legal pages x3 languages. The affiliate disclosure is deliberately not
    # generated: the site carries no affiliate links, so a disclosure page would
    # describe a relationship that does not exist.
    for fn, slug in (('privacy-policy.md', 'privacy-policy'),):
        meta, body = read_doc(os.path.join(SRC, 'legal', fn))
        langs, _ = split_langs(body)
        os.makedirs(os.path.join(OUT, 'legal'), exist_ok=True)
        for code, label, prefix in LANGS:
            if code not in langs:
                continue
            md = clean_md(langs[code])
            # these pages get their own <h1> below; drop any heading the
            # source carries (the shared trilingual one, or a per-language one)
            md = re.sub(r'^#[ \t]+[^\n]*\n', '', md, count=1).strip()
            title = {'en': 'Privacy Policy', 'kr': '개인정보 처리방침',
                     'es': 'Política de privacidad'}[code]
            alts = {'en': f'{DOMAIN}/legal/{slug}.html',
                    'kr': f'{DOMAIN}/kr/legal/{slug}.html',
                    'es': f'{DOMAIN}/es/legal/{slug}.html'}
            legal_desc = {
                ('privacy-policy', 'en'): 'What data Car Mod Review collects, how analytics are '
                    'handled, and how to request deletion.',
                ('privacy-policy', 'kr'): 'Car Mod Review가 수집하는 데이터, 분석 도구와 제휴 링크 처리 방식, 삭제 요청 방법.',
                ('privacy-policy', 'es'): 'Qué datos recoge Car Mod Review, cómo se manejan las '
                    'analíticas y los enlaces de afiliado, y cómo solicitar su eliminación.',
            }.get((slug, code), title)
            page = render_page(
                lang=code, title=f'{title} | Car Mod Review',
                desc=legal_desc, canonical=alts[code],
                body_html=f'  <h1>{html.escape(title)}</h1>\n' + md2html(md, '../../' if prefix else '../'),
                rel='../../' if prefix else '../', alts=alts, og_type='article')
            d = os.path.join(OUT, *( ([prefix.strip('/')] if prefix else []) + ['legal'] ))
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, f'{slug}.html'), 'w', encoding='utf-8').write(page)

    # contact + terms (new)
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
  <p><strong>Email:</strong> <a href="mailto:hello@carmodreview.com">hello@carmodreview.com</a></p>
  <p><strong>Products / PR:</strong> we do not accept paid placement. If you want a part
  considered for a guide, send the published specs and the manufacturer documentation,
  not a press release.</p>
  <p><strong>Partnerships:</strong> same address, subject line "partnership".</p>
"""
    page = render_page(lang='en', title='Contact | Car Mod Review',
                       desc='How to reach Car Mod Review, how corrections are handled, '
                            'and why we do not accept paid placement.',
                       canonical=f'{DOMAIN}/contact.html', body_html=contact_inner, rel='')
    open(os.path.join(OUT, 'contact.html'), 'w', encoding='utf-8').write(page)

    terms_inner = """
  <h1>Terms of Service</h1>
  <p><em>Last updated 4 November 2026.</em></p>
  <h2>What this site is</h2>
  <p>Car Mod Review publishes research and opinion about automotive parts. It is
  general information, not professional advice. Modification can affect your
  vehicle's safety, warranty, emissions compliance and resale value. Verify
  fitment and legality for your specific vehicle and jurisdiction before buying.</p>
  <h2>Accuracy</h2>
  <p>Prices, availability and specifications change without notice. Figures are
  reported as they appeared on the date stated on each page. We make no warranty
  that any listing, price or spec is current.</p>
  <h2>Liability</h2>
  <p>The site is provided "as is". To the extent permitted by law, Car Mod Review is
  not liable for damage to a vehicle, injury, failed inspection, voided warranty, or
  any other loss arising from use of the information here.</p>
  <h2>External links</h2>
  <p>We link to retailers and manufacturers we do not control and are not
  responsible for their content, pricing or policies.</p>
  <h2>Contact</h2>
  <p><a href="mailto:hello@carmodreview.com">hello@carmodreview.com</a></p>
"""
    page = render_page(lang='en', title='Terms of Service | Car Mod Review',
                       desc='The terms that govern use of Car Mod Review: accuracy, '
                            'accuracy, liability and external links.',
                       canonical=f'{DOMAIN}/legal/terms-of-service.html',
                       body_html=terms_inner, rel='../')
    open(os.path.join(OUT, 'legal', 'terms-of-service.html'), 'w', encoding='utf-8').write(page)

    # a 404 has nothing to index and nothing to rank; letting it be indexed
    # puts a dead URL in the results for the brand name
    nf = render_page(lang='en', title='Page not found | Car Mod Review',
                     desc='That page does not exist. Browse the guides index instead.',
                     canonical=f'{DOMAIN}/404.html', robots='noindex, follow',
                     body_html='  <h1>Not found</h1>\n  <p>That page does not exist. '
                               '<a href="index.html">Start from the homepage</a>.</p>', rel='')
    open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8').write(nf)
    print('  wrote static pages')


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
        out.append(f'  <h3><a href="{rel}{HUBLESS.get(catslug, catslug + "/index.html")}">'
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


def build_category_pages(arts):
    by_cat = {}
    for a in arts:
        by_cat.setdefault(a['meta'].get('category', 'Engine'), []).append(a)
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
            inner = (f'  <div class="kicker">Car Mod Review</div>\n'
                     f'  <h1>{html.escape(name)}</h1>\n'
                     + category_photo(cs, code, rel, PHOTO_ROOT) +
                     f'  <ul class="post-list">\n{"".join(rows)}  </ul>\n')
            alts = {'en': f'{DOMAIN}/{cs}/index.html',
                    'kr': f'{DOMAIN}/kr/{cs}/index.html',
                    'es': f'{DOMAIN}/es/{cs}/index.html'}
            trail = [('Home', f'{DOMAIN}/{prefix}/index.html' if prefix else f'{DOMAIN}/'),
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
                               jsonld=hub_jsonld, og_image=hub_img)
            d = os.path.join(OUT, *( ([prefix.strip('/')] if prefix else []) + [cs] ))
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page)
    print(f'  wrote {len(by_cat)} category hubs x3 langs')


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
    <nav class="nav">
      <a href="index.html">All posts</a>
      <a href="methodology.html">How we pick</a>
      <a href="search.html">Search</a>
      <a href="contact.html">Contact</a>
    </nav>
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
        inject_analytics(SEARCH_PAGE.replace("{domain}", DOMAIN)))
    print(f'  search: {len(payload)} guides indexed')


def build_feed(items):
    """RSS 2.0 feed of the English guides, newest first.

    Every page links to this at /feed.xml, so it has to exist — a rel=alternate
    pointing at a 404 is worse than no link at all. Dates are the real
    datePublished values, not the build date.
    """
    def rfc822(d):
        return datetime.datetime.strptime(d, '%Y-%m-%d').strftime('%a, %d %b %Y 00:00:00 +0000')

    items = sorted(items, key=lambda i: (i['published'], i['url']), reverse=True)
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
    urls = []
    today = datetime.date.today().isoformat()
    for a in arts:
        cs = CATEGORIES.get(a['meta'].get('category'), ('engine',))[0]
        slug = a['meta'].get('slug') or slugify(a['file'])
        d = str(a['meta'].get('last_updated', today))
        for code, _, prefix in LANGS:
            if code in a['langs']:
                urls.append((f'{DOMAIN}{prefix}/{cs}/{slug}.html', d))
    # Static pages do not all exist in every language — about, methodology,
    # contact and terms are per-language authored, not generated. List a URL only
    # when build_static_pages actually writes it, or the sitemap advertises 404s.
    for path in ('index.html', 'about.html', 'methodology.html', 'contact.html',
                 'legal/privacy-policy.html',
                 'legal/terms-of-service.html'):
        for code, _, prefix in LANGS:
            if os.path.exists(os.path.join(OUT, *(prefix.strip('/').split('/')
                                                 if prefix else []), path)):
                urls.append((f'{DOMAIN}{prefix}/{path}', today))
    cats = sorted({CATEGORIES.get(a['meta'].get('category'), ('engine',))[0] for a in arts})
    for c in cats:
        for code, _, prefix in LANGS:
            urls.append((f'{DOMAIN}{prefix}/{c}/index.html', today))

    # hand-written pages carried forward from the pre-generator site
    urls.append((f'{DOMAIN}/cold-air-intakes/', '2026-10-30'))
    urls.append((f'{DOMAIN}/cold-air-intakes/best-cold-air-intake-f150-50l.html', '2026-10-30'))

    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, d in urls:
        sm.append(f'  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>')
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
