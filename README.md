# crispyclankers.com

One-page static site for Crispy Clankers (agentic AI + robotics, NL, global). Plain HTML/CSS, no build step, no external assets.

- Deploy: GitHub Pages from `main` (root). `CNAME` pins the custom domain; DNS lives at Porkbun (A records → GitHub Pages IPs, `www` CNAME → `florisvanlieshout.github.io`).
- Pages: `index.html` (English) and `nl/index.html` (Dutch).

## Chat previews

Both pages expose Open Graph metadata in their initial HTML (no JavaScript needed),
with a locale-specific 1200×630 PNG in `assets/`. Twitter-compatible large-card tags
provide a fallback for consumers using that format. The cards reuse the site palette
and robot mark; no remote image service or third-party artwork is required.

- Run all site checks: `python3 -m unittest discover -s tests -v` (stdlib only).
- Optional image authoring: install Pillow in a development environment, then run
  `python3 tools/render_social_previews.py --font /path/to/bold.ttf`.
  The committed cards were rendered with the locally installed Avenir Next Bold font.
  Font files are not distributed and are not requested by visitors or crawlers.
- Publish HTML and images together. If artwork changes later, version its filename
  and update the metadata so image caches do not retain the old design.
- Verify the public page and image return HTTP 200 with `text/html` and `image/png`,
  including for messaging crawler user agents. Never submit the lead form as a test.
- iMessage/WhatsApp choose their own card layout and cache metadata. Existing message
  previews may not refresh. Correct metadata does not force a particular native UI.
