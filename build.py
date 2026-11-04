#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — turn ~/carmodreview/content/*.md into a static site in ~/carmodreview/docs/.

No framework, no build step in CI. Run locally, commit the output.

Design contract (matches the existing hand-written pages):
  * English is the primary route at /<category>/<slug>.html
  * Korean and Spanish are alternates at /kr/... and /es/...
  * Every page: affiliate disclosure above the fold, "What we could not verify"
    block before the footer, real publish dates only.
"""
import os, re, json, html, shutil, datetime, sys

import markdown
import yaml

ROOT = os.path.expanduser('~/carmodreview')
SRC = os.path.join(ROOT, 'content')
OUT = os.path.join(ROOT, 'docs')
DOMAIN = 'https://carmodreview.com'

CATEGORIES = {
    'Suspension':      ('suspension',      'Suspension',      '서스펜션',      'Suspensión'),
    'Wheels & Tires':  ('wheels-tires',    'Wheels & Tires',  '휠 & 타이어',   'Llantas y neumáticos'),
    'Engine':          ('engine',          'Engine & Intake', '엔진 & 인테이크', 'Motor y admisión'),
    'Exhaust':         ('exhaust',         'Exhaust',         '배기',          'Escape'),
    'Brakes':          ('brakes',          'Brakes',          '브레이크',      'Frenos'),
    'Tuning':          ('tuning',          'Tuning',          '튜닝',          'Reprogramación'),
}

LANGS = [('en', 'EN', ''), ('kr', 'KR', '/kr'), ('es', 'ES', '/es')]

UI = {
    'en': dict(all_posts='All posts', how='How we pick', home='Home',
               published='Published', minread='min read', verified='What we could not verify',
               disc_title='Affiliate note',
               disc_body=('We earn commissions from qualifying purchases made through links '
                          'on this page. Commission never decides which products we pick or '
                          'where they rank.'),
               nav_cats='Categories', other='Read this in', on='on'),
    'kr': dict(all_posts='모든 글', how='선정 기준', home='홈',
               published='발행일', minread='분 소요', verified='확인하지 못한 것',
               disc_title='제휴 고지',
               disc_body=('이 페이지의 링크를 통해 구매가 이루어지면 저희는 수수료를 받습니다. '
                          '수수료는 어떤 제품을 고르는지, 순위가 어떻게 되는지를 결정하지 않습니다.'),
               nav_cats='카테고리', other='다른 언어', on=''),
    'es': dict(all_posts='Todas las guías', how='Cómo elegimos', home='Inicio',
               published='Publicado', minread='min de lectura', verified='Lo que no pudimos verificar',
               disc_title='Nota de afiliación',
               disc_body=('Ganamos comisiones por compras realizadas a través de los enlaces de '
                          'esta página. La comisión nunca decide qué productos elegimos ni en qué '
                          'posición se clasifican.'),
               nav_cats='Categorías', other='Leer en', on=''),
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
    it, so we never emit a link to a page that does not exist.
    """
    hubless = {'tuning': 'engine/ecu-tuning-explained.html'}

    def cat_sub(m):
        slug = m.group(1)
        if slug in hubless:
            return f'href="{rel}{hubless[slug]}"'
        return f'href="{rel}{slug}/index.html"'
    html_text = re.sub(r'href="cat:([a-z0-9-]+)"', cat_sub, html_text)
    html_text = re.sub(r'href="page:([a-z0-9/.-]+)"', r'href="' + rel + r'\1.html"', html_text)
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
<link rel="canonical" href="{canonical}">
{alt_links}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Car Mod Review">
<meta property="og:locale" content="{og_locale}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{domain}/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{rel}style.css">
{jsonld}
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
      <a href="{rel}contact.html">Contact</a>
    </nav>
  </div>
</header>

<main class="wrap">
<article>
{body}
</article>
</main>

<footer>
  <div class="wrap">
    <p><strong>Car Mod Review</strong> &mdash; car parts coverage that states its
    sources and says when it doesn't know.</p>
    <p>We earn commissions from links on this site. We do not accept payment for placement.</p>
    <p>
      <a href="{rel}methodology.html">{how}</a> &middot;
      <a href="{rel}contact.html">Contact</a> &middot;
      <a href="{rel}about.html">About</a> &middot;
      <a href="{rel}legal/affiliate-disclosure.html">Affiliate disclosure</a> &middot;
      <a href="{rel}legal/privacy-policy.html">Privacy</a> &middot;
      <a href="{rel}legal/terms-of-service.html">Terms</a>
    </p>
    <p class="lang-switch">{other}: <a href="{alt_en}">English</a> &middot;
      <a href="{alt_kr}">한국어</a> &middot; <a href="{alt_es}">Español</a></p>
  </div>
