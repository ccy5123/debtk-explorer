"""The bioaccumulation model, as the frozen run computes it, with growth left free in time.

Every equation here is lifted from runs/ieam-p8-popscan/artifacts/popscan_official.py, which is the run's
own frozen code and must not be imported (it executes a whole scan and is Evidence-bearing). The tie back to
it is tests/test_model_against_run.py, which re-computes the run's per-chemical table from this module and
requires it to match. If that test fails, this module is wrong, not the run.

What is here that the frozen run does not have: the run evaluates one fish of one fixed size, while the
companion framework (Lee & Joe, ChemRxiv 10.26434/chemrxiv.15002330/v1, eq 7) is written for a growing
organism. `simulate` integrates the concentration and the body size together, so k_e,r, k_1 and the growth
dilution all move as the animal grows.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

T_REF = 293.15

# ---------------------------------------------------------------------------- DEB chemistry (addchem)
DENS = 0.2
MU_X, MU_V, MU_E, MU_P = 525000.0, 500000.0, 550000.0, 480000.0
N_O = np.array([[1, 1, 1, 1], [1.8] * 4, [0.5] * 4, [0.15] * 4])          # C,H,O,N x X,V,E,P
N_M = np.array([[1, 0, 0, 0], [0, 2, 0, 3], [2, 1, 2, 0], [0, 0, 0, 1]])  # CO2,H2O,O2,NH3
W_O = N_O.T @ np.array([12.0, 1.0, 16.0, 14.0])
W_V, W_E = W_O[1], W_O[2]


def c_T(p: dict, T_C: float) -> float:
    """Arrhenius correction to the entry's reference temperature."""
    return float(np.exp(p["T_A"] / T_REF - p["T_A"] / (T_C + 273.15)))


def derived(p: dict):
    """[E_m], omega, L_m and eta_O. The densities and the chemical potentials come from the entry when it
    carries its own (some fish are d_V = d_E = 0.3) and are the addchem defaults otherwise."""
    d_V, d_E = p.get("d_V", DENS), p.get("d_E", DENS)
    mu_X, mu_E, mu_P = p.get("mu_X", MU_X), p.get("mu_E", MU_E), p.get("mu_P", MU_P)
    E_m = p["p_Am"] / p["v"]
    ome = E_m * W_E / (mu_E * d_E)
    L_m = p["kap"] * p["p_Am"] / p["p_M"]
    y_V_E = mu_E * (d_V / W_V) / p["E_G"]
    y_E_X = p["kap_X"] * mu_X / mu_E
    y_P_E = (p["kap_P"] * mu_X / mu_P) / y_E_X
    eta_O = np.array([[-(1 / y_E_X) / mu_E, 0, 0],
                      [0, 0, y_V_E / mu_E],
                      [1 / mu_E, -1 / mu_E, -1 / mu_E],
                      [y_P_E / mu_E, 0, 0]])
    return E_m, ome, L_m, eta_O


def J_O(p: dict, W_g: float, T_C: float, f: float = 1.0, stage: str | None = None) -> float:
    """mol O2 / d. Juvenile and adult differ in how maturity is dissipated; by default the weight decides."""
    E_m, ome, _, eta_O = derived(p)
    L = (W_g / (1 + f * ome)) ** (1 / 3)
    cT, s = c_T(p, T_C), p["s_M"]
    E = f * E_m
    p_A = cT * p["p_Am"] * s * f * L ** 2
    p_S = cT * p["p_M"] * L ** 3
    p_C = E * L ** 3 * (p["E_G"] * cT * p["v"] * s / L + p["p_M"] * cT) / (p["kap"] * E + p["E_G"])
    p_G = p["kap"] * p_C - p_S
    adult = (W_g >= p["Ww_p"]) if stage is None else (stage == "adult")
    if adult:
        p_J = cT * p["k_J"] * p["E_Hp"]
        p_R = (1 - p["kap"]) * p_C - p_J
        p_D = p_S + p_J + (1 - p["kap_R"]) * p_R
    else:
        p_D = p_S + (1 - p["kap"]) * p_C
    J_M = -np.linalg.solve(N_M, N_O) @ eta_O @ np.array([p_A, p_D, p_G])
    return float(-J_M[2])


