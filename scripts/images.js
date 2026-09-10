#!/usr/bin/env node
/**
 * Image pipeline. Reads originals from src/images/ and assets/photos/band/,
 * writes optimized web versions into assets/, and records their pixel
 * dimensions in src/image-dims.json so build.js can emit width/height
 * attributes (no layout shift) without needing sharp at build time.
 *
 * Add a new image: drop the original in src/images/, add a job below,
 * run `npm run images`, then `npm run build`.
 */
const path = require('path');
const fs = require('fs');
const sharp = require('sharp');

const ROOT = path.resolve(__dirname, '..');

// Festival logos render at most 185x125 CSS px (Salamander 420x105), so a
// 400px box (900px for the banner) covers 2x retina with room to spare.
const LOGO = { width: 400, height: 400, fit: 'inside', withoutEnlargement: true };
const MEMBER = { width: 240, height: 240, fit: 'cover' }; // shown at 100x100

const jobs = [
  // Festival logos
  { src: 'src/images/festivals/globalquerque.avif',        out: 'assets/logos/festivals/globalquerque.webp',        resize: LOGO, webp: { quality: 88 } },
  { src: 'src/images/festivals/crestone-energy-fair.webp', out: 'assets/logos/festivals/crestone-energy-fair.webp', resize: LOGO, webp: { quality: 88 } },
  { src: 'src/images/festivals/unison-festival.png',       out: 'assets/logos/festivals/unison-festival.webp',      resize: LOGO, webp: { quality: 88 } },
  { src: 'src/images/festivals/tribal-vision.webp',        out: 'assets/logos/festivals/tribal-vision.webp',        resize: LOGO, webp: { quality: 88 } },
  { src: 'src/images/festivals/convergence.png',           out: 'assets/logos/festivals/convergence.webp',          resize: LOGO, webp: { quality: 88 } },
  { src: 'src/images/festivals/salamander-fest.png',       out: 'assets/logos/festivals/salamander-fest.webp',      resize: { width: 900, withoutEnlargement: true }, webp: { quality: 88 } },

  // Wordmark (hero + press kit header). 965px wide original, keep size.
  { src: 'src/images/logos/sanji-logo-transparent.png',    out: 'assets/logos/sanji-logo.webp', webp: { quality: 92 } },

  // Member portraits
  { src: 'src/images/photos/members/miles-anderson.jpg',   out: 'assets/photos/members/miles-anderson.jpg',  resize: MEMBER, jpeg: { quality: 84, mozjpeg: true } },
  { src: 'src/images/photos/members/rob-usher.jpg',        out: 'assets/photos/members/rob-usher.jpg',       resize: MEMBER, jpeg: { quality: 84, mozjpeg: true } },
  { src: 'src/images/photos/members/mitchell-olson.jpg',   out: 'assets/photos/members/mitchell-olson.jpg',  resize: MEMBER, jpeg: { quality: 84, mozjpeg: true } },
  { src: 'src/images/photos/members/fred-simpson.png',     out: 'assets/photos/members/fred-simpson.jpg',    resize: MEMBER, jpeg: { quality: 84, mozjpeg: true } },

  // Backgrounds (CSS url()). Portrait hero is used as cover, keep 1800 wide.
  { src: 'src/images/photos/taos-aurora.jpg',              out: 'assets/photos/taos-aurora.webp',        resize: { width: 1800, withoutEnlargement: true }, webp: { quality: 74 } },
  { src: 'src/images/photos/taos-aurora-footer.jpg',       out: 'assets/photos/taos-aurora-footer.webp', resize: { width: 1800, withoutEnlargement: true }, webp: { quality: 74 } },

  // Stage plot (press kit inline). Diagram, so keep it crisp.
  { src: 'src/images/epk/stage_plot_color_light.png',      out: 'assets/epk/stage-plot.webp', resize: { width: 1600, withoutEnlargement: true }, webp: { quality: 90 } },

  // Social preview: 1200x630 is the Open Graph / Twitter standard.
  { src: 'assets/photos/band/sanji-unison-festival-01.jpg', out: 'assets/photos/og-cover.jpg', resize: { width: 1200, height: 630, fit: 'cover', position: 'attention' }, jpeg: { quality: 82, mozjpeg: true } },

  // Press kit photo previews (full-res originals stay as the download).
  { src: 'assets/photos/band/sanji-unison-festival-01.jpg', out: 'assets/photos/band/sanji-unison-festival-01-web.jpg', resize: { width: 1400, withoutEnlargement: true }, jpeg: { quality: 78, mozjpeg: true } },
  { src: 'assets/photos/band/sanji-unison-festival-02.jpg', out: 'assets/photos/band/sanji-unison-festival-02-web.jpg', resize: { width: 1400, withoutEnlargement: true }, jpeg: { quality: 78, mozjpeg: true } },
];

(async () => {
  const dims = {};
  for (const job of jobs) {
    const src = path.join(ROOT, job.src);
    const out = path.join(ROOT, job.out);
    fs.mkdirSync(path.dirname(out), { recursive: true });
    let img = sharp(src).rotate(); // honour EXIF orientation
    if (job.resize) img = img.resize(job.resize);
    if (job.webp) img = img.webp(job.webp);
    if (job.jpeg) img = img.jpeg(job.jpeg);
    if (job.png) img = img.png(job.png);
    const info = await img.toFile(out);
    dims[job.out] = { width: info.width, height: info.height };
    const before = fs.statSync(src).size, after = info.size;
    console.log(`${job.out.padEnd(58)} ${info.width}x${info.height}  ${(before/1024).toFixed(0)}K -> ${(after/1024).toFixed(0)}K`);
  }
  // Originals that are linked directly (downloads) also need dimensions.
  for (const f of ['assets/photos/band/sanji-unison-festival-01.jpg', 'assets/photos/band/sanji-unison-festival-02.jpg', 'assets/logos/sanji-logo-hd.png']) {
    const m = await sharp(path.join(ROOT, f)).metadata();
    dims[f] = { width: m.width, height: m.height };
  }
  fs.writeFileSync(path.join(ROOT, 'src/image-dims.json'), JSON.stringify(dims, null, 2) + '\n');
  console.log('wrote src/image-dims.json');
})().catch(e => { console.error(e); process.exit(1); });
