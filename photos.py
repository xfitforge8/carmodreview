#!/usr/bin/env python3
"""Photograph helpers for CarModReview.

Every figure on this site is a real photograph. Nothing here is drawn, generated
or synthesised, and no illustration is ever passed off as a photo of a specific
vehicle. Sources are licensed for commercial use and are credited in the
caption, because a caption that names its source is the whole point.

Photos live in content/photos/<slug>/ and are picked up at build time. A photo
only appears if the file exists on disk, so the build never emits a broken <img>.
Captions come from a sidecar <name>.txt beside the image; with no sidecar the
photo appears uncaptioned rather than with an invented description.
"""
import os
import re
import html
import shutil
import subprocess
import functools

IMG_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.avif')

# Photos display at no more than 620px tall and one column wide, so 1600px
# originals at 300-500 KB each send every visitor far more pixels than any of
# them sees. GitHub Pages is static and does no per-request work, so the build
# is the only place this can be fixed.
MAX_EDGE = 1200
JPEG_QUALITY = 72
WEBP_QUALITY = 78
_PUBLISHED = {}

# cwebp, when it exists, cuts these photos by around 59% at a quality that
# still beats the JPEG they replace -- measured across all 39 images, not
# assumed. Cloudflare's own field data put the home hero as the worst LCP
# element on the site at 4,439ms, so the saving is the point rather than a
# nice-to-have. When cwebp is absent the build still publishes the JPEG and
# the <picture> picks it up, so this stays an optimisation, not a dependency.
CWEBP = shutil.which('cwebp')
# AVIF encodes far smaller still, but nothing in this environment can write it
# and a format we cannot verify is not one to serve.
WEBP_EXT = '.webp'

# Set by build.py to content/photos, and to docs/img/photos. Width and height
# have to describe the file the browser actually downloads, which is the
# resized copy, not the original on disk in content/.
SOURCE_ROOT = None
OUT_ROOT = None


def configure(source_root, out_root):
    global SOURCE_ROOT, OUT_ROOT
    SOURCE_ROOT, OUT_ROOT = source_root, out_root


def _published_path(src):
    """Where this photo lands in the built site."""
    if not (SOURCE_ROOT and OUT_ROOT):
        return src
    return os.path.join(OUT_ROOT, os.path.relpath(src, SOURCE_ROOT))


@functools.lru_cache(maxsize=None)
def _dimensions(path):
    """Intrinsic pixel size of an image, so <img> can reserve the right box.

    Emitting a width/height that does not match the file is worse than emitting
    none: the browser reserves the wrong space and the text jumps on load. Read
    the real size instead. sips ships with macOS; on any other platform, or for
    a format it cannot read, fall back to omitting the attributes entirely.
    """
    try:
        out = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', path],
                             capture_output=True, text=True, timeout=10).stdout
        w = re.search(r'pixelWidth:\s*(\d+)', out)
        h = re.search(r'pixelHeight:\s*(\d+)', out)
        if w and h:
            return int(w.group(1)), int(h.group(1))
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def publish_image(src, dst):
    """Write an image to dst, downscaled and recompressed when that saves bytes.

    Falls back to a plain copy if sips is missing or the result is not smaller,
    so a build on another platform still produces every figure.

    Also writes a WebP beside it when cwebp is available. The WebP is an extra
    output, never a replacement: the JPEG half of the <picture> is what every
    crawler and every element-reading social scraper will find, and og:image
    still points at the JPEG because Facebook's crawler does not fetch WebP
    reliably.
    """
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if src in _PUBLISHED:
        return

    # A WebP source stays WebP. Running it through `sips -s format jpeg` would
    # put JPEG bytes in a file still named .webp, which the server types as
    # image/webp and the browser then fails to decode.
    if os.path.splitext(src)[1].lower() == WEBP_EXT:
        _write_webp(src, dst)
        _PUBLISHED[src] = dst
        return

    try:
        # resize AND recompress in one pass: -Z alone keeps the original JPEG
        # quality, which is why it barely moved the byte count.
        cmd = ['sips', '-Z', str(MAX_EDGE),
               '-s', 'format', 'jpeg', '-s', 'formatOptions', str(JPEG_QUALITY),
               src, '--out', dst]
        subprocess.run(cmd, capture_output=True, timeout=60, check=True)
        if not os.path.exists(dst) or os.path.getsize(dst) >= os.path.getsize(src):
            raise OSError('no saving')
    except (OSError, subprocess.SubprocessError):
        shutil.copy(src, dst)
    if CWEBP:
        webp = os.path.splitext(dst)[0] + WEBP_EXT
        try:
            subprocess.run([CWEBP, '-quiet', '-q', str(WEBP_QUALITY),
                            '-resize', str(MAX_EDGE), '0', dst, '-o', webp],
                           capture_output=True, timeout=60, check=True)
            # A WebP larger than the JPEG it would replace is not worth the
            # <source> element; drop it so the browser keeps the JPEG.
            if not os.path.exists(webp) or os.path.getsize(webp) >= os.path.getsize(dst):
                if os.path.exists(webp):
                    os.remove(webp)
        except (OSError, subprocess.SubprocessError):
            if os.path.exists(webp):
                os.remove(webp)
    _PUBLISHED[src] = dst


