"""What the app runs on: the 866 scanned structures and the 3,039 Add-my-Pet fish entries.

Both files are already built and checked elsewhere, and are read here rather than rebuilt:

  exploratory/pops_scan/simulator/sim_data.json   the structures, their partition coefficients at each of the
      three tabulated temperatures, and the gill-geometry sets (exploratory/pops_scan/export_simulator_data.py)
  exploratory/amp_collection/fish_species.json    every AmP fish entry whose own oxygen-flux statistics the
      implementation reproduces, with its shape coefficient (exploratory/amp_collection/build_fish_species.py)
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from . import model as M

# A deployed copy carries the two files in data/ beside the app (export_deploy.sh puts them there);
# in the workspace they are read where they are built.
_LOCAL = Path(__file__).resolve().parents[1] / "data"
if (_LOCAL / "sim_data.json").exists():
    SIM, FISH = _LOCAL / "sim_data.json", _LOCAL / "fish_species.json"
else:
    WS = Path(__file__).resolve().parents[3]
    SIM = WS / "exploratory/pops_scan/simulator/sim_data.json"
    FISH = WS / "exploratory/amp_collection/fish_species.json"

PARTITIONS = {"consensus": 0, "RDKit descriptors": 1, "package (m6)": 2}
AMP_PARS = ("p_Am", "v", "kap", "p_M", "E_G", "T_A", "k_J", "kap_R", "E_Hp", "kap_X", "kap_P", "s_M", "Ww_p")
AMP_CHEM = ("d_V", "d_E", "mu_X", "mu_V", "mu_E", "mu_P")


@lru_cache(maxsize=1)
def sim() -> dict:
    return json.loads(SIM.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def fish_entries() -> dict:
    return json.loads(FISH.read_text(encoding="utf-8"))


def temperatures() -> list[float]:
    return list(sim()["temps"])


def chemical_rows() -> list[dict]:
    return sim()["chemicals"]


def chemical_label(c: dict) -> str:
    return c.get("nm") or f"{c['f']} {c.get('h', '')}".strip()


def find_chemicals(query: str, limit: int = 60) -> list[int]:
    """Indices into chemical_rows() whose name, CAS or family contains the query."""
    q = (query or "").strip().lower()
    rows = chemical_rows()
    if not q:
        return list(range(min(limit, len(rows))))
    out = []
    for i, c in enumerate(rows):
        hay = f"{chemical_label(c)} {c.get('cas', '')} {c['f']} {c.get('h', '')}".lower()
        if q in hay:
            out.append(i)
            if len(out) >= limit:
                break
    return out


def chemical_at(i: int, T_C: float, partition: str = "consensus") -> M.Chemical:
    """One structure at one of the three tabulated temperatures."""
    c = chemical_rows()[i]
    ti = temperatures().index(T_C)
    pi = PARTITIONS[partition]
    return M.Chemical(logKow=c["k"], logPintr=c["p"][ti], logD=c["dd"][ti],
                      logPWd=c["wd"][pi], logPBd=c["bd"][pi],
                      log_kmN_qsar=c.get("q"), name=chemical_label(c))


def measured_bcf(i: int):
    """[median, min, max, n] of the measured whole-body BCF, or None."""
    return chemical_rows()[i].get("mb")


def gill_sets() -> dict:
    return sim()["sigma_h_sets"]


def species_names() -> list[str]:
    return sorted(fish_entries())


def species_label(key: str) -> str:
    e = fish_entries()[key]
    return e.get("en") or key.replace("_", " ")


def find_species(query: str, limit: int = 60) -> list[str]:
    q = (query or "").strip().lower()
    ent = fish_entries()
    if not q:
        return []
    out = []
    for k, e in ent.items():
        if (q in species_label(k).lower() or q in k.replace("_", " ").lower()
                or q in e["fam"].lower() or q in e["ord"].lower()):
            out.append(k)
            if len(out) >= limit:
                break
    return sorted(out)


def make_fish(key: str, W_g: float, T_C: float, f: float = 1.0, gill: str = "AmP E_O=0.8",
              l_pin: float | None = None) -> M.Fish:
    """An animal from its AmP entry and one of the fitted gill-geometry sets."""
    e = fish_entries()[key]
    par = {k: e[k] for k in AMP_PARS}
    par.update({k: e[k] for k in AMP_CHEM if k in e})
    s = gill_sets()[gill]
    return M.Fish(par=par, del_M=e.get("dm") or 0.10543, W_g=W_g, T_C=T_C, f=f,
                  sigma=s["sigma"], h_um=s["h"], E_O=s.get("E_O", 0.80),
                  name=species_label(key), l_pin=l_pin)


def entry_note(key: str) -> dict:
    """What the page should say about where this animal's numbers come from."""
    e = fish_entries()[key]
    return {"latin": key.replace("_", " "), "family": e["fam"], "order": e["ord"],
            "completeness": e["cmp"], "mre": e["mre"], "T_typ": e["T_typ"],
            "Ww_p": e["Ww_p"], "Ww_i": e["Ww_i"], "del_M": e.get("dm"),
            "flux_check_ultimate": e["chk"][1], "flux_check_puberty": e["chk"][0],
            "url": f"https://www.bio.vu.nl/thb/deb/deblab/add_my_pet/entries_web/{key}/{key}_res.html"}


