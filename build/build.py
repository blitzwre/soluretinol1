#!/usr/bin/env python3
"""Packager for the SoluRetinol CheckoutChamp delivery (PARTNER-DELIVERY-KIT.md)."""
import re, os, shutil, base64, json, urllib.parse

SRC   = "/Users/mogulmurray/Desktop/swipe"
BUILD = os.path.join(SRC, "build")
OUT   = os.path.join(SRC, "soluretinol")
IMG   = os.path.join(OUT, "images")

# ----------------------------------------------------------------- tag spans
SKIP = re.compile(r'<(script|style)\b[^>]*>.*?</\1\s*>|<!--.*?-->', re.S | re.I)

def masked(h):
    out = bytearray(h, 'utf-8', 'surrogatepass') if False else list(h)
    for m in SKIP.finditer(h):
        for i in range(m.start(), m.end()):
            out[i] = ' '
    return ''.join(out)

def span(hm, start, tag):
    o_re = re.compile(r'<%s\b' % tag, re.I)
    c_re = re.compile(r'</%s\s*>' % tag, re.I)
    gt = hm.find('>', start)
    if gt == -1: return None
    depth, pos = 1, gt + 1
    while depth:
        o = o_re.search(hm, pos); c = c_re.search(hm, pos)
        if not c: return None
        if o and o.start() < c.start():
            depth += 1; pos = o.end()
        else:
            depth -= 1; pos = c.end()
    return (start, pos)

def drop_elements(h, pattern, tag, label):
    n = 0
    while True:
        hm = masked(h)
        m = re.search(pattern, hm)
        if not m: break
        sp = span(hm, m.start(), tag)
        if not sp:
            print("   !! unclosed %s @%d" % (label, m.start())); break
        h = h[:sp[0]] + h[sp[1]:]; n += 1
    print("   - removed %d x %s" % (n, label))
    return h

# ------------------------------------------------------------- button -> <a>
CSS_BTN = re.compile(r'(?<![\w.#\-\[=:"\'])button(?![\w\-])')

def split_sel(s):
    parts, depth, cur = [], 0, ''
    for ch in s:
        if ch == '(': depth += 1
        elif ch == ')': depth -= 1
        if ch == ',' and depth == 0:
            parts.append(cur); cur = ''
        else:
            cur += ch
    parts.append(cur)
    return parts

CSS_COMMENT = re.compile(r'/\*.*?\*/', re.S)

def css_extend_button(css):
    """Give every rule that selects the `button` element type an a[role=button] twin.

    Comments must be masked first: prose like `/* ... the ADD TO CART button ... */`
    contains the bare word `button`, and rewriting it into the selector list makes the
    whole rule invalid, which silently drops it (that is how the ATC lost its styling)."""
    out, i, n = [], 0, 0
    while True:
        b = css.find('{', i)
        if b == -1:
            out.append(css[i:]); break
        chunk = css[i:b]
        blind = CSS_COMMENT.sub(lambda m: ' ' * len(m.group(0)), chunk)   # comments -> spaces
        cut = blind.rfind('}')                     # a '}' inside a comment must not split here
        prefix, sel = chunk[:cut + 1], chunk[cut + 1:]
        sel_nc = CSS_COMMENT.sub(' ', sel)         # match/rewrite against comment-free selector
        if sel_nc.lstrip().startswith('@') or not CSS_BTN.search(sel_nc):
            out.append(chunk)
        else:
            twins = [CSS_BTN.sub('a:where([role=button])', p).strip()
                     for p in split_sel(sel_nc) if CSS_BTN.search(p)]
            twins = [t for t in twins if t]
            out.append(prefix + sel + (',' + ','.join(twins) if twins else '')); n += 1
        out.append('{')
        i = b + 1
    print("   - css: extended %d button rules" % n)
    return ''.join(out)

