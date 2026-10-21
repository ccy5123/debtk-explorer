"""Fish bioaccumulation explorer.

Two readings of the same model. Plain keeps the fish, the time course and where the loss goes, with the
settings a non-specialist would change. Expert adds the whole 866-structure library, the comparison against
the published one-box models and against a constant k2, what limits uptake over size and hydrophobicity, the
structure-derived inputs, the equations, and every setting.

English and Korean, chosen independently of that: a specialist may want Korean and a first-time reader may
want English. Every sentence lives in debtk/i18n.py.

The model is debtk/model.py, which reproduces the frozen run chemical by chemical
(tests/test_model_against_run.py). Nothing here re-derives an equation.

Run it:  streamlit run app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).resolve().parent))
from debtk import ctx, data as D, fish_svg, i18n, model as M, panels as PN    # noqa: E402

st.set_page_config(page_title="Fish bioaccumulation (DEB-TK)", layout="wide", page_icon="🐟")

TEAL, RUST, GREEN, SLATE = PN.TEAL, PN.RUST, PN.GREEN, PN.SLATE

st.markdown("""
<style>
  .block-container {padding-top: 2.2rem; max-width: 1500px}
  [data-testid="stMetricValue"] {font-size: 1.7rem}
  [data-testid="stMetricLabel"] p {font-size: .78rem; letter-spacing: .03em; text-transform: uppercase}
  .pill {display:inline-block;padding:3px 12px;border-radius:999px;font-size:.82rem;font-weight:600}
  .pill.warn {background:#F7E3D6;color:#C05621} .pill.ok {background:#DCEDE2;color:#2F7A52}
  .note {color:#59706C;font-size:.85rem;line-height:1.5}
  .check {display:inline-block;margin-top:6px;font-size:.72rem;letter-spacing:.02em;padding:2px 9px;
          border-radius:999px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
  .check.ok {background:#DCEDE2;color:#2F7A52} .check.bad {background:#F7E3D6;color:#B4442E}
</style>
""", unsafe_allow_html=True)

st.session_state.setdefault("pinned", [])
for _k, _v in dict(Cw=1.0, t_exp=365.0, t_max=500.0, day=60.0).items():
    st.session_state.setdefault(_k, _v)

# ============================================================ language and detail
c_lang, c_mode = st.sidebar.columns(2)
lang_name = c_lang.selectbox("🌐", list(i18n.LANGS), label_visibility="collapsed")
lang = i18n.LANGS[lang_name]


def L(key: str, **fmt) -> str:
    return i18n.t(key, lang, **fmt)


expert = c_mode.toggle(L("mode_expert"), value=True, help=L("mode_help"))
st.sidebar.divider()

EXPOSURES = {
    L("sc_chronic"): dict(Cw=1.0, t_exp=365.0, t_max=500.0),
    L("sc_spill"): dict(Cw=1000.0, t_exp=7.0, t_max=90.0),
    L("sc_pore"): dict(Cw=10.0, t_exp=60.0, t_max=150.0),
}

# ============================================================ sidebar: exposure
st.sidebar.subheader(L("exposure"))
pre = st.sidebar.selectbox(L("scenario"), list(EXPOSURES), label_visibility="collapsed")
if st.sidebar.button(L("use_scenario"), width="stretch"):
    st.session_state.update(EXPOSURES[pre])
    st.rerun()
e1, e2 = st.sidebar.columns(2)
Cw = e1.number_input(L("water_conc"), min_value=0.0, format="%.4g", key="Cw")
t_exp = e2.number_input(L("lasts"), min_value=1.0, key="t_exp")
if expert:
    t_max = st.sidebar.number_input(L("follow_for"), min_value=float(t_exp), key="t_max",
                                    help=L("follow_help"))
else:
    t_max = max(float(st.session_state.t_max), float(t_exp) * 1.3)

# ============================================================ sidebar: chemical
st.sidebar.subheader(L("chemical"))
SOURCES = [L("src_library"), L("src_ctx"), L("src_hand")]
source = SOURCES[0] if not expert else st.sidebar.radio("where", SOURCES, label_visibility="collapsed")
ci = None                 # an index into the library, or None for a chemical built from three numbers
custom_in = None          # (log K_OW, molar mass, halogen atoms, name)
custom_note = ""

if source == SOURCES[0]:
    fams = sorted({c["f"] for c in D.chemical_rows()})
    fam = st.sidebar.selectbox(L("family"), [L("all")] + fams)
    cq = st.sidebar.text_input(L("search_chem"), "hexachlorobenzene")
    hits = [i for i in D.find_chemicals(cq, limit=400)
            if fam == L("all") or D.chemical_rows()[i]["f"] == fam]
    if not hits:
        st.sidebar.warning(L("no_chem_match"))
        st.stop()

    def chem_option(i: int) -> str:
        c = D.chemical_rows()[i]
        mb = c.get("mb")
        return (f"{D.chemical_label(c)} — log Kow {c['k']:.2f}"
                + (" · " + L("measured_logbcf_short", v=mb[0]) if mb else ""))

    ci = st.sidebar.selectbox(L("one_match") if len(hits) == 1 else L("n_matches", n=len(hits)),
                              hits, format_func=chem_option)
    cas = D.chemical_rows()[ci].get("cas")
    st.sidebar.caption(f"{D.chemical_rows()[ci]['f']}{' · CAS ' + cas if cas else ''}")
    if expert:
        p1, p2 = st.sidebar.columns([3, 2])
        if p1.button(L("pin"), width="stretch") and ci not in st.session_state.pinned:
            st.session_state.pinned = (st.session_state.pinned + [ci])[-8:]
        if p2.button(L("clear"), width="stretch", disabled=not st.session_state.pinned):
            st.session_state.pinned = []

elif source == SOURCES[1]:
    key = ctx.api_key(st.session_state.get("ctx_key"))
    if not key:
        st.sidebar.text_input(L("ctx_key"), type="password", key="ctx_key", help=L("ctx_key_help"))
        key = ctx.api_key(st.session_state.get("ctx_key"))
    q = st.sidebar.text_input(L("ctx_query"), "chlordecone")
    prefer = st.sidebar.radio(L("kow_prefer"), [L("kow_measured"), L("kow_opera")])
    if not key:
        st.sidebar.warning(L("ctx_key_needed"))
        st.stop()
    try:
        found = ctx.lookup(q, key, "experimental" if prefer == L("kow_measured") else "predicted")
    except RuntimeError as exc:
        st.sidebar.error(str(exc))
        st.stop()
    if not found:
        st.sidebar.warning(L("ctx_no_match", q=q))
        st.stop()
    hit = st.sidebar.selectbox(L("ctx_entry"), found,
                               format_func=lambda h: f"{h.name} — {h.casrn or h.dtxsid}")
    _est = D.custom_estimators()
    pf = ctx.parse_formula(hit.formula, _est["masses"], _est["halogens"])
    if hit.logKow is None or not pf:
        st.sidebar.error(L("ctx_unusable"))
        st.stop()
    custom_in = (hit.logKow, pf[0], pf[1], hit.name)
    custom_note = (f"[{hit.name}]({hit.url}) · {hit.casrn or hit.dtxsid} · {hit.formula} · "
                   f"MW {pf[0]:,.1f} · {pf[1]} · log K_OW {hit.logKow:.2f} ({hit.logKow_source})"
                   + "".join(f" · {n}" for n in hit.notes))

else:
    cn = st.sidebar.text_input(L("name_it"), L("my_chemical"))
    ck = st.sidebar.number_input("log K_OW", -2.0, 12.0, 6.0, 0.05)
    cm = st.sidebar.number_input(L("molar_mass"), 30.0, 2000.0, 360.9, 0.1)
    chl = st.sidebar.number_input(L("halogens"), 0, 30, 6, 1)
    custom_in = (float(ck), float(cm), int(chl), cn)
    custom_note = L("by_hand_note", n=cn, k=ck, m=cm, h=int(chl))

# ============================================================ sidebar: fish
st.sidebar.subheader(L("fish"))
preset = st.sidebar.selectbox(L("start_from"),
                              [v["label"] for v in D.RECORDED_FISH.values()] + [L("any_amp")],
                              help=L("recorded_help"))
if preset == L("any_amp"):
    sq = st.sidebar.text_input(L("search_species", n=f"{len(D.species_names()):,}"), "Thunnus thynnus",
                               help=L("species_help"))
    found_sp = D.find_species(sq)
    if not found_sp:
        st.sidebar.warning(L("no_species"))
        st.stop()
    species = st.sidebar.selectbox(L("species"), found_sp,
                                   format_func=lambda k: f"{D.species_label(k)} — {k.replace('_', ' ')}")
    _e = D.fish_entries()[species]
    W_default = float(min(max(_e["Ww_p"], 0.05), _e["Ww_i"]))
    T_default = min(D.temperatures(), key=lambda T: abs(T - _e["T_typ"]))
else:
    species = next(k for k, v in D.RECORDED_FISH.items() if v["label"] == preset)
    W_default, T_default = D.RECORDED_FISH[species]["W_g"], D.RECORDED_FISH[species]["T_C"]

ent = D.fish_entries()[species]
note = D.entry_note(species)
st.sidebar.caption(L("fish_caption", fam=note["family"], wi=ent["Ww_i"], t=ent["T_typ"]))
W_g = st.sidebar.number_input(L("body_weight"), min_value=0.001, max_value=float(ent["Ww_i"]) * 2,
                              value=float(W_default), format="%.4g", key=f"W_{species}")
T_C = st.sidebar.select_slider(L("temperature"), options=D.temperatures(), value=T_default,
                               help=L("temp_help"))

f_food, kBt = 1.0, "zero"
gill_set, sigma, h_um, E_O, kb_pin = "AmP E_O=0.8", None, None, None, None
route_key, plateau, partition = "mechanistic", None, "consensus"
outlier_cut, halogen_free_only = 6.0, False

if expert:
    f_food = st.sidebar.slider(L("food_level"), 0.3, 1.0, 1.0, 0.05, help=L("food_help"))
    kBt = st.sidebar.radio(L("biotransformation"), ["zero", "qsar"], index=0, horizontal=True,
                           format_func=lambda s: L("none") if s == "zero" else L("qsar_estimate"))
    with st.sidebar.expander(L("advanced")):
        gill_set = st.selectbox(L("gill_set"), list(D.gill_sets()), index=1, help=L("gill_set_help"))
        gs = D.gill_sets()[gill_set]
        sigma = st.slider(L("sigma"), 5000.0, 90000.0, float(gs["sigma"]), 250.0, format="%.0f")
        log_h = st.slider(L("h_path"), -3.0, 4.0, float(np.log10(gs["h"])), 0.05, help=L("h_help"))
        h_um = 10 ** log_h
        E_O = st.slider(L("eo"), 0.30, 0.95, float(gs.get("E_O", 0.80)), 0.01)
        kb_mode = st.radio(L("kb_mode"), [L("kb_allometry"), L("kb_hand")], horizontal=True)
        if kb_mode == L("kb_hand"):
            kb_pin = 10 ** st.slider(L("kb_log"), -4.0, 3.0,
                                     float(np.log10(max(M.k_b_of(W_g, T_C), 1e-4))), 0.05)
        route = st.radio(L("ker_route"), [L("route_mech"), L("route_plateau")], horizontal=True)
        route_key = "mechanistic" if route == L("route_mech") else "empirical"
        if route_key != "mechanistic":
            plateau = st.number_input(L("plateau_input"), min_value=1.0, value=130.0, help=L("plateau_help"))
        partition = st.selectbox(L("partition"), list(D.PARTITIONS), index=0, help=L("partition_help"))
        outlier_cut = st.slider(L("outlier_cut"), 0.5, 6.0, 6.0, 0.25)
        halogen_free_only = st.checkbox(L("halogen_free"))
else:
    gs = D.gill_sets()[gill_set]
    sigma, h_um, E_O = float(gs["sigma"]), float(gs["h"]), float(gs.get("E_O", 0.80))

# ============================================================ the model
if ci is not None:
    chem = D.chemical_at(ci, T_C, partition)
else:
    chem = D.chemical_from_properties(custom_in[0], custom_in[1], custom_in[2], T_C, custom_in[3])
fish = D.make_fish(species, W_g, T_C, f_food, gill_set)
fish.sigma, fish.h_um, fish.E_O, fish.k_b_pin = sigma, h_um, E_O, kb_pin
r = M.rates(fish, chem, kBt, route_key, plateau)
BCF = M.bcf(fish, chem, kBt, route_key, plateau)
grown = M.simulate(fish, chem, Cw, t_exp, t_max, kBt, grow=True)
fixed = M.simulate(fish, chem, Cw, t_exp, t_max, kBt, grow=False)

# ============================================================ headline
verdict = (L("verdict_very"), "warn") if BCF >= 5000 else \
          (L("verdict_bio"), "warn") if BCF >= 2000 else \
          (L("verdict_below"), "ok")
left, right = st.columns([5, 2])
left.title(chem.name)
left.markdown("<span class='note'>" + L("subtitle", sp=D.species_label(species), w=W_g, t=T_C,
                                        k=chem.logKow, f=f_food) + "</span>", unsafe_allow_html=True)
sc = D.self_check()
sc_ok = sc["worst"] < 0.01
right.markdown(
    f"<div style='text-align:right;padding-top:18px'><span class='pill {verdict[1]}'>{verdict[0]}</span>"
    f"<br><span class='check {'ok' if sc_ok else 'bad'}'>"
    + L("check_ok" if sc_ok else "check_bad", run=sc["run"], w=sc["worst"], n=sc["n"])
    + "</span></div>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric(L("m_bcf"), f"{BCF:,.0f} L/kg", f"log {np.log10(BCF):.2f}", delta_color="off")
m2.metric(L("m_k1"), f"{r['k1']:,.1f} L kg⁻¹ d⁻¹",
          L("m_k1_delta", lim=L("lim_" + str(r["limiting"]))), delta_color="off")
m3.metric(L("m_t95"), f"{np.log(20) / r['k2']:,.0f} d", L("m_t95_delta", v=np.log(2) / r["k2"]),
          delta_color="off")
mb = D.measured_bcf(ci) if ci is not None else None
m4.metric(L("m_measured"), f"{mb[0]:.2f}" if mb else "—",
          (L("m_measured_delta", v=np.log10(BCF), n=mb[3]) if mb else L("m_measured_none")),
          delta_color="off")

if custom_note:
    st.info(custom_note + "  \n\n" + L("ctx_note_tail"))
st.caption(L("loss_caption", ker=r["k_er"], kg=r["k_g"],
             bt=L("loss_bt", v=r["k_Bt"]) if r["k_Bt"] else "",
             share=L("loss_share", p=100 * r["k_g"] / r["k2"]) if r["k2"] else "",
             meas=L("loss_meas", lo=mb[1], hi=mb[2]) if mb else ""))

# ============================================================ tabs
if expert:
    tabs = st.tabs([L("tab_fish"), L("tab_time"), L("tab_loss"), L("tab_library"), L("tab_bench"),
                    L("tab_compare", n=len(st.session_state.pinned)), L("tab_batch"), L("tab_model")])
else:
    tabs = st.tabs([L("tab_fish"), L("tab_time"), L("tab_loss")])
    st.caption(L("plain_more"))

# ---------------------------------------------------------------- 1. the fish
with tabs[0]:
    if not expert:
        st.markdown(L("plain_intro"))
    cc1, cc2 = st.columns([5, 1])
    if "next_day" in st.session_state:          # set by Play on the previous run
        st.session_state.day = st.session_state.pop("next_day")
    st.session_state.day = float(min(st.session_state.day, t_max))
    day = cc1.slider(L("day_slider"), 0.0, float(t_max), step=1.0, format="%d", key="day",
                     help=L("day_help"))
    playing = cc2.toggle(L("play"), help=L("play_help"))
    i = min(max(int(np.searchsorted(grown.t, day)), 0), len(grown.t) - 1)
    r_now = M.rates(fish.at_length(float(grown.l[i])), chem, kBt, route_key, plateau)
    exposure = day <= t_exp
    svg = fish_svg.render(C_fish=float(grown.C[i]), C_water=Cw if exposure else 0.0, day=float(day),
                          exposure=exposure, rates=r_now, del_M=ent.get("dm"),
                          species_label=D.species_label(species), steady=float(grown.BCF_inst[i]) * Cw,
                          lang=lang)
    # st.markdown and st.html both strip the SVG shapes; a component frame does not
    components.html(f'<div style="width:100%;max-width:1000px;margin:0 auto">{svg}</div>', height=410)
    lg1, lg2 = st.columns([1, 3])
    with lg1:
        components.html(fish_svg.ramp_legend(300, 42), height=52)
    lg2.caption(L("fish_caption_long"))
    g1, g2, g3 = st.columns(3)
    g1.metric(L("weight_now"), f"{grown.W[i]:,.3g} g", L("weight_from", w=grown.W[0]), delta_color="off")
    g2.metric(L("in_fish_now"), f"{grown.C[i]:,.0f} ng/kg", delta_color="off")
    g3.metric(L("heading_for"), f"{grown.BCF_inst[i] * Cw:,.0f} ng/kg",
              L("was_on_day0", v=grown.BCF_inst[0] * Cw), delta_color="off")
    if not expert:
        tot = r["k_er"] + r["k_g"] + r["k_Bt"]
        st.markdown(L("plain_reading", bcf=BCF, verdict=verdict[0],
                      pct=100 * grown.C[i] / max(grown.BCF_inst[i] * Cw, 1e-30),
                      t95=np.log(20) / r["k2"], lossshare=100 * r["k_er"] / tot if tot else 0,
                      met=L("plain_met", p=100 * r["k_Bt"] / tot) if r["k_Bt"] else ""))
    if playing and day < t_max:
        import time
        time.sleep(0.12)
        st.session_state.next_day = min(t_max, day + max(1.0, t_max / 120))
        st.rerun()

# ---------------------------------------------------------------- 2. time course
with tabs[1]:
    st.markdown(L("time_intro"))
    if grown.meta["pin_dropped"]:
        st.info(L("pin_dropped", l=grown.meta["l0"]))
    df = pd.concat([pd.DataFrame({"d": grown.t, "y": grown.C, "case": L("case_grows")}),
                    pd.DataFrame({"d": fixed.t, "y": fixed.C, "case": L("case_fixed")})], ignore_index=True)
    st.altair_chart(alt.Chart(df).mark_line(size=2).encode(
        x=alt.X("d:Q", title=L("day")), y=alt.Y("y:Q", title=L("y_conc")),
        color=alt.Color("case:N", title=None, scale=alt.Scale(
            domain=[L("case_grows"), L("case_fixed")], range=[TEAL, RUST])),
        tooltip=["d:Q", "y:Q", "case:N"]).properties(height=330).interactive(), width="stretch")
    at_end = min(int(np.searchsorted(grown.t, t_exp)), len(grown.t) - 1)
    c1, c2, c3 = st.columns(3)
    c1.metric(L("w_at_end"), f"{grown.W[at_end]:,.3g} g", L("weight_from", w=grown.W[0]), delta_color="off")
    c2.metric(L("burden_at_end"), f"{grown.C[at_end]:,.0f} ng/kg",
              (L("vs_fixed", p=100 * (grown.C[at_end] / fixed.C[at_end] - 1)) if fixed.C[at_end] > 0 else ""),
              delta_color="off")
    c3.metric(L("steady_heading"), f"{grown.BCF_inst[at_end] * Cw:,.0f} ng/kg",
              L("was_on_day0", v=grown.BCF_inst[0] * Cw), delta_color="off")
    st.markdown(L("what_moves"))
    mv = pd.DataFrame({L("day"): grown.t, L("q_ker"): grown.k_er, L("q_growth"): grown.k_g,
                       L("q_l"): grown.l}).melt(L("day"), var_name="q", value_name="v")
    st.altair_chart(alt.Chart(mv).mark_line(size=2).encode(
        x=alt.X(f"{L('day')}:Q"), y=alt.Y("v:Q", scale=alt.Scale(type="log"), title=None),
        color=alt.Color("q:N", title=None, scale=alt.Scale(range=[TEAL, GREEN, SLATE])),
        tooltip=[f"{L('day')}:Q", "q:N", "v:Q"]).properties(height=250).interactive(), width="stretch")

# ---------------------------------------------------------------- 3. where the loss goes
with tabs[2]:
    st.markdown(L("loss_intro"))
    routes = [L("route_gill"), L("route_growth"), L("route_met")]
    loss = pd.concat([
        pd.DataFrame({"d": grown.t, "flux": grown.k_er * grown.C, "route": routes[0]}),
        pd.DataFrame({"d": grown.t, "flux": grown.k_g * grown.C, "route": routes[1]}),
        pd.DataFrame({"d": grown.t, "flux": r["k_Bt"] * grown.C, "route": routes[2]})], ignore_index=True)
    st.altair_chart(alt.Chart(loss).mark_area().encode(
        x=alt.X("d:Q", title=L("day")), y=alt.Y("flux:Q", stack="zero", title=L("y_loss")),
        color=alt.Color("route:N", title=None,
                        scale=alt.Scale(domain=routes, range=[SLATE, GREEN, RUST])),
        tooltip=["d:Q", "route:N", "flux:Q"]).properties(height=320).interactive(), width="stretch")
    share = pd.DataFrame({"route": routes, "share": [r["k_er"], r["k_g"], r["k_Bt"]]})
    share["share"] = share["share"] / share["share"].sum()
    st.altair_chart(alt.Chart(share[share.share > 0]).mark_bar().encode(
        x=alt.X("share:Q", title=L("share_axis"), axis=alt.Axis(format="%")),
        y=alt.Y("route:N", sort="-x", title=None),
        color=alt.Color("route:N", legend=None, scale=alt.Scale(domain=routes, range=[SLATE, GREEN, RUST])),
        tooltip=[alt.Tooltip("share:Q", format=".1%")]).properties(height=140), width="stretch")

if not expert:
    st.stop()

# ---------------------------------------------------------------- the library, for three expert tabs
lib = D.library(T_C, partition)
fr = M.frame(fish, lib["logKow"], lib["logPintr"], lib["logD"], lib["logPWd"], lib["logPBd"],
             lib["log_kmN"], kBt, route_key, plateau)
keep = np.ones(len(lib["logKow"]), bool)
if halogen_free_only:
    keep &= lib["halogens"] == 0
keep &= np.abs(fr["log_k1"] - np.nanmedian(fr["log_k1"])) <= outlier_cut
rec = D.record()
kow_window = (rec.get("kow_lo"), rec.get("kow_hi")) if rec.get("kow_lo") else None

# ---------------------------------------------------------------- 4. across the library
with tabs[3]:
    segs = [L("seg_k1"), L("seg_ker"), L("seg_bcf"), L("seg_inputs")]
    what = st.segmented_control(L("show"), segs, default=segs[0])
    st.caption(L("lib_caption", n=int(keep.sum()), tot=len(keep))
               + (L("lib_halogen") if halogen_free_only else "")
               + (L("lib_outlier", c=outlier_cut) if outlier_cut < 6 else "")
               + (L("lib_window", lo=kow_window[0], hi=kow_window[1]) if kow_window else ""))
    if what == segs[0]:
        st.altair_chart(PN.scatter_vs_kow(lib["logKow"][keep], fr["log_k1"][keep], fr["limiting"][keep],
                                          lib["name"][keep], L("y_logk1"), kow_window,
                                          (chem.logKow, float(np.log10(r["k1"])), chem.name)), width="stretch")
    elif what == segs[1]:
        st.altair_chart(PN.scatter_vs_kow(lib["logKow"][keep], np.log10(fr["k_er"][keep]),
                                          fr["limiting"][keep], lib["name"][keep], L("y_logker"), kow_window,
                                          (chem.logKow, float(np.log10(r["k_er"])), chem.name)),
                        width="stretch")
    elif what == segs[2]:
        st.altair_chart(PN.scatter_vs_kow(lib["logKow"][keep], fr["log_BCF"][keep], fr["limiting"][keep],
                                          lib["name"][keep], L("y_logbcf"), kow_window,
                                          (chem.logKow, float(np.log10(BCF)), chem.name)), width="stretch")
    else:
        st.altair_chart(PN.inputs_2x2(lib["logKow"][keep], {
            L("in_pintr"): lib["logPintr"][keep], L("in_d"): lib["logD"][keep],
            L("in_pwd"): lib["logPWd"][keep], L("in_pbd"): lib["logPBd"][keep]},
            lib["halogens"][keep]), width="stretch")
        st.caption(L("inputs_caption"))

# ---------------------------------------------------------------- 5. benchmarks and limits
with tabs[4]:
    bsegs = [L("seg_bench"), L("seg_limit"), L("seg_k2")]
    which = st.segmented_control(L("show"), bsegs, default=bsegs[0], key="bench_seg")
    if which == bsegs[0]:
        Kow = 10 ** lib["logKow"][keep]
        bins = {L("curve_model"): M.binned_median(lib["logKow"][keep], fr["log_BCF"][keep]),
                L("curve_ceiling"): M.binned_median(lib["logKow"][keep], fr["log_ceiling"][keep]),
                L("curve_ag"): M.binned_median(lib["logKow"][keep], M.arnot_gobas(Kow, W_g / 1000.0, T_C)),
                L("curve_om"): M.binned_median(lib["logKow"][keep], M.omega(Kow, W_g / 1000.0))}
        mm = keep & np.isfinite(lib["measured"])
        meas = pd.DataFrame({"log Kow": lib["logKow"][mm], "median": lib["measured"][mm],
                             "lo": lib["measured_lo"][mm], "hi": lib["measured_hi"][mm],
                             "n": lib["measured_n"][mm], "chemical": lib["name"][mm]})
        st.altair_chart(PN.benchmark_panel(bins, meas, L("y_logbcf")), width="stretch")
        st.caption(L("bench_caption", w=W_g, t=T_C, n=len(meas)))
    elif which == bsegs[1]:
        ks = np.round(np.arange(2.5, 9.01, 0.25), 2)
        wmax = float(min(ent["Ww_i"], 1e5))
        ws = np.unique(np.round(np.logspace(np.log10(max(0.01, wmax * 1e-5)), np.log10(wmax), 22), 3))
        order = np.argsort(lib["logKow"])
        ip = {k: np.interp(ks, lib["logKow"][order], lib[k][order])
              for k in ("logPintr", "logD", "logPWd", "logPBd")}
        grid = []
        for W in ws:
            fw = fish.at_weight(float(W))
            fw.sigma, fw.h_um, fw.E_O, fw.k_b_pin = sigma, h_um, E_O, kb_pin
            grid.append(list(M.frame(fw, ks, ip["logPintr"], ip["logD"], ip["logPWd"], ip["logPBd"],
                                     None, "zero", route_key, plateau)["limiting"]))
        st.altair_chart(PN.limit_map(list(ks), [float(w) for w in ws], grid,
                                     L("limit_y", sp=D.species_label(species))), width="stretch")
        st.caption(L("limit_caption"))
    else:
        st.markdown(L("k2_intro"))
        cal_l = st.slider(L("k2_slider"), 0.10, 0.95, 0.20, 0.05)
        ls = np.linspace(0.08, min(0.95, f_food), 60)
        ker, bcf_mech, bcf_const = [], [], []
        k2_const = M.rates(fish.at_length(float(cal_l)), chem, kBt, route_key, plateau)["k_er"]
        for l in ls:
            fl = fish.at_length(float(l))
            fl.sigma, fl.h_um, fl.E_O, fl.k_b_pin = sigma, h_um, E_O, kb_pin
            rr = M.rates(fl, chem, kBt, route_key, plateau)
            ker.append(rr["k_er"])
            bcf_mech.append(M.bcf(fl, chem, kBt, route_key, plateau))
            bcf_const.append(rr["k1"] / (k2_const + rr["k_Bt"] + rr["k_g"]))
        const_label = L("k2_const_label", l=cal_l)

        def two(mech, const, title):
            d2 = pd.concat([pd.DataFrame({"l": ls, "y": mech, "model": L("curve_model")}),
                            pd.DataFrame({"l": ls, "y": const, "model": const_label})], ignore_index=True)
            lo, hi = float(np.nanmin(d2.y)), float(np.nanmax(d2.y))
            pad = (hi / lo) ** 0.05 if lo > 0 else 1.0
            return alt.Chart(d2).mark_line(size=2).encode(
                x=alt.X("l:Q", title=L("x_l"),
                        scale=alt.Scale(domain=[float(ls[0]), float(ls[-1])], nice=False)),
                y=alt.Y("y:Q", title=title,
                        scale=alt.Scale(type="log", domain=[lo / pad, hi * pad], nice=False)),
                color=alt.Color("model:N", title=None, scale=alt.Scale(
                    domain=[L("curve_model"), const_label], range=[TEAL, RUST])),
                tooltip=["l:Q", "y:Q", "model:N"]).properties(height=250)

        st.altair_chart(two(ker, [k2_const] * len(ls), L("q_ker")), width="stretch")
        st.altair_chart(two(bcf_mech, bcf_const, L("y_logbcf")), width="stretch")
        st.caption(L("k2_caption", c=cal_l, a=bcf_const[0] / bcf_mech[0], la=ls[0],
                     b=bcf_const[-1] / bcf_mech[-1], lb=ls[-1]))

# ---------------------------------------------------------------- 6. compare
with tabs[5]:
    if not st.session_state.pinned:
        st.info(L("compare_empty"))
    else:
        rows = []
        for j in st.session_state.pinned:
            cj = D.chemical_at(j, T_C, partition)
            rj = M.rates(fish, cj, kBt, route_key, plateau)
            bj = M.bcf(fish, cj, kBt, route_key, plateau)
            mbj = D.measured_bcf(j)
            rows.append({"chemical": cj.name, "log Kow": cj.logKow, "log P_Wd": cj.logPWd,
                         "BCF (L/kg)": bj, "log BCF": float(np.log10(bj)),
                         "measured log BCF": mbj[0] if mbj else np.nan,
                         "time to 95% (d)": float(np.log(20) / rj["k2"]), "limited by": rj["limiting"]})
        tb = pd.DataFrame(rows)
        st.dataframe(tb, hide_index=True, width="stretch")
        st.download_button(L("download_table"), tb.to_csv(index=False).encode(),
                           file_name="pinned_chemicals.csv", mime="text/csv")
        base = alt.Chart(tb).encode(x=alt.X("log Kow:Q", scale=alt.Scale(zero=False)),
                                    tooltip=["chemical:N", "log Kow:Q", "log BCF:Q", "limited by:N"])
        st.altair_chart((base.mark_circle(size=140, color=TEAL).encode(
            y=alt.Y("log BCF:Q", scale=alt.Scale(zero=False)))
            + base.mark_point(size=140, shape="triangle", filled=True, color=RUST).encode(
            y=alt.Y("measured log BCF:Q", title="log BCF"))).properties(height=320).interactive(),
            width="stretch")
        st.caption(L("compare_caption"))

# ---------------------------------------------------------------- 7. score a list
with tabs[6]:
    st.markdown(L("batch_intro"))
    bkey = ctx.api_key(st.session_state.get("ctx_key"))
    if not bkey:
        st.text_input(L("ctx_key"), type="password", key="ctx_key", help=L("ctx_key_help"))
        bkey = ctx.api_key(st.session_state.get("ctx_key"))
    text = st.text_area(L("the_list"), "hexachlorobenzene\nmirex\n50-29-3\nchlordecone", height=140)
    b1, b2 = st.columns([1, 3])
    prefer_b = b2.radio(L("kow_prefer"), [L("kow_measured"), L("kow_opera")], horizontal=True,
                        key="prefer_batch")
    if b1.button(L("score_them"), width="stretch", disabled=not bkey) and bkey:
        queries = [q.strip() for q in text.splitlines() if q.strip()][:60]
        _est = D.custom_estimators()
        prog = st.progress(0.0, text=L("asking_ctx"))
        out, failed = [], []
        for n_done, q in enumerate(queries, 1):
            prog.progress(n_done / len(queries), text=f"{q} ({n_done}/{len(queries)})")
            try:
                found_b = ctx.lookup(q, bkey,
                                     "experimental" if prefer_b == L("kow_measured") else "predicted")
            except RuntimeError as exc:
                failed.append((q, str(exc)))
                continue
            if not found_b:
                failed.append((q, L("no_match_ctx")))
                continue
            hb = found_b[0]
            pfb = ctx.parse_formula(hb.formula, _est["masses"], _est["halogens"])
            if hb.logKow is None or not pfb:
                failed.append((q, L("no_kow")))
                continue
            cqb = D.chemical_from_properties(hb.logKow, pfb[0], pfb[1], T_C, hb.name)
            rqb = M.rates(fish, cqb, kBt, route_key, plateau)
            bqb = M.bcf(fish, cqb, kBt, route_key, plateau)
            out.append({"asked for": q, "chemical": hb.name, "CAS": hb.casrn, "DTXSID": hb.dtxsid,
                        "formula": hb.formula, "log Kow": hb.logKow, "log Kow source": hb.logKow_source,
                        "log P_Wd": cqb.logPWd, "BCF (L/kg)": bqb, "log BCF": float(np.log10(bqb)),
                        "time to 95% (d)": float(np.log(20) / rqb["k2"]), "limited by": rqb["limiting"],
                        "screen": (L("verdict_very") if bqb >= 5000 else
                                   L("verdict_bio") if bqb >= 2000 else L("verdict_below"))})
        prog.empty()
        st.session_state["batch"] = (pd.DataFrame(out), failed,
                                     L("cond_label", sp=D.species_label(species), w=W_g, t=T_C, f=f_food))

    if "batch" in st.session_state:
        tb_b, failed, cond = st.session_state["batch"]
        st.caption(L("batch_done", n=len(tb_b), cond=cond)
                   + (L("batch_failed", n=len(failed)) if failed else ""))
        if len(tb_b):
            st.dataframe(tb_b, hide_index=True, width="stretch")
            st.download_button(L("download_table"), tb_b.to_csv(index=False).encode(),
                               file_name="scored_chemicals.csv", mime="text/csv")
            st.altair_chart(alt.Chart(tb_b).mark_circle(size=140).encode(
                x=alt.X("log Kow:Q", scale=alt.Scale(zero=False)),
                y=alt.Y("log BCF:Q", scale=alt.Scale(zero=False)),
                color=alt.Color("limited by:N", scale=alt.Scale(
                    domain=list(PN.LIMIT_COLOURS), range=list(PN.LIMIT_COLOURS.values()))),
                tooltip=["chemical:N", "CAS:N", "log Kow:Q", "log BCF:Q", "screen:N"]
            ).properties(height=320).interactive(), width="stretch")
        for q, why in failed:
            st.warning(f"{q}: {why}")
        st.caption(L("batch_caption"))

# ---------------------------------------------------------------- 8. the model
with tabs[7]:
    st.markdown(L("model_written"))
    st.latex(r"\mathrm{BCF}=\frac{P_{Wd}}"
             r"{1+\dot{k}_{Bt}/\dot{k}_{e,r}+3\dot{r}_B\,(f-l)\,/\,(l\,\dot{k}_{e,r})}"
             r"\qquad \mathrm{BCF}_{\max}=P_{Wd}")
    st.markdown(L("model_uptake"))
    st.latex(r"\dot{k}_1=\frac{E_W\,\dot{k}_r}{W},\qquad "
             r"E_W=\frac{1-e^{-\lambda}}{r-e^{-\lambda}},\quad \lambda=\beta\,(r-1),\quad "
             r"\beta=\frac{P_{app}\,\sigma\,W^{2/3}\cdot 86.4}{\dot{k}_r},\quad r=\frac{\dot{k}_r}{k_b P_{Bd}}")
    st.latex(r"\frac{1}{P_{app}}=\frac{1}{P_{intr}}+\frac{h}{D}")
    st.markdown(L("model_vent"))
    st.latex(r"\dot{k}_r=\frac{J_O\cdot 32000}{E_O\,C_{OX}},\qquad C_{OX}=-0.24\,T+14.04,\qquad "
             r"k_b=24\,W\,(0.23\,T-0.78)")
    st.markdown(L("model_growth"))
    st.latex(r"\frac{dl}{dt}=\dot{r}_B\,(f-l),\qquad "
             r"\dot{r}_B=\frac{\dot{k}_M\,g}{3\,(f+g)},\quad \dot{k}_M=\frac{[\dot{p}_M]}{[E_G]},\quad "
             r"g=\frac{\dot{v}}{\dot{k}_M L_m}")
    st.markdown(L("model_ode"))
    st.latex(r"\frac{d[M_Q]^W}{dt}=\dot{k}_1\,c_d-\left(\dot{k}_{e,r}+\dot{k}_{Bt}"
             r"+\frac{3\dot{r}_B (f-l)}{l}\right)[M_Q]^W")

    st.markdown(L("kr_heading"))
    st.markdown(L("kr_body"))
    st.latex(r"\dot{k}_r \;=\; k_0 \;+\; \{\dot{k}_r\}\,L^{2} \;+\; [\dot{k}_r]\,L^{3}")
    st.markdown(L("kr_tail", chk=note["flux_check_ultimate"]))

    st.markdown(L("this_animal"))
    st.markdown(L("animal_line", latin=note["latin"], url=note["url"], fam=note["family"],
                  c=note["completeness"], m=note["mre"], t=note["T_typ"], wi=ent["Ww_i"]))

    st.markdown(L("check_heading"))
    st.markdown(L("check_body", n=sc["n"], w=sc["worst"]))

    st.markdown(L("what_heading"))
    st.markdown(L("what_body"))