def deb_r_B(p: dict, T_C: float, f: float = 1.0):
    """von Bertalanffy rate and L_m: k_M = p_M/E_G, g = v/(k_M L_m), r_B = k_M g / [3(f+g)], Arrhenius."""
    L_m = p["kap"] * p["p_Am"] / p["p_M"]
    k_M = p["p_M"] / p["E_G"]
    g = p["v"] / (k_M * L_m)
    return k_M * g / (3.0 * (f + g)) * c_T(p, T_C), L_m


def scaled_length(p: dict, del_M: float, W_g: float) -> float:
    """l = del_M L_w / L_m with the physical length from Fulton's condition factor K = 1."""
    L_m = p["kap"] * p["p_Am"] / p["p_M"]
    return del_M * (100.0 * W_g) ** (1.0 / 3.0) / L_m


def weight_from_l(p: dict, del_M: float, l: float) -> float:
    """The inverse of scaled_length, so an integration in l can report a weight."""
    L_m = p["kap"] * p["p_Am"] / p["p_M"]
    return (l * L_m / del_M) ** 3 / 100.0


def C_OX(T_C: float) -> float:
    """Oxygen solubility in the ventilated water, mg/L."""
    return -0.24 * T_C + 14.04


def k_r_of(p: dict, W_g: float, T_C: float, f: float = 1.0, E_O: float = 0.80) -> float:
    """Ventilation, L/d, from the DEB oxygen demand and the extraction efficiency."""
    return J_O(p, W_g, T_C, f=f) * 32000.0 / (E_O * C_OX(T_C))


def k_b_of(W_g: float, T_C: float) -> float:
    """Gill blood flow, L/d (Barron: 0.23 T - 0.78 L/kg/h)."""
    return 24.0 * (W_g / 1000.0) * (0.23 * T_C - 0.78)


def em_ew(Pintr, D, PBd, sigma, h_um, W_kg, k_r, k_b):
    """Erickson-McKim countercurrent gill extraction."""
    P_app = 1.0 / (1.0 / Pintr + h_um * 1e-4 / D)
    beta = P_app * sigma * W_kg ** (2.0 / 3.0) * 86.4 / k_r
    r = k_r / (k_b * PBd)
    lam = beta * (r - 1.0)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        EW = np.where(np.isclose(r, 1.0, atol=1e-6), beta / (1.0 + beta),
                      (1.0 - np.exp(-lam)) / (r - np.exp(-lam)))
    return np.clip(EW, 1e-12, 0.999999)


LIMIT_NAMES = ("membrane", "boundary layer", "ventilation", "perfusion")


@dataclass
class Fish:
    """One animal: an AmP entry, a weight, a temperature, a food level, and the gill geometry."""
    par: dict                      # the AmP entry's primary parameters
    del_M: float
    W_g: float
    T_C: float
    f: float = 1.0
    sigma: float = 28761.0         # gill area coefficient, cm2/kg^(2/3)
    h_um: float = 1153.0           # diffusion path
    E_O: float = 0.80              # oxygen extraction efficiency
    name: str = ""
    l_pin: float | None = None     # the run pins l for two of its fish rather than deriving it
    k_b_pin: float | None = None   # blood flow set by hand instead of Barron's allometry

    def l(self) -> float:
        return self.l_pin if self.l_pin is not None else scaled_length(self.par, self.del_M, self.W_g)

    def r_B(self) -> float:
        return deb_r_B(self.par, self.T_C, self.f)[0]

    def accelerated(self) -> bool:
        return self.l() > 1.0

    def k_r(self) -> float:
        return k_r_of(self.par, self.W_g, self.T_C, self.f, self.E_O)

    def k_b(self) -> float:
        return self.k_b_pin if self.k_b_pin is not None else k_b_of(self.W_g, self.T_C)

    def growth_dilution(self) -> float:
        """3 r_B (f - l) / l, per day; the acceleration factor applies to f where l > 1."""
        l = self.l()
        f_eff = self.f * self.par["s_M"] if l > 1.0 else self.f
        return 3.0 * self.r_B() * (f_eff - l) / l

    def at_weight(self, W_g: float) -> "Fish":
        """The same animal at another weight. A pinned l does not survive: it described one size."""
        return Fish(self.par, self.del_M, W_g, self.T_C, self.f, self.sigma, self.h_um, self.E_O, self.name,
                    k_b_pin=self.k_b_pin)

    def at_length(self, l: float) -> "Fish":
        f2 = self.at_weight(weight_from_l(self.par, self.del_M, l))
        f2.l_pin = l
        return f2