def convert_buttons(h):
    n = len(re.findall(r'<button\b', h, re.I))
    h = re.sub(r'<button\b', '<a role=button tabindex=0', h, flags=re.I)
    h = re.sub(r'</button\s*>', '</a>', h, flags=re.I)
    h = re.sub(r'(<style[^>]*>)(.*?)(</style>)',
               lambda m: m.group(1) + css_extend_button(m.group(2)) + m.group(3), h, flags=re.S)
    h = h.replace("'.button-add-to-cart, button[name=add], #solu-psticky-btn'",
                  "'.button-add-to-cart, [name=add], #solu-psticky-btn'")
    h = h.replace("querySelectorAll('button')", "querySelectorAll('[role=button]')")
    h = h.replace('querySelectorAll("button")', 'querySelectorAll("[role=button]")')
    shim = ("<style id=solu-btn-shim>:where(a[role=button]){display:inline-block;text-align:center;"
            "text-decoration:none;color:inherit;cursor:pointer;font:inherit;background:none;border:0}</style>")
    h = h.replace('</head>', shim + '</head>', 1)
    print("   - converted %d <button> -> <a role=button>" % n)
    return h

# ------------------------------------------------------------------ url scrub
def scrub_urls(h):
    h = re.sub(r'<!--\s*(Page saved with SingleFile|saved from url).*?-->', '', h, flags=re.S | re.I)
    # widget data attributes carry escaped HTML + provenance URLs that href-scrubbing cannot see through
    h = re.sub(r'\sdata-yotpo-(description|image-url|url|price|name)=("[^"]*"|\'[^\']*\'|[^\s>]+)', ' ', h)
    # the old link guard whitelisted the pre-rename filenames; every link is '#' now, so it is dead weight
    h = re.sub(r'<script id=solu-linkguard>.*?</script>', '', h, flags=re.S)
    h = re.sub(r'<link[^>]+rel=["\']?(canonical|alternate|preconnect|dns-prefetch|preload|manifest)["\']?[^>]*>', '', h, flags=re.I)
    h = re.sub(r'<meta[^>]+(?:property|name)=["\']?(?:og:|twitter:)[^>]*>', '', h, flags=re.I)
    h = re.sub(r'<script[^>]+type=["\']?application/ld\+json["\']?[^>]*>.*?</script>', '', h, flags=re.S | re.I)
    h = re.sub(r'\ssrcset="[^"]*"', ' ', h)
    h = re.sub(r'\ssizes="[^"]*"', ' ', h)
    h = re.sub(r'\bhref=("[^"]*"|\'[^\']*\'|[^\s>]+)',
               lambda m: 'href="#"' if re.match(r'^["\']?(https?:|//|mailto:|tel:)', m.group(1)) else m.group(0), h)
    h = re.sub(r'\bhref=["\']?(privacy|terms|refund|shipping|contact|index)\.html["\']?', 'href="#"', h, flags=re.I)
    h = re.sub(r'\baction=("[^"]*"|\'[^\']*\'|[^\s>]+)',
               lambda m: 'action="#"', h)
    h = re.sub(r'\sdata-(shop|store|mpid)=("[^"]*"|\'[^\']*\'|[^\s>]+)', ' ', h)
    # NOTE: the URL character class must exclude * { } ; ,  -- a CSS banner ends
    # `https://tailwindcss.com*/` and a greedy class eats the `*/` comment terminator plus the
    # next selector, leaving an unterminated comment that silently swallows Preflight.
    URLCHARS = r'[^\s"\'<>)\\*{};,]+'
    h = re.sub(r'https?://(?!www\.w3\.org|schema\.org)' + URLCHARS, '#', h)
    h = re.sub(r'(?<=["\'=])//(?:www\.)?[a-z0-9.-]+\.[a-z]{2,}' + URLCHARS.replace('+', '*'), '#', h)
    return h

def strip_dashes(h):
    return h.replace('—', ', ').replace('–', '-')

# ------------------------------------------------------------------- images
MANIFEST, COPIED = [], {}

