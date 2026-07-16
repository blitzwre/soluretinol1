#!/usr/bin/env python3
"""Split the combined soluretinol/ build into two self-contained CheckoutChamp funnels.

  funnel-1/  advertorial.html + pdp-1.html   (advertorial pre-sell -> PDP 1)
  funnel-2/  listicle.html   + pdp-2.html    (listicle slideshow pre-sell -> PDP 2)

Each funnel gets ONLY the images its two pages reference, a manifest filtered to those
pages, and its own DELIVERY.md. Images shared across funnels are copied into both, so each
folder opens from disk with the network off and needs nothing outside itself (kit sec.1)."""
import re, os, json, shutil, zipfile

SRC   = "/Users/mogulmurray/Desktop/swipe"
COMB  = os.path.join(SRC, "soluretinol")           # combined build (source)
CIMG  = os.path.join(COMB, "images")

MANI = json.load(open(os.path.join(COMB, "image-manifest.json")))
REF  = re.compile(r'images/([A-Za-z0-9._-]+)')

FUNNELS = {
 "funnel-1": dict(pages=["advertorial.html", "pdp-1.html"],
                  presell="advertorial.html", pdp="pdp-1.html",
                  presell_label="advertorial pre-sell article (“The Skin Report”)"),
 "funnel-2": dict(pages=["listicle.html", "pdp-2.html"],
                  presell="listicle.html", pdp="pdp-2.html",
                  presell_label="listicle slideshow pre-sell (“The Skin Report”, paginated click-through)"),
}

def delivery_md(name, f):
    presell, pdp = f["presell"], f["pdp"]
    pdp_is_shopify = pdp == "pdp-2.html"
    return f"""# Delivery: Solu Wellness · SoluRetinol Day & Night System ({name})

A two-page direct-response funnel for the SoluRetinol Day & Night System (a two-step
water-soluble retinol serum pair, $59 for 1 pair / $100 for 2 / $120 for 3). It ships as one
pre-sell page plus one product page. Each page is a self-contained standalone HTML file for
CheckoutChamp: it opens from disk, renders with the network off, and needs nothing outside
this folder.

| File | Role |
|---|---|
| `{presell}` | The {f['presell_label']} |
| `{pdp}` | {'PDP 2, the Shopify-theme product page (full gallery, reviews, FAQ)' if pdp_is_shopify else 'PDP 1, the lean custom product page'} |

This is one of two sister funnels delivered together. This folder is funnel: **{presell} → {pdp}**.
The other funnel pairs the {'advertorial with PDP 1' if name == 'funnel-2' else 'listicle slideshow with PDP 2'}.

## CheckoutChamp / standalone

Both pages render with zero network calls. Fonts are inlined as base64 `@font-face`, every image
is a real file in `images/` referenced by a relative path, and there is no external CSS, JS, CDN,
or tracker. Upload the two HTML files and the `images/` folder together so the relative
`images/...` paths resolve. Every in-page link is `#`; wire the real URLs at deploy.

## Functional state

Everything below works offline, with no backend:

{'- **Slideshow pre-sell.** `' + presell + '` is a paginated click-through: a cover slide, five numbered belief slides, and an offer slide. Back / Next controls, a top progress bar, arrow-key support, and a per-slide counter all work with no backend.' if presell == 'listicle.html' else '- **Advertorial pre-sell.** `' + presell + '` is a single-scroll article with an open/close FAQ.'}
- **Supply/tier selection ({pdp}).** Selecting 1 / 2 / 3 pairs updates the headline price, the
  compare-at price, and the sticky bar price.{' On pdp-2.html it also swaps the gallery image.' if pdp_is_shopify else ''}
- **Sticky ADD TO CART bar.** Pinned on mobile; its price stays in sync with the selected tier.
- **Accordions / FAQ.** Open and close on the product page.
{'- **Product gallery + testimonial row on pdp-2.html.** Main image plus thumbnails; the "happy customers" strip is injected by an inline script (images pdp-testimonial-02/03/04).' if pdp_is_shopify else ''}
- **Pre-sell CTAs are intentionally inert.** They are `<a class="cta">`{' (and the slideshow Back/Next are `<a role="button">`)' if presell == 'listicle.html' else ''} with no `href`, per the request to keep the pre-sell unwired from the PDP.

Every former `<button>` on the product page was converted to `<a role="button">` for CheckoutChamp
routing, with the theme's button CSS extended so the controls render identically.

## Before going live (the deployer's checklist)

- Put real production URLs into every `#` link: checkout / ADD TO CART, legal pages (Privacy,
  Terms, Shipping, Refund), Contact, header logo, nav, and social.
- **Wire the pre-sell CTAs.** They have no `href` right now, so they do nothing until you point
  them at {pdp} or straight at checkout.
- **Restore the PDP ADD TO CART destination.** The product page's ATC previously routed to the
  CheckoutChamp funnel at the client's storefront root; that URL was stubbed to `#` under the
  zero-URL rule. Put the real funnel URL back before launch.
- Add production canonical / Open Graph meta if you want it; all SEO and social meta was stripped.

## Images

All done. Every file in `images/` is referenced by a page and listed in `image-manifest.json`.
No `pending` entries, so there is no `IMAGE-PROMPTS.md` and nothing to generate. Images are
optimized to a 1200px longest edge, quality ~85, metadata stripped; opaque photos were converted
from PNG to JPG per the naming spec.

## Compliance

The pre-sell carries its disclosure block in the footer, verbatim: it states the page is a paid
advertisement and not an independent news article, that the individual featured is a composite and
the photos are illustrative, the FDA statement ("Statements have not been evaluated by the FDA.
This product is not intended to diagnose, treat, cure, or prevent any disease."),
external-cosmetic-use-only, and "Individual results may vary." The pre-sell has no guarantee copy.

## Known items

- **The 60-day money-back guarantee is live copy on {pdp}**{', as is the trust-badge row (60-DAY GUARANTEE / CRUELTY FREE / MADE IN USA / PARABEN FREE)' if pdp_is_shopify else ''}. It is the client's own offer content, consistent with the Refund Policy link. The pre-sell has no guarantee copy; confirm the split is intentional before launch.
{'- **pdp-2.html is ~2.9 MB.** It is a captured Shopify theme and the kit forbids tree-shaking its CSS, so the full theme stylesheet ships as-is. It renders fine; it is just a big file.' if pdp_is_shopify else '- **pdp-1.html is ~162 KB.** Lean custom page; Tailwind compiled to a local stylesheet, fonts inlined.'}
- **Exempt URLs left in the code, as permitted:** `xmlns="http://www.w3.org/2000/svg"` appears on
  inline SVG. These are XML namespace identifiers, not navigable links. No `schema.org` reference
  remains anywhere.
"""

