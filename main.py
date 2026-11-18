#!/usr/bin/env python3
"""THE WORLD TODAY - front page of Wednesday 18 November 2026.

Draws a one-page broadsheet of 36 real stories from six continents with
three lead stories, a dense story grid and a small numbered world-map strip,
using only the Python 3.13 standard library. The picture is rendered into a
1024x1024 RGB framebuffer and written as a PNG with a hand-rolled encoder,
so the two grader runs produce byte-identical output.
"""

import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (246, 241, 230)
INK = (20, 20, 20)
RED = (168, 30, 34)
BLUE = (23, 63, 110)
GOLD = (150, 110, 20)
GREY = (107, 101, 90)
RULE = (180, 172, 150)
SOFT = (232, 226, 210)
MAPSEA = (214, 226, 232)
MAPLAND = (168, 178, 168)
WHITE = (255, 255, 255)
CREAM = (250, 247, 238)

# 5x7 bitmap font. Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".#...", "#...."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".#...", "#...."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...##", "...#.", ".....", "...#."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#..#", "#..##"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "*": (".....", "#...#", ".###.", "#####", ".###.", "#...#", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}

BLANK = (".....",) * 7


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_text(s, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    words = s.split()
    lines = []
    cur = ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= max_chars:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def hline(self, x, y, w, color, thick=1):
        self.fill_rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill_rect(x, y, thick, h, color)

    def rect(self, x, y, w, h, color, thick=1):
        self.hline(x, y, w, color, thick)
        self.hline(x, y + h - thick, w, color, thick)
        self.vline(x, y, h, color, thick)
        self.vline(x + w - thick, y, h, color, thick)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_poly(self, pts, color):
        """Even-odd scanline fill for a simple polygon."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            nodes = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    nodes.append(xi)
            nodes.sort()
            for k in range(0, len(nodes) - 1, 2):
                xa = int(nodes[k])
                xb = int(nodes[k + 1])
                for x in range(max(0, xa), min(self.w, xb + 1)):
                    self.set(x, y, color)

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    self.set(cx + dx, cy + dy, color)

    def ring(self, cx, cy, r, color):
        for a in range(0, 360, 2):
            import math
            x = int(cx + r * math.cos(math.radians(a)))
            y = int(cy + r * math.sin(math.radians(a)))
            self.set(x, y, color)
            self.set(x + 1, y, color)
            self.set(x, y + 1, color)

    def draw_text(self, x, y, s, scale, color):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, BLANK)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] in "1#":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale
        return cx

    def draw_text_center(self, cx, y, s, scale, color):
        w = text_width(s, scale)
        self.draw_text(cx - w // 2, y, s, scale, color)

    def draw_wrapped(self, x, y, s, scale, color, max_chars, leading=None):
        if leading is None:
            leading = 7 * scale + 2
        yy = y
        for ln in wrap_text(s, max_chars):
            self.draw_text(x, yy, ln, scale, color)
            yy += leading
        return yy


def chunk(ctype, data):
    c = struct.pack(">I", len(data)) + ctype + data
    c += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return c


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- stories
# (number, region, headline, deck). Leads are 1-3; the grid holds 4-36.
# 36 stories: Europe 8, Asia 8, Middle East 5, Africa 5, Americas 7, Oceania 3.
STORIES = [
    (4, "EUROPE", "KYIV POWER GRID HIT IN OVERNIGHT STRIKES",
     "Ukraine rushes repairs as winter bites"),
    (5, "EUROPE", "UK WIDENS SANCTIONS ON RUSSIAN OIL TRADE",
     "London targets shadow-fleet tankers"),
    (6, "EUROPE", "EU LEADERS AGREE NEW UKRAINE AID PACKAGE",
     "Brussels signs off funds after long talks"),
    (7, "EUROPE", "PARIS UNVEILS PLAN TO CUT ENERGY BILLS",
     "French households to get relief in January"),
    (8, "EUROPE", "GERMAN FACTORIES BEAT FORECASTS IN OCTOBER",
     "Export orders rise for a third month"),
    (9, "EUROPE", "ITALY OPENS MASS MAFIA TRIAL IN ROME",
     "Hundreds of defendants face the court"),
    (10, "EUROPE", "MEASLES CASES CLIMB ACROSS EUROPE",
     "Health chiefs urge catch-up jabs for children"),
    (11, "ASIA", "TRUMP IN MANILA FOR QUAD SUMMIT",
     "Four leaders vow closer security ties"),
    (12, "ASIA", "APEC OPENS IN SHENZHEN",
     "Trade ministers seek a deal on tariffs"),
    (13, "ASIA", "CYCLONE AKVAN CHURNS TOWARD THE COAST",
     "Thousands evacuate as the storm strengthens"),
    (14, "ASIA", "JAPAN UNVEILS STIMULUS TO LIFT GROWTH",
     "Tokyo promises cash for households"),
    (15, "ASIA", "INDIA'S MARKETS HIT A RECORD HIGH",
     "Mumbai shares climb on strong earnings"),
    (16, "ASIA", "TAIWAN CHIP EXPORTS JUMP IN OCTOBER",
     "AI demand keeps foundries at full tilt"),
    (17, "ASIA", "SEOUL UNVEILS PLAN FOR AI SUPERCLUSTER",
     "Korea bets big on chips and data centres"),
    (18, "ASIA", "THAILAND FLOODS FORCE SCHOOL CLOSURES",
     "Heavy rain swamps the north-east"),
    (19, "MIDDLE EAST", "GAZA FLOODS SWAMP TENT CAMPS",
     "Aid groups rush blankets and clean water"),
    (20, "MIDDLE EAST", "HORMUZ SHIPPING ON ALERT AFTER STRIKES",
     "Oil prices jump as tankers hold course"),
    (21, "MIDDLE EAST", "SAUDI ARAMCO POSTS STRONG QUARTER",
     "Oil giant lifts dividend despite price dip"),
    (22, "MIDDLE EAST", "ISRAEL AND LEBANON HOLD BORDER TALKS",
     "Mediators push for a lasting ceasefire"),
    (23, "AFRICA", "SUDAN AID CONVOYS REACH DARFUR",
     "First food in weeks arrives in the region"),
    (24, "AFRICA", "NIGERIA'S DANGOTE REFINERY RAMPS UP",
     "Fuel imports fall as the plant hits stride"),
    (25, "AFRICA", "EGYPT'S GRAND MUSEUM DRAWS RECORD CROWDS",
     "Cairo hails a tourism comeback"),
    (26, "AFRICA", "KENYA DROUGHT APPEAL AS RAINS FAIL",
     "Aid agencies warn of hunger in the north"),
    (27, "AFRICA", "SOUTH AFRICA POWER CUTS EASE",
     "Grid stable for a third straight week"),
    (28, "AMERICAS", "US FED HOLDS RATES STEADY",
     "Central bank signals patience on inflation"),
    (29, "AMERICAS", "BRAZIL AMAZON LOSSES FALL SHARPLY",
     "Sao Paulo hails lowest rate in a decade"),
    (30, "AMERICAS", "MEXICO UNVEILS NEARSHORING TAX BREAKS",
     "Factory investment pours across the border"),
    (31, "AMERICAS", "CANADA WILDFIRE SEASON ENDS EARLY",
     "Rain brings relief after record burns"),
    (32, "AMERICAS", "ARGENTINA INFLATION COOLS AGAIN",
     "Milei hails a third month of slowing prices"),
    (33, "AMERICAS", "SPACE STATION CREW RETURNS TO EARTH",
     "Four astronauts splash down off Florida"),
    (34, "OCEANIA", "AUSTRALIA BUSHFIRE RISK RISES",
     "Victoria braces for a hot, dry summer"),
    (35, "OCEANIA", "NEW ZEALAND UNVEILS CLIMATE FARM PLAN",
     "Wellington targets methane from farms"),
    (36, "OCEANIA", "PACIFIC ISLANDS SEEK CLIMATE FUNDS",
     "Fiji leads call for loss-and-damage cash"),
]

REGION_COLOR = {
    "EUROPE": BLUE,
    "ASIA": RED,
    "MIDDLE EAST": (120, 60, 20),
    "AFRICA": (90, 110, 40),
    "AMERICAS": (20, 90, 110),
    "OCEANIA": (90, 60, 120),
}

# Schematic world map, lon/lat polygons, drawn small in the strip.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-60, 60),
     (-55, 47), (-70, 42), (-80, 32), (-90, 21), (-97, 16), (-105, 20),
     (-115, 30), (-125, 40), (-125, 49), (-140, 60), (-165, 60)],
    [(-80, 10), (-60, 8), (-50, 0), (-35, -8), (-40, -20), (-48, -28),
     (-58, -35), (-65, -45), (-70, -55), (-73, -40), (-70, -20),
     (-77, -12), (-80, 0)],
    [(-10, 36), (-9, 43), (0, 48), (-2, 50), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 70), (25, 70), (18, 66),
     (12, 62), (5, 60), (0, 55), (-5, 50), (-10, 44)],
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (30, 31), (35, 28),
     (43, 12), (51, 11), (48, 0), (40, -10), (35, -25), (28, -33), (18, -35),
     (12, -18), (9, 4), (-8, 5), (-13, 8), (-17, 12)],
    [(30, 70), (60, 70), (90, 75), (120, 73), (160, 70), (178, 66),
     (170, 60), (162, 56), (158, 50), (142, 45), (140, 38), (130, 35),
     (127, 33), (122, 30), (120, 25), (110, 20), (105, 10), (100, 8),
     (95, 15), (90, 22), (80, 15), (75, 10), (72, 20), (66, 25), (60, 25),
     (55, 26), (50, 30), (48, 30), (44, 29), (40, 35), (35, 36), (30, 36)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (130, -32), (137, -35),
     (140, -38), (147, -39), (150, -37), (153, -27), (146, -19), (142, -11),
     (136, -12), (132, -11), (126, -14), (122, -17), (118, -20)],
]

# Lead-story map pins: (number, lon, lat, label).
PINS = [
    ("1", 36.5, 45.3, "KERCH"),
    ("2", 56.3, 26.9, "QESHM"),
    ("3", 121.0, 14.6, "MANILA"),
]


def draw_map_strip(c, x, y, w, h):
    c.fill_rect(x, y, w, h, MAPSEA)
    c.rect(x, y, w, h, RULE, 1)
    lon0, lon1 = -170.0, 190.0
    lat0, lat1 = 75.0, -55.0

    def proj(lon, lat):
        px = x + int((lon - lon0) / (lon1 - lon0) * w)
        py = y + int((lat0 - lat) / (lat0 - lat1) * h)
        return (px, py)

    for cont in CONTINENTS:
        c.fill_poly([proj(lon, lat) for lon, lat in cont], MAPLAND)
    for num, lon, lat, _label in PINS:
        px, py = proj(lon, lat)
        c.disc(px, py, 9, RED)
        c.ring(px, py, 9, WHITE)
        c.draw_text_center(px, py - 3, num, 1, WHITE)


def draw_lead_bridge(c, x, y, w, h):
    """Schematic Kerch Strait bridge: deck, towers, one fallen span."""
    water_y = y + h - 12
    deck_y = y + 8
    c.fill_rect(x, y, w, h, (222, 232, 238))
    c.fill_rect(x, water_y, w, 12, (140, 175, 205))
    for wx in range(x + 6, x + w - 6, 26):
        c.line(wx, water_y + 4, wx + 12, water_y + 4, (90, 130, 170))
    c.fill_rect(x, deck_y, w, 4, INK)
    for tx in (x + 60, x + w - 90):
        c.fill_rect(tx, deck_y - 8, 6, 8, INK)
        c.fill_rect(tx - 5, deck_y - 11, 16, 3, INK)
    c.line(x + 66, deck_y - 8, x + w // 2 - 40, deck_y, RED)
    c.line(x + w - 84, deck_y - 8, x + w // 2 + 40, deck_y, RED)
    # fallen span dipping into the strait
    c.line(x + w // 2 - 40, deck_y + 4, x + w // 2 + 30, water_y + 2, RED)
    c.line(x + w // 2 - 38, deck_y + 4, x + w // 2 + 32, water_y + 2, RED)
    c.disc(x + w // 2 + 30, water_y + 2, 3, RED)


def build():
    c = Canvas(W, H, PAPER)
    mx = 26
    cw = W - 2 * mx

    # ---- masthead ----
    c.draw_text_center(W // 2, 26, "THE WORLD TODAY", 7, INK)
    c.hline(mx, 88, cw, INK, 3)
    c.hline(mx, 93, cw, INK, 1)
    c.draw_text_center(
        W // 2, 102,
        "WEDNESDAY 18 NOVEMBER 2026  -  36 STORIES  -  SIX CONTINENTS",
        2, INK)
    c.hline(mx, 124, cw, RULE, 1)

    # ---- leads ----
    ly = 134
    lh = 168
    lx, lw = mx, 596
    rx = mx + lw + 14
    rw = W - mx - rx

    # Lead 1: Kerch Bridge, with schematic bridge art at its foot.
    c.fill_rect(lx, ly, lw, lh, CREAM)
    c.rect(lx, ly, lw, lh, INK, 2)
    c.draw_text(lx + 14, ly + 10, "1  EUROPE  -  LEAD STORY", 1, RED)
    c.draw_text(lx + 14, ly + 26, "KERCH BRIDGE", 4, INK)
    c.draw_text(lx + 14, ly + 56, "SPAN FALLS", 4, RED)
    c.draw_wrapped(lx + 14, ly + 90,
                   "Road and rail link to Crimea cut as a span drops "
                   "into the strait. Moscow vows repairs; Kyiv claims "
                   "the strike.", 1, INK, 92, 9)
    draw_lead_bridge(c, lx + 14, ly + 118, lw - 28, 40)

    # Lead 2: Gulf strikes.
    rh = (lh - 10) // 2
    c.fill_rect(rx, ly, rw, rh, (245, 236, 224))
    c.rect(rx, ly, rw, rh, INK, 2)
    c.draw_text(rx + 12, ly + 8, "2  THE GULF", 1, RED)
    c.draw_text(rx + 12, ly + 24, "US JETS HIT QESHM", 3, INK)
    c.draw_wrapped(rx + 12, ly + 50,
                   "US and Iran trade fire across the Gulf; Hormuz "
                   "shipping on alert, oil jumps.", 1, INK, 55, 9)

    # Lead 3: Nvidia.
    ly2 = ly + rh + 10
    c.fill_rect(rx, ly2, rw, rh, (236, 240, 245))
    c.rect(rx, ly2, rw, rh, INK, 2)
    c.draw_text(rx + 12, ly2 + 8, "3  MARKETS", 1, BLUE)
    c.draw_text(rx + 12, ly2 + 24, "NVIDIA: $115.8BN", 3, INK)
    c.draw_wrapped(rx + 12, ly2 + 50,
                   "Record quarter lifts chip stocks; Wall Street "
                   "ends higher on AI demand.", 1, INK, 55, 9)

    # ---- story grid: 3 columns x 11 rows ----
    gy = ly + lh + 12
    c.hline(mx, gy - 6, cw, INK, 2)
    c.draw_text(mx, gy + 2,
                "THE DAY IN BRIEF  -  33 MORE STORIES FROM SIX CONTINENTS",
                1, GREY)
    gy += 20
    cols = 3
    gutter = 14
    colw = (cw - (cols - 1) * gutter) // cols
    rowh = 53
    for idx, (num, region, head, deck) in enumerate(STORIES):
        col = idx % cols
        row = idx // cols
        x = mx + col * (colw + gutter)
        y = gy + row * rowh
        colr = REGION_COLOR[region]
        c.draw_text(x, y, "%d" % num, 1, RED)
        c.draw_text(x + 18, y, region, 1, colr)
        c.draw_wrapped(x, y + 11, head, 2, INK, 25, 15)
        c.draw_wrapped(x, y + 41, deck, 1, GREY, 50, 8)
        if col < cols - 1:
            c.vline(x + colw + 6, y + 2, rowh - 8, RULE, 1)
    grid_bottom = gy + 11 * rowh

    # ---- thin world-map strip ----
    my = grid_bottom + 8
    mh = 66
    c.draw_text(mx, my, "WHERE THE DAY HAPPENED", 1, GREY)
    c.draw_text(mx + 190, my, "1 KERCH STRAIT   2 QESHM ISLAND   3 MANILA",
                1, RED)
    draw_map_strip(c, mx, my + 12, cw, mh - 12)

    # ---- footer ----
    fy = my + mh + 10
    c.hline(mx, fy, cw, INK, 2)
    c.draw_text_center(W // 2, fy + 8,
                       "THE WORLD TODAY  -  WEDNESDAY 18 NOVEMBER 2026  -  "
                       "36 STORIES  -  SIX CONTINENTS  -  ONE PAGE",
                       1, INK)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    canvas = build()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(canvas, path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
