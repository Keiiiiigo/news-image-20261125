#!/usr/bin/env python3
"""Draw the 25 Nov 2026 news front page as a 1024x1024 PNG (PIL, no network).

Layout (broadsheet, newsprint cream):
  top strip / masthead / story-count line / ticker / 3 illustrated panels /
  12 featured stories (3 cols x 4 rows) / world map with numbered pins +
  index of remaining stories / date-check footer.
Every story is dated Wednesday 25 November 2026 (happened or first reported
that day, in some timezone); the footer names the stories deliberately left
out because they belong to other days.
"""
import json
from PIL import Image, ImageDraw, ImageFont
import textwrap

W = H = 1024
BG = (247, 242, 231)      # newsprint cream
INK = (26, 26, 26)
RED = (185, 28, 28)
MUTED = (90, 84, 72)
RULE = (200, 190, 168)
CARD = (255, 253, 247)
BLUE = (30, 64, 175)
GREEN = (21, 101, 52)
ORANGE = (194, 65, 12)
SEA = (214, 230, 240)
LAND = (216, 200, 158)
LAND_EDGE = (160, 140, 100)

FD = "/usr/share/fonts/truetype/dejavu/"
FB = FD + "DejaVuSerif-Bold.ttf"
FR = FD + "DejaVuSerif.ttf"
SB = FD + "DejaVuSans-Bold.ttf"
SR = FD + "DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, width):
    """Wrap text to pixel width, returning a list of lines."""
    lines = []
    for para in text.split("\n"):
        for raw in textwrap.wrap(para, width=200) or [""]:
            line = raw
            while draw.textlength(line, font=fnt) > width and " " in line:
                cut = line.rfind(" ", 0, int(len(line) * width / max(draw.textlength(line, font=fnt), 1)))
                if cut <= 0:
                    cut = len(line) // 2
                lines.append(line[:cut])
                line = line[cut + 1:]
            lines.append(line)
    return lines


