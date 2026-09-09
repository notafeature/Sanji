#!/usr/bin/env node
/**
 * Site builder for sanji.band.
 *
 *   npm run build   renders src/templates/*.html with src/content.json and
 *                   writes index.html, sanji-press-kit.html, 404.html and
 *                   sitemap.xml to the repo root (what GitHub Pages serves).
 *   npm run check   same, but only reports whether the committed output is
 *                   stale (used by CI on pull requests).
 *
 * Edit src/content.json for copy, lineup, festivals, contact. Edit the
 * templates or partials for markup and styles. Never hand-edit the root
 * HTML files: the next build overwrites them.
 */
const fs = require('fs');
const path = require('path');
const Mustache = require('mustache');

// Escape only what is unsafe inside a double-quoted attribute or text node.
// Mustache's default also turns `/` into &#x2F;, which mangles URLs for crawlers.
Mustache.escape = (t) => String(t).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const ROOT = __dirname;
const SRC = path.join(ROOT, 'src');
const CHECK = process.argv.includes('--check');

const read = (p) => fs.readFileSync(path.join(SRC, p), 'utf8');
const content = JSON.parse(read('content.json'));
const dims = JSON.parse(read('image-dims.json'));

// ---- helpers ---------------------------------------------------------------

/** {src,width,height} for an asset path, using dimensions recorded by scripts/images.js */
function img(file) {
  const d = dims[file];
  if (!d) throw new Error(`No dimensions recorded for ${file}. Run \`npm run images\`.`);
  return { src: file, width: d.width, height: d.height };
}

const absolute = (p) => content.site.url + (p.startsWith('/') ? p : '/' + p);

// ---- derived data ----------------------------------------------------------

const site = content.site;
const band = content.band;
const members = content.members.people.map((m) => ({ ...m, rolesText: m.roles.join(' · '), img: img(m.photo) }));
const festivalLogos = content.festivals.logos.map((f) => ({ ...f, img: img(f.file) }));
const photos = content.pressKit.photos.items.map((p) => ({ ...p, img: img(p.web) }));
const wordmark = img(site.wordmark);
const stagePlot = img(content.pressKit.stagePlot.image);
const ogImage = { url: absolute(site.ogImage), ...img(site.ogImage), alt: content.pressKit.photos.items[0].alt };
const year = new Date().getUTCFullYear();

// ---- structured data (schema.org JSON-LD) ----------------------------------

const BAND_ID = absolute('/#band');
const SITE_ID = absolute('/#website');

const musicGroup = {
  '@type': 'MusicGroup',
  '@id': BAND_ID,
  name: site.name,
  url: absolute('/'),
  logo: absolute(site.logoHiRes),
  image: ogImage.url,
  description: content.pages.index.description,
  genre: band.genres,
  foundingLocation: { '@type': 'Place', name: band.basedIn },
  address: { '@type': 'PostalAddress', addressLocality: band.locality, addressRegion: band.region, addressCountry: band.country },
  member: members.map((m) => ({ '@type': 'Person', name: m.name, description: m.rolesText, image: absolute(m.photo) })),
  sameAs: content.socials.map((s) => s.url),
  email: content.booking.email,
  contactPoint: { '@type': 'ContactPoint', contactType: 'booking', email: content.booking.email },
  subjectOf: { '@type': 'WebPage', '@id': absolute(content.pages.pressKit.path) },
};

const webSite = { '@type': 'WebSite', '@id': SITE_ID, name: site.name, url: absolute('/'), publisher: { '@id': BAND_ID } };

function jsonld(page, extra) {
  const webPage = {
    '@type': 'WebPage',
    '@id': absolute(page.path),
    url: absolute(page.path),
    name: page.title,
    description: page.description,
    isPartOf: { '@id': SITE_ID },
    about: { '@id': BAND_ID },
    primaryImageOfPage: ogImage.url,
    inLanguage: 'en',
    ...extra,
  };
  return JSON.stringify({ '@context': 'https://schema.org', '@graph': [webSite, musicGroup, webPage] }, null, 1);
}

// ---- pages -----------------------------------------------------------------

const pageView = (key, ogType, extra) => {
  const p = content.pages[key];
  return {
    ...p,
    canonical: absolute(p.path),
    ogType,
    ogTitle: p.ogTitle || p.title,
    ogDescription: p.ogDescription || p.description,
    ogImage,
    jsonld: jsonld(p, extra),
  };
};

const pages = [
  { template: 'index.html',     page: pageView('index', 'website') },
  { template: 'press-kit.html', page: pageView('pressKit', 'article', { additionalType: 'https://schema.org/MediaObject', keywords: 'press kit, EPK, stage plot, tech rider, booking' }) },
  { template: '404.html',       page: pageView('notFound', 'website') },
];

const partials = {
  head: read('partials/head.html'),
  analytics: read('partials/analytics.html'),
  'base.css': read('partials/base.css'),
  'booking.css': read('partials/booking.css'),
  booking: read('partials/booking.html'),
};

const baseView = {
  ...content,
  members: { ...content.members, people: members },
  festivals: { ...content.festivals, logos: festivalLogos },
  pressKit: { ...content.pressKit, photos: { ...content.pressKit.photos, items: photos } },
  wordmark,
  stagePlot,
  memberCount: members.length,
  year,
};

const outputs = {};
for (const { template, page } of pages) {
  const html = Mustache.render(read(`templates/${template}`), { ...baseView, page }, partials);
  outputs[page.file] = html.replace(/\n{3,}/g, '\n\n');
}

// sitemap: only indexable pages
const today = new Date().toISOString().slice(0, 10);
outputs['sitemap.xml'] =
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  [content.pages.index, content.pages.pressKit]
    .map((p) => `  <url>\n    <loc>${absolute(p.path)}</loc>\n    <lastmod>${today}</lastmod>\n  </url>`)
    .join('\n') +
  '\n</urlset>\n';

// ---- write / check ---------------------------------------------------------

let stale = [];
for (const [file, text] of Object.entries(outputs)) {
  const dest = path.join(ROOT, file);
  const current = fs.existsSync(dest) ? fs.readFileSync(dest, 'utf8') : null;
  // sitemap lastmod changes daily; only compare the URL list when checking.
  const same = file === 'sitemap.xml'
    ? current && current.replace(/<lastmod>.*?<\/lastmod>/g, '') === text.replace(/<lastmod>.*?<\/lastmod>/g, '')
    : current === text;
  if (same) continue;
  stale.push(file);
  if (!CHECK) {
    fs.writeFileSync(dest, text);
    console.log(`wrote ${file} (${(text.length / 1024).toFixed(1)}K)`);
  }
}

if (CHECK) {
  if (stale.length) {
    console.error(`Stale build output: ${stale.join(', ')}\nRun \`npm run build\` and commit the result.`);
    process.exit(1);
  }
  console.log('Build output is up to date.');
} else if (!stale.length) {
  console.log('Nothing changed.');
}
