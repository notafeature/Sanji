# sanji.band work list

Plain checklist. Tick things off in a PR, or delete lines that no longer matter.
Everything on the site itself is driven by `src/content.json`; see README.md.

## Now

- [ ] Delete the merged `claude/*` branches on GitHub (Branches page, trash icon).
- [ ] Turn on Settings > General > Pull Requests > "Automatically delete head branches".

## Next

- [ ] **Shows.** There are no dates on the site. Add a `shows` array to
      `src/content.json` (date, venue, city, ticket link), render a Shows
      section on the homepage only when the array has upcoming entries, and
      emit `MusicEvent` structured data so Google can show dates in results.
      Alternative: a Bandsintown or Songkick widget if the band already
      maintains dates there.
- [ ] **Live video in the press kit.** The homepage has the YouTube embed; the
      kit does not. Bookers decide from footage. Add the embed, or a link to a
      full live set.
- [ ] **Two quotes for the press kit.** One from a festival director, one from
      a venue. A line each, with name and event.
- [ ] **Current four-piece promo photo.** Both kit photos are from behind the
      band; the only front-facing shot is the old seven-person lineup. One
      front-facing shot of the current lineup, for the kit and as the social
      preview image (`site.ogImage`).
- [ ] **Fee and travel line** in the press kit's At a Glance: touring party of
      four, based in Taos, fees on request.
- [ ] **Streaming links** (Spotify, Bandcamp, Apple Music) if recordings exist:
      footer, press kit, and `socials` in content.json so they land in the
      structured data too.
- [ ] **YouTube click-to-play.** Today the YouTube iframe downloads the whole
      YouTube player (roughly half a megabyte of script) for every visitor,
      whether or not they press play. Replace it with the video's thumbnail
      and a play button; on click, swap in the real iframe with autoplay. The
      visitor sees the same thing, and the page only pays for YouTube when
      someone actually watches.
- [ ] **Google Search Console.** Verify sanji.band, submit `sitemap.xml`. This
      is the only way to see whether Google has indexed the pages and what
      searches bring people in.

## Later

- [ ] **Admin panel for calendar and events, with a manager login.** GitHub
      Pages is static, so this needs one of:
      1. *Decap CMS* (formerly Netlify CMS): a `/admin` page on the site, login
         through GitHub, edits `src/content.json` and commits; the Build site
         Action rebuilds. Zero infrastructure; the manager needs a GitHub
         account with write access.
      2. *Cloudflare Worker + D1 + Cloudflare Access*: an events API the page
         fetches at load, with a small admin UI behind an email login. No
         GitHub involvement for the manager; both Cloudflare accounts already
         exist.
      3. *External calendar as the source* (Bandsintown, Google Calendar): the
         manager edits there, the site reads it.
      Recommend 1 if the manager is comfortable with GitHub, 2 if not.
