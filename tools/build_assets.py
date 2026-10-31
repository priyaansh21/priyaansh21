"""
Generates every SVG plate used by the profile README.

All colours, type stacks and motion rules live in the TOKENS block below, so the
visual system can be changed in one place. Run from the repository root:

    python tools/build_assets.py

Design constraints (GitHub renders README SVGs through <img>):
  - no external fonts or images; type falls back to system stacks
  - CSS animation is additive only: the static frame is the full composition
  - anything that must be readable on a phone is repeated in README text
"""

from __future__ import annotations

import random
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# ---------------------------------------------------------------- TOKENS
BG = "#0d1117"       # matches GitHub dark canvas; reads as a printed plate in light mode
GRID = "#151b23"
GRID_MAJOR = "#1b222c"
LINE = "#262e39"
LINE_2 = "#38414d"
INK = "#e6e3dc"      # warm paper white
MUTED = "#8b929b"
DIM = "#5b636d"
ACCENT = "#d9a441"   # sodium amber: the single accent
DENY = "#c8553d"     # verdict red, used only for refusals
ALLOW = "#8fb3c4"    # cold blue, used only in the closing frame

SERIF = "Georgia, 'Iowan Old Style', 'Palatino Linotype', 'Times New Roman', serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

W = 1200
M = 64  # outer margin

BASE_CSS = f"""
.serif{{font-family:{SERIF}}}
.mono{{font-family:{MONO};letter-spacing:.08em}}
.flow{{stroke-dasharray:6 8;animation:flow 2.4s linear infinite}}
.pulse{{animation:pulse 3.2s ease-in-out infinite}}
.sweep{{animation:sweep 9s linear infinite}}
@keyframes flow{{to{{stroke-dashoffset:-28}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.45}}}}
@keyframes sweep{{0%{{transform:translateX(0)}}100%{{transform:translateX(var(--sweep,400px))}}}}
@media (prefers-reduced-motion:reduce){{.flow,.pulse,.sweep{{animation:none}}}}
"""


# ---------------------------------------------------------------- PRIMITIVES
def svg(h: int, title: str, desc: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" '
        f'role="img" aria-labelledby="t d">\n'
        f'<title id="t">{escape(title)}</title>\n<desc id="d">{escape(desc)}</desc>\n'
        f"<style>{BASE_CSS}</style>\n"
        f'<rect width="{W}" height="{h}" fill="{BG}"/>\n{body}\n</svg>\n'
    )


def text(x, y, s, size=16, fill=INK, cls="mono", anchor="start", weight=None, italic=False, extra=""):
    attrs = [f'x="{x}"', f'y="{y}"', f'font-size="{size}"', f'fill="{fill}"']
    if 'class=' not in extra:
        attrs.append(f'class="{cls}"')
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if italic:
        attrs.append('font-style="italic"')
    if extra:
        attrs.append(extra)
    return f"<text {' '.join(attrs)}>{escape(s)}</text>"


def line(x1, y1, x2, y2, stroke=LINE, width=1, extra=""):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}" {extra}/>'