def _write_webp(src, dst):
    """Write src to dst as WebP, downscaled to MAX_EDGE, or copy if that fails.

    cwebp writes to a temp name and then moves into place. Writing straight to
    dst is what lost every product photograph once already: cwebp refuses to
    overwrite its own input, and the recovery path removed the file it had just
    produced, leaving the build with <img> tags pointing at nothing.
    """
    if not CWEBP:
        shutil.copy(src, dst)
        return
    tmp = dst + '.tmp.webp'
    try:
        subprocess.run([CWEBP, '-quiet', '-q', str(WEBP_QUALITY),
                        '-resize', str(MAX_EDGE), '0', src, '-o', tmp],
                       capture_output=True, timeout=60, check=True)
        if os.path.exists(tmp) and os.path.getsize(tmp) > 0:
            os.replace(tmp, dst)
            return
    except (OSError, subprocess.SubprocessError):
        pass
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    shutil.copy(src, dst)


def find_photos(photo_root, slug):
    """Real photographs on disk for this slug, in filename order."""
    d = os.path.join(photo_root, slug)
    if not os.path.isdir(d):
        return []
    files = [f for f in sorted(os.listdir(d)) if f.lower().endswith(IMG_EXT)]
    return [os.path.join(d, f) for f in files]


def _caption_for(path):
    """Sidecar caption, or '' — never an invented one."""
    cap_path = os.path.splitext(path)[0] + '.txt'
    if os.path.exists(cap_path):
        return open(cap_path, encoding='utf-8').read().strip()
    return ''