RECORDED_FISH = {       # the three the frozen run covers, with the settings it used
    "Oncorhynchus_mykiss": dict(label="rainbow trout (original scan)", W_g=10.0, T_C=15.0, l_pin=0.25),
    "Poecilia_reticulata": dict(label="guppy (original scan)", W_g=0.1, T_C=22.0, l_pin=0.406),
    "Pimephales_promelas": dict(label="fathead minnow (original scan)", W_g=0.4, T_C=25.0, l_pin=None),
}


@lru_cache(maxsize=8)
def library(T_C: float, partition: str = "consensus") -> dict:
    """Every structure at one temperature, as arrays: what the sweep panels and the limiting-step map run on.

    Keys: logKow, logPintr, logD, logPWd, logPBd, log_kmN (QSAR, NaN where absent), halogens, family,
    name, measured (median log BCF or NaN), measured_lo, measured_hi, measured_n.
    """
    import numpy as np
    rows = chemical_rows()
    ti = temperatures().index(T_C)
    pi = PARTITIONS[partition]
    out = {k: [] for k in ("logKow", "logPintr", "logD", "logPWd", "logPBd", "log_kmN", "halogens",
                           "family", "name", "measured", "measured_lo", "measured_hi", "measured_n")}
    for c in rows:
        out["logKow"].append(c["k"])
        out["logPintr"].append(c["p"][ti])
        out["logD"].append(c["dd"][ti])
        out["logPWd"].append(c["wd"][pi])
        out["logPBd"].append(c["bd"][pi])
        q = c.get("q")
        out["log_kmN"].append(float("nan") if q is None else q)
        out["halogens"].append(c.get("nh", 0))
        out["family"].append(c["f"])
        out["name"].append(chemical_label(c))
        mb = c.get("mb")
        out["measured"].append(mb[0] if mb else float("nan"))
        out["measured_lo"].append(mb[1] if mb else float("nan"))
        out["measured_hi"].append(mb[2] if mb else float("nan"))
        out["measured_n"].append(mb[3] if mb else 0)
    for k in ("logKow", "logPintr", "logD", "logPWd", "logPBd", "log_kmN",
              "measured", "measured_lo", "measured_hi"):
        out[k] = np.asarray(out[k], float)
    out["halogens"] = np.asarray(out["halogens"], int)
    out["measured_n"] = np.asarray(out["measured_n"], int)
    for k in ("family", "name"):
        out[k] = np.asarray(out[k], object)
    return out


def record() -> dict:
    """What the frozen run recorded about itself: the validated log Kow window and the reference points."""
    return sim().get("record", {})


