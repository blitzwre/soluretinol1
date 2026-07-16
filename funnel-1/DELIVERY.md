# Delivery: Solu Wellness · SoluRetinol Day & Night System (funnel-1)

A two-page direct-response funnel for the SoluRetinol Day & Night System (a two-step
water-soluble retinol serum pair, $59 for 1 pair / $100 for 2 / $120 for 3). It ships as one
pre-sell page plus one product page. Each page is a self-contained standalone HTML file for
CheckoutChamp: it opens from disk, renders with the network off, and needs nothing outside
this folder.

| File | Role |
|---|---|
| `advertorial.html` | The advertorial pre-sell article (“The Skin Report”) |
| `pdp-1.html` | PDP 1, the lean custom product page |

This is one of two sister funnels delivered together. This folder is funnel: **advertorial.html → pdp-1.html**.
The other funnel pairs the listicle slideshow with PDP 2.

## CheckoutChamp / standalone

Both pages render with zero network calls. Fonts are inlined as base64 `@font-face`, every image
is a real file in `images/` referenced by a relative path, and there is no external CSS, JS, CDN,
or tracker. Upload the two HTML files and the `images/` folder together so the relative
`images/...` paths resolve. Every in-page link is `#`; wire the real URLs at deploy.

## Functional state

Everything below works offline, with no backend:

- **Advertorial pre-sell.** `advertorial.html` is a single-scroll article with an open/close FAQ.
- **Supply/tier selection (pdp-1.html).** Selecting 1 / 2 / 3 pairs updates the headline price, the
  compare-at price, and the sticky bar price.
- **Sticky ADD TO CART bar.** Pinned on mobile; its price stays in sync with the selected tier.
- **Accordions / FAQ.** Open and close on the product page.

- **Pre-sell CTAs are intentionally inert.** They are `<a class="cta">` with no `href`, per the request to keep the pre-sell unwired from the PDP.

Every former `<button>` on the product page was converted to `<a role="button">` for CheckoutChamp
routing, with the theme's button CSS extended so the controls render identically.

## Before going live (the deployer's checklist)

- Put real production URLs into every `#` link: checkout / ADD TO CART, legal pages (Privacy,
  Terms, Shipping, Refund), Contact, header logo, nav, and social.
- **Wire the pre-sell CTAs.** They have no `href` right now, so they do nothing until you point
  them at pdp-1.html or straight at checkout.
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

- **The 60-day money-back guarantee is live copy on pdp-1.html**. It is the client's own offer content, consistent with the Refund Policy link. The pre-sell has no guarantee copy; confirm the split is intentional before launch.
- **pdp-1.html is ~162 KB.** Lean custom page; Tailwind compiled to a local stylesheet, fonts inlined.
- **Exempt URLs left in the code, as permitted:** `xmlns="http://www.w3.org/2000/svg"` appears on
  inline SVG. These are XML namespace identifiers, not navigable links. No `schema.org` reference
  remains anywhere.