def emit(src_abs, target, page, slot, role, alt, transparent=False, prompt=None):
    dst = os.path.join(IMG, target)
    if target not in COPIED:
        shutil.copy2(src_abs, dst); COPIED[target] = True
    try:
        from PIL import Image
        with Image.open(dst) as im: w, hh = im.size
    except Exception:
        w = hh = 0
    MANIFEST.append(dict(id=os.path.splitext(target)[0], page=page, slot=slot, role=role,
                         alt=alt, target_filename=target, width=w, height=hh,
                         aspect=("%s:%s" % (w, hh) if w else ""), transparent=transparent,
                         prompt=prompt or ("Client asset placed in the %s slot." % slot),
                         status="done"))
    return "images/" + target

def externalize_datauris(h, page, prefix):
    """Write every data:image URI out to images/ and rewrite the reference.

    Two passes, quoted first: an unencoded inline SVG data URI contains spaces and '<'/'>'
    (data:image/svg+xml,<svg xmlns=... />), so a whitespace-terminated match truncates it and
    leaves the tail of the SVG stranded in the attribute."""
    # Three shapes, matched in priority order. Group 3 is the parameter segment
    # (";base64", ";utf8", ";charset=utf-8", or empty); group 4 is the payload.
    #  - QUOTED  : attribute or JS string. Payload may contain backslash escapes (\").
    #  - CSSURL  : unquoted url(...). Payload uses CSS escapes for spaces and quotes
    #              (url(data:image/svg+xml,%3Csvg\ viewBox=\'0\ 0\ 13\ 13\'...)), so it must run
    #              to the unescaped ')' -- stopping at the first quote truncates it to 11 bytes.
    #  - BARE    : unquoted HTML attribute (poster=data:image/svg+xml;utf8,%3Csvg%20xmlns='...').
    #              An unquoted attribute value ends at whitespace or '>', NOT at a quote, so the
    #              payload must be allowed to contain ' and ( ) or it truncates at "<svg xmlns=".
    QUOTED = r'(["\'])data:image/([a-z.+-]+)([^,]*),((?:\\.|(?!\1).)*?)\1'
    CSSURL = r'()url\(\s*data:image/([a-z.+-]+)([^,]*),((?:\\.|[^)\\])*)\)'
    BARE   = r'()data:image/([a-z.+-]+)([^,\s>]*),([^\s>"]+)()'

    hits, spans = [], []
    for pat, kind in ((QUOTED, 'quoted'), (CSSURL, 'cssurl'), (BARE, 'bare')):
        for m in re.finditer(pat, h):
            if any(a <= m.start() < b for a, b in spans):
                continue                       # already covered by a higher-priority shape
            hits.append((m, kind)); spans.append(m.span())
    hits.sort(key=lambda t: t[0].start(), reverse=True)   # right-to-left keeps offsets valid
    n = 0
    for m, shape in hits:
        kind, params, payload = m.group(2), m.group(3) or '', m.group(4)
        isb64 = 'base64' in params
        ext = {'svg+xml': 'svg', 'jpeg': 'jpg', 'x-icon': 'ico'}.get(kind, kind)
        if not isb64:
            payload = re.sub(r'\\(.)', r'\1', payload, flags=re.S)   # undo JS/CSS escaping
        try:
            raw = base64.b64decode(payload) if isb64 else urllib.parse.unquote(payload).encode()
        except Exception:
            continue
        if ext == 'svg' and b'</svg>' not in raw and not raw.rstrip().endswith(b'/>'):
            print("   !! TRUNCATED svg (%d bytes): %r" % (len(raw), raw[:50])); continue
        n += 1
        name = "%s-icon-%02d.%s" % (prefix, n, ext)
        with open(os.path.join(IMG, name), 'wb') as f: f.write(raw)
        COPIED[name] = True
        MANIFEST.append(dict(id=os.path.splitext(name)[0], page=page,
                             slot="%s / inline UI asset (externalized from a data URI)" % prefix,
                             role="icon-or-decorative", alt="",
                             target_filename=name, width=0, height=0, aspect="",
                             transparent=(ext in ('svg', 'png', 'webp')),
                             prompt="Theme UI icon or decoration. Externalized from an inline data URI; no regeneration needed.",
                             status="done"))
        if shape == 'quoted':                 # the match spans its own quotes; put them back
            q = m.group(1)
            repl = q + "images/" + name + q
        elif shape == 'cssurl':               # the match spans url( ... ); rebuild it
            repl = 'url("images/' + name + '")'
        else:
            repl = "images/" + name
        h = h[:m.start()] + repl + h[m.end():]
    print("   - externalized %d data: images" % n)
    return h

