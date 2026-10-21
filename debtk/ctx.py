"""Look a chemical up in EPA CompTox, the way the rice model does.

The HTML explorer had to ask PubChem, because a page without a server cannot call CTX: CTX wants its key in a
request header, which forces a CORS preflight, and that preflight is answered 401 with no allowed headers.
This app has a server, so it can use CTX itself - the same source the library's own log K_OW values come from.

The key comes from the environment (EPA_API_KEY or CTX_API_KEY), or from Streamlit secrets, or is typed into
the sidebar; it is never written into the repository.

The traps, all of which fail silently and all of which bit before:
  * the batch search body is newline-separated text, but the batch property body is a JSON array
  * 'NaN', 'inf', 'null' and 'N/A' arrive as strings - reject before float()
  * property records are camelCase (propName, propValue, propUnit, sourceName)
  * measured against predicted is known only from the URL called, so it is tagged at call time
  * name search is case-sensitive, and a miss returns suggestions rather than an error
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

BASE = "https://comptox.epa.gov/ctx-api"
TIMEOUT = 30
MIN_GAP = 0.4            # seconds between calls; the service cuts off a burst
_last_call = [0.0]
BAD = {"nan", "inf", "-inf", "null", "n/a", "na", "none", ""}
LOGKOW_PROP = "LogKow: Octanol-Water"


def api_key(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit.strip()
    for name in ("EPA_API_KEY", "CTX_API_KEY"):
        v = os.environ.get(name)
        if v:
            return v.strip()
    try:
        import streamlit as st
        for name in ("ctx_api_key", "EPA_API_KEY", "CTX_API_KEY"):
            if name in st.secrets:
                return str(st.secrets[name]).strip()
    except Exception:                                                   # noqa: BLE001
        pass
    return None


def _num(v):
    """A CTX number, or None. The service sends 'NaN' and friends as strings."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v) if v == v and abs(v) != float("inf") else None
    if str(v).strip().lower() in BAD:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f and abs(f) != float("inf") else None


def _call(path: str, key: str, body=None, retries: int = 3):
    url = f"{BASE}{path}"
    data = None
    headers = {"x-api-key": key, "accept": "application/json",
               "user-agent": "debtk-explorer/1.0"}
    if body is not None:
        if isinstance(body, str):
            data = body.encode()
            headers["content-type"] = "text/plain"
        else:
            data = json.dumps(body).encode()
            headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    for attempt in range(retries):
        gap = MIN_GAP - (time.monotonic() - _last_call[0])
        if gap > 0:
            time.sleep(gap)
        _last_call[0] = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return None          # a query the service cannot read is a miss, not a failure
            if e.code in (429, 502, 503, 504) and attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise RuntimeError(f"CompTox answered {e.code} for {path}") from e
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise RuntimeError(f"CompTox could not be reached: {e.reason}") from e
        except OSError as e:
            # a reset mid-read is not a URLError and would otherwise escape the retry; being cut off means
            # the calls were too close together, so back off hard rather than retrying straight away
            if attempt < retries - 1:
                time.sleep(2.0 * 2 ** attempt)
                continue
            raise RuntimeError(f"CompTox dropped the connection: {e}. It does that when calls arrive in a "
                               f"burst; wait a moment and ask again.") from e
    return None


@dataclass
class Hit:
    dtxsid: str
    name: str
    casrn: str = ""
    smiles: str = ""
    formula: str = ""
    mw: float | None = None
    logKow: float | None = None
    logKow_source: str = ""          # "experimental (median of n)" or "predicted, OPERA" etc.
    logKow_n: int = 0
    notes: list = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"https://comptox.epa.gov/dashboard/chemical/details/{self.dtxsid}"