@dataclass
class Chemical:
    """One structure, at the temperature the fish sits at."""
    logKow: float
    logPintr: float                # PerMM membrane permeability, log cm/s
    logD: float                    # aqueous diffusivity, log cm2/s
    logPWd: float                  # whole-body - water partition
    logPBd: float                  # blood - water partition
    log_kmN_qsar: float | None = None
    name: str = ""


def rates(fish: Fish, chem: Chemical, kBt: str = "zero", ker_route: str = "mechanistic",
          plateau: float | None = None) -> dict:
    """k_1, k_e,r, k_Bt, growth dilution and the step that limits uptake, all per day."""
    W_kg = fish.W_g / 1000.0
    k_r, k_b = fish.k_r(), fish.k_b()
    Pintr, D, PBd, PWd = 10 ** chem.logPintr, 10 ** chem.logD, 10 ** chem.logPBd, 10 ** chem.logPWd
    EW = float(em_ew(Pintr, D, PBd, fish.sigma, fish.h_um, W_kg, k_r, k_b))
    k1 = EW * k_r / W_kg
    S_r = fish.sigma * W_kg ** (2.0 / 3.0)
    limits = {"membrane": Pintr * S_r * 86.4 / W_kg,
              "boundary layer": (D / (fish.h_um * 1e-4)) * S_r * 86.4 / W_kg,
              "ventilation": k_r / W_kg,
              "perfusion": k_b * PBd / W_kg}
    # the run offers two routes to respiratory elimination: the gill model's own k_1, or a measured plateau
    k_er = (k1 if ker_route == "mechanistic" or not plateau else plateau) / PWd
    if kBt == "qsar" and chem.log_kmN_qsar is not None:
        k_Bt = 10 ** chem.log_kmN_qsar * (fish.W_g / 10.0) ** -0.25 * np.exp(0.06 * (fish.T_C - 15.0))
    else:
        k_Bt = 0.0
    k_g = fish.growth_dilution()
    k2 = k_er + k_Bt + k_g
    return {"E_W": EW, "k1": k1, "k_er": k_er, "k_Bt": float(k_Bt), "k_g": k_g, "k2": k2,
            "BCF": k1 / k2 if k2 > 0 else np.inf, "PWd": PWd, "k_r": k_r, "k_b": k_b,
            "limiting": min(limits, key=limits.get), "limits": limits}


def bcf(fish: Fish, chem: Chemical, kBt: str = "zero", ker_route: str = "mechanistic",
        plateau: float | None = None) -> float:
    """Equation 1 / companion eq 8, written as the frozen run writes it."""
    r = rates(fish, chem, kBt, ker_route, plateau)
    return 10 ** chem.logPWd / (1.0 + r["k_Bt"] / r["k_er"] + r["k_g"] / r["k_er"])


# ---------------------------------------------------------------------------- dietary pathway
# The DEB-TK framework writes the food-exposed burden as (companion eq 9, growing animal, k_1 c_d dropped):
#   dC/dt = alpha_f * G_D * c_X - (k_e,r + k_Bt + k_g) * C                                        (per day)
# where G_D is the specific ingestion rate (g food wet / g fish wet / d), set by the DEB primary p_Xm. The
# steady state is BMF = C/c_X = alpha_f * G_D / (k_e,r + k_Bt + k_g).
#
# alpha_f is the whole-gut assimilation efficiency for the chemical. The dietary arc on this project
# (ieam-p8-alphaf, 2026-10-22) records the plug-flow mechanistic bound and the measured central value and
# their gap: the measurement is a factor of two below the bound, and the bound fails outright at seven
# heptachlorobiphenyls. The app does not try to resolve the gap - it reports the central value with the
# lab-reproducibility interval, the bracket, and the heptachlorination domain limit, so the reader sees the
# discrepancy rather than one number alone.
ALPHA_F_CENTRAL = 0.55
ALPHA_F_LOW, ALPHA_F_HIGH = 0.30, 0.80           # bracket, central case for persistent neutral chemicals
ALPHA_F_LOG10_SD = 0.12                          # lab reproducibility floor (dietary arc 2026-10-22)
HEPTA_HALOGENS = 7                               # the plug-flow bound fails at and beyond this many halogens