DRAW = (b'<path', b'<circle', b'<polygon', b'<polyline', b'<ellipse', b'<text',
        b'<image', b'<use', b'<line')

def neutralize_placeholders(h):
    """SingleFile substitutes a flat coloured <rect> for every image it could not capture.

    In the original those declarations do not paint (the capture leaves them computing to
    background-image: none). Externalizing them into valid files would make them render as
    stray coloured boxes, which is a visual regression against the approved build. So: any
    externalized SVG that is nothing but a rect gets its CSS reference set to `none`, and the
    file is dropped if nothing else still points at it."""
    killed = 0
    for name in sorted([f for f in os.listdir(IMG) if f.endswith('.svg')]):
        raw = open(os.path.join(IMG, name), 'rb').read()
        if b'<rect' not in raw or any(d in raw.lower() for d in DRAW):
            continue                                   # a real icon, keep it
        before = h
        h = h.replace('url("images/%s")' % name, 'none')
        if h == before:
            continue
        if 'images/%s' % name not in h:                # nothing references it any more
            os.remove(os.path.join(IMG, name))
            MANIFEST[:] = [e for e in MANIFEST if e['target_filename'] != name]
            COPIED.pop(name, None)
        killed += 1
    print("   - neutralized %d SingleFile placeholder rects" % killed)
    return h

# ================================================================== DRIVER
def read(p):  return open(p, encoding="utf-8", errors="replace").read()
def write(p, s): open(p, "w", encoding="utf-8").write(s)

if os.path.isdir(OUT): shutil.rmtree(OUT)
os.makedirs(IMG)

FONTS_ADV   = read(os.path.join(BUILD, "fonts-adv.css"))
FONTS_PDP1  = read(os.path.join(BUILD, "fonts-pdp1.css"))
FONTS_ICONS = read(os.path.join(BUILD, "fonts-icons.css"))
TW_CSS      = read(os.path.join(BUILD, "tw", "out.css"))

# Force every page to open at the top: disable the browser's scroll restoration and
# scroll to 0 on pageshow (covers fresh load, reload, and back/forward bfcache restore).
SCROLLTOP = ("<script>try{history.scrollRestoration='manual';}catch(e){}"
             "window.addEventListener('pageshow',function(){window.scrollTo(0,0);});</script>")

def remap(h, page, table):
    for old, (new, slot, role, alt, tr) in table.items():
        rel = emit(os.path.join(SRC, old), new, page, slot, role, alt, tr)
        h = re.sub(re.escape(old) + r'(\?[^"\'\s>]*)?', rel, h)
        # A theme CSS trick targets images by filename stem: img[src*="tcard-4"]{display:none}.
        # Those selectors carry the bare stem (no assets/ prefix, no extension), so the src
        # rewrite above misses them and the rule silently stops matching after the rename.
        old_stem = os.path.splitext(os.path.basename(old))[0]
        new_stem = os.path.splitext(os.path.basename(new))[0]
        if old_stem != new_stem:
            h = re.sub(r'(\[src\*=(["\']))' + re.escape(old_stem) + r'(\2\])',
                       r'\g<1>' + new_stem + r'\g<3>', h)
    return h

