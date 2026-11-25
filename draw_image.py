#!/usr/bin/env python3
"""Draw the 25 Nov 2026 news front page as a 1024x1024 PNG (PIL, no network).

Design language follows the two winning entries (24 Nov: 35 stories;
23 Nov: 33 stories):
  masthead + story/region count line + one-line ticker of 3 complete short
  headlines + big-number stat strip + 3 illustrated panels with real drawn
  scenes and number boxes + featured stories with a small icon, number badge,
  region tag, status tag, complete headline, complete deck and source +
  world map with region-coloured pins and a legend + "ALSO ON" index of
  complete one-line headlines + a complete DATE CHECK footer.
IRON RULE: zero ellipses anywhere. Text is shortened to fit, never truncated.
The fit helpers below raise instead of truncating, so a bad fit fails loudly.
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont

W = H = 1024
BG = (247, 242, 231)      # newsprint cream
INK = (26, 26, 26)
RED = (185, 28, 28)
MUTED = (96, 90, 78)
RULE = (200, 190, 168)
CARD = (255, 253, 247)
SEA = (214, 230, 240)
LAND = (216, 200, 158)
LAND_EDGE = (160, 140, 100)
NAVY = (11, 30, 58)

FD = "/usr/share/fonts/truetype/dejavu/"
FB = FD + "DejaVuSerif-Bold.ttf"   # masthead + panel headlines
FR = FD + "DejaVuSerif.ttf"
SB = FD + "DejaVuSans-Bold.ttf"
SR = FD + "DejaVuSans.ttf"

REGION_COLOUR = {
    "EUROPE": (29, 78, 216),
    "MIDDLE EAST": (185, 28, 28),
    "ASIA": (194, 65, 12),
    "AFRICA": (21, 128, 61),
    "AMERICAS": (124, 58, 237),
    "OCEANIA": (15, 118, 110),
    "GLOBAL": (87, 83, 78),
}
TAG_COLOUR = {"CONFIRMED": (21, 128, 61), "OFFICIAL": (29, 78, 216),
              "CLAIM": (194, 65, 12)}


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap_lines(draw, text, fnt, width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_lines(draw, text, path, start, width, max_lines, minimum=10):
    """Largest font size at which text wraps to <= max_lines. Raises if it
    cannot fit even at `minimum` (fix the wording instead of truncating)."""
    size = start
    while size >= minimum:
        fnt = font(path, size)
        lines = wrap_lines(draw, text, fnt, width)
        if len(lines) <= max_lines:
            return fnt, lines
        size -= 1
    raise ValueError(f"cannot fit in {max_lines} lines: {text!r}")


def fit_one_line(draw, text, path, start, width, minimum=10):
    size = start
    while size >= minimum:
        fnt = font(path, size)
        if draw.textlength(text, font=fnt) <= width:
            return fnt
        size -= 1
    raise ValueError(f"cannot fit on one line: {text!r}")


def fit_size(draw, text, path, start, width, minimum=10):
    size = start
    while size > minimum and draw.textlength(text, font=font(path, size)) > width:
        size -= 1
    return size


# ---------------------------------------------------------------- stories
# n: display number; region: count-line bucket + pin colour; tag: region label;
# status: CONFIRMED / OFFICIAL / CLAIM; head: headline; body: deck;
# src: outlet; place: short place label; lat/lon: map pin; dx/dy: pin offset.
STORIES = [
    dict(n=1, region="MIDDLE EAST", tag="MIDDLE EAST - WAR", status="CONFIRMED",
         head="Saudi-led coalition strikes Yemen's Hodeidah port",
         body="Jets hit the Red Sea port after an evacuation order, and targets in Saada and Amran.",
         src="Al Jazeera", place="HODEIDAH, YEMEN", lat=14.80, lon=42.95),
    dict(n=2, region="ASIA", tag="ASIA - SPACE", status="OFFICIAL",
         head="China launches Shenzhou-24 with Pakistan's first astronaut",
         body="Long March-2F lifts off from Jiuquan at 08:18 with Tang Hongbo, Wu Yi and Pakistan's Zeeshan Ali.",
         src="Reuters / Xinhua", place="JIUQUAN, CHINA", lat=40.96, lon=100.29),
    dict(n=3, region="ASIA", tag="ASIA - MARKETS", status="CONFIRMED",
         head="Asian stocks tumble as tech rally fizzles",
         body="KOSPI falls 5.54% to 4,728.81, below 5,000. Nikkei is down 2.9% and Taiwan 5.1% as Nvidia slides.",
         src="Yonhap / Moneycontrol", place="SEOUL, KOREA", lat=37.57, lon=126.98),
    dict(n=4, region="OCEANIA", tag="OCEANIA", status="OFFICIAL",
         head="Australia and Solomons sign sweeping security treaty",
         body="Albanese and Wale sign in Canberra. Australia becomes the islands' defence partner of choice.",
         src="Reuters", place="CANBERRA", lat=-35.28, lon=149.13, dx=-7, dy=-5, icon="doc"),
    dict(n=5, region="EUROPE", tag="EUROPE", status="CONFIRMED",
         head="BBC: Russia's own figures show 490,334 war dead",
         body="Leaked death records count at least 490,334 Russian soldiers dead since the 2022 invasion.",
         src="BBC", place="MOSCOW", lat=55.75, lon=37.62, icon="flag"),
    dict(n=6, region="MIDDLE EAST", tag="MIDDLE EAST", status="CONFIRMED",
         head="Israeli strike kills four in a Gaza City apartment",
         body="An airstrike hits a home near the Shati camp in western Gaza City, killing four people.",
         src="Al Jazeera", place="GAZA CITY", lat=31.50, lon=34.47, icon="burst"),
    dict(n=7, region="EUROPE", tag="UK", status="OFFICIAL",
         head="Met Police \u2018still institutionally racist\u2019, review finds",
         body="The 389-page Fairfield Review finds \u2018no good progress\u2019 on any Casey recommendation.",
         src="The Guardian", place="LONDON", lat=51.50, lon=-0.12, dx=-8, dy=-6, icon="shield"),
    dict(n=8, region="AMERICAS", tag="USA", status="CONFIRMED",
         head="Trump pardons turkeys, laments midterm loss",
         body="Freedom and Feathers are pardoned. Trump claims the US would be \u2018$6 trillion\u2019 richer.",
         src="AP", place="WASHINGTON", lat=38.89, lon=-77.04, dx=-9, dy=-7, icon="feather"),
    dict(n=9, region="GLOBAL", tag="USA - IRAN", status="CLAIM",
         head="Trump: Iran war funding lasts through January",
         body="Trump says war funding runs to the end of January. Toppling Iran is \u2018probably doable\u2019, not his goal.",
         src="Jerusalem Post", place="WASHINGTON", lat=38.60, lon=-77.20, dx=9, dy=-7, icon="target"),
    dict(n=10, region="AMERICAS", tag="USA - WEATHER", status="CONFIRMED",
         head="Record king tides flood California coast",
         body="San Francisco sets a November tide record. Humboldt Bay is forecast at 10\u201311 ft, near its all-time high.",
         src="ABC7 / NWS", place="SAN FRANCISCO", lat=37.77, lon=-122.42, dx=-7, dy=-5, icon="wave"),
    dict(n=11, region="GLOBAL", tag="GLOBAL - SECURITY", status="CONFIRMED",
         head="CIA open-source system breached in cyberattack",
         body="An unclassified CIA network is breached; no classified data is involved and the issue is resolved.",
         src="NYT / CNN", place="LANGLEY, VA", lat=39.20, lon=-76.80, dx=9, dy=7, icon="lock"),
    dict(n=12, region="OCEANIA", tag="AUSTRALIA", status="OFFICIAL",
         head="Australia apologises to LGBTQ veterans",
         body="Defence minister Richard Marles apologises in parliament, 34 years after the service ban was lifted.",
         src="Reuters", place="CANBERRA", lat=-35.60, lon=149.40, dx=7, dy=5, icon="heart"),
    dict(n=13, region="ASIA", tag="KOREA", status="CONFIRMED",
         head="Seoul Metro strike called off at the last minute",
         body="A deal in the early hours: wages capped at +3.5%, 2,212 job cuts on hold, 500 new staff to be hired.",
         src="Yonhap", place="SEOUL", lat=37.57, lon=126.98, dx=-10, dy=-6, icon="train"),
    dict(n=14, region="ASIA", tag="KOREA", status="OFFICIAL",
         head="South Korea births jump 12.2% in September",
         body="25,113 babies are born, the 27th straight monthly rise. January\u2013September births are up 14.3%.",
         src="Yonhap", place="SEOUL", lat=37.57, lon=126.98, dx=10, dy=-6, icon="person"),
    dict(n=15, region="ASIA", tag="KOREA", status="OFFICIAL",
         head="Korean K-goods exports hit a record $28.65bn",
         body="Beauty exports reach $13.65bn and food $10.94bn. Total exports pass $1 trillion for the first time.",
         src="Yonhap", place="SEOUL", lat=37.57, lon=126.98, dx=0, dy=8, icon="bag"),
    # ---- index (complete one-line headlines, "Place: headline") ----
    dict(n=16, region="MIDDLE EAST", status="CLAIM",
         head="Jeddah: Houthis threaten all Saudi ports",
         src="Al Jazeera", lat=21.49, lon=39.19),
    dict(n=17, region="MIDDLE EAST", status="CLAIM",
         head="Ras Tanura: Saudi defences down drones",
         src="Al Jazeera", lat=26.65, lon=50.06),
    dict(n=18, region="GLOBAL", status="CONFIRMED",
         head="Oil: Brent falls to $90.97 on glut fears",
         src="Reuters", lat=57.50, lon=1.50),
    dict(n=19, region="AMERICAS", status="CONFIRMED",
         head="Ecuador: US pauses joint military ops",
         src="Reuters", lat=-0.18, lon=-78.47),
    dict(n=20, region="AMERICAS", status="CONFIRMED",
         head="Cartagena: 10 of about 30 hostages freed",
         src="Sky News", lat=10.40, lon=-75.51),
    dict(n=21, region="GLOBAL", status="CONFIRMED",
         head="Bitcoin: slips below $60,000",
         src="Chosun Biz", lat=40.75, lon=-73.97),
    dict(n=22, region="AMERICAS", status="CONFIRMED",
         head="Nvidia: Huang apologises, says in therapy",
         src="WSJ", lat=37.37, lon=-121.96, dx=7, dy=5),
    dict(n=23, region="AMERICAS", status="CONFIRMED",
         head="Venezuela: Citi weighs return after 5 years",
         src="Reuters", lat=10.48, lon=-66.88),
    dict(n=24, region="AMERICAS", status="OFFICIAL",
         head="Los Angeles: Meghan Markle's father indicted",
         src="CNN / Reuters", lat=34.05, lon=-118.24),
    dict(n=25, region="AFRICA", status="CONFIRMED",
         head="Kenya: 740GB eCitizen hack claim probed",
         src="Daily Nation", lat=-1.29, lon=36.82),
    dict(n=26, region="ASIA", status="CONFIRMED",
         head="Shanghai: leaders pledge loyalty after probe",
         src="Reuters", lat=31.23, lon=121.47),
    dict(n=27, region="EUROPE", status="OFFICIAL",
         head="Ofgem: January cap set; \u00a32,166 bill forecast",
         src="Cornwall Insight", lat=51.50, lon=-0.12, dx=8, dy=6),
    dict(n=28, region="AMERICAS", status="CLAIM",
         head="Washington: Trump floats pardon for Huang",
         src="NY Post", lat=38.89, lon=-77.04, dx=-9, dy=7),
    dict(n=29, region="OCEANIA", status="OFFICIAL",
         head="Tauranga: $152,318 payout to ex-chief",
         src="RNZ", lat=-37.69, lon=176.17),
    dict(n=30, region="ASIA", status="CONFIRMED",
         head="India: Foxconn unit faces insolvency suit",
         src="Moneycontrol", lat=12.97, lon=77.59),
]

# every story text must be free of truncation markers
for _s in STORIES:
    for _k in ("head", "body", "src", "tag", "place"):
        if _k in _s:
            assert "..." not in _s[_k] and "\u2026" not in _s[_k], _s

TICKER = ("Saudi jets hit Hodeidah port  \u25c6  Shenzhou-24 lifts off with "
          "Pakistan's first astronaut  \u25c6  Asian stocks tumble as tech rally fizzles")

STATS = [("490,334", "Russian war dead, BBC count"),
         ("-5.54%", "KOSPI, to 4,728.81"),
         ("$60,000", "Bitcoin slips below it"),
         ("740GB", "Kenya eCitizen hack claim"),
         ("30", "hostages in Cartagena")]

DATE_CHECK = ("DATE CHECK  Left out as other days\u2019 news. 24 Nov: UN femicide brief; "
              "Seoul jets; CDC measles; Senegal AFCON; Lula package; WHO H5N1. "
              "2025: EU\u2013Africa Luanda summit, 24\u201325 Nov 2025. "
              "Tue US = Wed Asia: turkey pardon, Iran chat, Huang apology, pardon hint, Markle case. "
              "Ofgem \u00a32,166 is a forecast, not the cap.")

FOOTER_LINE = ("Every story here happened or was first reported on Wednesday 25 November 2026, "
               "as the named outlets reported it. Maps and drawings are original.")

# ---------------------------------------------------------------- map data
_GEO = "/tmp/ne_110m_land.geojson"
if not os.path.exists(_GEO):
    _GEO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "land.geojson")
with open(_GEO) as f:
    LAND_GEO = json.load(f)["features"]


def land_layer(box, lon0, lon1, lat0, lat1, sea=SEA, land=LAND):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    layer = Image.new("RGB", (w, h), sea)
    ld = ImageDraw.Draw(layer)

    def px(lon, lat):
        return ((lon - lon0) / (lon1 - lon0) * w,
                (lat1 - lat) / (lat1 - lat0) * h)

    for feat in LAND_GEO:
        g = feat["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            for ring in poly:
                pts = [px(lon, lat) for lon, lat in ring]
                ld.polygon(pts, fill=land, outline=LAND_EDGE)
    return layer


def pin(d, x, y, n, colour, r=7):
    d.ellipse([x - r, y - r, x + r, y + r], fill=colour, outline=(255, 255, 255), width=1)
    f = font(SB, 8 if n < 10 else 7)
    d.text((x, y), str(n), font=f, fill=(255, 255, 255), anchor="mm")


def burst(d, cx, cy, r, fill=(245, 158, 11), core=(220, 38, 38)):
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=fill, outline=core)
    d.ellipse([cx - r * 0.32, cy - r * 0.32, cx + r * 0.32, cy + r * 0.32], fill=core)


def number_box(d, x, y, w, big, small, big_size=20):
    """White box, red border: big number over a small label."""
    d.rectangle([x, y, x + w, y + 44], fill=(255, 255, 255),
                outline=RED, width=2)
    f = fit_one_line(d, big, SB, big_size, w - 12, minimum=13)
    d.text((x + w // 2, y + 6), big, font=f, fill=RED, anchor="ma")
    fs = fit_one_line(d, small, SB, 10, w - 12, minimum=8)
    d.text((x + w // 2, y + 28), small, font=fs, fill=INK, anchor="ma")


def status_badge(d, x, y, status):
    """Small outlined tag, right-aligned ending at x."""
    col = TAG_COLOUR[status]
    f = font(SB, 9)
    tw = d.textlength(status, font=f)
    w = int(tw) + 10
    d.rectangle([x - w, y, x, y + 14], outline=col, width=1)
    d.text((x - w // 2, y + 7), status, font=f, fill=col, anchor="mm")


# ---------------------------------------------------------------- icons
def draw_icon(d, name, x, y, s, col):
    """Tiny pictogram inside a s x s box at (x, y), colour col."""
    if name == "doc":
        d.rectangle([x + s * 0.2, y + s * 0.12, x + s * 0.8, y + s * 0.88],
                    outline=col, width=2)
        d.polygon([(x + s * 0.8, y + s * 0.12), (x + s * 0.62, y + s * 0.12),
                   (x + s * 0.8, y + s * 0.3)], fill=col)
        for i, yy in enumerate((0.38, 0.55, 0.72)):
            d.line([(x + s * 0.3, y + s * yy), (x + s * 0.7, y + s * yy)],
                   fill=col, width=2)
    elif name == "flag":
        d.line([(x + s * 0.25, y + s * 0.1), (x + s * 0.25, y + s * 0.9)],
               fill=col, width=2)
        d.polygon([(x + s * 0.25, y + s * 0.12), (x + s * 0.85, y + s * 0.28),
                   (x + s * 0.25, y + s * 0.44)], fill=col)
    elif name == "burst":
        burst(d, x + s // 2, y + s // 2, s * 0.38)
    elif name == "shield":
        d.polygon([(x + s * 0.5, y + s * 0.08), (x + s * 0.88, y + s * 0.22),
                   (x + s * 0.88, y + s * 0.55), (x + s * 0.5, y + s * 0.92),
                   (x + s * 0.12, y + s * 0.55), (x + s * 0.12, y + s * 0.22)],
                  outline=col, width=2)
        d.line([(x + s * 0.32, y + s * 0.5), (x + s * 0.46, y + s * 0.64),
                (x + s * 0.7, y + s * 0.36)], fill=col, width=2)
    elif name == "feather":
        d.polygon([(x + s * 0.2, y + s * 0.75), (x + s * 0.55, y + s * 0.1),
                   (x + s * 0.85, y + s * 0.35), (x + s * 0.5, y + s * 0.85)],
                  outline=col, width=2)
        d.line([(x + s * 0.28, y + s * 0.68), (x + s * 0.78, y + s * 0.32)],
               fill=col, width=2)
    elif name == "target":
        for r in (0.4, 0.28, 0.15):
            d.ellipse([x + s * (0.5 - r), y + s * (0.5 - r),
                       x + s * (0.5 + r), y + s * (0.5 + r)], outline=col, width=2)
        d.ellipse([x + s * 0.44, y + s * 0.44, x + s * 0.56, y + s * 0.56], fill=col)
    elif name == "wave":
        for k, yy in enumerate((0.35, 0.62)):
            pts = [(x + s * (0.1 + 0.8 * i / 12),
                    y + s * yy + s * 0.09 * math.sin(i * 1.1 + k)) for i in range(13)]
            d.line(pts, fill=col, width=2)
    elif name == "lock":
        d.arc([x + s * 0.28, y + s * 0.08, x + s * 0.72, y + s * 0.52],
              180, 360, fill=col, width=2)
        d.rectangle([x + s * 0.2, y + s * 0.48, x + s * 0.8, y + s * 0.9],
                    outline=col, width=2)
        d.ellipse([x + s * 0.45, y + s * 0.6, x + s * 0.55, y + s * 0.7], fill=col)
    elif name == "heart":
        d.ellipse([x + s * 0.14, y + s * 0.18, x + s * 0.5, y + s * 0.52], fill=col)
        d.ellipse([x + s * 0.5, y + s * 0.18, x + s * 0.86, y + s * 0.52], fill=col)
        d.polygon([(x + s * 0.16, y + s * 0.42), (x + s * 0.84, y + s * 0.42),
                   (x + s * 0.5, y + s * 0.88)], fill=col)
    elif name == "train":
        d.rectangle([x + s * 0.15, y + s * 0.12, x + s * 0.85, y + s * 0.78],
                    outline=col, width=2)
        d.rectangle([x + s * 0.25, y + s * 0.25, x + s * 0.42, y + s * 0.42], fill=col)
        d.rectangle([x + s * 0.58, y + s * 0.25, x + s * 0.75, y + s * 0.42], fill=col)
        d.ellipse([x + s * 0.25, y + s * 0.78, x + s * 0.38, y + s * 0.9], fill=col)
        d.ellipse([x + s * 0.62, y + s * 0.78, x + s * 0.75, y + s * 0.9], fill=col)
    elif name == "person":
        d.ellipse([x + s * 0.38, y + s * 0.1, x + s * 0.62, y + s * 0.34], fill=col)
        d.pieslice([x + s * 0.15, y + s * 0.42, x + s * 0.85, y + s * 1.05],
                   180, 360, fill=col)
    elif name == "bag":
        d.polygon([(x + s * 0.22, y + s * 0.35), (x + s * 0.78, y + s * 0.35),
                   (x + s * 0.88, y + s * 0.88), (x + s * 0.12, y + s * 0.88)],
                  outline=col, width=2)
        d.arc([x + s * 0.32, y + s * 0.08, x + s * 0.68, y + s * 0.45],
              180, 360, fill=col, width=2)


# ---------------------------------------------------------------- page
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)
M = 16
CW = W - 2 * M

# ---- top strip ----
d.text((M, 8), "THE WORLD IN ONE DAY", font=font(SB, 15), fill=INK)
d.text((W // 2, 8), "DAY 329 OF 2026", font=font(SB, 15), fill=RED, anchor="ma")
d.text((W - M, 8), "EVERY STORY DATED WEDNESDAY 25 NOV", font=font(SB, 15),
       fill=INK, anchor="ra")
d.line([(M, 30), (W - M, 30)], fill=RULE, width=2)

# ---- masthead ----
mast = "Wednesday 25 November 2026"
msize = fit_size(d, mast, FB, 54, CW)
d.text((M, 36), mast, font=font(FB, msize), fill=INK)
regions = {}
order = ["EUROPE", "MIDDLE EAST", "ASIA", "AFRICA", "AMERICAS", "OCEANIA", "GLOBAL"]
for s in STORIES:
    regions[s["region"]] = regions.get(s["region"], 0) + 1
count_line = ("30 STORIES, ALL FROM WEDNESDAY 25 NOV  \u2022  " +
              "  \u2022  ".join(f"{k} {regions[k]}" for k in order if k in regions))
csize = fit_size(d, count_line, SR, 14, CW, minimum=11)
d.text((M, 96), count_line, font=font(SR, csize), fill=MUTED)
d.line([(M, 118), (W - M, 118)], fill=RED, width=4)
d.line([(M, 124), (W - M, 124)], fill=RULE, width=2)

# ---- ticker: 3 complete short headlines, one line ----
tf = fit_one_line(d, TICKER, SB, 15, CW, minimum=12)
d.text((M, 129), TICKER, font=tf, fill=INK)
d.line([(M, 150), (W - M, 150)], fill=RULE, width=2)

# ---- big-number stat strip ----
cell_w = CW // len(STATS)
for i, (big, label) in enumerate(STATS):
    cx = M + i * cell_w
    bf = fit_one_line(d, big, SB, 20, cell_w - 16, minimum=15)
    d.text((cx + 8, 156), big, font=bf, fill=INK)
    lf = fit_one_line(d, label, SR, 10, cell_w - 16, minimum=9)
    d.text((cx + 8, 178), label, font=lf, fill=MUTED)
    if i:
        d.line([(cx, 158), (cx, 190)], fill=RULE, width=1)
d.line([(M, 194), (W - M, 194)], fill=RULE, width=2)

# ---- three illustrated panels ----
PY, PH = 200, 88          # visual area
PW = (CW - 2 * 16) // 3
for i, s in enumerate(STORIES[0:3]):
    x0 = M + i * (PW + 16)
    x1 = x0 + PW
    if i == 0:
        # Red Sea / Yemen map + strikes + ship
        layer = land_layer((0, 0, PW, PH), 32, 60, 12, 32)
        ld = ImageDraw.Draw(layer)
        hx = (42.95 - 32) / 28 * PW
        hy = (32 - 14.80) / 20 * PH
        sx = (36.5 - 32) / 28 * PW
        sy = (32 - 20.0) / 20 * PH
        # ship in the Red Sea
        ld.polygon([(sx - 14, sy), (sx + 14, sy), (sx + 10, sy + 7),
                    (sx - 10, sy + 7)], fill=(38, 68, 120))
        ld.rectangle([sx - 8, sy - 7, sx + 8, sy], fill=(220, 38, 38))
        ld.text((sx, sy + 12), "RED SEA", font=font(SB, 9), fill=(38, 68, 120),
                anchor="ma")
        burst(ld, hx - 26, hy - 14, 12)
        burst(ld, (43.5 - 32) / 28 * PW, (32 - 16.5) / 20 * PH, 10)
        pin(ld, hx, hy, 1, RED, r=11)
        ld.text((8, 6), "HODEIDAH", font=font(SB, 12), fill=INK)
        img.paste(layer, (x0, PY))
        d.rectangle([x0, PY, x1, PY + PH], outline=RULE, width=2)
        number_box(d, x1 - 118, PY + PH - 50, 110, "3", "AREAS STRUCK")
    elif i == 1:
        # night sky + rocket + orbit + station (drawn on a clipped layer)
        layer = Image.new("RGB", (PW, PH), NAVY)
        ld = ImageDraw.Draw(layer)
        stars = [(0.08, 0.15), (0.2, 0.08), (0.32, 0.2), (0.45, 0.1),
                 (0.58, 0.16), (0.7, 0.08), (0.82, 0.2), (0.92, 0.1),
                 (0.14, 0.4), (0.38, 0.32), (0.66, 0.38), (0.9, 0.45),
                 (0.06, 0.7), (0.5, 0.55), (0.78, 0.62), (0.94, 0.72)]
        for fx, fy in stars:
            ld.ellipse([fx * PW - 1, fy * PH - 1, fx * PW + 1, fy * PH + 1],
                       fill=(255, 255, 255))
        # orbit arc (clipped to the layer)
        ld.arc([PW * 0.45, -PH * 0.35, PW * 1.05, PH * 0.7],
               180, 320, fill=(147, 197, 253), width=2)
        # station on the arc, upper right
        stx, sty = int(PW * 0.8), int(PH * 0.1)
        ld.rectangle([stx - 3, sty, stx + 3, sty + 8], fill=(255, 255, 255))
        ld.rectangle([stx - 16, sty + 2, stx - 4, sty + 6], fill=(147, 197, 253))
        ld.rectangle([stx + 4, sty + 2, stx + 16, sty + 6], fill=(147, 197, 253))
        # rocket, centre-left, nose up
        rx, ry = int(PW * 0.3), int(PH * 0.42)
        ld.polygon([(rx - 7, ry + 26), (rx + 7, ry + 26), (rx + 7, ry - 6),
                    (rx, ry - 20), (rx - 7, ry - 6)], fill=(255, 255, 255),
                   outline=(200, 200, 200))
        ld.polygon([(rx - 7, ry + 14), (rx - 15, ry + 28), (rx - 7, ry + 26)],
                   fill=(220, 38, 38))
        ld.polygon([(rx + 7, ry + 14), (rx + 15, ry + 28), (rx + 7, ry + 26)],
                   fill=(220, 38, 38))
        ld.polygon([(rx - 4, ry + 26), (rx + 4, ry + 26), (rx + 8, ry + 44),
                    (rx, ry + 52), (rx - 8, ry + 44)], fill=(245, 158, 11))
        ld.ellipse([rx - 9, ry + 50, rx + 9, ry + 62], fill=(226, 232, 240))
        ld.text((8, PH - 18), "JIUQUAN", font=font(SB, 11),
                fill=(255, 255, 255))
        number_box(ld, PW - 118, PH - 50, 110, "08:18", "LIFTOFF")
        img.paste(layer, (x0, PY))
        d.rectangle([x0, PY, x1, PY + PH], outline=RULE, width=2)
    else:
        # candlestick chart, falling
        d.rectangle([x0, PY, x1, PY + PH], fill=(255, 253, 247), outline=RULE, width=2)
        for gy in (0.25, 0.5, 0.75):
            d.line([(x0 + 6, PY + PH * gy), (x1 - 6, PY + PH * gy)],
                   fill=(226, 220, 205), width=1)
        candles = [(0.10, 0.18, 0.40), (0.26, 0.28, 0.50), (0.42, 0.38, 0.60),
                   (0.58, 0.48, 0.68), (0.74, 0.56, 0.74)]
        for fx, top, bot in candles:
            cx = x0 + PW * fx
            d.line([(cx, PY + PH * (top - 0.06)), (cx, PY + PH * (bot + 0.06))],
                   fill=RED, width=2)
            d.rectangle([cx - 9, PY + PH * top, cx + 9, PY + PH * bot], fill=RED)
        d.line([(x0 + 8, PY + PH * 0.14), (x1 - 8, PY + PH * 0.70)],
               fill=RED, width=1)
        for k in range(1, 7):
            d.line([(x0 + PW * k / 7 - 3, PY + PH * (0.14 + 0.56 * k / 7)),
                    (x0 + PW * k / 7 + 3, PY + PH * (0.14 + 0.56 * k / 7))],
                   fill=RED, width=2)
        d.text((x0 + 8, PY + PH - 18), "KOSPI  \u2022  NIKKEI -2.9%  \u2022  TAIWAN -5.1%",
               font=font(SB, 10), fill=MUTED)
        number_box(d, x1 - 118, PY + 6, 110, "-5.54%", "KOSPI")
    # caption
    cy = PY + PH + 6
    d.text((x0, cy), s["tag"], font=font(SB, 12), fill=RED)
    d.text((x1, cy), s["status"], font=font(SB, 12),
           fill=TAG_COLOUR[s["status"]], anchor="ra")
    y = cy + 18
    hf, hlines = fit_lines(d, s["head"], FB, 17, PW, 2, minimum=14)
    for line in hlines:
        d.text((x0, y), line, font=hf, fill=INK)
        y += 20
    bf, blines = fit_lines(d, s["body"], SR, 12, PW, 2, minimum=10)
    for line in blines:
        d.text((x0, y), line, font=bf, fill=MUTED)
        y += 14
    d.text((x0, y + 2), s["src"], font=font(SB, 10), fill=RED)

# ---- featured stories: 3 cols x 4 rows ----
FY = 396
FH = 100
FW = (CW - 2 * 16) // 3
for idx, s in enumerate(STORIES[3:15]):
    col, row = idx % 3, idx // 3
    x0 = M + col * (FW + 16)
    x1 = x0 + FW
    y0 = FY + row * FH
    # icon box + number badge + region tag + status tag
    colr = REGION_COLOUR[s["region"]]
    d.rectangle([x0, y0, x0 + 24, y0 + 24], fill=(238, 234, 222),
                outline=RULE, width=1)
    draw_icon(d, s["icon"], x0, y0, 24, colr)
    d.ellipse([x0 + 14, y0 + 14, x0 + 30, y0 + 30], fill=RED,
              outline=(255, 255, 255), width=1)
    d.text((x0 + 22, y0 + 22), str(s["n"]), font=font(SB, 9),
           fill=(255, 255, 255), anchor="mm")
    d.text((x0 + 36, y0 + 3), s["tag"], font=font(SB, 11), fill=RED)
    status_badge(d, x1, y0 + 1, s["status"])
    y = y0 + 28
    hf, hlines = fit_lines(d, s["head"], SB, 15, FW, 2, minimum=13)
    for line in hlines:
        d.text((x0, y), line, font=hf, fill=INK)
        y += 17
    bf, blines = fit_lines(d, s["body"], SR, 11, FW, 2, minimum=10)
    for line in blines:
        d.text((x0, y), line, font=bf, fill=MUTED)
        y += 12
    d.text((x0, y + 1), s["src"], font=font(SB, 10), fill=RED)
    if col < 2:
        d.line([(x0 + FW + 8, y0 + 2), (x0 + FW + 8, y0 + FH - 10)], fill=RULE, width=1)

# ---- bottom band: world map + index ----
BY = FY + 4 * FH + 8
d.line([(M, BY - 4), (W - M, BY - 4)], fill=INK, width=3)
map_w, map_h = 284, 100
d.rectangle([M, BY, M + 168, BY + 20], fill=INK)
d.text((M + 8, BY + 3), "WHERE IT HAPPENED", font=font(SB, 12),
       fill=(255, 255, 255))
d.text((M + 176, BY + 4), "pins carry the numbers", font=font(SR, 10),
       fill=MUTED)
d.rectangle([M, BY + 24, M + map_w, BY + 24 + map_h], fill=SEA, outline=RULE, width=2)
draw_land_layer = land_layer((0, 0, map_w, map_h), -180, 180, -60, 85)
img.paste(draw_land_layer, (M, BY + 24))
for s in STORIES:
    px_ = M + (s["lon"] + 180) / 360 * map_w
    py_ = BY + 24 + (85 - s["lat"]) / 145 * map_h
    pin(d, px_ + s.get("dx", 0), py_ + s.get("dy", 0), s["n"],
        REGION_COLOUR[s["region"]], r=7)
# legend under the map (2 rows)
leg_y = BY + 24 + map_h + 4
leg_items = [("EUROPE", "Europe"), ("MIDDLE EAST", "Middle East"),
             ("ASIA", "Asia"), ("AFRICA", "Africa")]
lx = M
for key, label in leg_items:
    d.ellipse([lx, leg_y + 2, lx + 8, leg_y + 10], fill=REGION_COLOUR[key])
    d.text((lx + 12, leg_y), label, font=font(SR, 10), fill=INK)
    lx += 12 + d.textlength(label, font=font(SR, 10)) + 12
leg_y2 = leg_y + 12
leg_items2 = [("AMERICAS", "Americas"), ("OCEANIA", "Oceania"),
              ("GLOBAL", "Global")]
lx = M
for key, label in leg_items2:
    d.ellipse([lx, leg_y2 + 2, lx + 8, leg_y2 + 10], fill=REGION_COLOUR[key])
    d.text((lx + 12, leg_y2), label, font=font(SR, 10), fill=INK)
    lx += 12 + d.textlength(label, font=font(SR, 10)) + 12

# index
ix = M + map_w + 20
iw = W - M - ix
d.text((ix, BY + 3), "ALSO ON WEDNESDAY 25 NOV", font=font(SB, 14), fill=INK)
idx_stories = STORIES[15:]
col_w = (iw - 16) // 2
for j, s in enumerate(idx_stories):
    col, row = j % 2, j // 2
    x0 = ix + col * (col_w + 16)
    y0 = BY + 26 + row * 14
    d.text((x0, y0), str(s["n"]), font=font(SB, 12), fill=RED)
    f = fit_one_line(d, s["head"], SB, 12, col_w - 22, minimum=10)
    d.text((x0 + 22, y0), s["head"], font=f, fill=INK)
src_line = ("Sources: Al Jazeera, Reuters, Yonhap, BBC, AP, CNN, WSJ, NY Post, "
            "Sky News, RNZ, Daily Nation, Chosun Biz, Moneycontrol.")
sf = fit_one_line(d, src_line, SR, 10, iw, minimum=9)
d.text((ix, BY + 24 + map_h + 16), src_line, font=sf, fill=MUTED)

# ---- footer ----
fy = BY + 24 + map_h + 30
d.line([(M, fy), (W - M, fy)], fill=RULE, width=2)
ff, flines = fit_lines(d, DATE_CHECK, SR, 11, CW - 16, 2, minimum=10)
box_h = len(flines) * 14 + 10
d.rectangle([M, fy + 6, W - M, fy + 6 + box_h], outline=RED, width=2)
yy = fy + 11
for line in flines:
    d.text((M + 8, yy), line, font=ff, fill=INK)
    yy += 14
fl2 = fit_one_line(d, FOOTER_LINE, SR, 10, CW, minimum=9)
d.text((M, fy + 6 + box_h + 6), FOOTER_LINE, font=fl2, fill=MUTED)

img.save("entry.png", optimize=True)
print("saved entry.png")
import os as _os
print("bytes:", _os.path.getsize("entry.png"))
