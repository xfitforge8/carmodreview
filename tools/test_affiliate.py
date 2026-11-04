"""Regression tests for affiliate link handling.

Run: python3 tools/test_affiliate.py
Covers the two failure modes that are silent in production:
  1. a live program's links going out untagged
  2. an unapproved merchant's links being marked rel="sponsored"
"""
import json, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

CFG = 'content/affiliate.json'
ORIGINAL = open(CFG, encoding='utf-8').read()

def set_programs(enabled_names, ids=None):
    cfg = json.loads(ORIGINAL)
    ids = ids or {}
    for p in cfg['programs']:
        p['enabled'] = p['name'] in enabled_names
        p['id'] = ids.get(p['name'], 'TESTID123')
        if p['link_format'] == 'template':
            p['template'] = ('https://rover.ebay.com/rover/1/711-53200-19255-0/1'
                             '?campid={id}&toolid=10001&mpre={url}')
            p['template_host'] = 'rover.ebay.com'
    json.dump(cfg, open(CFG, 'w', encoding='utf-8'), indent=2)
    sys.modules.pop('build', None)
    import build
    return build

AT = 'https://www.americantrucks.com/readylift-kit.html'
RT = 'https://realtruck.com/p/cover/'
AM = 'https://www.amazon.com/dp/B00X?th=1'
EB = 'https://www.ebay.com/itm/123?x=1'
PLAIN = 'https://example.com/page'

fails = []
def check(label, cond, detail=''):
    print(('  PASS  ' if cond else '  FAIL  ') + label + (('  <- ' + detail) if not cond and detail else ''))
    if not cond: fails.append(label)

try:
    print('\nnothing enabled (shipped state)')
    b = set_programs([])
    for name, u in [('AT', AT), ('RT', RT), ('AM', AM), ('EB', EB)]:
        check(f'{name} url untouched', b.affiliate_url(u) == u, b.affiliate_url(u))
        check(f'{name} not sponsored', 'sponsored' not in b.affiliate_rel(u), b.affiliate_rel(u))
    check('disclosure not claimed', b.affiliate_active() is False)

    print('\nonly RealTruck enabled')
    b = set_programs(['RealTruck'])
    check('RealTruck tagged', 'irclickid=TESTID123' in b.affiliate_url(RT), b.affiliate_url(RT))
    check('RealTruck sponsored', 'sponsored' in b.affiliate_rel(RT), b.affiliate_rel(RT))
    check('AmericanTrucks NOT tagged', b.affiliate_url(AT) == AT, b.affiliate_url(AT))
    check('AmericanTrucks NOT sponsored', 'sponsored' not in b.affiliate_rel(AT), b.affiliate_rel(AT))
    check('AmericanTrucks still nofollow', 'nofollow' in b.affiliate_rel(AT), b.affiliate_rel(AT))

    print('\nall enabled')
    b = set_programs(['RealTruck','Summit Racing','AmericanTrucks','Amazon Associates','eBay Partner Network'],
                     {'Amazon Associates': 'mytag-20'})
    check('Amazon uses ?tag=', 'tag=mytag-20' in b.affiliate_url(AM), b.affiliate_url(AM))
    check('Amazon keeps existing params', 'th=1' in b.affiliate_url(AM), b.affiliate_url(AM))
    check('Amazon not a path segment', '/tag=' not in b.affiliate_url(AM), b.affiliate_url(AM))
    check('eBay wraps in rover', b.affiliate_url(EB).startswith('https://rover.ebay.com/'), b.affiliate_url(EB))
    check('eBay destination encoded', 'mpre=https%3A%2F%2F' in b.affiliate_url(EB), b.affiliate_url(EB))
    check('non-merchant untouched', b.affiliate_url(PLAIN) == PLAIN, b.affiliate_url(PLAIN))
    check('non-merchant no rel pollution', b.affiliate_rel(PLAIN) == 'rel="noopener" target="_blank"', b.affiliate_rel(PLAIN))

    print('\nidempotency')
    for name, u in [('AT', AT), ('RT', RT), ('AM', AM), ('EB', EB)]:
        once = b.affiliate_url(u)
        check(f'{name} tagging twice is stable', b.affiliate_url(once) == once, b.affiliate_url(once))

    print('\nmd2html tags literal HTML product cards')
    import build as bb
    body = f'<p class="buyrow"><a class="buy" href="{AT}" rel="nofollow noopener">See it</a></p>'
    out = bb.md2html(body, '../')
    check('card url tagged', 'utm_source=' in out, out)
    check('card rel sponsored', 'rel="sponsored' in out, out)
finally:
    open(CFG, 'w', encoding='utf-8').write(ORIGINAL)

print('\n' + ('ALL PASS' if not fails else f'{len(fails)} FAILED: ' + ', '.join(fails)))
sys.exit(1 if fails else 0)