# ---------------------------------------------------------------- ADVERTORIAL
print("[advertorial.html]")
h = read(os.path.join(SRC, "advertorial.html"))
h = remap(h, "advertorial.html", {
 "assets/adv-hero.jpg":         ("adv-hero-01.jpg", "advertorial / hero before-after", "hero",
                                 "A woman before and after, with brighter, smoother, more radiant skin", False),
 "assets/adv-ba-proof1-r6.jpg": ("adv-proof-01.jpg", "advertorial / proof section, first before-after", "content",
                                 "A customer before and after the routine, with softer lines and brighter skin", False),
 "assets/adv-ba-proof2-r5.jpg": ("adv-proof-02.jpg", "advertorial / proof section, second before-after", "content",
                                 "Another customer before and after, with calmer redness and softer lines", False),
 "assets/solusinglepair.png":   ("product-pair-single-01.png", "advertorial / product reveal card", "product",
                                 "SoluRetinol Daytime and Nighttime serum pair", True),
})
h = re.sub(r'<link[^>]+fonts\.googleapis[^>]*>', '', h, flags=re.I)
h = h.replace('</head>', '<style id=solu-fonts>' + FONTS_ADV + '</style></head>', 1)
h = scrub_urls(h); h = strip_dashes(h)
write(os.path.join(OUT, "advertorial.html"), h)
print("   ok, %.0f KB" % (len(h) / 1024))

# ----------------------------------------------------------------- LISTICLE
# Sister pre-sell for funnel 2. Same design system + fonts as the advertorial,
# so it shares FONTS_ADV and reuses the advertorial's hero / proof / product art.
# CTAs are inert <a class=cta> (no <button>), so no button conversion is needed.
print("[listicle.html]")
h = read(os.path.join(SRC, "listicle.html"))
h = remap(h, "listicle.html", {
 "assets/adv-hero.jpg":         ("adv-hero-01.jpg", "listicle / cover before-after", "hero",
                                 "A woman before and after, with brighter, smoother, more radiant skin", False),
 "assets/list-r1-cream.png":    ("list-r1-cream-01.png", "listicle / reason 1 hero, cream on skin surface", "content",
                                 "A dab of face cream resting on the surface of skin", False),
 "assets/list-r2-needle.png":   ("list-r2-needle-01.png", "listicle / reason 2 hero, cosmetic syringe", "content",
                                 "A single cosmetic syringe on a smooth grey surface", False),
 "assets/list-r3-lab.png":      ("list-r3-lab-01.png", "listicle / reason 3 hero, laboratory dropper and vial", "content",
                                 "A dropper releasing serum into a vial on a laboratory bench", False),
 "assets/list-r4-serum.png":    ("list-r4-serum-01.png", "listicle / reason 4 hero, serum drop", "content",
                                 "A single glossy drop of serum with a gel-like texture", False),
 "assets/adv-ba-proof1-r6.jpg": ("adv-proof-01.jpg", "listicle / reason 5 before-after", "content",
                                 "A customer before and after the routine, with softer lines and brighter skin", False),
 "assets/solusinglepair.png":   ("product-pair-single-01.png", "listicle / offer reveal card", "product",
                                 "SoluRetinol Daytime and Nighttime serum pair", True),
})
h = re.sub(r'<link[^>]+fonts\.googleapis[^>]*/?>', '', h, flags=re.I)
h = h.replace('</head>', '<style id=solu-fonts>' + FONTS_ADV + '</style></head>', 1)
h = scrub_urls(h); h = strip_dashes(h)
write(os.path.join(OUT, "listicle.html"), h)
print("   ok, %.0f KB" % (len(h) / 1024))

