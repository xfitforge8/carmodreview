# Switching on affiliate programs

Everything is built. The only thing missing is the IDs, which come from
accounts that have to be in your name.

## What I need from you

Create the accounts, then send me **only these four things**. Nothing else.

| Program | What to send | Where it lives |
|---|---|---|
| RealTruck | your Impact **tracking link** | Impact dashboard → Campaigns → RealTruck → Links |
| Summit Racing | your Impact **tracking link** | Impact dashboard → Campaigns → Summit Racing → Links |
| Amazon Associates | your **Store ID**, looks like `mytag-20` | Associates Central → Account Settings |
| eBay Partner Network | your **campaign ID** (a number) | EPN portal → Campaigns |

Plus, if you get one: AmericanTrucks' tracking parameter.

That is it. Do **not** paste passwords, tax IDs, bank details or the full
text of any agreement into this session. An affiliate ID is not a secret — it
appears in the public HTML of every link — but nothing else in those accounts
should ever come near a chat window.

## What happens then

For each program, one entry in `content/affiliate.json` gets its `id` filled
in and `enabled` flipped to `true`. Then `python3 build.py` tags every
matching link and the disclosure block appears automatically. That is the
whole change.

I will not flip a program on before its approval is real. The build refuses
to emit `rel="sponsored"` for a merchant with no agreement, because that is a
false statement to Google and to the reader.

## Why the file is in the repo, not in my head

`content/affiliate.json` is the single source of truth. It is readable, it is
version-controlled, and the disclosure page reads from it so the site cannot
claim a relationship it does not have.

## How each network builds a link

The `link_format` field exists because guessing here fails silently: the site
looks correctly configured and every click earns nothing.

| Format | Produces | Used by |
|---|---|---|
| `query_param` | `url?param=id` | Impact, AmericanTrucks, Amazon |
| `template` | a wrapper URL with `{url}` and `{id}` | eBay rover links |

**Amazon** takes `?tag=mytag-20` in the query string. It is *not* a path
segment — a path form is not a valid Amazon URL.

**eBay** issues "rover" wrapper links. Paste the whole wrapper into
`template`, leaving `{url}` as a literal placeholder:

```
https://rover.ebay.com/rover/1/711-53200-19255-0/1?campid={id}&toolid=10001&mpre={url}
```

**Impact** may give you a complete tracking URL from its dashboard rather than
a single parameter. If it does, use `link_format: "template"` and paste that
URL with `{url}` where the destination belongs.

## Verifying it worked

```
python3 build.py
grep -c 'utm_source=YOURID' docs/suspension/silverado-leveling-kit.html
grep -o 'rel="sponsored[^"]*"' docs/suspension/silverado-leveling-kit.html | head -1
```

The first should be 3 on that page. The second should read
`rel="sponsored nofollow noopener"`.

## The trap that was fixed

Article product cards are written as literal HTML inside the markdown, so they
never passed through the normal link handler. With an ID configured they would
have gone out untagged — the site would have looked correct and earned nothing.
Tagging now happens inside `md2html()`, which every markdown body goes through.

`rel="sponsored"` is also decided per host rather than globally. If RealTruck
approves the site but AmericanTrucks has not, AmericanTrucks links stay
`rel="nofollow"`. A test covers both cases.