# The chemical potential of food and the per-C-mol dry mass that convert p_Xm to a wet mass flux. d_X is the
# addchem default food dry-mass fraction; the AmP primaries use d_V for the organism and d_X falls on the
# same value in the published addchem.
D_X_DEFAULT = 0.2
W_X_MOL_DEFAULT = float(W_O[0])                  # 23.9 g dry food per C-mol with the addchem n_O defaults


def ingestion(fish: "Fish") -> dict:
    """DEB ingestion at the animal's current size, food level and temperature.

        p_X    = c_T * f * p_Xm * s_M_eff * L^2      (J / d)
        J_X    = p_X / mu_X                           (mol-C / d)
        G_dry  = J_X * W_X_mol                        (g dry food / d)
        G_wet  = G_dry / d_X                          (g wet food / d)
        G_D    = G_wet / W_g                          (g wet food / g fish wet / d)

    s_M_eff = s_M where l > 1 (metabolic acceleration applies to p_Xm the same way it does to p_Am), and 1
    otherwise. The addchem defaults for mu_X, W_X_mol and d_X are used unless the entry carries its own.
    """
    p = fish.par
    p_Xm = p.get("p_Xm")
    if p_Xm is None:                               # back out from the primaries when the field is absent
        p_Xm = p["p_Am"] / p["kap_X"]
    mu_X = p.get("mu_X", MU_X)
    d_X = p.get("d_X", D_X_DEFAULT)
    L = (fish.W_g / (1.0 + fish.f * derived(p)[1])) ** (1.0 / 3.0)
    l = fish.l()
    s_eff = p["s_M"] if l > 1.0 else 1.0
    p_X = c_T(p, fish.T_C) * fish.f * p_Xm * s_eff * L ** 2
    J_X = p_X / mu_X
    G_dry = J_X * W_X_MOL_DEFAULT
    G_wet = G_dry / d_X
    G_D = G_wet / fish.W_g
    return {"p_X": float(p_X), "J_X": float(J_X), "G_dry": float(G_dry),
            "G_wet": float(G_wet), "G_D": float(G_D), "L": float(L), "s_M_eff": float(s_eff)}


def diet_rates(fish: "Fish", chem: Chemical, alpha_f: float = ALPHA_F_CENTRAL,
               kBt: str = "zero", ker_route: str = "mechanistic",
               plateau: float | None = None) -> dict:
    """Food-only steady state and the loss terms it sits against.

    Water is set to zero; the respiratory elimination term k_e,r still runs as the gill model's own, because
    an animal eating chemical in clean water still loses it back out of the gill. This is the companion's
    eq 9 at steady state with c_d = 0.
    """
    gill = rates(fish, chem, kBt, ker_route, plateau)
    gD = ingestion(fish)["G_D"]
    k2 = gill["k_er"] + gill["k_Bt"] + gill["k_g"]
    BMF = alpha_f * gD / k2 if k2 > 0 else float("inf")
    return {"alpha_f": float(alpha_f), "G_D": float(gD),
            "k_er": gill["k_er"], "k_Bt": gill["k_Bt"], "k_g": gill["k_g"], "k2": float(k2),
            "BMF": float(BMF), "limiting": gill["limiting"]}


def alpha_f_interval(alpha_f: float = ALPHA_F_CENTRAL,
                     log10_sd: float = ALPHA_F_LOG10_SD) -> tuple[float, float]:
    """One-sigma interval on alpha_f at the lab reproducibility floor, in natural units."""
    log_a = np.log10(alpha_f)
    return float(10 ** (log_a - log10_sd)), float(10 ** (log_a + log10_sd))