</footer>

</body>
</html>
"""

TAGLINE = {
    'en': 'Car parts, tested against the marketing',
    'kr': '마케팅이 아니라 실물로 검증하는 자동차 부품',
    'es': 'Piezas de auto puestas a prueba contra el marketing',
}


def render_page(*, lang, title, desc, canonical, body_html, rel, jsonld='',
                og_type='website', alts=None):
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
        canonical=canonical, alt_links=alt, og_type=og_type, og_locale=OG_LOCALE[lang],
        domain=DOMAIN, rel=rel, jsonld=jsonld, body=body_html,
        tagline=TAGLINE[lang], all_posts=ui['all_posts'], how=ui['how'], other=ui['other'],
        alt_en=alts.get('en', canonical), alt_kr=alts.get('kr', canonical),
        alt_es=alts.get('es', canonical),
    )


def disclosure_html(lang):
    ui = UI[lang]
    return (f'  <div class="disclosure">\n'
            f'    <strong>{ui["disc_title"]}:</strong> {ui["disc_body"]}\n'
            f'  </div>\n')


def article_jsonld(title, desc, canonical, date, section, lang):
    return ('<script type="application/ld+json">\n' + json.dumps({
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': title,
        'description': desc,
        'datePublished': date,
        'dateModified': date,
        'inLanguage': HTML_LANG[lang],
        'articleSection': section,
        'image': [f'{DOMAIN}/og.png'],
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
        for asset in ('style.css', 'og.png'):
            p = os.path.join(prev, asset)
            if os.path.exists(p):
                shutil.copy(p, os.path.join(OUT, asset))

    index_entries = []
    for a in arts:
        meta = a['meta']
        meta['langs_all'] = set(a['langs'])
        cat = meta.get('category', 'Engine')
        catslug, catlabel, catkr, cates = CATEGORIES.get(cat, ('engine', cat, cat, cat))
        slug = meta.get('slug') or slugify(a['file'])
        date = str(meta.get('last_updated', '2026-11-01'))
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
            body_html.append(f'  <div class="byline">\n'
                             f'    <span>{UI[code]["published"]} {date}</span>\n'
                             f'    <span>{words:,} words</span>\n'
                             f'    <span>{mins} {UI[code]["minread"]}</span>\n'
                             f'  </div>\n')
            body_html.append(disclosure_html(code))
            body_html.append(md2html(inner, '../' if not prefix else '../../'))
            if unver:
                body_html.append(
                    f'\n  <div class="unverified">\n'
                    f'    <h3>{UI[code]["verified"]}</h3>\n'
                    f'    {md2html(unver, "../" if not prefix else "../../")}\n'
                    f'  </div>\n')

            rel = '../' if not prefix else '../../'
            canon = altmap[code]
            page = render_page(
                lang=code, title=title, desc=dek or title, canonical=canon,
                body_html='\n'.join(body_html), rel=rel,
                jsonld=article_jsonld(title, dek or title, canon, date,
                                      catlabel if code == 'en' else cat, code),
                og_type='article', alts=altmap,
            )
            outdir = os.path.join(OUT, *( ([prefix.strip('/')] if prefix else []) + [catslug] ))
            os.makedirs(outdir, exist_ok=True)
            with open(os.path.join(outdir, f'{slug}.html'), 'w', encoding='utf-8') as f:
                f.write(page)
    print(f'  wrote {len(arts)} articles x {len(LANGS)} langs')

    build_static_pages(index_entries)
    build_category_pages(arts)
    build_legacy_pages()
    build_sitemap(arts)


def build_legacy_pages():
    """Carry the hand-written pages that predate this generator forward verbatim.

    These are real published articles, not generated output; rmtree at the top
    of build() would otherwise delete them.
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
        shutil.copy(src, dst)
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
            page = render_page(
                lang=code, title=title if code != 'en' else
                'Car Mod Review — Car, Truck & SUV Parts, Ranked',
                desc='Car, truck and SUV parts ranked three ways: price, design, all-round value. '
                     'We name our sources and say when we do not know.',
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
                desc='Who writes CarModReview, what vehicle we test on, and what we will not do.',
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
            page = render_page(
                lang='en', title='How we pick products | Car Mod Review',
                desc='Our selection method: how products are compared, ranked and sourced.',
                canonical=f'{DOMAIN}/methodology.html', body_html=inner, rel='')
            open(os.path.join(OUT, 'methodology.html'), 'w', encoding='utf-8').write(page)

    # legal pages x3 languages
    for fn, slug in (('affiliate-disclosure.md', 'affiliate-disclosure'),
                     ('privacy-policy.md', 'privacy-policy')):
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
            title = {'en': 'Affiliate Disclosure' if slug == 'affiliate-disclosure' else 'Privacy Policy',
                     'kr': '제휴 고지' if slug == 'affiliate-disclosure' else '개인정보 처리방침',
                     'es': 'Divulgación de afiliación' if slug == 'affiliate-disclosure' else 'Política de privacidad'}[code]
            alts = {'en': f'{DOMAIN}/legal/{slug}.html',
                    'kr': f'{DOMAIN}/kr/legal/{slug}.html',
                    'es': f'{DOMAIN}/es/legal/{slug}.html'}
            page = render_page(
                lang=code, title=f'{title} | Car Mod Review',
                desc=title, canonical=alts[code],
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
  <p><strong>Affiliate and partnerships:</strong> same address, subject line "partnership".</p>
"""
    page = render_page(lang='en', title='Contact | Car Mod Review',
                       desc='How to reach CarModReview, and how corrections are handled.',
                       canonical=f'{DOMAIN}/contact.html', body_html=contact_inner, rel='')
    open(os.path.join(OUT, 'contact.html'), 'w', encoding='utf-8').write(page)

    terms_inner = """
  <h1>Terms of Service</h1>
  <p><em>Last updated 1 November 2026.</em></p>
  <h2>What this site is</h2>
  <p>Car Mod Review publishes research and opinion about automotive parts. It is
  general information, not professional advice. Modification can affect your
  vehicle's safety, warranty, emissions compliance and resale value. Verify
  fitment and legality for your specific vehicle and jurisdiction before buying.</p>
  <h2>Affiliate relationships</h2>
  <p>Some outbound links are affiliate links. If you buy through them we may earn a
  commission at no extra cost to you. See our
  <a href="affiliate-disclosure.html">affiliate disclosure</a>.</p>
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
                       desc='Terms governing use of CarModReview.',
                       canonical=f'{DOMAIN}/legal/terms-of-service.html',
                       body_html=terms_inner, rel='../')
    open(os.path.join(OUT, 'legal', 'terms-of-service.html'), 'w', encoding='utf-8').write(page)

    nf = render_page(lang='en', title='Page not found | Car Mod Review',
                     desc='That page does not exist.', canonical=f'{DOMAIN}/404.html',
                     body_html='  <h1>Not found</h1>\n  <p>That page does not exist. '
                               '<a href="index.html">Start from the homepage</a>.</p>', rel='')
    open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8').write(nf)
    print('  wrote static pages')


def index_list_html(index_entries, code, rel):
    by_cat = {}
    for e in index_entries:
        if code not in (e[7].get('langs_all') or set()):
            continue
        by_cat.setdefault(e[3], []).append(e)
    out = [f'\n  <h2>{UI[code]["nav_cats"]}</h2>\n']
    for catslug, items in by_cat.items():
        label = items[0][4] if code == 'en' else (items[0][5] if code == 'kr' else items[0][6])
        out.append(f'  <h3><a href="{rel}{catslug}/index.html">{html.escape(label)}</a></h3>\n')
        out.append('  <ul class="post-list">\n')
        for e in items:
            date, slug, cat, cs, cl, ck, ce, meta = e
            t = (meta.get('title') or {}).get(code) or (meta.get('title') or {}).get('en')
            t = re.sub(r'^#+\s*', '', t or slug).strip().strip('"')
            out.append(f'    <li><a href="{rel}{cs}/{slug}.html">{html.escape(t)}</a>'
                       f'<div class="meta">{date}</div></li>\n')
        out.append('  </ul>\n')

    if code == 'en':
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
                     f'  <ul class="post-list">\n{"".join(rows)}  </ul>\n')
            alts = {'en': f'{DOMAIN}/{cs}/index.html',
                    'kr': f'{DOMAIN}/kr/{cs}/index.html',
                    'es': f'{DOMAIN}/es/{cs}/index.html'}
            page = render_page(lang=code, title=f'{name} | Car Mod Review',
                               desc=f'{name} guides, ranked and sourced.',
                               canonical=alts[code], body_html=inner, rel=rel, alts=alts)
            d = os.path.join(OUT, *( ([prefix.strip('/')] if prefix else []) + [cs] ))
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page)
    print(f'  wrote {len(by_cat)} category hubs x3 langs')


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
    for path in ('index.html', 'about.html', 'methodology.html', 'contact.html',
                 'legal/affiliate-disclosure.html', 'legal/privacy-policy.html',
                 'legal/terms-of-service.html'):
        urls.append((f'{DOMAIN}/{path}', today))
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