# ---------------------------------------------------------------------------- a chemical outside the library
def custom_estimators() -> dict:
    """The estimators fitted on the 866 library structures (exploratory/pops_scan/
    fit_custom_chemical_estimators.py): molar volume from molar mass, aqueous diffusivity from that volume,
    and membrane permeability from volume and halogen count. Each carries its own error."""
    return sim()["custom"]


def chemical_from_properties(logKow: float, MW: float, n_halogen: int, T_C: float,
                             name: str = "entered by hand", log_kmN=None) -> M.Chemical:
    """What the model needs, from the three numbers a lookup can supply.

    Partitioning falls back to the three K_OW-based forms rather than the ppLFER consensus the library rows
    carry, because a ppLFER needs Abraham descriptors and a structure. A library chemical and a hand-built
    copy of it will therefore not match exactly.
    """
    import numpy as np
    est = custom_estimators()
    key = f"{T_C:g}"
    logVA = est["VA"]["a"] + est["VA"]["b"] * np.log10(MW)
    logD = est["D"][key]["a"] - 0.6 * logVA
    P = est["Pintr"][key]
    logPintr = P["a"] + P["b"] * logVA + P["c"] * n_halogen
    K = 10.0 ** logKow
    wb = {"alb": 0.003, "nap": 0.158, "sl": 0.045, "ml": 0.005, "water": 0.789}
    bl = {"alb": 0.007, "nap": 0.089, "sl": 0.008, "ml": 0.006, "water": 0.890}

    def comp(c):
        return float(np.log10((c["sl"] + c["ml"]) * K + 0.05 * (c["alb"] + c["nap"]) * K + c["water"]))

    logPWd = float(np.median([comp(wb), logKow + np.log10(0.07), logKow - 1.32]))
    logPBd = float(np.median([comp(bl), np.log10(10.0 ** (0.73 * logKow) * 0.16 + 0.84)]))
    return M.Chemical(logKow=logKow, logPintr=float(logPintr), logD=float(logD),
                      logPWd=logPWd, logPBd=logPBd, log_kmN_qsar=log_kmN, name=name)


def estimator_errors() -> dict:
    """What to tell the reader about those estimates."""
    est = custom_estimators()
    return {"VA_rmse_log": est["VA"].get("rmse_log"), "VA_r2": est["VA"].get("r2"),
            "Pintr_rmse": est["Pintr"][f"{temperatures()[0]:g}"].get("rmse_log")}


# ---------------------------------------------------------------------------- does this still match the run?
@lru_cache(maxsize=1)
def self_check() -> dict:
    """Recompute the run's own recorded reference points and report the worst disagreement.

    These are the points sim_data.json carries from runs/ieam-p8-popscan: 24 fish-chemical pairs with the k_1
    and BCF the run recorded, at the settings the run used. The same comparison over the whole 2,598-row table
    is tests/test_model_against_run.py; this one is cheap enough to run on every page load.
    """
    import numpy as np
    refs = record().get("refs", [])
    latin = {v["label"].split(" (")[0]: k for k, v in RECORDED_FISH.items()}
    name_to_key = {"rainbow trout": "Oncorhynchus_mykiss", "guppy": "Poecilia_reticulata",
                   "fathead minnow": "Pimephales_promelas"}
    worst, n = 0.0, 0
    for ref in refs:
        key = name_to_key.get(ref["fish"]) or latin.get(ref["fish"])
        if key is None:
            continue
        spec = RECORDED_FISH[key]
        f = make_fish(key, spec["W_g"], spec["T_C"], 1.0, "AmP E_O=0.8", l_pin=spec["l_pin"])
        c = chemical_at(ref["i"], spec["T_C"], "consensus")
        r = M.rates(f, c, "zero")
        worst = max(worst, abs(np.log10(r["k1"]) - ref["k1"]),
                    abs(np.log10(M.bcf(f, c, "zero")) - ref["bcf"]))
        n += 1
    return {"worst": float(worst), "n": n, "run": record().get("run", "")}