def rect(x, y, w, h, stroke=LINE_2, fill="none", width=1.5, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" {extra}/>'


def grid(h: int, step: int = 40, major: int = 200) -> str:
    out = []
    for x in range(0, W + 1, step):
        out.append(line(x, 0, x, h, GRID_MAJOR if x % major == 0 else GRID))
    for y in range(0, h + 1, step):
        out.append(line(0, y, W, y, GRID_MAJOR if y % major == 0 else GRID))
    return "\n".join(out)


def crop_marks(h: int, inset: int = 28, size: int = 14) -> str:
    out = []
    for cx, dx in ((inset, 1), (W - inset, -1)):
        for cy, dy in ((inset, 1), (h - inset, -1)):
            out.append(line(cx, cy, cx + dx * size, cy, LINE_2))
            out.append(line(cx, cy, cx, cy + dy * size, LINE_2))
    return "\n".join(out)


def plate_header(kicker: str, title: str, status: str, subtitle: str) -> str:
    return "\n".join(
        [
            text(M, 72, kicker, 15, ACCENT),
            text(W - M, 72, status, 14, MUTED, anchor="end"),
            text(M, 136, title, 54, INK, cls="serif"),
            text(M, 176, subtitle, 15, MUTED),
            line(M, 200, W - M, 200, LINE),
        ]
    )


def mono_w(s: str, size: float) -> float:
    """Conservative width estimate for monospace text with .08em tracking."""
    return len(s) * size * 0.68


# ---------------------------------------------------------------- THE ENFILADE
# The identity motif: six rooms in a row of aligned doors, one per input that
# CloudContextGuard evaluates before it will produce a verdict.
GATES = ["IAM", "VPC", "POLICY", "MFA", "RISK", "DECISION"]


def enfilade(cx, cy, outer, door_side="right", fail_at=None, verdict="DENY",
             path_color=ACCENT, verdict_color=DENY):
    step = (outer - 40) / (len(GATES) - 1)
    gap = 15
    out = []
    halves = [outer - i * step for i in range(len(GATES))]
    for name, hv in zip(GATES, halves):
        x0, x1, y0, y1 = cx - hv, cx + hv, cy - hv, cy + hv
        colour = INK if name == "DECISION" else LINE_2
        w = 2 if name == "DECISION" else 1.5
        if door_side == "right":
            d = f"M{x1},{cy - gap} L{x1},{y0} L{x0},{y0} L{x0},{y1} L{x1},{y1} L{x1},{cy + gap}"
            lx, anchor = x0 + 10, "start"
        else:
            d = f"M{x0},{cy - gap} L{x0},{y0} L{x1},{y0} L{x1},{y1} L{x0},{y1} L{x0},{cy + gap}"
            lx, anchor = x1 - 10, "end"
        out.append(f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{w}"/>')
        if name != "DECISION":
            out.append(text(lx, y0 + 22, name, 13, MUTED, anchor=anchor))

    sign = 1 if door_side == "right" else -1
    edge = cx + sign * (outer + 120)
    if fail_at is None:
        out.append(line(edge, cy, cx + sign * 50, cy, path_color, 2.5, 'class="flow"'))
    else:
        stop = cx + sign * halves[fail_at]
        out.append(line(edge, cy, stop, cy, path_color, 2.5, 'class="flow"'))
        out.append(line(stop, cy, cx + sign * 50, cy, DIM, 1.5, 'stroke-dasharray="3 6"'))
        out.append(line(stop, cy - gap - 4, stop, cy + gap + 4, verdict_color, 4))
        out.append(text(stop, cy + gap + 26, "FAIL", 13, verdict_color, anchor="middle"))
        if fail_at > 0:
            passed = cx + sign * halves[fail_at - 1]
            out.append(text(passed, cy - gap - 14, "PASS", 13, INK, anchor="middle"))
    out.append(text(cx, cy + 7, verdict, 20, verdict_color, anchor="middle", weight="bold",
                    extra='class="mono pulse"'))
    return "\n".join(out)


# ---------------------------------------------------------------- PLATES
def hero() -> str:
    h = 600
    body = [
        grid(h),
        crop_marks(h),
        text(M, 74, "PRIYAANSH21 — A MONOGRAPH, VOL. I", 14, MUTED),
        text(W - M, 74, "FRAME 00 / THE VERDICT", 14, MUTED, anchor="end"),
        text(M, 252, "Priyaansh", 92, INK, cls="serif"),
        text(M, 346, "Jaiswal", 92, INK, cls="serif"),
        line(M, 392, M + 84, 392, ACCENT, 3),
        text(M, 448, "Systems that decide", 40, INK, cls="serif", italic=True),
        f'<text x="{M}" y="498" font-size="40" fill="{INK}" class="serif" font-style="italic">'
        f'what to <tspan fill="{ACCENT}">trust.</tspan></text>',
        text(M, 548, "SECURITY ENGINEERING · APPLIED ML · SYSTEMS", 15, MUTED),
        enfilade(900, 312, 205, "right", fail_at=1),
        line(M, 566, W - M, 566, LINE),
        text(M, 586, "T+00:00:00:00", 13, DIM),
        text(W - M, 586, "contractor01 → financial-records   IAM PASS   VPC FAIL   → DENY", 13, DIM, anchor="end"),
    ]
    return svg(
        h,
        "Priyaansh Jaiswal — Systems that decide what to trust",
        "Opening frame. Left: the name Priyaansh Jaiswal and the line 'Systems that decide what to trust.' "
        "Right: an architectural plan of six nested rooms with aligned doors labelled IAM, VPC, POLICY, MFA, "
        "RISK and DECISION. A request enters, passes the IAM door, fails at the VPC door, and the decision "
        "room reads DENY — a real scenario from the CloudContextGuard threat model.",
        "\n".join(body),
    )


def closing() -> str:
    h = 520
    body = [
        grid(h),
        crop_marks(h),
        text(M, 74, "FRAME 06 / THE REVERSE SHOT", 14, MUTED),
        text(W - M, 74, "END OF VOLUME I", 14, MUTED, anchor="end"),
        enfilade(330, 290, 180, "left", fail_at=None, verdict="ALLOW",
                 path_color=ALLOW, verdict_color=ALLOW),
        text(680, 228, "Trust is", 52, INK, cls="serif", italic=True),
        text(680, 292, "a conclusion,", 52, INK, cls="serif", italic=True),
        f'<text x="680" y="356" font-size="52" fill="{INK}" class="serif" font-style="italic">'
        f'not a <tspan fill="{ACCENT}">default.</tspan></text>',
        line(680, 398, 764, 398, ACCENT, 3),
        text(680, 436, "PRIYAANSH JAISWAL", 15, MUTED),
        line(M, 486, W - M, 486, LINE),
        text(M, 506, "T−00:00:00:00", 13, DIM),
        text(W - M, 506, "ALL SIX INPUTS EVALUATED   → ALLOW", 13, DIM, anchor="end"),
    ]
    return svg(
        h,
        "Closing frame — Trust is a conclusion, not a default",
        "Closing frame, mirrored from the opening. The six-room plan now sits on the left with its doors "
        "facing left; a request passes every door and the decision room reads ALLOW. Right: the line "
        "'Trust is a conclusion, not a default.'",
        "\n".join(body),
    )


CHAPTERS = [
    ("00", "The Verdict", "THE ENDING, SHOWN FIRST"),
    ("01", "The Person", "WHO BUILDS THE SYSTEMS"),
    ("02", "The Work", "THREE EXHIBITS, TWO STUDIES"),
    ("03", "The Landscape", "CAPABILITY, MAPPED TO SOURCE"),
    ("04", "The Thinking", "SIX AXIOMS, EACH WITH A CITATION"),
    ("05", "The Connection", "CHANNELS"),
    ("06", "The Final Frame", "THE REVERSE SHOT"),
]


def chapter(idx: int) -> str:
    num, title, kicker = CHAPTERS[idx]
    h = 160
    body = [
        text(M, 96, num, 76, ACCENT, cls="serif"),
        text(M + 128, 92, title, 46, INK, cls="serif"),
        text(W - M, 48, f"CHAPTER {num} / 06", 13, MUTED, anchor="end"),
    ]
    sq, gap = 14, 8
    x0 = W - M - (len(CHAPTERS) * (sq + gap) - gap)
    for i in range(len(CHAPTERS)):
        x = x0 + i * (sq + gap)
        if i == idx:
            body.append(rect(x, 66, sq, sq, ACCENT, ACCENT, 1))
        elif i < idx:
            body.append(rect(x, 66, sq, sq, MUTED, MUTED, 1))
        else:
            body.append(rect(x, 66, sq, sq, LINE_2, "none", 1))
    body.append(line(M, 118, W - M, 118, LINE_2))
    for x in range(M, W - M + 1, 16):
        tall = (x - M) % 80 == 0
        body.append(line(x, 118, x, 118 + (10 if tall else 5), LINE_2 if tall else LINE))
    body.append(text(M, 150, kicker, 13, DIM))
    return svg(h, f"Chapter {num} — {title}", f"Chapter divider: {num}, {title}. {kicker.capitalize()}.",
               "\n".join(body))


def ccg_plate() -> str:
    h = 700
    out = [
        grid(h),
        plate_header("EVIDENCE I", "CloudContextGuard", "IMPLEMENTATION · LOCAL SIMULATION",
                     "SIX INDEPENDENT INPUTS → ONE AUTHORITY → ALLOW | DENY"),
    ]
    cols = [("IAM", "permission?"), ("VPC", "origin?"), ("POLICY", "rules?"),
            ("MFA", "provided?"), ("RISK", "score 0–100")]
    y0, ch, cw = 232, 150, 112
    cy = y0 + ch / 2 + 12
    xs = [M + 20 + i * 160 for i in range(len(cols))]
    out.append(line(M - 20, cy, xs[1] + cw / 2, cy, ACCENT, 2.5, 'class="flow"'))
    out.append(line(xs[1] + cw / 2, cy, 900, cy, DIM, 1.5, 'stroke-dasharray="3 6"'))
    for (name, q), x in zip(cols, xs):
        out.append(rect(x, y0, cw, ch, LINE_2, BG))
        out.append(text(x + cw / 2, y0 + 28, q, 12, MUTED, anchor="middle"))
        out.append(text(x + cw / 2, y0 + ch + 30, name, 20, INK, anchor="middle"))
        if name == "IAM":
            out.append(text(x + cw / 2, cy + 6, "PASS", 18, INK, anchor="middle", weight="bold"))
        elif name == "VPC":
            out.append(rect(x, y0, cw, ch, DENY, "none", 2))
            out.append(text(x + cw / 2, cy + 6, "FAIL", 18, DENY, anchor="middle", weight="bold"))
        else:
            out.append(text(x + cw / 2, cy + 5, "evaluated", 13, DIM, anchor="middle"))
    dx = 900 + (W - M - 900) / 2
    out += [
        rect(900, y0, W - M - 900, ch, INK, BG, 2),
        text(dx, y0 + 28, "DECISION ENGINE", 12, MUTED, anchor="middle"),
        text(dx, cy + 16, "DENY", 44, DENY, anchor="middle", weight="bold", extra='class="mono pulse"'),
        text(dx, y0 + ch + 30, "sole authority", 14, MUTED, anchor="middle"),
        text(W - M, y0 + ch + 56, "scenario T2 · trusted identity, untrusted network", 12, DIM, anchor="end"),
        line(M, 470, W - M, 470, LINE),
        text(M, 504, "RISK FACTORS — NAMED, WEIGHTED, NO HIDDEN TERMS", 13, MUTED),
        text(720, 504, "LEVELS", 13, MUTED),
    ]
    factors = [("External network", 40), ("RESTRICTED resource", 40), ("CONFIDENTIAL resource", 30),
               ("Missing MFA", 30), ("Unknown/untrusted source", 20), ("Suspicious request", 20),
               ("Repeated failed requests", 10)]
    for i, (name, pts) in enumerate(factors):
        y = 536 + i * 22
        out.append(text(M, y + 5, name, 13, INK))
        out.append(rect(330, y - 6, pts * 6, 10, "none", ACCENT, 0, f'opacity="{0.35 + pts / 80:.2f}"'))
        out.append(text(330 + pts * 6 + 10, y + 5, f"+{pts}", 13, MUTED))
    sx, sw, sy = 720, W - M - 720, 548
    bands = [(0, 30, "LOW", 0.12), (30, 60, "MEDIUM", 0.3), (60, 80, "HIGH", 0.55), (80, 100, "CRITICAL", 0.9)]
    for a, b, name, op in bands:
        x, wdt = sx + sw * a / 100, sw * (b - a) / 100
        colour = DENY if name == "CRITICAL" else ACCENT
        out.append(rect(x, sy, wdt, 26, BG, colour, 1, f'fill-opacity="{op}"'))
        out.append(text(x + wdt / 2, sy + 52, name, 12, MUTED, anchor="middle"))
    for t in (0, 30, 60, 80, 100):
        out.append(text(sx + sw * t / 100, sy - 10, str(t), 12, DIM, anchor="middle"))
    out.append(text(sx, sy + 96, "pure functions · structured results", 12, DIM))
    out.append(text(sx, sy + 116, "policy re-read on every request", 12, DIM))
    return svg(h, "Evidence I — CloudContextGuard decision pipeline",
               "Plate showing five evaluator columns — IAM, VPC, POLICY, MFA, RISK — feeding a decision engine. "
               "In scenario T2 IAM passes, VPC fails, the remaining checks are still evaluated, and the decision "
               "engine returns DENY. Below: the seven named risk factors and their points (external network 40, "
               "restricted resource 40, confidential resource 30, missing MFA 30, unknown/untrusted source 20, suspicious "
               "request 20, repeated failed requests 10) and the level thresholds LOW, MEDIUM at 30, HIGH at 60, "
               "CRITICAL at 80.",
               "\n".join(out))


def nids_plate() -> str:
    h = 660
    rng = random.Random(21)
    out = [
        grid(h),
        plate_header("EVIDENCE II", "SentinelSphere NIDS", "IMPLEMENTATION · SYNTHETIC TRAINING DATA",
                     "LIVE CAPTURE OR SIMULATED TRAFFIC → HYBRID DETECTION → SOC DASHBOARD"),
    ]
    axis, now, sec = 372, 1000, 9
    out.append(line(M, axis, W - M, axis, LINE_2))
    x = M + 2
    while x < now:
        burst = now - 90 < x
        hgt = rng.randint(28, 62) if burst else rng.choice([4, 6, 8, 10, 12, 16, 22])
        out.append(line(x, axis, x, axis - hgt, ACCENT if burst else DIM, 2 if burst else 1.2))
        x += rng.choice([3, 4]) if burst else rng.choice([5, 7, 9, 12])
    out.append(text(now - 45, axis - 76, "SYN BURST", 12, ACCENT, anchor="middle"))
    windows = [(60, "60 s · authentication attempts", 236), (30, "30 s · unique dst ports · flow volume", 268),
               (10, "10 s · SYN rate · ICMP rate", 300)]
    for secs, label, y in windows:
        x0 = now - secs * sec
        out.append(line(x0, y, now, y, MUTED, 1.5))
        out.append(line(x0, y - 6, x0, y + 6, MUTED, 1.5))
        out.append(text(x0 - 12, y + 5, label, 13, INK, anchor="end"))
    out.append(line(now, 222, now, axis + 8, INK, 1, 'stroke-dasharray="2 4"'))
    out.append(text(now, axis + 28, "now", 12, MUTED, anchor="middle"))
    out.append(text(M, axis + 28, "packets per source IP · rolling state", 12, DIM))

    def chips(y, items, hot=None):
        xx, end = 210, 210
        for item in items:
            wdt = mono_w(item, 13) + 28
            hl = item == hot
            out.append(rect(xx, y, wdt, 36, ACCENT if hl else LINE_2, BG, 1.5))
            out.append(text(xx + 14, y + 23, item, 13, ACCENT if hl else INK))
            end = xx + wdt
            xx += wdt + 12
        return end

    out.append(line(M, 424, W - M, 424, LINE))
    out.append(text(M, 474, "SIGNATURES", 13, MUTED))
    e1 = chips(452, ["SYN FLOOD", "ICMP FLOOD", "PORT SCAN", "BRUTE FORCE", "ARP SPOOF"], hot="SYN FLOOD")
    out.append(text(M, 538, "MODELS", 13, MUTED))
    e2 = chips(516, ["ISOLATION FOREST · ANOMALY", "RANDOM FOREST · 5 FAMILIES"])
    out.append(text(210, 576, "Normal · DoS/DDoS · Probe · R2L · U2R", 12, DIM))
    bx = 960
    bc = bx + (W - M - bx) / 2
    out += [
        line(e1, 470, bx, 470, ACCENT, 2, 'class="flow"'),
        line(e2, 534, bx, 534, DIM, 1.5, 'stroke-dasharray="3 6"'),
        rect(bx, 446, W - M - bx, 112, INK, BG, 2),
        text(bc, 500, "ALERT", 30, INK, anchor="middle", weight="bold", extra='class="mono pulse"'),
        text(bc, 530, "signature overrides", 11, MUTED, anchor="middle"),
        text(bc, 546, "model adds confidence", 11, MUTED, anchor="middle"),
        line(M, 606, W - M, 606, LINE),
        text(M, 634, "Scapy AsyncSniffer · FastAPI · JWT roles · SQLite · WebSocket stream · React + Recharts", 12, DIM),
    ]
    return svg(h, "Evidence II — SentinelSphere hybrid intrusion detection",
               "Plate showing a packet stream on a time axis with a SYN burst near 'now', and three rolling windows: "
               "60 seconds for authentication attempts, 30 seconds for unique destination ports and flow volume, "
               "10 seconds for SYN and ICMP rates. Below, five signature rules (SYN flood, ICMP flood, port scan, "
               "brute force, ARP spoof) and two models (Isolation Forest anomaly scoring, Random Forest over five "
               "attack families) feed an alert; signatures override the model.",
               "\n".join(out))


def qr_plate() -> str:
    h = 640
    rng = random.Random(7)
    out = [
        grid(h),
        plate_header("EVIDENCE III", "QR Shield", "IMPLEMENTATION · PROTOTYPE-SCALE DATA",
                     "DECODE THE IMAGE · INTERROGATE THE URL · THEN DECIDE"),
    ]
    n, s, qx, qy = 21, 12, M, 250

    def finder(r, c):
        return any(r0 <= r < r0 + 7 and c0 <= c < c0 + 7 for r0, c0 in ((0, 0), (0, 14), (14, 0)))

    for r in range(n):
        for c in range(n):
            if finder(r, c):
                rr, cc = r % 14 if r >= 14 else r, c % 14 if c >= 14 else c
                on, drift, op = rr in (0, 6) or cc in (0, 6) or (2 <= rr <= 4 and 2 <= cc <= 4), 0, 1
            else:
                on = rng.random() < 0.46
                drift = max(0, c - 15) * rng.uniform(0, 7)
                op = max(1 - max(0, c - 15) * 0.12, .25)
            if on:
                out.append(f'<rect x="{qx + c * s + drift:.1f}" y="{qy + r * s}" width="{s - 1}" height="{s - 1}" '
                           f'fill="{INK}" opacity="{op:.2f}"/>')
    out.append(text(qx, qy + n * s + 34, "OpenCV · pyzbar decode", 12, DIM))
    out.append(text(qx, qy + n * s + 54, "FastAPI · MV3 extension", 12, DIM))

    lx = 400
    out.append(text(lx, 236, "decoded →", 13, MUTED))
    out.append(text(lx + 110, 236, "hxxps://secure-rnicrosoft.example/reset", 15, INK))
    layers = [("01", "FEEDBACK", "analyst verdicts override everything"),
              ("02", "REPUTATION", "blacklist · raw-IP host · suspicious TLD"),
              ("03", "PATTERNS", "homograph · punycode · obfuscation · typosquat"),
              ("04", "MODEL", "gradient boosting · 30 lexical features"),
              ("05", "VERIFY", "SSL validity · redirect chain")]
    for i, (num, name, detail) in enumerate(layers):
        y = 262 + i * 56
        hot = name == "PATTERNS"
        out.append(rect(lx, y, W - M - lx, 44, ACCENT if hot else LINE, BG, 1.5 if hot else 1))
        out.append(text(lx + 16, y + 28, num, 13, DIM))
        out.append(text(lx + 56, y + 28, name, 14, ACCENT if hot else INK))
        out.append(text(lx + 200, y + 28, detail, 13, MUTED))
        out.append(rect(W - M - 30, y + 15, 14, 14, ACCENT if hot else LINE_2, ACCENT if hot else "none", 1))
    sy = 572
    sx0, sx1 = lx + 80, W - M
    out.append(text(lx, sy - 10, "SCORE", 13, MUTED))
    out.append(line(sx0, sy - 14, sx1, sy - 14, LINE_2, 2))
    for t in range(0, 101, 25):
        x = sx0 + (sx1 - sx0) * t / 100
        out.append(line(x, sy - 20, x, sy - 8, LINE_2))
        out.append(text(x, sy + 10, str(t), 11, DIM, anchor="middle"))
    nx = sx0 + (sx1 - sx0) * 0.86
    out.append(f'<path d="M{nx - 7},{sy - 32} L{nx + 7},{sy - 32} L{nx},{sy - 18} Z" fill="{DENY}" class="pulse"/>')
    out.append(text(W - M, 612, "illustrative URL — layers run in this order", 11, DIM, anchor="end"))
    return svg(h, "Evidence III — QR Shield layered URL analysis",
               "Plate showing a QR code dissolving into a decoded, defanged example URL, which then passes through "
               "five ordered layers: feedback overrides; reputation checks (blacklist, raw-IP host, suspicious "
               "TLD); pattern checks (homograph, punycode, obfuscation, typosquat); a gradient-boosting model over "
               "30 lexical features; and live verification of SSL and redirects. A 0–100 score scale ends the plate.",
               "\n".join(out))


def studies_plate() -> str:
    h = 480
    out = [grid(h), line(600, 60, 600, h - 50, LINE)]
    out += [
        text(M, 72, "STUDY IV", 15, ACCENT),
        text(M, 128, "MalSim", 44, INK, cls="serif"),
        text(M, 162, "ARCHITECTURE STUDY · SANDBOX SIMULATED", 12, MUTED),
        text(M, 214, "COMPOSITE THREAT SCORE", 12, MUTED),
    ]
    x, bw = M, 600 - 2 * M
    for name, wgt, op in (("STATIC", .35, .95), ("DYNAMIC", .30, .7), ("YARA", .20, .48), ("NET", .15, .3)):
        seg = bw * wgt
        out.append(rect(x, 252, seg - 3, 34, "none", ACCENT, 0, f'opacity="{op}"'))
        out.append(text(x, 242, name, 12, INK))
        out.append(text(x, 310, f"×{wgt:.2f}", 13, MUTED))
        x += seg
    for a, b, lvl in ((0, 10, "CLEAN"), (10, 40, "LOW"), (40, 70, "MEDIUM"), (70, 100, "HIGH")):
        xx = M + bw * a / 100
        out.append(line(xx, 344, xx, 354, LINE_2))
        out.append(text(xx, 392, str(a), 11, DIM, anchor="middle"))
        out.append(text(M + bw * (a + b) / 200, 372, lvl, 11, DENY if lvl == "HIGH" else MUTED, anchor="middle"))
    out.append(line(M, 349, M + bw, 349, LINE_2))
    out.append(text(M, 432, "computed: SHA-256 · SHA-1 · MD5", 12, DIM))

    rx = 600 + M
    out += [
        text(rx, 72, "STUDY V", 15, ACCENT),
        text(rx, 128, "HEALIX", 44, INK, cls="serif"),
        text(rx, 162, "HACKATHON PROTOTYPE", 12, MUTED),
    ]
    # HealixSystem.process_signal, in order; drawn as a serpentine so GOVERN sits on the turn
    bw_, bh_, gx = 140, 46, 26
    cols_x = [rx + i * (bw_ + gx) for i in range(3)]
    stages = [("INGEST", cols_x[0], 214), ("CONTEXT", cols_x[1], 214), ("REASON", cols_x[2], 214),
              ("GOVERN", cols_x[2], 320), ("ACT", cols_x[1], 320), ("LEARN", cols_x[0], 320)]
    for name, nx, ny in stages:
        gov = name == "GOVERN"
        out.append(rect(nx, ny, bw_, bh_, ACCENT if gov else LINE_2, BG, 1.5))
        out.append(text(nx + bw_ / 2, ny + 29, name, 14, ACCENT if gov else INK, anchor="middle"))
    out += [
        line(cols_x[0] + bw_, 237, cols_x[1], 237, MUTED, 1.5, 'class="flow"'),
        line(cols_x[1] + bw_, 237, cols_x[2], 237, MUTED, 1.5, 'class="flow"'),
        line(cols_x[2] + bw_ / 2, 260, cols_x[2] + bw_ / 2, 320, MUTED, 1.5, 'class="flow"'),
        line(cols_x[2], 343, cols_x[1] + bw_, 343, MUTED, 1.5, 'class="flow"'),
        line(cols_x[1], 343, cols_x[0] + bw_, 343, MUTED, 1.5, 'class="flow"'),
        text(rx, 296, "specialists: payments · auth · infra", 12, DIM),
        text(rx, 400, "payment actions: autonomy 0.0, approval required", 12, MUTED),
        text(rx, 420, "LLM: Ollama → OpenAI → simulated fallback", 12, DIM),
    ]
    return svg(h, "Studies IV and V — MalSim scoring and the HEALIX governed pipeline",
               "Left: MalSim's composite threat score, weighted static 0.35, dynamic 0.30, YARA 0.20, network 0.15, "
               "mapped to CLEAN below 10, LOW from 10, MEDIUM from 40, HIGH from 70; sandbox stages are simulated, file hashes are computed. "
               "Right: HEALIX's six-stage pipeline — ingest, context, reason, govern, act, learn — with governance "
               "highlighted. Payment actions have zero autonomy and always require approval.",
               "\n".join(out))


def landscape_plate() -> str:
    cols = ["CloudContextGuard", "SentinelSphere", "QR Shield", "MalSim", "HEALIX",
            "StudyAssistant", "Resume Ranker", "FinPlanPremium", "EnerVision", "IoT (team)"]
    # One character per column above: P = primary evidence in source, S = supporting, . = none
    rows = [
        ("Security engineering", "PPPPS....."),
        ("Machine learning", ".PP.S.P.S."),
        ("LLMs & agents", "....PP...."),
        ("Backend & APIs", "PPPPS..P.."),
        ("Interfaces & visualisation", "PPS.SSSPS."),
        ("Networks & traffic", "SP........"),
        ("Testing & documentation", "PS........"),
        ("Embedded & IoT", ".........P"),
    ]
    h = 700
    cx0, cstep, ry0, rstep = 470, 66, 330, 40
    out = [
        grid(h),
        text(M, 72, "FIG. 03", 15, ACCENT),
        text(W - M, 72, "DERIVED FROM REPOSITORY SOURCE", 14, MUTED, anchor="end"),
        text(M, 132, "Evidence matrix", 50, INK, cls="serif"),
        text(M, 172, "DOMAINS × REPOSITORIES", 15, MUTED),
    ]
    for j, name in enumerate(cols):
        x = cx0 + j * cstep
        out.append(line(x, ry0 - 22, x, ry0 + (len(rows) - 1) * rstep + 18, GRID_MAJOR))
        out.append(text(x + 4, ry0 - 34, name, 13, INK, extra=f'transform="rotate(-40 {x + 4} {ry0 - 34})"'))
    for i, (name, marks) in enumerate(rows):
        y = ry0 + i * rstep
        out.append(line(M, y + 20, cx0 + (len(cols) - 1) * cstep + 24, y + 20, GRID_MAJOR))
        out.append(text(M, y + 7, name, 22, INK, cls="serif"))
        for j, mk in enumerate(marks):
            x = cx0 + j * cstep
            if mk == "P":
                out.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{ACCENT}"/>')
            elif mk == "S":
                out.append(f'<circle cx="{x}" cy="{y}" r="6.5" fill="none" stroke="{MUTED}" stroke-width="2"/>')
            else:
                out.append(f'<circle cx="{x}" cy="{y}" r="1.5" fill="{LINE_2}"/>')
    ly = h - 46
    out += [
        line(M, ly - 30, W - M, ly - 30, LINE),
        f'<circle cx="{M + 8}" cy="{ly - 4}" r="8" fill="{ACCENT}"/>',
        text(M + 26, ly + 1, "primary evidence", 13, INK),
        f'<circle cx="{M + 246}" cy="{ly - 4}" r="6.5" fill="none" stroke="{MUTED}" stroke-width="2"/>',
        text(M + 264, ly + 1, "supporting evidence", 13, INK),
        f'<circle cx="{M + 516}" cy="{ly - 4}" r="1.5" fill="{LINE_2}"/>',
        text(M + 532, ly + 1, "no public evidence — left empty", 13, MUTED),
    ]
    return svg(h, "Figure 03 — Evidence matrix of domains and repositories",
               "Dot matrix with eight domains as rows and ten repositories as columns. Security engineering is "
               "primary in CloudContextGuard, SentinelSphere, QR Shield and MalSim. Machine learning is primary "
               "in SentinelSphere, QR Shield and Resume Ranker. LLMs and agents in HEALIX and StudyAssistant. "
               "Backend and APIs in CloudContextGuard, SentinelSphere, QR Shield, MalSim and FinPlanPremium. "
               "Networks and traffic in SentinelSphere. Testing and documentation in CloudContextGuard. Embedded "
               "and IoT in a team IoT project.",
               "\n".join(out))


def mark() -> str:
    """Standalone identity mark: the enfilade without labels, for reuse at small sizes."""
    s = 240
    c = s / 2
    parts = []
    for i in range(6):
        hv = 100 - i * 16
        colour = INK if i == 5 else LINE_2 if i else MUTED
        parts.append(f'<path d="M{c + hv},{c - 9} L{c + hv},{c - hv} L{c - hv},{c - hv} L{c - hv},{c + hv} '
                     f'L{c + hv},{c + hv} L{c + hv},{c + 9}" fill="none" stroke="{colour}" stroke-width="3"/>')
    parts.append(line(s, c, c + 12, c, ACCENT, 4))
    parts.append(f'<rect x="{c - 6}" y="{c - 6}" width="12" height="12" fill="{ACCENT}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}" width="{s}" height="{s}" '
            f'role="img" aria-label="Enfilade mark: six nested rooms with aligned doors">'
            f'<rect width="{s}" height="{s}" fill="{BG}"/>{"".join(parts)}</svg>\n')


# ---------------------------------------------------------------- BUILD
def main() -> None:
    files = {
        "hero/opening-frame.svg": hero(),
        "hero/closing-frame.svg": closing(),
        "identity/enfilade-mark.svg": mark(),
        "projects/01-cloudcontextguard.svg": ccg_plate(),
        "projects/02-sentinelsphere-nids.svg": nids_plate(),
        "projects/03-qr-shield.svg": qr_plate(),
        "projects/04-studies.svg": studies_plate(),
        "diagrams/evidence-matrix.svg": landscape_plate(),
    }
    for i in range(1, len(CHAPTERS)):
        files[f"visual-system/chapter-{CHAPTERS[i][0]}.svg"] = chapter(i)
    for rel, content in files.items():
        path = ASSETS / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote {rel} ({len(content):,} bytes)")


if __name__ == "__main__":
    main()