def in_hepta_domain(n_halogen: int) -> bool:
    """True while the plug-flow bound this app reports still applies. The ieam-p8-alphaf run refuted the
    bound outright for every heptachlorobiphenyl it ran, so the app withholds the number at and beyond."""
    return n_halogen < HEPTA_HALOGENS


@dataclass
class Trajectory:
    t: np.ndarray                  # d
    C: np.ndarray                  # ng/kg
    W: np.ndarray                  # g
    l: np.ndarray
    k1: np.ndarray
    k_er: np.ndarray
    k_g: np.ndarray
    BCF_inst: np.ndarray           # the steady state the animal is heading for at that instant
    meta: dict = field(default_factory=dict)


def simulate(fish: Fish, chem: Chemical, Cw: float, t_exp: float, t_max: float,
             kBt: str = "zero", n: int = 1200, grow: bool = True) -> Trajectory:
    """Integrate concentration and body size together (companion eq 7, water exposure only).

        dl/dt   = r_B (f_eff - l)                      von Bertalanffy in scaled length
        dC/dt   = k_1(W) Cw - (k_e,r(W) + k_Bt + 3 r_B (f_eff - l)/l) C

    k_1 and k_e,r are recomputed at the current weight rather than held at the starting one, so the ventilation,
    the blood flow and the gill area all follow the animal. With grow=False the size is held fixed, which is
    what the frozen run and the HTML explorer do, and what a constant-k_2 model assumes.
    """
    t = np.linspace(0.0, t_max, n)
    dt = t[1] - t[0]
    L_m = fish.par["kap"] * fish.par["p_Am"] / fish.par["p_M"]
    # a pinned l describes one size; growth starts from the weight and derives the length from it
    start = Fish(fish.par, fish.del_M, fish.W_g, fish.T_C, fish.f, fish.sigma, fish.h_um, fish.E_O, fish.name,
                 k_b_pin=fish.k_b_pin)
    pin_dropped = fish.l_pin is not None and abs(fish.l_pin - start.l()) > 1e-9
    fish = start
    l = fish.l()
    C = 0.0
    out = {k: np.empty(n) for k in ("C", "W", "l", "k1", "k_er", "k_g", "BCF_inst")}
    for i in range(n):
        here = fish.at_length(l)
        W = here.W_g
        r = rates(here, chem, kBt)
        out["C"][i], out["W"][i], out["l"][i] = C, W, l
        out["k1"][i], out["k_er"][i], out["k_g"][i] = r["k1"], r["k_er"], r["k_g"]
        out["BCF_inst"][i] = r["BCF"]
        if i == n - 1:
            break
        water = Cw if t[i] <= t_exp else 0.0
        dC = r["k1"] * water - (r["k_er"] + r["k_Bt"] + r["k_g"]) * C
        C = max(0.0, C + dC * dt)
        if grow:
            f_eff = fish.f * fish.par["s_M"] if l > 1.0 else fish.f
            l = l + fish.r_B() * (f_eff - l) * dt
            l = min(l, 0.999 * (fish.par["s_M"] if l > 1.0 else 1.0) * fish.f) if f_eff > l else l
    return Trajectory(t, out["C"], out["W"], out["l"], out["k1"], out["k_er"], out["k_g"], out["BCF_inst"],
                      meta={"L_m": L_m, "grow": grow, "kBt": kBt, "pin_dropped": pin_dropped,
                            "l0": out["l"][0], "W0": out["W"][0]})


