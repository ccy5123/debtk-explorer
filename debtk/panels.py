"""The charts the technical explorer carries, rebuilt on the Python model.

Each function takes already-computed arrays and returns an Altair chart; nothing here touches the model, so a
panel cannot quietly disagree with the numbers shown elsewhere on the page.
"""
from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd

TEAL, RUST, GREEN, SLATE, DEEP, WARN = "#0E7C86", "#B4442E", "#2F7A52", "#5C726E", "#10354F", "#C05621"
LIMIT_COLOURS = {"boundary layer": "#4FA3A8", "ventilation": GREEN, "membrane": WARN, "perfusion": DEEP}


def _dom(v, pad=0.05, log=False):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if not len(v):
        return None
    lo, hi = float(v.min()), float(v.max())
    if log and lo > 0:
        f = (hi / lo) ** pad
        return [lo / f, hi * f]
    span = (hi - lo) or abs(hi) or 1.0
    return [lo - span * pad, hi + span * pad]


def scatter_vs_kow(logKow, y, limiting, name, y_title: str, kow_window=None, highlight=None):
    """One modelled quantity over hydrophobicity, coloured by the step that limits uptake."""
    d = pd.DataFrame({"log Kow": logKow, "y": y, "limited by": limiting, "chemical": name})
    d = d[np.isfinite(d.y)]
    ch = alt.Chart(d).mark_circle(size=34, opacity=0.65).encode(
        x=alt.X("log Kow:Q", scale=alt.Scale(domain=_dom(d["log Kow"]), nice=False), title="log K_OW"),
        y=alt.Y("y:Q", scale=alt.Scale(domain=_dom(d.y), nice=False), title=y_title),
        color=alt.Color("limited by:N", title="limited by", scale=alt.Scale(
            domain=list(LIMIT_COLOURS), range=list(LIMIT_COLOURS.values()))),
        tooltip=["chemical:N", "log Kow:Q", alt.Tooltip("y:Q", title=y_title), "limited by:N"],
    )
    layers = [ch]
    if kow_window:
        band = alt.Chart(pd.DataFrame({"lo": [kow_window[0]], "hi": [kow_window[1]]})).mark_rect(
            opacity=0.07, color=TEAL).encode(x="lo:Q", x2="hi:Q")
        layers.insert(0, band)
    if highlight is not None and highlight[0] is not None:     # no log K_OW, no place on this axis
        hl = alt.Chart(pd.DataFrame({"log Kow": [highlight[0]], "y": [highlight[1]],
                                     "chemical": [highlight[2]]})).mark_point(
            size=220, shape="diamond", filled=True, color=RUST).encode(
            x="log Kow:Q", y="y:Q", tooltip=["chemical:N"])
        layers.append(hl)
    return alt.layer(*layers).properties(height=340).interactive()


def benchmark_panel(bins: dict, measured: pd.DataFrame | None, y_title="log BCF"):
    """Binned medians: this model, the partition ceiling, and the two published one-box models."""
    frames = []
    for label, (x, y) in bins.items():
        frames.append(pd.DataFrame({"log Kow": x, "y": y, "curve": label}))
    d = pd.concat(frames, ignore_index=True)
    colours = {"this model": TEAL, "partition ceiling (P_Wd)": SLATE,
               "Arnot & Gobas 2004": WARN, "OMEGA (Hendriks 2001)": RUST}
    line = alt.Chart(d).mark_line(size=2.5, point=True).encode(
        x=alt.X("log Kow:Q", title="log K_OW", scale=alt.Scale(domain=_dom(d["log Kow"]), nice=False)),
        y=alt.Y("y:Q", title=y_title, scale=alt.Scale(domain=_dom(d.y), nice=False)),
        color=alt.Color("curve:N", title=None, scale=alt.Scale(
            domain=[k for k in colours if k in bins], range=[colours[k] for k in colours if k in bins])),
        tooltip=["curve:N", "log Kow:Q", "y:Q"],
    )
    if measured is not None and len(measured):
        pts = alt.Chart(measured).mark_point(shape="square", size=70, filled=True, color="#11201F").encode(
            x="log Kow:Q", y="median:Q",
            tooltip=["chemical:N", "median:Q", "lo:Q", "hi:Q", "n:Q"])
        bars = alt.Chart(measured).mark_rule(color="#11201F", opacity=0.45).encode(
            x="log Kow:Q", y="lo:Q", y2="hi:Q")
        return alt.layer(line, bars, pts).properties(height=360).interactive()
    return line.properties(height=360).interactive()


def limit_map(logKow_grid, weights, limiting_grid, species_label: str):
    """Which step limits uptake, over hydrophobicity and body weight."""
    def wlabel(W):
        return f"{W:,.0f}" if W >= 100 else f"{W:,.1f}" if W >= 10 else f"{W:.2g}"

    rows = []
    for i, W in enumerate(weights):
        for j, k in enumerate(logKow_grid):
            rows.append({"log Kow": k, "weight": wlabel(W), "W": W, "limited by": limiting_grid[i][j]})
    d = pd.DataFrame(rows)
    return alt.Chart(d).mark_rect().encode(
        x=alt.X("log Kow:O", title="log K_OW",
                axis=alt.Axis(labelAngle=0, values=[v for v in sorted(set(d["log Kow"]))
                                                    if abs(v - round(v)) < 1e-9])),
        y=alt.Y("weight:O", title=f"{species_label} weight (g)",
                sort=alt.EncodingSortField(field="W", order="descending")),
        color=alt.Color("limited by:N", title="limited by", scale=alt.Scale(
            domain=list(LIMIT_COLOURS), range=list(LIMIT_COLOURS.values()))),
        tooltip=["log Kow:O", alt.Tooltip("weight:O", title="weight (g)"), "limited by:N"],
    ).properties(height=380)


def inputs_2x2(logKow, series: dict, halogens=None):
    """The structure-derived inputs, one panel each, so a small one is not buried under a large one."""
    frames = []
    for label, v in series.items():
        frames.append(pd.DataFrame({"log Kow": logKow, "value": v, "quantity": label,
                                    "halogens": halogens if halogens is not None else 0}))
    d = pd.concat(frames, ignore_index=True)
    d = d[np.isfinite(d.value)]
    return alt.Chart(d).mark_circle(size=26, opacity=0.6).encode(
        x=alt.X("log Kow:Q", title="log K_OW", scale=alt.Scale(zero=False, nice=False)),
        y=alt.Y("value:Q", title=None, scale=alt.Scale(zero=False, nice=False)),
        color=alt.Color("halogens:Q", title="halogen atoms",
                        scale=alt.Scale(scheme="teals")),
        tooltip=["log Kow:Q", "value:Q", "halogens:Q"],
    ).properties(width=330, height=210).facet(
        facet=alt.Facet("quantity:N", title=None, sort=list(series)), columns=2
    ).resolve_scale(y="independent")