def build(name, f):
    out = os.path.join(SRC, name)
    img = os.path.join(out, "images")
    if os.path.isdir(out): shutil.rmtree(out)
    os.makedirs(img)

    # copy the two pages, collect every images/<file> they reference
    referenced = set()
    for page in f["pages"]:
        html = open(os.path.join(COMB, page), encoding="utf-8").read()
        shutil.copy2(os.path.join(COMB, page), os.path.join(out, page))
        referenced.update(REF.findall(html))

    # copy exactly those image files
    for fn in sorted(referenced):
        s = os.path.join(CIMG, fn)
        if not os.path.exists(s):
            raise SystemExit("!! %s references images/%s but it is not in the build" % (name, fn))
        shutil.copy2(s, os.path.join(img, fn))

    # manifest filtered to this funnel's pages
    imgs = [e for e in MANI["images"] if e["page"] in f["pages"]]
    mani_files = {e["target_filename"] for e in imgs}
    missing = referenced - mani_files
    if missing:
        raise SystemExit("!! %s: referenced images with no manifest entry: %s" % (name, sorted(missing)))
    orphan = mani_files - referenced
    if orphan:
        raise SystemExit("!! %s: manifest lists images no page references: %s" % (name, sorted(orphan)))
    mani = {"brand": MANI["brand"], "funnel": MANI["funnel"] + " (%s)" % name, "images": imgs}
    json.dump(mani, open(os.path.join(out, "image-manifest.json"), "w"), indent=2)
    open(os.path.join(out, "image-manifest.json"), "a").write("\n")

    open(os.path.join(out, "DELIVERY.md"), "w", encoding="utf-8").write(delivery_md(name, f))

    # zip the folder
    zp = os.path.join(SRC, name + ".zip")
    if os.path.exists(zp): os.remove(zp)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(out):
            for fn in sorted(files):
                ap = os.path.join(root, fn)
                z.write(ap, os.path.join(name, os.path.relpath(ap, out)))

    total = sum(os.path.getsize(os.path.join(img, fn)) for fn in os.listdir(img))
    print("[%s]  %s + %s  |  %d images (%.1f MB)  |  %d manifest entries  |  zip %.1f MB"
          % (name, f["presell"], f["pdp"], len(referenced), total / 1e6, len(imgs),
             os.path.getsize(zp) / 1e6))

for name, f in FUNNELS.items():
    build(name, f)
print("done.")
