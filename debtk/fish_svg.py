"""Draw the fish: the author's drawing, coloured by what is in the animal and stretched to its body shape.

The drawing is assets/fish.svg, kept as it was supplied. This module only
  * recolours the parts it names (body, muscle, fins, tail, gill, liver, blood),
  * stretches the outline by the species' shape coefficient,
  * hangs the four fluxes on the anchors the drawing provides,
and leaves everything else alone.

The stretch: structural length is del_M times the length someone measured, so at a fixed weight the structural
volume L^3 is fixed and the physical length is L/del_M; with a round cross-section the depth-to-length ratio
goes as del_M^1.5. That factor is applied at half strength against the trout the drawing is, because applied in
full the median AmP entry is twice as deep as a trout and most of the collection pins against any clamp that
keeps the picture drawable - and part of the spread is not shape at all, since del_M is fitted against whichever
length an entry's data reported. The ordering is the model's; the magnitude is pulled in on purpose.
"""
from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path

ASSET = Path(__file__).resolve().parent.parent / "assets" / "fish.svg"

# the concentration ramp, pale to hot, over 10^0 .. 10^6 ng/kg
RAMP = ["#FBF4E6", "#F6DFA8", "#EFB263", "#DD7B3F", "#B4442E"]
CONC_LO, CONC_HI = 0.0, 6.0

DM_TROUT = 0.10543          # the entry the drawing is of
SHAPE_DAMP = 0.5
SHAPE_CLAMP = (0.55, 2.3)
CX, CY = 430.0, 186.0       # the middle of the drawing

ARROW_COLOUR = {"uptake": "#0E7C86", "respiratory loss": "#5C726E",
                "metabolism": "#B4442E", "growth dilution": "#2F7A52"}


@lru_cache(maxsize=1)
def _template() -> str:
    return ASSET.read_text(encoding="utf-8")


def conc_fraction(c_ng_kg: float) -> float:
    """Where a concentration sits on the ramp, 0 to 1, on a log scale."""
    c = max(c_ng_kg, 10 ** CONC_LO)
    return min(1.0, max(0.0, (math.log10(c) - CONC_LO) / (CONC_HI - CONC_LO)))