# ------------------------------------------------------------------- PDP 1
print("[pdp-1.html]")
h = read(os.path.join(SRC, "SoluRetinol.html"))
h = remap(h, "pdp-1.html", {
 "assets/soluwellnesslgoo.webp": ("logo-soluwellness-01.webp", "pdp-1 / header logo", "logo-or-wordmark",
                                  "SoluWellness", True),
 "assets/solusinglepair.png":    ("product-pair-single-01.png", "pdp-1 / gallery, 1 pair", "product",
                                  "SoluRetinol single pair", True),
 "assets/soludoublepair.png":    ("product-pair-double-01.png", "pdp-1 / gallery, 2 pairs", "product",
                                  "SoluRetinol two pairs", True),
 "assets/solutriplepair.png":    ("product-pair-triple-01.png", "pdp-1 / gallery, 3 pairs", "product",
                                  "SoluRetinol three pairs", True),
 "assets/real-ba-dayface.webp":  ("review-ba-dayface-01.webp", "pdp-1 / review card before-after", "review",
                                  "Customer before and after", False),
 "assets/review-ba-1.png":       ("review-ba-eyes-01.png", "pdp-1 / review card before-after", "review",
                                  "Customer before and after, eye area", False),
 "assets/review-smile-ba.png":   ("review-ba-smile-01.png", "pdp-1 / review card before-after", "review",
                                  "Customer before and after, smile lines", False),
})
h = re.sub(r'<script[^>]+cdn\.tailwindcss\.com[^>]*>\s*</script>', '', h, flags=re.I)
h = re.sub(r'<script id="tailwind-config">.*?</script>', '', h, flags=re.S)
h = re.sub(r'<link[^>]+fonts\.googleapis[^>]*/?>', '', h, flags=re.I)
h = h.replace('</head>', '<style id=solu-tailwind>' + TW_CSS + '</style>'
                         '<style id=solu-fonts>' + FONTS_PDP1 + FONTS_ICONS + '</style></head>', 1)
h = convert_buttons(h)
h = externalize_datauris(h, "pdp-1.html", "pdp1")
h = neutralize_placeholders(h)
h = scrub_urls(h); h = strip_dashes(h)
write(os.path.join(OUT, "pdp-1.html"), h)
print("   ok, %.0f KB" % (len(h) / 1024))

# ------------------------------------------------------- PDP 2  -> pdp-2.html
print("[pdp-2.html  (PDP 2)]")
h = read(os.path.join(SRC, "SoluRetinol Product.html"))

# 1. reference cross-sell carousels (whole Shopify sections) + cart rebuy widgets
h = drop_elements(h, r'<section[^>]*id=shopify-section-template--18148350689444__1715808421279ebe06[^>]*>',
                  'section', 'rebuy cross-sell section A')
h = drop_elements(h, r'<section[^>]*id=shopify-section-template--18148350689444__1715809139c23c480e[^>]*>',
                  'section', 'rebuy cross-sell section B')
h = drop_elements(h, r'<div[^>]*\bdata-rebuy-id=[^>]*>', 'div', 'rebuy cart widget')

# 2. reference reviews left in the Yotpo list.
#    Body FIRST: the title text is a prefix of the body, so replacing the title first
#    would clobber the body's opening words and the body pattern would stop matching.
PET = ("that has been supplied in the past fro Solu has had numerous "
       "advantages for our skin who has started to suffer from arthritis and allergies to name a few! "
       "This product has greatly improved her mob...")
FIX = ("I started on the Night serum first because my skin reacts to almost everything, and it never stung once. "
       "Three months in, the lines around my eyes and mouth are visibly softer and my tone is far more even.")
for pre in ("We&#39;ve found that the SoluRetinol ", "We've found that the SoluRetinol "):
    h = h.replace(pre + PET, FIX)
assert PET not in h, "pet review body survived"
h = h.replace('My GSD gets this added', 'The deep lines are softening')
h = h.replace("We&#39;ve found that the SoluRetinol", 'It has made a real difference')
h = h.replace("We've found that the SoluRetinol", 'It has made a real difference')

# 2b. review dates were left in AU day-first format on a US store
for au, us in (("15/06/26", "06/15/26"), ("27/02/26", "02/27/26"),
               ("22/11/25", "11/22/25"), ("11/01/26", "01/11/26")):
    h = h.replace(au, us)
h = re.sub(r'<a role=button tabindex=0[^>]*class=yotpo-read-more\b[^>]*>.*?</a>', '', h, flags=re.S)
h = re.sub(r'<button[^>]*class=yotpo-read-more\b[^>]*>.*?</button>', '', h, flags=re.S)

