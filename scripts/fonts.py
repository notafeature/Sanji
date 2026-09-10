#!/usr/bin/env python3
"""
Builds the self-hosted web fonts in assets/fonts/ from the variable TTFs
published in Google's font repository (SIL Open Font License; licence texts
are kept in src/fonts/). The TTFs are downloaded into src/fonts/ on first run
and are not committed.

    npm run fonts        (or: python3 scripts/fonts.py)

Each output is trimmed to the Latin character set and to the weight range the
site actually uses, then packed as WOFF2. Requires: pip install fonttools brotli
"""
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src/fonts"
OUT = ROOT / "assets/fonts"

# Google Fonts' "latin" range plus Latin-1 Supplement and Latin Extended-A, which
# covers names like Kouyaté, Keïta, Touré, and the typographic punctuation in the bios.
UNICODES = "U+0000-024F,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"

UPSTREAM = "https://raw.githubusercontent.com/google/fonts/main/ofl"

JOBS = [
    # (upstream family dir, source file, output, axis limits: pinned value or (min, max))
    ("dmsans",            "DMSans[opsz,wght].ttf",              "dm-sans.woff2",                   {"wght": (400, 600), "opsz": 14}),
    ("cormorantgaramond", "CormorantGaramond[wght].ttf",        "cormorant-garamond.woff2",        {"wght": (400, 700)}),
    ("cormorantgaramond", "CormorantGaramond-Italic[wght].ttf", "cormorant-garamond-italic.woff2", {"wght": (400, 700)}),
]


def fetch(family, src):
    """Download the variable TTF from Google's font repo if it is not already here."""
    dest = SRC / src
    if dest.exists():
        return
    SRC.mkdir(parents=True, exist_ok=True)
    url = f"{UPSTREAM}/{family}/{urllib.request.quote(src)}"
    print(f"downloading {url}")
    urllib.request.urlretrieve(url, dest)


def build(src, out, limits):
    font = TTFont(SRC / src, lazy=False)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]      # keep kerning, ligatures, etc.
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=subset.parse_unicodes(UNICODES))
    sub.subset(font)
    font = instancer.instantiateVariableFont(font, limits, inplace=False, updateFontNames=False)
    OUT.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(OUT / out)
    return (SRC / src).stat().st_size, (OUT / out).stat().st_size


if __name__ == "__main__":
    for family, src, out, limits in JOBS:
        fetch(family, src)
        before, after = build(src, out, limits)
        print(f"{out:36s} {before/1024:6.0f}K -> {after/1024:5.0f}K")
