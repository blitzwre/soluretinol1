# Delivery: Solu Wellness · SoluRetinol Day & Night System (funnel-2)

A two-page direct-response funnel for the SoluRetinol Day & Night System (a two-step
water-soluble retinol serum pair, $59 for 1 pair / $100 for 2 / $120 for 3). It ships as one
pre-sell page plus one product page. Each page is a self-contained standalone HTML file for
CheckoutChamp: it opens from disk, renders with the network off, and needs nothing outside
this folder.

| File | Role |
|---|---|
| `listicle.html` | The listicle slideshow pre-sell (“The Skin Report”, paginated click-through) |
| `pdp-2.html` | PDP 2, the Shopify-theme product page (full gallery, reviews, FAQ) |

This is one of two sister funnels delivered together. This folder is funnel: **listicle.html → pdp-2.html**.
The other funnel pairs the advertorial with PDP 1.

## CheckoutChamp / standalone

Both pages render with zero network calls. Fonts are inlined as base64 `@font-face`, every image
is a real file in `images/` referenced by a relative path, and there is no external CSS, JS, CDN,
or tracker. Upload the two HTML files and the `images/` folder together so the relative
`images/...` paths resolve. Every in-page link is `#`; wire the real URLs at deploy.

## Functional state

Everything below works offline, with no backend:

- **Slideshow pre-sell.** `listicle.html` is a paginated click-through: a cover slide, five numbered belief slides, and an offer slide. Back / Next controls, a top progress bar, arrow-key support, and a per-slide counter all work with no backend.
- **Supply/tier selection (pdp-2.html).** Selecting 1 / 2 / 3 pairs updates the headline price, the
  compare-at price, and the sticky bar price. On pdp-2.html it also swaps the gallery image.
- **Sticky ADD TO CART bar.** Pinned on mobile; its price stays in sync with the selected tier.
- **Accordions / FAQ.** Open and close on the product page.
- **Product gallery + testimonial row on pdp-2.html.** Main image plus thumbnails; the "happy customers" strip is injected by an inline script (images pdp-testimonial-02/03/04).
- **Pre-sell CTAs are intentionally inert.** They are `<a class="cta">` (and the slideshow Back/Next arrows are `<a role="button">` driven by inline JS) with no `href`, per the zero-URL rule. Wire them at deploy.

Every former `<button>` on the product page was converted to `<a role="button">` for CheckoutChamp
routing, with the theme's button CSS extended so the controls render identically.

## Before going live (the deployer's checklist)

- Put real production URLs into every `#` link: checkout / ADD TO CART, legal pages (Privacy,
  Terms, Shipping, Refund), Contact, header logo, nav, and social.
- **Wire the pre-sell CTAs.** They have no `href` right now, so they do nothing until you point
  them at pdp-2.html or straight at checkout.
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

- **The 60-day money-back guarantee is live copy on pdp-2.html**, as is the trust-badge row (60-DAY GUARANTEE / CRUELTY FREE / MADE IN USA / PARABEN FREE). It is the client's own offer content, consistent with the Refund Policy link. The pre-sell has no guarantee copy; confirm the split is intentional before launch.
- **pdp-2.html is ~2.9 MB.** It is a captured Shopify theme and the kit forbids tree-shaking its CSS, so the full theme stylesheet ships as-is. It renders fine; it is just a big file.
- **Exempt URLs left in the code, as permitted:** `xmlns="http://www.w3.org/2000/svg"` appears on
  inline SVG. These are XML namespace identifiers, not navigable links. No `schema.org` reference
  remains anywhere.