def fit(draw, text, fnt, width, max_lines):
    """Wrap text and clip to max_lines, adding an ellipsis if clipped."""
    lines = wrap(draw, text, fnt, width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .") + "..."
    return lines


def fit_size(draw, text, path, start, width, minimum=12):
    """Largest font size (<= start) at which text fits width."""
    size = start
    while size > minimum and draw.textlength(text, font=font(path, size)) > width:
        size -= 1
    return size


# ---------------------------------------------------------------- stories
# n: display number; region: count-line bucket; tag: label shown on the page;
# head: headline; body: 1-2 line summary; src: outlet; lat/lon: map pin.
# Panels = stories[0:3]; featured = stories[3:15]; index = stories[15:].
STORIES = [
    # ---- panels (top 3) ----
    dict(n=1, region="MIDDLE EAST", tag="MIDDLE EAST - WAR",
         head="Saudi-led coalition strikes Yemen's Hodeidah port",
         body="Coalition jets hit the Houthi-run Red Sea port early on Wednesday after ordering civilians to evacuate, and strike targets in Saada and Amran; the Houthis threaten retaliation.",
         src="Reuters / Al Jazeera", lat=14.80, lon=42.95),
    dict(n=2, region="ASIA", tag="ASIA - SPACE",
         head="China launches Shenzhou-24 with Pakistan's first astronaut",
         body="Long March-2F lifts off from Jiuquan at 08:18, carrying Tang Hongbo, Wu Yi and Pakistani payload specialist Muhammad Zeeshan Ali, the first foreign astronaut to board Tiangong station.",
         src="ECNS / Arab News", lat=40.96, lon=100.29),
    dict(n=3, region="ASIA", tag="ASIA - MARKETS",
         head="Asian stocks tumble as tech rally fizzles",
         body="KOSPI falls 5.54% to 4,728.81, dropping below 5,000; Nikkei down 2.9% and Taiwan 5.1% as Nvidia's 5.9% overnight fall and fresh US tariff fears hit the region.",
         src="Yonhap / Moneycontrol", lat=37.57, lon=126.98),
    # ---- featured (3 cols x 4 rows) ----
    dict(n=4, region="OCEANIA", tag="OCEANIA",
         head="Australia and Solomons sign sweeping security treaty",
         body="Prime ministers Albanese and Wale sign in Canberra, making Australia the islands' defence partner of choice and ruling out any foreign military base.",
         src="The Straits Times", lat=-35.28, lon=149.13),
    dict(n=5, region="EUROPE", tag="EUROPE",
         head="BBC: Russia's own figures show almost 500,000 war dead",
         body="Analysis of leaked death records finds at least 490,334 Russian soldiers died since the 2022 invasion; 65% of 18- to 24-year-olds who died in Russia in 2025 died in the war.",
         src="BBC", lat=55.75, lon=37.62),
    dict(n=6, region="MIDDLE EAST", tag="MIDDLE EAST",
         head="Israeli strike kills four in a Gaza City apartment",
         body="An airstrike hits a residential apartment in western Gaza City near the Shati refugee camp, killing at least four people and wounding several others.",
         src="Al Jazeera", lat=31.50, lon=34.47),
    dict(n=7, region="EUROPE", tag="UK",
         head="Met Police 'still institutionally racist', review finds",
         body="The 389-page Fairfield Review finds 'no good progress' on any of the Casey report's recommendations; further scandals are 'highly likely' unless its culture is addressed.",
         src="The Guardian", lat=51.50, lon=-0.12),
    dict(n=8, region="AMERICAS", tag="USA",
         head="Trump pardons turkeys, laments midterm loss",
         body="At the White House ceremony, Trump pardons two turkeys, Freedom and Feathers, and claims the US would have been '$6 trillion' richer if Republicans had won the midterms.",
         src="AP", lat=38.89, lon=-77.04),
    dict(n=9, region="AMERICAS", tag="USA - IRAN",
         head="Trump: Iran war funding lasts through January",
         body="In an Oval Office interview, Trump says US war funding lasts until roughly the end of January and that Israel's goal of toppling Iran is 'probably doable' but not his objective.",
         src="Jerusalem Post", lat=38.60, lon=-77.20),
    dict(n=10, region="AMERICAS", tag="USA - WEATHER",
         head="Record king tides flood California coast",
         body="Major to extreme coastal flooding hits the San Francisco Bay Area, breaking a November tide record, with Humboldt Bay forecast to reach its highest level ever measured.",
         src="ABC7 / NWS", lat=37.77, lon=-122.42),
    dict(n=11, region="GLOBAL", tag="GLOBAL - SECURITY",
         head="CIA open-source system breached in cyberattack",
         body="An unclassified CIA network used for open-source intelligence was breached, AP reports; no classified information was involved and the issue has been resolved.",
         src="AP", lat=39.20, lon=-76.80),
    dict(n=12, region="OCEANIA", tag="AUSTRALIA",
         head="Australia apologises to LGBTQ veterans",
         body="Defence minister Richard Marles apologises in parliament for decades of discrimination, 34 years after the ban on gay and lesbian people serving was lifted.",
         src="Reuters", lat=-35.60, lon=149.40),
    dict(n=13, region="ASIA", tag="KOREA",
         head="Seoul Metro strike called off at the last minute",
         body="All three unions reach a deal in the early hours: wages capped at +3.5%, a plan to cut 2,212 jobs put on hold, 500 new staff to be hired.",
         src="Yonhap", lat=37.30, lon=127.20),
    dict(n=14, region="ASIA", tag="KOREA",
         head="South Korea births jump 12.2% in September",
         body="25,113 babies born, the 27th straight monthly rise; January-September births up 14.3%, the sharpest nine-month growth since records began in 1981.",
         src="Yonhap", lat=37.85, lon=126.70),
    dict(n=15, region="ASIA", tag="KOREA - DEFENCE",
         head="Seoul protests as Russian jets near its airspace",
         body="South Korea scrambles fighters and summons a Russian military attache after several Russian aircraft enter its air defence zone near Ulleung Island.",
         src="NHK World-Japan", lat=37.48, lon=130.91),
    # ---- index (2 cols) ----
    dict(n=16, region="MIDDLE EAST", tag="MIDDLE EAST",
         head="Houthis threaten Jeddah, all Saudi Red Sea ports",
         body="", src="Reuters", lat=21.49, lon=39.19),
    dict(n=17, region="MIDDLE EAST", tag="MIDDLE EAST",
         head="Saudi defences intercept drones over Ras Tanura",
         body="", src="Al Jazeera", lat=26.65, lon=50.06),
    dict(n=18, region="GLOBAL", tag="GLOBAL",
         head="Oil prices fall on supply-glut fears",
         body="", src="Reuters", lat=51.50, lon=-0.12),
    dict(n=19, region="AMERICAS", tag="AMERICAS",
         head="US pauses joint military operations with Ecuador",
         body="", src="New York Times", lat=-0.18, lon=-78.47),
    dict(n=20, region="AMERICAS", tag="AMERICAS",
         head="Gunmen take about 30 hostage in Cartagena shop",
         body="", src="AFP", lat=10.40, lon=-75.51),
    dict(n=21, region="GLOBAL", tag="GLOBAL",
         head="UN: five women killed each hour by relatives",
         body="", src="AFP", lat=40.75, lon=-73.97),
    dict(n=22, region="GLOBAL", tag="GLOBAL",
         head="Nvidia's Huang apologises to staff, in therapy",
         body="", src="Outlook India", lat=37.37, lon=-121.96),
    dict(n=23, region="AMERICAS", tag="AMERICAS",
         head="Citi weighs return to Venezuela after five years",
         body="", src="Reuters", lat=10.48, lon=-66.88),
    dict(n=24, region="AMERICAS", tag="AMERICAS",
         head="CDC director defends leadership amid measles wave",
         body="", src="AP", lat=33.75, lon=-84.39),
    dict(n=25, region="AFRICA", tag="AFRICA",
         head="EU-Africa leaders hold second day of Luanda summit",
         body="", src="Reuters", lat=-8.84, lon=13.23),
    dict(n=26, region="ASIA", tag="CHINA",
         head="Shanghai leaders pledge loyalty after Chen probe",
         body="", src="Reuters / CNA", lat=31.23, lon=121.47),
    dict(n=27, region="EUROPE", tag="UK",
         head="Ofgem sets January energy price cap",
         body="", src="BBC", lat=52.00, lon=0.50),
    dict(n=28, region="AMERICAS", tag="USA",
         head="Trump floats pardon for Nvidia chief Huang",
         body="", src="Outlook India", lat=38.89, lon=-77.04),
    dict(n=29, region="OCEANIA", tag="NEW ZEALAND",
         head="Tauranga reveals $152,318 payout to ex-chief",
         body="", src="RNZ", lat=-37.69, lon=176.17),
    dict(n=30, region="ASIA", tag="INDIA",
         head="Foxconn India unit faces insolvency suit",
         body="", src="Moneycontrol", lat=12.97, lon=77.59),
]

# Stories deliberately left out because they belong to other days.
DATE_CHECK = ("Left out as other days' news. 23 Nov: Xpeng deal; states sue Musk firms. "
              "24 Nov: Huawei verdict; Hasina plan; Turkish crash; Eisenkot pact; ECHR rulings.")

# ---------------------------------------------------------------- map data
with open("/tmp/ne_110m_land.geojson") as f:
    LAND_GEO = json.load(f)["features"]


def land_layer(box, lon0, lon1, lat0, lat1):
    """Render land polygons onto a layer exactly box-sized (clips overflow)."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    layer = Image.new("RGB", (w, h), SEA)
    ld = ImageDraw.Draw(layer)

    def px(lon, lat):
        return ((lon - lon0) / (lon1 - lon0) * w,
                (lat1 - lat) / (lat1 - lat0) * h)

    for feat in LAND_GEO:
        g = feat["geometry"]
        polys = []
        if g["type"] == "Polygon":
            polys = [g["coordinates"]]
        elif g["type"] == "MultiPolygon":
            polys = g["coordinates"]
        for poly in polys:
            for ring in poly:
                pts = [px(lon, lat) for lon, lat in ring]
                ld.polygon(pts, fill=LAND, outline=LAND_EDGE)
    return layer


def draw_land(img, d, box, lon0, lon1, lat0, lat1):
    """Draw land into box (clipped layer pasted onto img)."""
    layer = land_layer(box, lon0, lon1, lat0, lat1)
    img.paste(layer, (box[0], box[1]))


def pin(d, x, y, n, r=11):
    d.ellipse([x - r, y - r, x + r, y + r], fill=RED, outline=(255, 255, 255), width=2)
    t = str(n)
    f = font(SB, 13 if len(t) < 2 else 11)
    d.text((x, y), t, font=f, fill=(255, 255, 255), anchor="mm")


# ---------------------------------------------------------------- page
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
M = 40  # margin
CW = W - 2 * M  # content width

# ---- top strip ----
d.text((M, 6), "THE WORLD IN ONE DAY", font=font(SB, 17), fill=INK)
d.text((W - M, 6), "DAY 329 OF 2026", font=font(SB, 17), fill=RED, anchor="ra")
d.line([(M, 32), (W - M, 32)], fill=RULE, width=2)

# ---- masthead (auto-fit) ----
mast = "Wednesday 25 November 2026"
msize = fit_size(d, mast, FB, 58, CW)
d.text((M, 40), mast, font=font(FB, msize), fill=INK)
regions = {}
order = ["EUROPE", "MIDDLE EAST", "ASIA", "AFRICA", "AMERICAS", "OCEANIA", "GLOBAL"]
for s in STORIES:
    key = s.get("region") or s["tag"].split(" - ")[0]
    regions[key] = regions.get(key, 0) + 1
region_bits = "  •  ".join(f"{k} {regions[k]}" for k in order if k in regions)
count_line = f"{len(STORIES)} stories, all from Wednesday 25 Nov  •  {region_bits}"
csize = fit_size(d, count_line, SR, 18, CW, minimum=13)
d.text((M, 112), count_line, font=font(SR, csize), fill=MUTED)
d.line([(M, 138), (W - M, 138)], fill=RED, width=5)
d.line([(M, 146), (W - M, 146)], fill=RULE, width=2)

# ---- ticker: short forms of the 3 biggest headlines (auto-fit to one line) ----
def short_head(h, n=38):
    return h if len(h) <= n else h[:n].rsplit(" ", 1)[0] + "..."
tick = "  ◆  ".join(short_head(s["head"]) for s in STORIES[0:3])
tsize = fit_size(d, tick, SB, 19, CW, minimum=14)
d.text((M, 154), tick, font=font(SB, tsize), fill=INK)
d.line([(M, 182), (W - M, 182)], fill=RULE, width=2)

# ---- three illustrated panels ----
PY = 192
PH = 200
PW = (CW - 2 * 16) // 3
for i, s in enumerate(STORIES[0:3]):
    x0 = M + i * (PW + 16)
    x1 = x0 + PW
    # visual area (100 tall), drawn on a clipped layer
    if i == 0:
        # regional map: Red Sea / Yemen, pin on Hodeidah
        layer = land_layer((0, 0, PW, 100), 32, 60, 12, 32)
        ld = ImageDraw.Draw(layer)
        px_ = (42.95 - 32) / 28 * PW
        py_ = (32 - 14.80) / 20 * 100
        pin(ld, px_, py_, 1, r=12)
        ld.text((8, 8), "HODEIDAH", font=font(SB, 14), fill=INK)
        img.paste(layer, (x0, PY))
        d.rectangle([x0, PY, x1, PY + 100], outline=RULE, width=2)
    elif i == 1:
        # regional map: East Asia, pin on Jiuquan
        layer = land_layer((0, 0, PW, 100), 75, 135, 18, 54)
        ld = ImageDraw.Draw(layer)
        px_ = (100.29 - 75) / 60 * PW
        py_ = (54 - 40.96) / 36 * 100
        pin(ld, px_, py_, 2, r=12)
        ld.text((8, 76), "JIUQUAN  •  08:18", font=font(SB, 14), fill=INK)
        img.paste(layer, (x0, PY))
        d.rectangle([x0, PY, x1, PY + 100], outline=RULE, width=2)
    else:
        # markets bar chart: KOSPI -5.54, Nikkei -2.9, Taiwan -5.1
        d.rectangle([x0, PY, x1, PY + 100], fill=SEA, outline=RULE, width=2)
        bars = [("KOSPI", -5.54), ("NIKKEI", -2.9), ("TAIWAN", -5.1)]
        bx, bw = x0 + 18, (PW - 36) // 3
        base = PY + 88
        for j, (name, v) in enumerate(bars):
            hgt = int(abs(v) / 6.0 * 56)
            cx = bx + j * bw
            d.rectangle([cx + 8, base - hgt, cx + bw - 8, base], fill=RED)
            d.text((cx + bw // 2, base - hgt - 18), f"{v}%", font=font(SB, 15), fill=RED, anchor="ma")
            d.text((cx + bw // 2, base + 4), name, font=font(SB, 12), fill=MUTED, anchor="ma")
    # caption
    cy = PY + 108
    d.text((x0, cy), s["tag"], font=font(SB, 14), fill=RED)
    y = cy + 20
    for line in fit(d, s["head"], font(FB, 19), PW, 2):
        d.text((x0, y), line, font=font(FB, 19), fill=INK)
        y += 23
    for line in fit(d, s["body"], font(SR, 13), PW, 2):
        d.text((x0, y), line, font=font(SR, 13), fill=MUTED)
        y += 16

# ---- featured stories: 3 cols x 4 rows ----
FY = PY + PH + 14
FH = 76
FW = (CW - 2 * 16) // 3
featured = STORIES[3:15]
for idx, s in enumerate(featured):
    col, row = idx % 3, idx // 3
    x0 = M + col * (FW + 16)
    y0 = FY + row * FH
    d.rectangle([x0, y0 + 4, x0 + 22, y0 + 26], fill=INK)
    d.text((x0 + 11, y0 + 15), str(s["n"]), font=font(SB, 13), fill=(255, 255, 255), anchor="mm")
    d.text((x0 + 30, y0 + 4), s["tag"], font=font(SB, 13), fill=RED)
    y = y0 + 22
    for line in fit(d, s["head"], font(SB, 16), FW, 2):
        d.text((x0, y), line, font=font(SB, 16), fill=INK)
        y += 19
    for line in fit(d, s["body"], font(SR, 13), FW, 1):
        d.text((x0, y), line, font=font(SR, 13), fill=MUTED)
        y += 16
    if col < 2:
        d.line([(x0 + FW + 8, y0 + 4), (x0 + FW + 8, y0 + FH - 8)], fill=RULE, width=1)

# ---- bottom band: world map + index ----
BY = FY + 4 * FH + 12
BH = 1024 - BY - 60
d.line([(M, BY - 6), (W - M, BY - 6)], fill=INK, width=3)
map_w = 470
d.rectangle([M, BY, M + 170, BY + 22], fill=INK)
d.text((M + 8, BY + 4), "WHERE IT HAPPENED", font=font(SB, 13), fill=(255, 255, 255))
d.rectangle([M, BY + 26, M + map_w, BY + BH - 4], fill=SEA, outline=RULE, width=2)
draw_land(img, d, (M, BY + 26, M + map_w, BY + BH - 4), -180, 180, -60, 85)
for s in STORIES:
    if s.get("lat") is None:
        continue
    px_ = M + (s["lon"] + 180) / 360 * map_w
    py_ = BY + 26 + (85 - s["lat"]) / 145 * (BH - 30)
    # small deterministic jitter so clustered pins stay readable
    ox = ((s["n"] * 37) % 7 - 3) * 2
    oy = ((s["n"] * 53) % 7 - 3) * 2
    pin(d, px_ + ox, py_ + oy, s["n"], r=10 if s["n"] < 10 else 11)

ix = M + map_w + 20
iw = W - M - ix
d.text((ix, BY + 4), "ALSO ON WEDNESDAY 25 NOV", font=font(SB, 15), fill=INK)
idx_stories = STORIES[15:39]
col_w = (iw - 16) // 2
for j, s in enumerate(idx_stories):
    col, row = j % 2, j // 2
    x0 = ix + col * (col_w + 16)
    y0 = BY + 30 + row * 19
    d.text((x0, y0), str(s["n"]), font=font(SB, 13), fill=RED)
    for line in fit(d, s["head"], font(SB, 13), col_w - 26, 1):
        d.text((x0 + 24, y0), line, font=font(SB, 13), fill=INK)
d.text((ix, BY + BH - 34), "Sources: Reuters, AP, AFP, BBC, Al Jazeera, Yonhap, NHK,",
       font=font(SR, 12), fill=MUTED)
d.text((ix, BY + BH - 18), "The Guardian, NYT, Straits Times, ECNS, RNZ, Moneycontrol.",
       font=font(SR, 12), fill=MUTED)

# ---- footer ----
d.line([(M, 1024 - 52), (W - M, 1024 - 52)], fill=RULE, width=2)
for line in fit(d, "DATE CHECK  " + DATE_CHECK, font(SR, 12), CW, 1):
    d.text((M, 1024 - 46), line, font=font(SR, 12), fill=MUTED)
for line in fit(d, "Every story here happened or was first reported on Wednesday 25 November 2026. "
                   "Maps are original drawings from public land data.",
                font(SR, 12), CW, 1):
    d.text((M, 1024 - 28), line, font=font(SR, 12), fill=MUTED)

img.save("entry.png", optimize=True)
print("saved entry.png")
import os
print("bytes:", os.path.getsize("entry.png"))