# ---------------------------------------------------------------------------- the whole library at once
def frame(fish: Fish, logKow, logPintr, logD, logPWd, logPBd, log_kmN=None, kBt: str = "zero",
          ker_route: str = "mechanistic", plateau: float | None = None) -> dict:
    """Every structure at one fish, vectorised. The scalar path (rates/bcf) and this one are the same
    equations; test_model_against_run.py checks both against the recorded table."""
    logKow = np.asarray(logKow, float)
    Pintr, D = 10.0 ** np.asarray(logPintr, float), 10.0 ** np.asarray(logD, float)
    PWd, PBd = 10.0 ** np.asarray(logPWd, float), 10.0 ** np.asarray(logPBd, float)
    W_kg = fish.W_g / 1000.0
    k_r, k_b = fish.k_r(), fish.k_b()
    EW = em_ew(Pintr, D, PBd, fish.sigma, fish.h_um, W_kg, k_r, k_b)
    k1 = EW * k_r / W_kg
    S_r = fish.sigma * W_kg ** (2.0 / 3.0)
    limits = {"membrane": Pintr * S_r * 86.4 / W_kg,
              "boundary layer": (D / (fish.h_um * 1e-4)) * S_r * 86.4 / W_kg,
              "ventilation": np.full(logKow.shape, k_r / W_kg),
              "perfusion": k_b * PBd / W_kg}
    names = np.array(list(limits))
    limiting = names[np.argmin(np.vstack([limits[k] for k in names]), axis=0)]
    k_er = (k1 if ker_route == "mechanistic" or not plateau else np.full(k1.shape, plateau)) / PWd
    if kBt == "qsar" and log_kmN is not None:
        q = np.asarray(log_kmN, float)
        k_Bt = np.where(np.isfinite(q),
                        10.0 ** np.nan_to_num(q, nan=0.0) * (fish.W_g / 10.0) ** -0.25
                        * np.exp(0.06 * (fish.T_C - 15.0)), 0.0)
    else:
        k_Bt = np.zeros(logKow.shape)
    k_g = fish.growth_dilution()
    return {"logKow": logKow, "k1": k1, "log_k1": np.log10(k1), "k_er": k_er, "k_Bt": k_Bt, "k_g": k_g,
            "log_BCF": np.asarray(logPWd, float) - np.log10(1.0 + k_Bt / k_er + k_g / k_er),
            "log_ceiling": np.asarray(logPWd, float), "limiting": limiting, "E_W": EW, "limits": limits}


# ---------------------------------------------------------------------------- the published one-box models
def arnot_gobas(Kow, W_kg: float, T_C: float):
    """Arnot & Gobas 2004 BCF, k_Bt = 0. Ported from the run ieam-p8-debtk-benchfairhb, unchanged."""
    Kow = np.asarray(Kow, float)
    Cox = -0.24 * T_C + 14.04
    Ew = 1.0 / (1.85 + 155.0 / Kow)
    Gv = 980.0 * W_kg ** 0.65 / Cox
    k1 = Ew * Gv / W_kg
    kG = 0.0005 * W_kg ** -0.2
    eL, eN, eW = 0.92, 0.60, 0.25
    nLD, nND, nWD = 0.05, 0.20, 0.75
    Dd = (1 - eL) * nLD + (1 - eN) * nND + (1 - eW) * nWD
    nLG, nNG, nWG = (1 - eL) * nLD / Dd, (1 - eN) * nND / Dd, (1 - eW) * nWD / Dd
    GD = 0.022 * W_kg ** 0.85 * np.exp(0.06 * T_C)
    ED = 1.0 / (3e-7 * Kow + 2.0)
    BETA = 0.035
    Kbw = 0.05 * Kow + 0.20 * BETA * Kow + 0.75
    k2 = k1 / Kbw
    KGB = (nLG * Kow + nNG * BETA * Kow + nWG) / Kbw
    kE = Dd * GD * ED * KGB / W_kg
    return np.log10(k1 / (k2 + kE + kG))


def omega(Kow, W_kg: float):
    """OMEGA (Hendriks et al. 2001) BCF, k_Bt = 0. Same source."""
    Kow = np.asarray(Kow, float)
    k1 = (W_kg ** -0.25) / (2.8e-3 + 68.0 / Kow + 1.0 / 200.0)
    kG = 0.0005 * W_kg ** -0.2
    return np.log10(k1 / (k1 / (0.05 * Kow) + kG))


BIN_EDGES = np.round(np.arange(2.75, 9.26, 0.5), 2)


def binned_median(x, y, min_n: int = 3):
    """Medians of y in the recorded log Kow bins; a bin with fewer than min_n points is dropped."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    xs, ys = [], []
    for lo, hi in zip(BIN_EDGES[:-1], BIN_EDGES[1:]):
        m = (x >= lo) & (x < hi) & np.isfinite(y)
        if m.sum() >= min_n:
            xs.append((lo + hi) / 2.0)
            ys.append(float(np.median(y[m])))
    return np.array(xs), np.array(ys)
