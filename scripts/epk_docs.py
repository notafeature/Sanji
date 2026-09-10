#!/usr/bin/env python3
"""
Generates the EPK PDFs (tech rider and input list) from src/content.json and
src/epk.json, in the site's visual language, at the paths the press kit links.

    npm run docs        (or: python3 scripts/epk_docs.py)

Requires: pip install reportlab pillow
"""
import json
from pathlib import Path

from io import BytesIO

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path(__file__).resolve().parent.parent
content = json.loads((ROOT / "src/content.json").read_text())
epk = json.loads((ROOT / "src/epk.json").read_text())

SITE = content["site"]
BOOKING = content["booking"]
LOGO = ROOT / "src/images/logos/sanji-logo-transparent.png"


def logo_reader(width_px=560):
    """The wordmark PNG is 965px wide; embed a smaller copy to keep the PDFs light."""
    im = PILImage.open(LOGO).convert("RGBA")
    im = im.resize((width_px, round(im.height * width_px / im.width)), PILImage.LANCZOS)
    buf = BytesIO()
    im.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return ImageReader(buf)


LOGO_READER = logo_reader()

OUT_RIDER = ROOT / "assets/epk/Stage Rider/Sanji EPK - Tech Rider.pdf"   # linked externally: keep path
OUT_INPUTS = ROOT / "assets/epk/Stage Plot/Sanji_Input_List.pdf"         # linked externally: keep path

# Palette (mirrors src/partials/base.css)
DEEP_EARTH = colors.HexColor("#2C1810")
OCHRE = colors.HexColor("#C4873B")
BURNT = colors.HexColor("#A0522D")
WARM_CREAM = colors.HexColor("#F5EDE0")
SAND = colors.HexColor("#E8D5B7")
DUST = colors.HexColor("#D4B896")
NIGHT = colors.HexColor("#15100C")
POP_YELLOW = colors.HexColor("#F4C518")
INK = colors.HexColor("#2C1810")
MUTED = colors.HexColor("#6B5A4E")

PAGE_W, PAGE_H = letter
MARGIN = 0.8 * inch
HEADER_H = 1.55 * inch

# ---- styles ---------------------------------------------------------------

body = ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=14.5, textColor=INK)
small = ParagraphStyle("small", parent=body, fontSize=8.5, leading=11.5, textColor=MUTED)
h2 = ParagraphStyle("h2", fontName="Times-Bold", fontSize=15, leading=18, textColor=DEEP_EARTH, spaceBefore=14, spaceAfter=6)
eyebrow = ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=BURNT, spaceAfter=2)
cell = ParagraphStyle("cell", parent=body, fontSize=9, leading=12)
cell_muted = ParagraphStyle("cell_muted", parent=cell, textColor=MUTED)
cell_head = ParagraphStyle("cell_head", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=DEEP_EARTH)
cell_ch = ParagraphStyle("cell_ch", parent=cell, fontName="Helvetica-Bold", alignment=TA_CENTER)
need_item = ParagraphStyle("need_item", fontName="Helvetica-Bold", fontSize=9.5, leading=12.5, textColor=DEEP_EARTH)
need_ch = ParagraphStyle("need_ch", parent=small, fontName="Helvetica", textColor=BURNT)


def spaced(text):
    """Letter-spaced uppercase label, like the site's section labels."""
    return " ".join(text.upper())


# ---- page furniture ---------------------------------------------------------

def draw_header(c, doc, title):
    c.saveState()
    # Dark band with the wordmark, like the site's hero
    c.setFillColor(NIGHT)
    c.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, stroke=0, fill=1)
    c.setFillColor(DEEP_EARTH)
    c.rect(0, PAGE_H - HEADER_H, PAGE_W, 3, stroke=0, fill=1)
    logo_w = 1.9 * inch
    logo_h = logo_w * 259 / 965
    c.drawImage(LOGO_READER, MARGIN, PAGE_H - HEADER_H + (HEADER_H - logo_h) / 2 - 2, logo_w, logo_h, mask="auto")
    # Title block, right aligned
    c.setFillColor(POP_YELLOW)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - HEADER_H / 2 + 14, spaced(SITE["name"]))
    c.setFillColor(WARM_CREAM)
    c.setFont("Times-Bold", 22)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - HEADER_H / 2 - 8, title)
    c.setFillColor(OCHRE)
    c.setFont("Helvetica", 7.5)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - HEADER_H / 2 - 24, spaced(SITE["tagline"].replace(" · ", "  ·  ")))
    c.restoreState()