def ramp_colour(frac: float) -> str:
    f = min(1.0, max(0.0, frac)) * (len(RAMP) - 1)
    i = min(int(f), len(RAMP) - 2)
    t = f - i
    a, b = RAMP[i].lstrip("#"), RAMP[i + 1].lstrip("#")
    out = [round(int(a[j:j + 2], 16) + (int(b[j:j + 2], 16) - int(a[j:j + 2], 16)) * t) for j in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(out)


def dark_fill(frac: float) -> bool:
    return frac > 0.62


def shape_of(del_M: float | None) -> dict:
    """How much deeper than the trout this animal is drawn, and the scale factors that do it."""
    if not del_M:
        return {"sx": 1.0, "sy": 1.0, "R": 1.0, "raw": 1.0, "del_M": None}
    raw = (del_M / DM_TROUT) ** 1.5
    R = min(SHAPE_CLAMP[1], max(SHAPE_CLAMP[0], raw ** SHAPE_DAMP))
    sy = math.sqrt(R)
    return {"sx": 1.0 / sy, "sy": sy, "R": R, "raw": raw, "del_M": del_M}


def _recolour(svg: str, part: str, fill: str) -> str:
    """Replace the fill on one named element, leaving every other attribute as drawn."""
    pat = re.compile(r'(<(?:path|g)\s+id="%s"[^>]*?)fill="[^"]*"' % re.escape(part))
    return pat.sub(lambda m: m.group(1) + 'fill="%s"' % fill, svg, count=1)


PART_TITLES = {
    "en": {
        "fish-body": "whole body — the concentration the model solves for",
        "fish-muscle": "muscle, drawn a shade behind the whole body",
        "fish-gill": "gill — where uptake and respiratory loss happen; its colour is the water, not the fish",
        "fish-liver": "liver — shaded by how much of the loss is biotransformation",
        "fish-blood": "blood — the gill exchanges with it; P_Bd is its partition coefficient",
        "fish-tail": "tail fin",
        "fish-fins": "fins",
    },
    "ko": {
        "fish-body": "전어체 — 모델이 계산하는 농도",
        "fish-muscle": "근육 — 전어체보다 한 단계 옅게 그립니다",
        "fish-gill": "아가미 — 흡수와 호흡 배출이 일어나는 곳. 색은 물고기가 아니라 물의 농도입니다",
        "fish-liver": "간 — 전체 손실 중 생물전환이 차지하는 비율로 색을 냅니다",
        "fish-blood": "혈액 — 아가미가 교환하는 상대이며, P_Bd가 그 분배계수입니다",
        "fish-tail": "꼬리지느러미",
        "fish-fins": "지느러미",
    },
}

LABELS = {
    "en": {"water": "water {c:.2f} ng/L — exposure", "clean": "clean water — depuration", "day": "day {d:.1f}",
           "uptake": "uptake {v:,.1f} ng kg⁻¹ d⁻¹", "out": "back out of the gill {v:,.1f}",
           "met": "metabolised {v:,.1f}", "growth": "diluted by growth {v:,.1f}",
           "steady": "{p:.0f}% of its steady state",
           "shape": " · outline {r:.2f}× deeper than the trout it is drawn as (shape coefficient {dm:g}, "
                    "stretch damped)",
           "noshape": " · drawn as the trout, no shape coefficient for it"},
    "ko": {"water": "물 {c:.2f} ng/L — 노출 중", "clean": "깨끗한 물 — 배출 중", "day": "{d:.1f}일차",
           "uptake": "흡수 {v:,.1f} ng kg⁻¹ /일", "out": "아가미로 되나감 {v:,.1f}",
           "met": "대사로 분해 {v:,.1f}", "growth": "성장으로 희석 {v:,.1f}",
           "steady": "정상상태의 {p:.0f}%",
           "shape": " · 그림의 바탕인 송어보다 {r:.2f}배 깊게 (형태계수 {dm:g}, 변형 완화 적용)",
           "noshape": " · 형태계수가 없어 송어 모양 그대로"},
}


def _add_titles(svg: str, lang: str = "en") -> str:
    """A <title> inside an element is the browser's own tooltip. No script, no library."""
    for part, text in PART_TITLES.get(lang, PART_TITLES["en"]).items():
        pat = re.compile(r'(<(path|g)\s+id="%s"[^>]*?)(/>|>)' % re.escape(part))
        m = pat.search(svg)
        if not m:
            continue
        if m.group(3) == "/>":
            svg = svg[:m.start()] + m.group(1) + f"><title>{text}</title></{m.group(2)}>" + svg[m.end():]
        else:
            svg = svg[:m.end()] + f"<title>{text}</title>" + svg[m.end():]
    return svg


def ramp_legend(width: int = 320, height: int = 40) -> str:
    """The colour scale, so a reader can put a number on a shade."""
    decades = int(CONC_HI - CONC_LO)
    bar_h = height - 16
    stops = "".join(f'<stop offset="{i / (len(RAMP) - 1):.3f}" stop-color="{c}"/>'
                    for i, c in enumerate(RAMP))
    ticks = "".join(
        f'<text x="{width * i / decades:.0f}" y="{height - 2}" font-size="9.5" '
        f'text-anchor="{"start" if i == 0 else "end" if i == decades else "middle"}" '
        f'fill="#59706C">10{"⁰¹²³⁴⁵⁶"[i]}</text>'
        for i in range(decades + 1))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"><defs><linearGradient id="ramp">{stops}</linearGradient></defs>'
            f'<rect x="0" y="0" width="{width}" height="{bar_h}" fill="url(#ramp)" rx="3"/>{ticks}</svg>')