# 3. reference geo (country selector)
h = h.replace('data-iso-code=AU', 'data-iso-code=US')
h = re.sub(r'<div class="country-flag[^"]*"[^>]*></div>', '', h)
h = re.sub(r'\n?\s*Australia\s*\n?\s*\(USD', ' United States (USD', h)
h = h.replace('Australia     (USD', 'United States (USD')
h = re.sub(r'>\s*Australia\s*(\(USD)', r'>United States \1', h)

# 4. hidden guarantee-badge overlay images (already display:none in the theme CSS)
h = re.sub(r'<img[^>]*assets/guarantee-badge\.png[^>]*>', '', h)

h = remap(h, "pdp-2.html", {
 "assets/soluwellnesslgoo.webp": ("logo-soluwellness-01.webp", "pdp-2 / header logo", "logo-or-wordmark",
                                  "SoluWellness", True),
 "assets/solusinglepair.png":    ("product-pair-single-01.png", "pdp-2 / product gallery, 1 pair", "product",
                                  "SoluRetinol Day & Night System", True),
 "assets/soludoublepair.png":    ("product-pair-double-01.png", "pdp-2 / product gallery, 2 pairs", "product",
                                  "SoluRetinol Day & Night System", True),
 "assets/solutriplepair.png":    ("product-pair-triple-01.png", "pdp-2 / product gallery, 3 pairs", "product",
                                  "SoluRetinol Day & Night System", True),
 "assets/hero-bottles-a.png":    ("pdp-gallery-01.png", "pdp-2 / product gallery, bottles", "product",
                                  "SoluRetinol Day & Night System", True),
 "assets/night-bottle.png":      ("pdp-gallery-02.png", "pdp-2 / product gallery, night bottle", "product",
                                  "SoluRetinol Nighttime serum", True),
 "assets/system-boxed.png":      ("pdp-gallery-03.png", "pdp-2 / product gallery, boxed system", "product",
                                  "SoluRetinol boxed system", True),
 "assets/before-after-eye.png":  ("pdp-gallery-04.png", "pdp-2 / product gallery, before-after", "content",
                                  "Before and after, eye area", True),
 "assets/serum-swatch-skin.png": ("pdp-gallery-05.png", "pdp-2 / product gallery, serum swatch", "content",
                                  "Serum swatch on skin", True),
 "assets/bottles-box.png":       ("pdp-mediagrid-01.png", "pdp-2 / media grid band", "content",
                                  "SoluRetinol bottles and box", True),
 "assets/review-ba-1.png":       ("review-ba-eyes-01.png", "pdp-2 / testimonial card", "review",
                                  "Customer before and after, eye area", False),
 "assets/real-ba-dayface.webp":  ("review-ba-dayface-01.webp", "pdp-2 / testimonial card", "review",
                                  "Customer before and after", False),
 "assets/review-smile-ba.png":   ("review-ba-smile-01.png", "pdp-2 / testimonial card", "review",
                                  "Customer before and after, smile lines", False),
 "assets/tcard-4.png":           ("pdp-testimonial-01.png", "pdp-2 / testimonial card", "review",
                                  "Customer portrait", False),
 "assets/day-bottle.png":       ("pdp-gallery-06.png", "pdp-2 / product gallery, day bottle", "product",
                                  "SoluRetinol Daytime serum", True),
})

# The "happy customers" testimonial row is built by script, so its image paths never appear as
# a literal <img src> and the remap above cannot see them. Rewrite the data array to carry full
# images/ paths (so the optimize step's png->jpg rename can find them too) and drop the assets/ prefix.
TM = {"lifestyle-mirror.png": ("pdp-testimonial-02.png", "Customer portrait, Diane K. testimonial"),
      "testimonial-2.png":    ("pdp-testimonial-03.png", "Customer portrait, Marisol R. testimonial"),
      "testimonial-3.png":    ("pdp-testimonial-04.png", "Customer portrait, Carol P. testimonial")}