def photo_html(paths, slug, code, rel, hero=False):
    """Photo figures for images that actually exist on disk.

    English carries the photography; the KR and ES pages keep their text and
    omit the figures rather than captioning a photo in a language it was not
    written in.
    """
    out = []
    for i, p in enumerate(paths):
        name = os.path.basename(p)
        cap = _caption_for(p)
        alt = cap or name
        role = ' fig--hero' if (hero and i == 0) else ''
        fig_cap = f'\n    <figcaption>{html.escape(cap)}</figcaption>' if cap else ''
        size = _dimensions(_published_path(p))
        dims = f' width="{size[0]}" height="{size[1]}"' if size else ''
        # Reserve the box from the file's real ratio even before the CSS lands.
        # width/height attributes alone let the browser guess during the window
        # between parsing the <img> and applying the stylesheet; an inline
        # aspect-ratio makes the reserved box correct under the actual rule
        # (.fig--photo caps height at 620px and lets width follow), so the text
        # below cannot be pushed down when the stylesheet resolves. Cloudflare
        # field data recorded 0.2744 CLS on this exact hero element -- a fail.
        ratio = (f' style="aspect-ratio:{size[0]}/{size[1]}"' if size else '')
        img_src = f'{rel}img/photos/{slug}/{name}'
        webp_name = os.path.splitext(name)[0] + WEBP_EXT
        webp_rel = f'{rel}img/photos/{slug}/{webp_name}'
        has_webp = os.path.exists(_published_path(p)[:-len(os.path.splitext(p)[1])] + WEBP_EXT) \
            if size else False
        # <picture> with a WebP source and a JPEG <img> fallback. The <img>
        # keeps the class, the alt, the dimensions and the loading hint so
        # anything that reads the tag still finds a complete image.
        src_set = (f'<source type="image/webp" srcset="{webp_rel}">'
                   if has_webp else '')
        out.append(
            f'\n  <figure class="fig fig--photo{role}">\n'
            f'    <picture>{src_set}'
            f'<img src="{img_src}" alt="{html.escape(alt)}" '
            # The hero image is the Largest Contentful Paint element: the browser
            # measures LCP when it finishes painting it. loading="lazy" tells the
            # browser to defer it until after layout, which delays LCP by roughly
            # the image's full download time. Every other photo stays lazy so it
            # does not compete for bandwidth with the hero.
            f'{"fetchpriority=\"high\"" if (hero and i == 0) else "loading=\"lazy\""}'
            f'{dims}{ratio} decoding="async"></picture>'
            f'{fig_cap}\n'
            f'  </figure>\n'
        )
    return ''.join(out)


def category_photo(category_slug, code, rel, photo_root):
    """One photograph for a category hub, or '' when the hub has none yet.

    A hub borrows the lead photo of its most representative article, so there is
    one copy of each image on disk rather than a duplicate per category.
    """
    if code != 'en':
        return ''
    for slug in CATEGORY_SOURCE.get(category_slug, []):
        shots = find_photos(photo_root, slug)
        if shots:
            return photo_html(shots[:1], slug, code, rel)
    return ''


# Which article's photo represents each hub, in order of preference.
CATEGORY_SOURCE = {
    'wheels-tires': ['wheels-buying-guide', '4x4-tire-buying-guide'],
    'suspension': ['leveling-kit-guide', 'suspension-upgrades-guide'],
    'engine': ['cold-air-intake-guide', 'turbo-four-cold-air-intake'],
    'exhaust': ['exhaust-systems-explained'],
    'brakes': ['brake-pads-rotors-guide'],
    'tuning': ['ecu-tuning-explained'],
    # Both were missing, so these were the only two hubs with no photograph on
    # them at all. Electrical has body photography; Tonneau has none -- its
    # article is about four specific covers -- and falls back to the listing
    # shot of the first one, in build.py.
    'electrical': ['auto-up-windows'],
    'tonneau': ['tonneau-covers-explained'],
}


def inject_photos(body_html, slug, code, rel, photo_paths):
    """Place photographs through an article body.

    The first photo is the hero and sits above the opening prose. The rest are
    distributed one per section heading so a long guide never runs far without
    a visual. Guides use <h3> for sections, so both h2 and h3 are split points.
    """
    if not photo_paths:
        return body_html

    # English only: the sidecar captions are written in English.
    if code != 'en':
        return body_html

    hero_html = photo_html(photo_paths[:1], slug, code, rel, hero=True)
    rest = photo_html(photo_paths[1:], slug, code, rel)

    figs = [f for f in re.split(r'(?=<figure)', rest) if f.strip()]
    if not figs:
        return hero_html + body_html

    parts = re.split(r'(?=<h[23][\s>])', body_html)
    if len(parts) < 2:
        return hero_html + body_html + ''.join(figs)

    # parts[0] is the lede (no heading); parts[1:] each begin with a heading.
    # A figure goes at the END of a section, never in the gap before a heading:
    # that gap is directly below the hero, and putting one there stacks two
    # photos above the first word of the article.
    out = [hero_html + parts[0]]
    queue = list(figs)
    for part in parts[1:]:
        out.append(part)
        if queue:
            out.append(queue.pop(0))
    out.extend(queue)
    return ''.join(out)