def _arrow(x1, y1, x2, y2, width, colour, opacity=1.0) -> str:
    """One flux. The head is a polygon sized from the line, so a thick flux keeps a head."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    head = min(0.45 * L, max(11.0, 2.1 * width))
    half = max(6.5, 1.25 * width)
    bx, by = x2 - ux * head, y2 - uy * head
    px, py = -uy, ux
    return (f'<g opacity="{opacity:.2f}">'
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{colour}" '
            f'stroke-width="{width:.2f}" stroke-linecap="butt"/>'
            f'<polygon points="{x2:.1f},{y2:.1f} {bx + px * half:.1f},{by + py * half:.1f} '
            f'{bx - px * half:.1f},{by - py * half:.1f}" fill="{colour}"/></g>')


def render(C_fish: float, C_water: float, day: float, exposure: bool, rates: dict,
           del_M: float | None = None, species_label: str = "", steady: float | None = None,
           lang: str = "en") -> str:
    """The whole picture as one SVG string."""
    frac = conc_fraction(C_fish)
    sh = shape_of(del_M)
    sx, sy = sh["sx"], sh["sy"]

    def T(x, y):
        return CX + (x - CX) * sx, CY + (y - CY) * sy

    met_share = 0.0
    out_flux = rates["k_er"] * C_fish
    met_flux = rates["k_Bt"] * C_fish
    grow_flux = rates["k_g"] * C_fish
    up_flux = rates["k1"] * C_water
    denom = max(out_flux + met_flux + grow_flux, 1e-30)
    met_share = met_flux / denom
    max_flux = max(up_flux, denom, 1e-30)

    def w(f):
        return 1.5 + 9.0 * math.sqrt(max(f, 0.0) / max_flux)

    svg = _template()
    svg = _recolour(svg, "fish-body", ramp_colour(frac))
    svg = _recolour(svg, "fish-muscle", ramp_colour(max(0.0, frac - 0.05)))
    svg = _recolour(svg, "fish-fins", ramp_colour(max(0.0, frac - 0.10)))
    svg = _recolour(svg, "fish-tail", ramp_colour(max(0.0, frac - 0.10)))
    svg = _recolour(svg, "fish-gill", ramp_colour(conc_fraction(C_water * 1000) if exposure else 0.05))
    svg = _recolour(svg, "fish-liver", ramp_colour(met_share) if met_flux > 0 else "#E7E2D8")
    svg = re.sub(r'(<path d="M 603,172[^"]*" stroke=)"#c0392b"', r'\1"%s"' % ramp_colour(frac), svg, count=1)

    svg = _add_titles(svg, lang)
    W = LABELS.get(lang, LABELS["en"])
    # wrap the drawing in the shape transform, then add the fluxes outside it so the text keeps its size
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    transform = (f'translate({CX} {CY}) scale({sx:.4f} {sy:.4f}) translate({-CX} {-CY})')

    water = "#CFE4EA" if exposure else "#EBF1F2"
    head = (f'<rect x="0" y="0" width="860" height="400" fill="{water}"/>'
            f'<text x="20" y="30" font-size="14" fill="#445956">'
            + (W["water"].format(c=C_water) if exposure else W["clean"])
            + f'</text><text x="20" y="50" font-size="13" fill="#6B7E7B">'
            + W["day"].format(d=day) + '</text>')

    mouth = T(739, 190)
    gill_out = T(644, 234)
    liver = T(550, 246)
    tail = T(236, 214)
    label = T(410, 222)
    sub = T(410, 242)

    arrows = [
        _arrow(830, 116, mouth[0], mouth[1], w(up_flux), ARROW_COLOUR["uptake"], 1.0 if exposure else 0.15),
        f'<text x="846" y="96" text-anchor="end" font-size="12.5" fill="{ARROW_COLOUR["uptake"]}">'
        + W["uptake"].format(v=up_flux) + '</text>',
        _arrow(gill_out[0], gill_out[1], 796, 302, w(out_flux), ARROW_COLOUR["respiratory loss"]),
        f'<text x="846" y="322" text-anchor="end" font-size="12.5" '
        f'fill="{ARROW_COLOUR["respiratory loss"]}">' + W["out"].format(v=out_flux) + '</text>',
        _arrow(tail[0], tail[1], 148, 308, w(grow_flux), ARROW_COLOUR["growth dilution"]),
        f'<text x="136" y="328" font-size="12.5" fill="{ARROW_COLOUR["growth dilution"]}">'
        + W["growth"].format(v=grow_flux) + '</text>',
    ]
    if met_flux > 0:
        arrows += [
            _arrow(liver[0], liver[1], liver[0], 332, w(met_flux), ARROW_COLOUR["metabolism"]),
            f'<text x="{liver[0]:.0f}" y="352" text-anchor="middle" font-size="12.5" '
            f'fill="{ARROW_COLOUR["metabolism"]}">' + W["met"].format(v=met_flux) + '</text>',
        ]

    ink = "#FFF6EC" if dark_fill(frac) else "#2B2B2B"
    ink2 = "#F3DCC8" if dark_fill(frac) else "#55514B"
    reading = (f'<text x="{label[0]:.0f}" y="{label[1]:.0f}" text-anchor="middle" font-size="17" '
               f'font-weight="600" fill="{ink}">{C_fish:,.0f} ng kg⁻¹</text>')
    if steady and steady > 0:
        reading += (f'<text x="{sub[0]:.0f}" y="{sub[1]:.0f}" text-anchor="middle" font-size="12" '
                    f'fill="{ink2}">' + W["steady"].format(p=100 * min(1.0, C_fish / steady)) + '</text>')

    caption = (f'<text x="840" y="386" text-anchor="end" font-size="12.5" fill="#6B7E7B">{species_label}'
               + (W["shape"].format(r=sh["R"], dm=sh["del_M"]) if sh["del_M"] else W["noshape"])
               + '</text>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 400" width="100%" '
            f'style="max-width:860px;font-family:system-ui,-apple-system,Segoe UI,sans-serif">'
            f'{head}<g transform="{transform}">{body}</g>{"".join(arrows)}{reading}{caption}</svg>')
