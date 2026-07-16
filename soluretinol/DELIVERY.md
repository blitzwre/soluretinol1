# Delivery: Solu Wellness · SoluRetinol Day & Night System

A three-page direct-response funnel for the SoluRetinol Day & Night System (a two-step water-soluble
retinol serum pair, $59 for 1 pair / $100 for 2 / $120 for 3). It ships as one advertorial pre-sell
page plus two product pages that are A/B alternates of each other. Each page is a self-contained
standalone HTML file for CheckoutChamp: it opens from disk, renders with the network off, and needs
nothing outside this folder.

| File | Role |
|---|---|
| `pdp-1.html` | PDP 1, the lean custom product page |
| `pdp-2.html` | PDP 2, the Shopify-theme product page (full gallery, reviews, FAQ) |
| `advertorial.html` | The advertorial pre-sell article ("The Skin Report") |

**Naming note (a deliberate deviation from the kit):** the kit's template names the main page
`index.html`. At the client's request the two product pages keep the house PDP 1 / PDP 2 naming
(`pdp-1.html`, `pdp-2.html`) instead, so this package has no `index.html`. Everything else follows the
kit. If your deploy target needs an `index.html`, rename `pdp-2.html` (the primary) to it.

## CheckoutChamp / standalone

All three pages render with zero network calls. Fonts are inlined as base64 `@font-face`, every image
is a real file in `images/` referenced by a relative path, and there is no external CSS, JS, CDN, or
tracker. Upload the three HTML files and the `images/` folder together so the relative `images/...`
paths resolve. Every in-page link is `#`; wire the real URLs at deploy (see "Before going live").

## Functional state

Everything below works offline, with no backend:

- **Supply/tier selection (both PDPs).** Selecting 1 / 2 / 3 pairs updates the headline price, the
  compare-at price, and the sticky bar price. On `pdp-2.html` it also swaps the gallery image.
- **Sticky ADD TO CART bar.** Pinned on mobile; its price stays in sync with the selected tier.
- **Product gallery.** Main image plus thumbnails, click to switch; carousel dots work.
- **Accordions / FAQ.** Open and close on both PDPs.
- **Testimonial row on `pdp-2.html`** shows three cards. The "happy customers" strip is injected by an
  inline script; its images are `pdp-testimonial-02/03/04`.
- **Advertorial CTAs are intentionally inert.** They are `<a class="cta">` with no `href`, per the
  request to unwire the advertorial from the PDPs.

Every former `<button>` was converted to `<a role="button">` for CheckoutChamp routing (132 on
`pdp-2.html`, 8 on `pdp-1.html`), with the theme's button CSS rules extended so the controls render
identically. Verified against the original: ADD TO CART styling, tier selection, and the sticky bar
all match.

## Before going live (the deployer's checklist)

- Put real production URLs into every `#` link: checkout / ADD TO CART, legal pages (Privacy, Terms,
  Shipping, Refund), Contact, header logo, nav, and social.
- **Wire the advertorial CTAs.** There are 5 (three inline `.cta`, the final `.cta`, and the sticky
  `.sbtn`). They have no `href` at all right now, so they do nothing until you point them at the live
  PDP or straight at checkout.
- **Restore the PDP ADD TO CART destination.** Both PDPs' ATC buttons previously routed to the
  CheckoutChamp funnel at the client's storefront root; that URL was stubbed to `#` under the zero-URL
  rule. Put the real funnel URL back on `.button-add-to-cart`, `[name=add]`, and `#solu-psticky-btn`
  (pdp-2.html) and on `.solu-atc-btn` (pdp-1.html).
- Decide which PDP is live, or run them as the A/B pair they were built as.
- Add production canonical / Open Graph meta if you want it; all SEO and social meta was stripped.

## Images

All done. 98 files in `images/`, every one referenced by a page and listed in `image-manifest.json`.
No `pending` entries, so there is no `IMAGE-PROMPTS.md` in this package and nothing to generate. The
manifest has 106 entries because an image shared across pages gets one entry per page-placement (same
`target_filename`, different `page` and `slot`), so a deployer can place every image without opening
the HTML.

Naming: page-specific images are prefixed by page (`adv-`, `pdp-` for pdp-2.html, `pdp1-`); images
shared across pages use a neutral prefix (`product-`, `review-`, `logo-`) because one file serves
several pages. `pdp-icon-*` and `pdp1-icon-*` are theme UI icons and decorations that the capture had
inlined as data URIs; they were externalized to real files and need no art direction.

All images are optimized to a 1200px longest edge, quality ~85, metadata stripped; opaque photos were
converted from PNG to JPG per the naming spec. Total `images/` weight: 2.7 MB (down from 21 MB).

## Compliance

The advertorial carries its disclosure block in the footer, verbatim: it states the page is a paid
advertisement and not an independent news article, that the individual featured is a composite and the
photos are illustrative, the FDA statement ("Statements have not been evaluated by the FDA. This
product is not intended to diagnose, treat, cure, or prevent any disease."), external-cosmetic-use-only,
and "Individual results may vary."

No earnings, affiliate, or TCPA consent disclaimers were required, and there are no lead forms in this
package. If the client's compliance notes call for anything beyond the above, it is not present yet.

## Known items

- **The 60-day money-back guarantee is still live copy on both PDPs**, as is the trust-badge row on
  `pdp-2.html` (60-DAY GUARANTEE / CRUELTY FREE / MADE IN USA / PARABEN FREE). I left both alone on
  purpose: they are the client's own offer content, consistent across both PDPs and with the Refund
  Policy link. The advertorial has no guarantee copy. Flagging it because it is the one place the
  three pages disagree, so confirm it is intentional before launch.
- **A cross-sell carousel was removed from `pdp-2.html`.** The template it was built from carried a
  "You may also like" widget in four placements whose product cards were leftover template content, not
  SoluRetinol products (wrong SKUs, wrong class tokens, wrong copy). It could not be made SoluRetinol by
  editing, so the whole widget was removed. If you want a cross-sell row there, it must be rebuilt with
  real SoluRetinol SKUs and art.
- **Two leftover template reviews on `pdp-2.html` were rewritten.** Two reviews in the list still held
  source-template copy that did not describe this product, so both were replaced with on-brand skincare
  reviews. Review dates were also converted from day-first to US month-first format (e.g. 15/06/26
  became 06/15/26).
- **`pdp-2.html` is 2.9 MB.** It is a captured Shopify theme and the kit forbids tree-shaking its CSS,
  so the full theme stylesheet ships as-is. It renders fine; it is just a big file. `pdp-1.html` is
  162 KB; `advertorial.html` is 450 KB (font-heavy because Newsreader and Rubik are inlined).
- **Exempt URLs left in the code, as permitted:** `xmlns="http://www.w3.org/2000/svg"` appears 262
  times in `pdp-2.html` and once in `advertorial.html`. These are XML namespace identifiers on inline
  SVG, not navigable links. No `schema.org` reference remains anywhere (all JSON-LD was deleted).
- **`data:,` placeholders (3, in `pdp-2.html`).** These are the Shopify theme's own lazy-load
  placeholders from the original capture. The theme already hides them with
  `img[src="data:,"]{display:none}`. They are not base64 images and not assets.
- **Pre-existing, not introduced here:** on `pdp-2.html` at very narrow widths (~330px and below) the
  "SAVE $30 / SAVE $59" badge can overlap the price in the 2-Pairs and 3-Pairs rows. Fine at 390px+.