h = h.replace("""src="assets/'+d[0]+'\"""", """src="'+d[0]+'\"""")
for old, (new, alt) in TM.items():
    emit(os.path.join(SRC, "assets", old), new, "pdp-2.html",
         "pdp-2 / 'happy customers' testimonial row (injected by script)", "review", alt, False)
    h = h.replace("['" + old + "'", "['images/" + new + "'")
# a page script gates on the old asset folder at runtime; repoint it at the delivered folder
h = h.replace("s.indexOf('assets/')===0", "s.indexOf('images/')===0")
assert "assets/" not in h, "an assets/ reference survived on pdp-2.html"

h = convert_buttons(h)
h = externalize_datauris(h, "pdp-2.html", "pdp")
h = neutralize_placeholders(h)
h = scrub_urls(h); h = strip_dashes(h)
write(os.path.join(OUT, "pdp-2.html"), h)
print("   ok, %.0f KB" % (len(h) / 1024))

# ------------------------------------------------------------------ manifest
mani = {"brand": "Solu Wellness", "funnel": "SoluRetinol Day & Night System",
        "images": sorted(MANIFEST, key=lambda x: (x["page"], x["target_filename"]))}
write(os.path.join(OUT, "image-manifest.json"), json.dumps(mani, indent=2) + "\n")
print("[manifest] %d entries, %d files" % (len(MANIFEST), len(COPIED)))

# ------------------------------------------------------- optimize + reformat
print("[optimize]")
from PIL import Image
renames, before = {}, 0
for fn in sorted(os.listdir(IMG)):
    p = os.path.join(IMG, fn); before += os.path.getsize(p)
    ext = fn.rsplit('.', 1)[-1].lower()
    if ext in ('svg', 'ico'): continue
    try:
        im = Image.open(p); im.load()
    except Exception:
        continue
    w, hh = im.size
    if max(w, hh) > 1200:
        r = 1200 / max(w, hh)
        im = im.resize((max(1, round(w * r)), max(1, round(hh * r))), Image.LANCZOS)
    has_alpha = False
    if im.mode in ('RGBA', 'LA', 'P'):
        has_alpha = im.convert('RGBA').split()[-1].getextrema()[0] < 255
    big = max(im.size) >= 256
    if ext == 'png' and not has_alpha and big:          # opaque photo -> jpg (kit 5b)
        new = fn[:-4] + '.jpg'
        im.convert('RGB').save(os.path.join(IMG, new), 'JPEG', quality=85, optimize=True, progressive=True)
        os.remove(p); renames[fn] = new
    elif ext == 'png':
        im.save(p, 'PNG', optimize=True)
    elif ext in ('jpg', 'jpeg'):
        im.convert('RGB').save(p, 'JPEG', quality=85, optimize=True, progressive=True)
    elif ext == 'webp':
        im.save(p, 'WEBP', quality=85, method=6)

for page in ("pdp-2.html", "advertorial.html", "listicle.html", "pdp-1.html"):
    pp = os.path.join(OUT, page); s = read(pp)
    for old, new in renames.items():
        s = s.replace("images/" + old, "images/" + new)
    if SCROLLTOP not in s:
        s = s.replace('</head>', SCROLLTOP + '</head>', 1)
    write(pp, s)

for e in mani["images"]:
    tf = e["target_filename"]
    if tf in renames:
        e["target_filename"] = renames[tf]; e["id"] = os.path.splitext(renames[tf])[0]
        e["transparent"] = False
    fp = os.path.join(IMG, e["target_filename"])
    if os.path.exists(fp):
        try:
            with Image.open(fp) as im:
                e["width"], e["height"] = im.size
                e["aspect"] = "%s:%s" % im.size
        except Exception:
            pass
write(os.path.join(OUT, "image-manifest.json"), json.dumps(mani, indent=2) + "\n")
after = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG))
print("   - %d png -> jpg; images %.1f MB -> %.1f MB" % (len(renames), before / 1e6, after / 1e6))
