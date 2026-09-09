# Working on sanji.band

- Copy and data live in `src/content.json`. Markup in `src/templates/`, shared pieces in `src/partials/`.
- `index.html`, `sanji-press-kit.html`, `404.html` and `sitemap.xml` are **generated**. Never edit them directly; edit the source and run `npm run build`, then commit both.
- New or replaced images go through `scripts/images.js` (`npm run images`) so the build has their dimensions.
- The EPK PDF paths under `assets/epk/` are linked from outside the site; do not rename them.
- See README.md for the full workflow.