def search(query: str, key: str) -> list[Hit]:
    """Resolve a name, CAS or InChIKey to entries. Name search is case-sensitive; a miss offers suggestions."""
    q = (query or "").strip()
    if not q:
        return []
    recs = _call(f"/chemical/search/equal/{urllib.parse.quote(q)}", key) or []
    hits = []
    for rec in recs if isinstance(recs, list) else []:
        if not rec.get("dtxsid"):
            continue
        hits.append(Hit(dtxsid=rec["dtxsid"], name=rec.get("preferredName") or q,
                        casrn=rec.get("casrn", "") or "", smiles=rec.get("smiles", "") or ""))
    if not hits:
        sug = _call(f"/chemical/search/start-with/{urllib.parse.quote(q)}", key) or []
        for rec in (sug if isinstance(sug, list) else [])[:8]:
            if rec.get("dtxsid"):
                hits.append(Hit(dtxsid=rec["dtxsid"], name=rec.get("preferredName") or q,
                                casrn=rec.get("casrn", "") or "", smiles=rec.get("smiles", "") or "",
                                notes=["matched by prefix, not exactly"]))
    return hits


def detail(hit: Hit, key: str) -> Hit:
    """Formula and molar mass, from the entry's own record."""
    rec = _call(f"/chemical/detail/search/by-dtxsid/{hit.dtxsid}", key) or {}
    if isinstance(rec, list):
        rec = rec[0] if rec else {}
    hit.formula = rec.get("molFormula") or hit.formula
    hit.mw = _num(rec.get("averageMass")) or _num(rec.get("monoisotopicMass")) or hit.mw
    hit.smiles = rec.get("smiles") or hit.smiles
    hit.name = rec.get("preferredName") or hit.name
    hit.casrn = rec.get("casrn") or hit.casrn
    return hit


def log_kow(hit: Hit, key: str, prefer: str = "experimental") -> Hit:
    """log K_OW, measured if the entry has one, otherwise OPERA's prediction. Tagged at call time."""
    exp = _call(f"/chemical/property/experimental/search/by-dtxsid/{hit.dtxsid}", key) or []
    vals = [_num(r.get("propValue")) for r in exp
            if str(r.get("propName", "")).strip() == LOGKOW_PROP]
    vals = [v for v in vals if v is not None]
    if prefer == "experimental" and vals:
        vals.sort()
        hit.logKow = vals[len(vals) // 2]
        hit.logKow_source = f"experimental, median of {len(vals)}"
        hit.logKow_n = len(vals)
        return hit
    pred = _call(f"/chemical/property/predicted/search/by-dtxsid/{hit.dtxsid}", key) or []
    opera = [(_num(r.get("propValue")), r) for r in pred
             if str(r.get("propName", "")).strip() == LOGKOW_PROP
             and "OPERA" in str(r.get("modelName", "") or r.get("sourceName", "")).upper()]
    opera = [(v, r) for v, r in opera if v is not None]
    if opera:
        v, rec = opera[0]
        hit.logKow = v
        ad = rec.get("adConclusionGlobal")
        hit.logKow_source = "predicted, OPERA" + (f" ({ad})" if ad else "")
        if vals:
            hit.notes.append(f"the entry also carries {len(vals)} measured values, median "
                             f"{sorted(vals)[len(vals) // 2]:.2f}")
        return hit
    if vals:
        vals.sort()
        hit.logKow = vals[len(vals) // 2]
        hit.logKow_source = f"experimental, median of {len(vals)}"
        hit.logKow_n = len(vals)
    return hit


def lookup(query: str, key: str, prefer: str = "experimental") -> list[Hit]:
    """One call from the interface: resolve, then fill in what the model needs."""
    hits = search(query, key)
    out = []
    for h in hits[:6]:
        try:
            out.append(log_kow(detail(h, key), key, prefer))
        except RuntimeError as e:
            h.notes.append(str(e))
            out.append(h)
    return out


FORMULA = re.compile(r"([A-Z][a-z]?)(\d*)")


def parse_formula(formula: str, masses: dict, halogen_names) -> tuple[float, int] | None:
    """Molar mass and halogen count from a molecular formula, or None if an element is unknown."""
    txt = re.sub(r"[()\s+\-]", "", formula or "")
    if not txt:
        return None
    mw, nhal, seen = 0.0, 0, False
    for el, n in FORMULA.findall(txt):
        if not el:
            continue
        if el not in masses:
            return None
        k = int(n) if n else 1
        mw += masses[el] * k
        if el in halogen_names:
            nhal += k
        seen = True
    return (mw, nhal) if seen else None