def draw_footer(c, doc):
    c.saveState()
    y = 0.55 * inch
    c.setStrokeColor(SAND)
    c.setLineWidth(0.8)
    c.line(MARGIN, y + 16, PAGE_W - MARGIN, y + 16)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(MUTED)
    c.drawString(MARGIN, y + 3, f"{BOOKING['label']}: {BOOKING['title']}  ·  {BOOKING['email']}  ·  {SITE['url'].replace('https://', '')}")
    c.drawRightString(PAGE_W - MARGIN, y + 3, f"Revised {epk['revised']}  ·  Page {doc.page}")
    c.restoreState()


def make_doc(path, title, subject):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path), pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=HEADER_H + 0.35 * inch, bottomMargin=1.0 * inch,
        title=f"{SITE['name']} {title}", author=SITE["name"], subject=subject, creator="sanji.band EPK generator",
    )
    def on_page(c, d):
        draw_header(c, d, title)
        draw_footer(c, d)
    return doc, on_page


def booking_block():
    """Same language as the site footer."""
    t = Table(
        [[Paragraph(spaced(BOOKING["label"]), ParagraphStyle("bl", parent=eyebrow, textColor=OCHRE))],
         [Paragraph(BOOKING["title"], ParagraphStyle("bt", fontName="Times-Bold", fontSize=13, leading=16, textColor=WARM_CREAM))],
         [Paragraph(f'<a href="mailto:{BOOKING["email"]}" color="#F4C518">{BOOKING["email"]}</a>', ParagraphStyle("be", parent=body, textColor=POP_YELLOW))]],
        colWidths=[PAGE_W - 2 * MARGIN],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 14), ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, 0), 12), ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
        ("TOPPADDING", (0, 1), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -2), 2),
        ("LINEABOVE", (0, 0), (-1, 0), 2, OCHRE),
    ]))
    return t


# ---- tech rider -------------------------------------------------------------

def build_rider():
    r = epk["rider"]
    doc, on_page = make_doc(OUT_RIDER, r["title"], "Technical requirements for live performance")
    W = PAGE_W - 2 * MARGIN
    story = [
        Paragraph(r["intro"], ParagraphStyle("lead", fontName="Times-Roman", fontSize=12.5, leading=17, textColor=DEEP_EARTH)),
        Spacer(1, 6),
        Paragraph(r["setLengths"], body),
        Paragraph("What we need from the venue", h2),
    ]
    rows = [[Paragraph(spaced("Item"), cell_head), Paragraph(spaced("Detail"), cell_head), Paragraph(spaced("Channels"), cell_head)]]
    for n in r["needs"]:
        rows.append([Paragraph(n["item"], need_item), Paragraph(n["detail"], cell), Paragraph(n["channels"] or " ", need_ch)])
    t = Table(rows, colWidths=[1.45 * inch, W - 1.45 * inch - 1.35 * inch, 1.35 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SAND),
        ("LINEBELOW", (0, 0), (-1, 0), 1, OCHRE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, WARM_CREAM]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, SAND),
    ]))
    story += [
        t,
        Spacer(1, 10),
        Paragraph(r["channelSummary"], body),
        Spacer(1, 4),
        Paragraph(r["bandProvides"], body),
        Spacer(1, 4),
        Paragraph(r["moreInfo"], small),
        KeepTogether([Spacer(1, 18), booking_block()]),
    ]
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return OUT_RIDER


# ---- input list -------------------------------------------------------------

def build_input_list():
    il = epk["inputList"]
    doc, on_page = make_doc(OUT_INPUTS, il["title"], "Channel and patch list matching the stage plot")
    W = PAGE_W - 2 * MARGIN
    story = [Paragraph(il["subtitle"], body), Spacer(1, 6)]
    rows = [[Paragraph(spaced(c), cell_head) for c in il["columns"]]]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), SAND),
        ("LINEBELOW", (0, 0), (-1, 0), 1, OCHRE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, WARM_CREAM]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, SAND),
    ]
    for i, c in enumerate(il["channels"], start=1):
        st = cell_muted if c.get("optional") else cell
        rows.append([Paragraph(str(c["ch"]), cell_ch), Paragraph(c["source"], st), Paragraph(c["mic"], st),
                     Paragraph(c["stand"], st), Paragraph(c["notes"] or " ", st)])
    t = Table(rows, colWidths=[0.45 * inch, 1.45 * inch, 1.15 * inch, 1.0 * inch, W - 4.05 * inch], repeatRows=1)
    t.setStyle(TableStyle(style))
    story += [
        t,
        Spacer(1, 8),
        Paragraph("Greyed rows are optional secondary DIs and can be dropped on a smaller console.", small),
        KeepTogether([Spacer(1, 14), booking_block()]),
    ]
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return OUT_INPUTS


if __name__ == "__main__":
    for out in (build_rider(), build_input_list()):
        print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1024:.0f}K)")
