"""Every sentence the app shows, in English and Korean.

Two reasons the strings live here rather than in app.py: a translation that sits next to its original is the
only kind that stays in step, and a reader can check what the app claims without reading the interface code.

Unlike the rice model, the language and the mode are independent here: a specialist may want Korean and a
first-time reader may want English, and tying the two together makes one of them impossible.

t("key", lang, **fmt) returns the string; a missing key returns the key itself, visibly, rather than silently
falling back to English.
"""
from __future__ import annotations

LANGS = {"English": "en", "한국어": "ko"}

T: dict[str, dict[str, str]] = {
    # ---------------------------------------------------------------- chrome
    "page_title": {"en": "Fish bioaccumulation (DEB-TK)", "ko": "어류 생물축적 (DEB-TK)"},
    "language": {"en": "Language", "ko": "언어"},
    "mode": {"en": "Detail", "ko": "보기 수준"},
    "mode_simple": {"en": "Plain", "ko": "간단히"},
    "mode_expert": {"en": "Expert", "ko": "전문가"},
    "mode_help": {"en": "Plain keeps the fish, the time course and where the loss goes. Expert adds the "
                        "whole library, the published-model benchmarks, the equations and every setting.",
                  "ko": "간단히 보기에는 물고기, 시간 경과, 손실 경로만 둡니다. 전문가 보기에는 866종 전체, "
                        "기존 모델 비교, 수식, 모든 설정이 더해집니다."},

    # ---------------------------------------------------------------- sidebar: exposure
    "exposure": {"en": "Exposure", "ko": "노출"},
    "scenario": {"en": "scenario", "ko": "시나리오"},
    "use_scenario": {"en": "use this scenario", "ko": "이 시나리오 적용"},
    "water_conc": {"en": "water (ng/L)", "ko": "물 농도 (ng/L)"},
    "lasts": {"en": "lasts (d)", "ko": "노출 기간 (일)"},
    "follow_for": {"en": "follow for (d)", "ko": "관찰 기간 (일)"},
    "follow_help": {"en": "after the exposure ends the fish sits in clean water",
                    "ko": "노출이 끝나면 물고기는 깨끗한 물에 있습니다"},
    "sc_chronic": {"en": "chronic, 1 ng/L for a year", "ko": "만성 노출: 1 ng/L, 1년"},
    "sc_spill": {"en": "spill: 1 µg/L for a week", "ko": "유출 사고: 1 µg/L, 1주"},
    "sc_pore": {"en": "sediment porewater, 10 ng/L for 60 d", "ko": "퇴적물 공극수: 10 ng/L, 60일"},

    # ---------------------------------------------------------------- sidebar: chemical
    "chemical": {"en": "Chemical", "ko": "물질"},
    "where_from": {"en": "where from", "ko": "어디서"},
    "src_library": {"en": "the library (866)", "ko": "라이브러리 (866종)"},
    "src_ctx": {"en": "look it up in CompTox", "ko": "CompTox에서 조회"},
    "src_hand": {"en": "type the numbers", "ko": "숫자 직접 입력"},
    "family": {"en": "family", "ko": "계열"},
    "all": {"en": "all", "ko": "전체"},
    "search_chem": {"en": "search by name or CAS", "ko": "이름 또는 CAS로 검색"},
    "no_chem_match": {"en": "nothing matches that search in this family",
                      "ko": "이 계열에서 검색어와 맞는 물질이 없습니다"},
    "n_matches": {"en": "{n} matches", "ko": "{n}건"},
    "one_match": {"en": "1 match", "ko": "1건"},
    "measured_logbcf_short": {"en": "measured log BCF {v:.2f}", "ko": "측정 log BCF {v:.2f}"},
    "pin": {"en": "pin to compare", "ko": "비교에 고정"},
    "clear": {"en": "clear", "ko": "비우기"},
    "ctx_key": {"en": "CompTox API key", "ko": "CompTox API 키"},
    "ctx_key_help": {"en": "free from EPA; or set EPA_API_KEY in the environment, or ctx_api_key in secrets",
                     "ko": "EPA에서 무료 발급. 환경변수 EPA_API_KEY나 Streamlit secrets의 ctx_api_key로도 됩니다"},
    "ctx_query": {"en": "name, CAS or DTXSID", "ko": "이름, CAS 또는 DTXSID"},
    "kow_prefer": {"en": "log K_OW", "ko": "log K_OW"},
    "kow_measured": {"en": "measured where there is one", "ko": "측정값이 있으면 측정값"},
    "kow_opera": {"en": "OPERA prediction", "ko": "OPERA 예측값"},
    "ctx_key_needed": {"en": "a CompTox key is needed for this", "ko": "이 기능에는 CompTox 키가 필요합니다"},
    "ctx_no_match": {"en": "CompTox has nothing matching “{q}”", "ko": "CompTox에 “{q}”와 맞는 항목이 없습니다"},
    "ctx_entry": {"en": "entry", "ko": "항목"},
    "ctx_unusable": {"en": "that entry carries no usable log K_OW or formula — try the OPERA prediction, or "
                           "type the numbers in",
                     "ko": "그 항목에는 쓸 수 있는 log K_OW나 분자식이 없습니다. OPERA 예측값을 쓰거나 숫자를 "
                           "직접 입력해 보세요"},
    "name_it": {"en": "name it", "ko": "이름"},
    "my_chemical": {"en": "my chemical", "ko": "내 물질"},
    "molar_mass": {"en": "molar mass (g/mol)", "ko": "분자량 (g/mol)"},
    "halogens": {"en": "halogen atoms", "ko": "할로겐 원자 수"},
    "by_hand_note": {"en": "{n} · log K_OW {k:.2f} · MW {m:,.1f} · {h} halogen atoms, all set by hand",
                     "ko": "{n} · log K_OW {k:.2f} · 분자량 {m:,.1f} · 할로겐 {h}개, 모두 직접 입력"},

    # ---------------------------------------------------------------- sidebar: fish
    "fish": {"en": "Fish", "ko": "물고기"},
    "start_from": {"en": "start from", "ko": "선택"},
    "any_amp": {"en": "any fish in Add-my-Pet", "ko": "Add-my-Pet의 모든 어종"},
    "recorded_help": {"en": "the three fish of the original 866-structure scan, at the weight and "
                            "temperature that scan used",
                      "ko": "866종 원 계산에 쓴 세 종. 그때의 체중과 온도 그대로입니다"},
    "search_species": {"en": "search {n} entries", "ko": "{n}종에서 검색"},
    "species_help": {"en": "common name, scientific name, family or order",
                     "ko": "일반명, 학명, 과 또는 목"},
    "no_species": {"en": "no species matches", "ko": "맞는 어종이 없습니다"},
    "species": {"en": "species", "ko": "어종"},
    "fish_caption": {"en": "{fam} · ultimate {wi:,.0f} g · AmP typical {t:.1f} °C",
                     "ko": "{fam} · 최대 체중 {wi:,.0f} g · AmP 기준 수온 {t:.1f} °C"},
    "body_weight": {"en": "body weight (g)", "ko": "체중 (g)"},
    "temperature": {"en": "temperature (°C)", "ko": "수온 (°C)"},
    "temp_help": {"en": "the partition coefficients are tabulated only at these three",
                  "ko": "분배계수가 이 세 온도에서만 계산되어 있습니다"},
    "food_level": {"en": "food level f", "ko": "먹이 수준 f"},
    "food_help": {"en": "scaled functional response: sets ingestion, growth and the ultimate size",
                  "ko": "먹이 가용성(0~1). 섭식량, 성장, 최대 체중을 함께 결정합니다"},
    "biotransformation": {"en": "biotransformation", "ko": "생물전환"},
    "none": {"en": "none", "ko": "없음"},
    "qsar_estimate": {"en": "QSAR estimate", "ko": "QSAR 추정"},
    "advanced": {"en": "gill, partitioning, display", "ko": "아가미·분배·표시 설정"},
    "gill_set": {"en": "σ, h set", "ko": "σ, h 세트"},
    "gill_set_help": {"en": "the fitted sets; moving a slider below overrides the set",
                      "ko": "적합된 세트. 아래 슬라이더를 움직이면 그 값이 우선합니다"},
    "sigma": {"en": "gill area σ (cm² kg^-2/3)", "ko": "아가미 면적 σ (cm² kg^-2/3)"},
    "h_path": {"en": "diffusion path h (log µm)", "ko": "확산 경로 h (log µm)"},
    "h_help": {"en": "log scale, so the membrane and the boundary layer can be put on the same footing",
               "ko": "로그 눈금이라 막 저항과 경계층 저항을 같은 선상에서 비교할 수 있습니다"},
    "eo": {"en": "O₂ extraction E_O", "ko": "산소 추출효율 E_O"},
    "kb_mode": {"en": "blood flow k_b", "ko": "혈류 k_b"},
    "kb_allometry": {"en": "Barron allometry", "ko": "Barron 상대성장식"},
    "kb_hand": {"en": "set by hand", "ko": "직접 지정"},
    "kb_log": {"en": "k_b (log L/d)", "ko": "k_b (log L/일)"},
    "ker_route": {"en": "respiratory elimination", "ko": "호흡 배출 경로"},
    "route_mech": {"en": "mechanistic", "ko": "기계론적"},
    "route_plateau": {"en": "measured k₁ plateau", "ko": "측정된 k₁ plateau"},
    "plateau_input": {"en": "k₁ plateau (L kg⁻¹ d⁻¹)", "ko": "k₁ plateau (L kg⁻¹ d⁻¹)"},
    "plateau_help": {"en": "a measured plateau is available only for trout and guppy",
                     "ko": "측정된 plateau는 송어와 구피에만 있습니다"},
    "partition": {"en": "partition coefficients", "ko": "분배계수"},
    "partition_help": {"en": "the original scan used the consensus values",
                       "ko": "원 계산은 consensus 값을 썼습니다"},
    "outlier_cut": {"en": "hide k₁ further than this from the median (log)",
                    "ko": "중앙값에서 이만큼 떨어진 k₁ 숨기기 (log)"},
    "halogen_free": {"en": "halogen-free structures only", "ko": "할로겐 없는 물질만"},

    # ---------------------------------------------------------------- headline
    "verdict_very": {"en": "very bioaccumulative (BCF ≥ 5,000)", "ko": "고축적성 (BCF ≥ 5,000)"},
    "verdict_bio": {"en": "bioaccumulative (BCF ≥ 2,000)", "ko": "축적성 (BCF ≥ 2,000)"},
    "verdict_below": {"en": "below the BCF 2,000 screen", "ko": "BCF 2,000 기준 미만"},
    "subtitle": {"en": "{sp}, {w:,.3g} g at {t:.0f} °C · log K_OW {k} · f = {f:.2f}",
                 "ko": "{sp}, {w:,.3g} g, {t:.0f} °C · log K_OW {k} · f = {f:.2f}"},
    "m_bcf": {"en": "steady-state BCF", "ko": "정상상태 BCF"},
    "m_k1": {"en": "uptake k₁", "ko": "흡수 k₁"},
    "m_k1_delta": {"en": "limited by the {lim}", "ko": "{lim}이(가) 제한"},
    "m_t95": {"en": "time to 95%", "ko": "95% 도달 시간"},
    "m_t95_delta": {"en": "half-life {v:,.1f} d", "ko": "반감기 {v:,.1f}일"},
    "m_measured": {"en": "measured log BCF", "ko": "측정 log BCF"},
    "m_measured_delta": {"en": "model log {v:.2f} · n = {n}", "ko": "모델 log {v:.2f} · n = {n}"},
    "m_measured_none": {"en": "no measured value for this structure", "ko": "이 물질에는 측정값이 없습니다"},
    "loss_caption": {"en": "loss: respiration {ker:.4g} d⁻¹{bt} · growth dilution {kg:.4g} d⁻¹{share}{meas}",
                     "ko": "손실: 호흡 {ker:.4g} /일{bt} · 성장 희석 {kg:.4g} /일{share}{meas}"},
    "loss_bt": {"en": " · biotransformation {v:.4g} d⁻¹", "ko": " · 생물전환 {v:.4g} /일"},
    "loss_share": {"en": " ({p:.0f}% of the total)", "ko": " (전체의 {p:.0f}%)"},
    "loss_meas": {"en": "   ·   measured BCF pooled over species and routes, range {lo:.2f}–{hi:.2f}",
                  "ko": "   ·   측정 BCF는 여러 종·노출경로를 합친 값, 범위 {lo:.2f}–{hi:.2f}"},
    "check_ok": {"en": "matches the original scan · max |Δlog| {w:.1e} over {n} reference points",
                 "ko": "원 계산과 일치 · 최대 |Δlog| {w:.1e}, 기준점 {n}개"},
    "check_bad": {"en": "DIFFERS FROM the original scan · max |Δlog| {w:.1e} over {n} reference points",
                  "ko": "원 계산과 불일치 · 최대 |Δlog| {w:.1e}, 기준점 {n}개"},
    "ctx_note_tail": {
        "en": "Partitioning for a chemical outside the library comes from the three K_OW-based forms, not the "
              "ppLFER consensus the library rows carry, and the membrane permeability is estimated from molar "
              "mass and halogen count. On hexachlorobenzene that estimate is 1.26 log off, which moves the BCF "
              "by 0.02 log — because the boundary layer, not the membrane, limits uptake for most of these "
              "chemicals. Where the membrane does limit, treat the number with care.",
        "ko": "라이브러리 밖 물질의 분배계수는 ppLFER consensus가 아니라 K_OW 기반 세 식에서 나오고, 막 투과도는 "
              "분자량과 할로겐 수로 추정합니다. 헥사클로로벤젠에서 그 추정치는 1.26 log 어긋나지만 BCF는 0.02 log만 "
              "움직입니다 — 대부분의 물질에서 막이 아니라 경계층이 흡수를 제한하기 때문입니다. 막이 제한하는 "
              "물질에서는 값을 조심해서 보십시오."},

    "lim_membrane": {"en": "membrane", "ko": "막"},
    "lim_boundary layer": {"en": "boundary layer", "ko": "경계층"},
    "lim_ventilation": {"en": "ventilation", "ko": "환기"},
    "lim_perfusion": {"en": "perfusion", "ko": "관류"},

    # ---------------------------------------------------------------- tabs
    "tab_fish": {"en": "The fish", "ko": "물고기"},
    "tab_time": {"en": "Time course", "ko": "시간 경과"},
    "tab_loss": {"en": "Where the loss goes", "ko": "손실 경로"},
    "tab_library": {"en": "Across the library", "ko": "866종 전체"},
    "tab_bench": {"en": "Benchmarks and limits", "ko": "기존 모델·제한단계"},
    "tab_compare": {"en": "Compare ({n})", "ko": "비교 ({n})"},
    "tab_batch": {"en": "Score a list", "ko": "목록 채점"},
    "tab_model": {"en": "The model", "ko": "모델"},

    # ---------------------------------------------------------------- the fish
    "day_slider": {"en": "day of the simulation", "ko": "경과 일수"},
    "day_help": {"en": "the animal grows as this moves: outline, arrows and colour follow it",
                 "ko": "이걸 움직이면 물고기가 자랍니다. 외형·화살표·색이 따라옵니다"},
    "play": {"en": "play", "ko": "재생"},
    "play_help": {"en": "steps the day forward until it reaches the end", "ko": "끝까지 하루씩 넘깁니다"},
    "weight_now": {"en": "weight now", "ko": "현재 체중"},
    "weight_from": {"en": "from {w:,.3g} g on day 0", "ko": "0일차 {w:,.3g} g에서"},
    "in_fish_now": {"en": "in the fish now", "ko": "현재 체내 농도"},
    "heading_for": {"en": "heading for", "ko": "향하고 있는 값"},
    "was_on_day0": {"en": "was {v:,.0f} on day 0", "ko": "0일차에는 {v:,.0f}"},
    "fish_caption_long": {
        "en": "Arrow width is the flux; hover any body part for what it is. The ramp is the same for every "
              "chemical, so two can be compared by eye. The outline is stretched by the species' shape "
              "coefficient — a hint, not anatomy; nothing computed depends on it.",
        "ko": "화살표 굵기가 물질 흐름입니다. 몸의 각 부위에 마우스를 올리면 설명이 뜹니다. 색 눈금은 모든 물질에 "
              "같으므로 두 물질을 눈으로 비교할 수 있습니다. 외형은 어종의 형태계수로 늘였을 뿐이며, 해부학이 "
              "아니라 참고용입니다 — 계산되는 값은 외형에 전혀 의존하지 않습니다."},

    # ---------------------------------------------------------------- time course
    "time_intro": {
        "en": "The companion framework is written for a growing organism: k_e,r falls as 1/l while the animal "
              "grows, and the growth term dilutes what is already inside. Both are integrated here.",
        "ko": "동반 논문의 틀은 자라는 생물을 전제로 씁니다. 물고기가 자라면 k_e,r은 1/l로 줄고, 성장 항은 이미 "
              "몸 안에 있는 양을 희석합니다. 여기서는 둘을 함께 적분합니다."},
    "pin_dropped": {
        "en": "The original scan fixes l for this fish at a value that does not match its weight under the "
              "condition-factor rule. Growth here starts from the weight: l = {l:.3f}.",
        "ko": "원 계산은 이 물고기의 l을 고정값으로 두는데, 비만도 규칙으로는 그 체중과 맞지 않습니다. 여기서 "
              "성장은 체중에서 출발합니다: l = {l:.3f}."},
    "case_grows": {"en": "the animal grows", "ko": "자라는 경우"},
    "case_fixed": {"en": "size held fixed", "ko": "크기 고정"},
    "y_conc": {"en": "concentration in the fish (ng kg⁻¹)", "ko": "체내 농도 (ng kg⁻¹)"},
    "day": {"en": "day", "ko": "일"},
    "w_at_end": {"en": "weight at the end of exposure", "ko": "노출 종료 시 체중"},
    "burden_at_end": {"en": "burden at the end of exposure", "ko": "노출 종료 시 체내량"},
    "vs_fixed": {"en": "{p:+.0f}% against a fixed size", "ko": "크기 고정 대비 {p:+.0f}%"},
    "steady_heading": {"en": "steady state it is heading for", "ko": "향하고 있는 정상상태"},
    "what_moves": {"en": "**What moves while it grows**", "ko": "**자라는 동안 무엇이 변하는가**"},
    "q_ker": {"en": "k_e,r (d⁻¹)", "ko": "k_e,r (/일)"},
    "q_growth": {"en": "growth dilution (d⁻¹)", "ko": "성장 희석 (/일)"},
    "q_l": {"en": "scaled length l", "ko": "무차원 체장 l"},

    # ---------------------------------------------------------------- loss
    "loss_intro": {
        "en": "Every route out, over the whole simulation. The bands are fluxes, so they shrink as the fish "
              "empties and as respiration slows with size.",
        "ko": "전체 기간에 걸친 배출 경로입니다. 띠의 두께는 유량이라, 물고기가 비워지고 체격이 커져 호흡이 "
              "느려지면 함께 줄어듭니다."},
    "route_gill": {"en": "back out of the gill", "ko": "아가미로 되나감"},
    "route_growth": {"en": "diluted by growth", "ko": "성장으로 희석"},
    "route_met": {"en": "metabolised", "ko": "대사로 분해"},
    "y_loss": {"en": "loss flux (ng kg⁻¹ d⁻¹)", "ko": "배출 유량 (ng kg⁻¹ /일)"},
    "share_axis": {"en": "share of the total loss at the current size",
                   "ko": "현재 체격에서 전체 손실 중 비율"},

    # ---------------------------------------------------------------- library
    "show": {"en": "show", "ko": "표시"},
    "seg_k1": {"en": "uptake k₁", "ko": "흡수 k₁"},
    "seg_ker": {"en": "elimination k_e,r", "ko": "배출 k_e,r"},
    "seg_bcf": {"en": "BCF", "ko": "BCF"},
    "seg_inputs": {"en": "structure-derived inputs", "ko": "구조에서 나온 입력값"},
    "lib_caption": {"en": "{n} of {tot} structures shown", "ko": "{tot}종 중 {n}종 표시"},
    "lib_halogen": {"en": " · halogen-free only", "ko": " · 할로겐 없는 물질만"},
    "lib_outlier": {"en": " · k₁ outliers beyond {c:.2f} log from the median hidden",
                    "ko": " · 중앙값에서 {c:.2f} log 넘게 떨어진 k₁ 숨김"},
    "lib_window": {"en": " · the shaded band is the range over which the model has been validated, "
                          "log Kow {lo}–{hi}",
                   "ko": " · 음영은 모델이 검증된 범위, log Kow {lo}–{hi}"},
    "y_logk1": {"en": "log k₁ (L kg⁻¹ d⁻¹)", "ko": "log k₁ (L kg⁻¹ /일)"},
    "y_logker": {"en": "log k_e,r (d⁻¹)", "ko": "log k_e,r (/일)"},
    "y_logbcf": {"en": "log BCF (L/kg)", "ko": "log BCF (L/kg)"},
    "in_pintr": {"en": "log P_intr (membrane permeability)", "ko": "log P_intr (막 투과도)"},
    "in_d": {"en": "log D (aqueous diffusivity)", "ko": "log D (수중 확산계수)"},
    "in_pwd": {"en": "log P_Wd (whole body – water)", "ko": "log P_Wd (전어체–물 분배)"},
    "in_pbd": {"en": "log P_Bd (blood – water)", "ko": "log P_Bd (혈액–물 분배)"},
    "inputs_caption": {
        "en": "Each input on its own axes, coloured by halogen count: membrane permeability rises with log "
              "K_OW only among halogen-free structures, which is what the halogen-free filter isolates.",
        "ko": "입력값마다 축을 따로 두고 할로겐 수로 색칠했습니다. 막 투과도가 log K_OW와 함께 오르는 것은 할로겐이 "
              "없는 물질에서만이며, 사이드바의 할로겐 필터가 그 부분을 떼어 봅니다."},

    # ---------------------------------------------------------------- benchmarks
    "seg_bench": {"en": "against the published models", "ko": "기존 모델과 비교"},
    "seg_limit": {"en": "what limits uptake", "ko": "무엇이 흡수를 제한하는가"},
    "seg_k2": {"en": "against a constant k₂", "ko": "상수 k₂와 비교"},
    "bench_caption": {
        "en": "Binned medians over the structures shown, all at {w:,.3g} g and {t:.0f} °C with no "
              "biotransformation in the two published models. Squares with whiskers: measured fish whole-body "
              "BCF, median and range, for {n} of them.",
        "ko": "표시된 물질들의 구간별 중앙값입니다. 모두 {w:,.3g} g, {t:.0f} °C이고 두 기존 모델에는 생물전환을 "
              "넣지 않았습니다. 사각형과 수염은 측정된 전어체 BCF의 중앙값과 범위이며 {n}종에 있습니다."},
    "curve_model": {"en": "this model", "ko": "이 모델"},
    "curve_ceiling": {"en": "partition ceiling (P_Wd)", "ko": "분배 상한 (P_Wd)"},
    "curve_ag": {"en": "Arnot & Gobas 2004", "ko": "Arnot & Gobas 2004"},
    "curve_om": {"en": "OMEGA (Hendriks 2001)", "ko": "OMEGA (Hendriks 2001)"},
    "limit_caption": {
        "en": "The library's inputs interpolated onto a regular log K_OW axis, then the model run at each "
              "weight. The step with the smallest conductance is the one shown.",
        "ko": "라이브러리의 입력값을 일정한 log K_OW 축에 보간한 뒤 체중마다 모델을 돌린 것입니다. 전도도가 가장 "
              "작은 단계를 표시합니다."},
    "limit_y": {"en": "{sp} weight (g)", "ko": "{sp} 체중 (g)"},
    "k2_intro": {
        "en": "A fugacity model carries one constant k₂, fitted at whatever size the test fish happened to be. "
              "Here k₂ is calibrated at one scaled length and then used at every other, against the "
              "mechanistic k_e,r ∝ 1/l of this model — the companion's Figure 2(b–d), computed rather than "
              "described.",
        "ko": "퓨가시티 모델은 시험어의 크기에서 맞춘 상수 k₂ 하나를 씁니다. 여기서는 한 체장에서 k₂를 보정한 뒤 "
              "다른 모든 체장에 그대로 적용해, 이 모델의 기계론적 k_e,r ∝ 1/l과 나란히 놓습니다 — 동반 논문 "
              "Figure 2(b–d)를 설명 대신 계산으로 보여주는 것입니다."},
    "k2_slider": {"en": "calibrate the constant k₂ at scaled length", "ko": "상수 k₂를 보정할 체장"},
    "k2_const_label": {"en": "constant k₂, fitted at l = {l:.2f}", "ko": "상수 k₂ (l = {l:.2f}에서 보정)"},
    "k2_caption": {"en": "Calibrated at l = {c:.2f}, the constant k₂ misses the mechanistic BCF by {a:.2f}× "
                         "at l = {la:.2f} and {b:.2f}× at l = {lb:.2f}.",
                   "ko": "l = {c:.2f}에서 보정한 상수 k₂는 기계론적 BCF를 l = {la:.2f}에서 {a:.2f}배, "
                         "l = {lb:.2f}에서 {b:.2f}배 빗나갑니다."},
    "x_l": {"en": "scaled length l", "ko": "무차원 체장 l"},

    # ---------------------------------------------------------------- compare and batch
    "compare_empty": {"en": "Pin chemicals in the sidebar to line them up here, all on this fish at this size.",
                      "ko": "사이드바에서 물질을 고정하면 이 물고기·이 체격 기준으로 나란히 비교합니다."},
    "download_table": {"en": "download this table (CSV)", "ko": "표 내려받기 (CSV)"},
    "compare_caption": {"en": "Circles: this model. Triangles: the measured whole-body BCF where the library "
                              "carries one.",
                        "ko": "원은 이 모델, 삼각형은 라이브러리에 측정값이 있는 경우의 전어체 BCF입니다."},
    "batch_intro": {
        "en": "Paste a list — one name, CAS number or DTXSID a line. Each is resolved in CompTox, built from "
              "its log K_OW, molar mass and halogen count, and run on the fish set in the sidebar.",
        "ko": "목록을 붙여넣으세요 — 한 줄에 이름, CAS 번호 또는 DTXSID 하나씩. 각각을 CompTox에서 찾아 log K_OW, "
              "분자량, 할로겐 수로 구성한 뒤 사이드바에 설정된 물고기로 계산합니다."},
    "the_list": {"en": "the list", "ko": "목록"},
    "score_them": {"en": "score them", "ko": "계산"},
    "asking_ctx": {"en": "asking CompTox…", "ko": "CompTox에 조회 중…"},
    "batch_done": {"en": "{n} scored on {cond}", "ko": "{cond} 기준으로 {n}종 계산"},
    "batch_failed": {"en": " · {n} could not be used", "ko": " · {n}종은 쓸 수 없었습니다"},
    "batch_caption": {
        "en": "Every row is built the way a single looked-up chemical is: the three K_OW-based partition forms "
              "and an estimated membrane permeability, not the ppLFER consensus the library rows carry. The "
              "screening labels are the BCF 2,000 and 5,000 lines, applied to this model's number for this "
              "one fish at this one size.",
        "ko": "각 행은 개별 조회와 같은 방식으로 만들어집니다 — K_OW 기반 분배식 셋과 추정된 막 투과도이며, "
              "라이브러리가 가진 ppLFER consensus가 아닙니다. 판정은 BCF 2,000과 5,000 기준선을, 이 물고기 "
              "이 체격에서 나온 이 모델의 값에 적용한 것입니다."},
    "no_match_ctx": {"en": "no match in CompTox", "ko": "CompTox에서 찾지 못함"},
    "no_kow": {"en": "no usable log K_OW or formula", "ko": "쓸 수 있는 log K_OW나 분자식 없음"},
    "cond_label": {"en": "{sp}, {w:,.3g} g at {t:.0f} °C, f = {f}", "ko": "{sp}, {w:,.3g} g, {t:.0f} °C, f = {f}"},

    # ---------------------------------------------------------------- the model tab
    "model_written": {"en": "#### The model, as written", "ko": "#### 모델 수식"},
    "model_uptake": {"en": "Uptake across the gill, from the countercurrent exchange of Erickson and McKim:",
                     "ko": "아가미 흡수 — Erickson과 McKim의 역류 교환식:"},
    "model_vent": {"en": "Ventilation from the DEB oxygen demand, and blood flow from Barron's allometry:",
                   "ko": "환기량은 DEB의 산소 요구에서, 혈류는 Barron의 상대성장식에서:"},
    "model_growth": {"en": "Growth, as von Bertalanffy in scaled length, which is what dilutes the burden:",
                     "ko": "성장은 무차원 체장의 von Bertalanffy 식이며, 체내량을 희석하는 것이 이 항입니다:"},
    "model_ode": {"en": "And the whole thing in time (companion eq 7, water exposure only):",
                  "ko": "전체를 시간에 대해 쓰면 (동반 논문 eq 7, 물 노출만):"},
    "kr_heading": {"en": "#### Where the ventilation rate comes from", "ko": "#### 환기량은 어디서 오는가"},
    "kr_body": {
        "en": "The oxygen demand is the DEB dissipating flux, so the ventilation that carries it is not an "
              "allometric fit but a sum of surface and volume terms. Writing the assimilation, dissipation and "
              "growth powers in structural length and collecting them gives",
        "ko": "산소 요구는 DEB의 소산 플럭스이므로, 그것을 실어 나르는 환기량은 상대성장식에 맞춘 값이 아니라 "
              "표면 항과 부피 항의 합입니다. 동화·소산·성장 power를 구조 체장으로 쓰고 정리하면"},
    "kr_tail": {
        "en": "with k₀ the adult maturity maintenance, {{k_r}} the surface-specific term carried by assimilation, "
              "and [k_r] the volume-specific term carried by somatic maintenance. The surface-only form used in "
              "much of the literature is the L ≪ {{k_r}}/[k_r] limit of this. Reproduced against AmP's own "
              "published oxygen statistics for every entry carried here (this one to {chk:.0e} at ultimate size).",
        "ko": "여기서 k₀는 성체 성숙 유지, {{k_r}}은 동화가 싣는 표면비 항, [k_r]은 체성분 유지가 싣는 부피비 항입니다. "
              "문헌에서 흔히 쓰는 표면 항만의 형태는 이 식의 L ≪ {{k_r}}/[k_r] 극한입니다. 여기 실린 모든 entry에 "
              "대해 AmP가 게시한 산소 통계로 재현을 확인했습니다 (이 종은 최대 체격에서 {chk:.0e})."},
    "this_animal": {"en": "#### This animal", "ko": "#### 이 어종"},
    "animal_line": {"en": "[{latin}]({url}) · {fam} · AmP completeness {c}, mean relative error {m:.3f} · AmP "
                          "typical temperature {t:.1f} °C · ultimate weight {wi:,.0f} g.",
                    "ko": "[{latin}]({url}) · {fam} · AmP 완전성 {c}, 평균상대오차 {m:.3f} · AmP 기준 수온 "
                          "{t:.1f} °C · 최대 체중 {wi:,.0f} g."},
    "check_heading": {"en": "#### Does this still match the original scan?",
                      "ko": "#### 원 계산과 여전히 일치하는가"},
    "check_body": {
        "en": "The badge at the top of the page recomputes {n} reference points from the original scan — "
              "fish, structure, k₁ and BCF, at the settings that scan used — every time the page loads, and "
              "reports the largest disagreement: **{w:.1e} log**. The same comparison over the whole scan, all "
              "2,598 fish–chemical pairs, matches every quantity to better than 1e-9.",
        "ko": "페이지 상단의 배지는 원 계산의 기준점 {n}개 — 물고기, 물질, k₁, BCF를 그 계산이 쓴 설정 그대로 — "
              "를 페이지가 열릴 때마다 다시 계산해 최대 차이를 보여줍니다: **{w:.1e} log**. 원 계산 전체, "
              "2,598개 물고기–물질 쌍에 대해 같은 비교를 하면 모든 값이 1e-9보다 작은 차이로 일치합니다."},
    "what_heading": {"en": "#### What this is and is not", "ko": "#### 이것이 무엇이고 무엇이 아닌가"},
    "what_body": {
        "en": "The app computes bioconcentration from water in a fish that grows, with the DEB-TK framework "
              "(Lee & Joe, ChemRxiv 10.26434/chemrxiv.15002330/v1). Its code reproduces an earlier scan of 866 "
              "persistent organic structures on three fish — rainbow trout 10 g at 15 °C, guppy 0.1 g at "
              "22 °C, fathead minnow 0.4 g at 25 °C — for all 2,598 fish–chemical pairs to better than 1e-9. "
              "Growth is integrated as the framework's eq 7; the dietary pathway (its eq 9–10, BAF and BMF) "
              "is **not** implemented, so everything here is water exposure only.\n\n"
              "Those three fish are the only ones with measured data behind their settings. Any other fish is "
              "the same chemistry run on that animal's Add-my-Pet physiology, with no measured uptake "
              "plateau. Measured BCF values are pooled over species and exposure routes, while the model is "
              "one species at one size.",
        "ko": "이 앱은 자라는 물고기가 물에서 물질을 생물농축하는 정도를 DEB-TK 틀(Lee & Joe, ChemRxiv "
              "10.26434/chemrxiv.15002330/v1)로 계산합니다. 코드는 앞서 수행한 계산 — 잔류성 유기 구조 866종을 "
              "세 어종(무지개송어 10 g·15 °C, 구피 0.1 g·22 °C, 팻헤드미노 0.4 g·25 °C)에 돌린 것 — 의 "
              "2,598개 물고기–물질 쌍을 1e-9보다 작은 차이로 재현합니다. 성장 적분은 이 틀의 eq 7이며, 먹이 "
              "경로(eq 9–10의 BAF·BMF)는 **구현되어 있지 않습니다**. 따라서 여기 있는 모든 것은 물 노출만입니다.\n\n"
              "측정 자료가 설정을 뒷받침하는 것은 이 세 종뿐입니다. 그 밖의 어종은 같은 화학을 그 동물의 "
              "Add-my-Pet 생리로 돌린 것이고, 측정된 흡수 plateau도 없습니다. 측정 BCF는 여러 종과 노출경로를 "
              "합친 값인 반면 모델은 한 종, 한 체격입니다."},

    # ---------------------------------------------------------------- plain mode
    "plain_intro": {
        "en": "How much of a chemical a fish takes up from water, and how long it keeps it. The fish grows "
              "while the clock runs, which changes both.",
        "ko": "물고기가 물에서 물질을 얼마나 받아들이고 얼마나 오래 품고 있는지를 보여줍니다. 시간이 가는 동안 "
              "물고기가 자라며, 그 때문에 둘 다 달라집니다."},
    "plain_reading": {
        "en": "**What the numbers say.** At steady state this fish would hold about {bcf:,.0f} times the water "
              "concentration — {verdict}. It gets {pct:.0f}% of the way there in {t95:,.0f} days. Of everything "
              "leaving the fish, {lossshare:.0f}% goes back out through the gill and the rest is diluted as the "
              "animal grows{met}.",
        "ko": "**숫자가 말하는 것.** 정상상태에서 이 물고기는 물 농도의 약 {bcf:,.0f}배를 품게 됩니다 — "
              "{verdict}. 거기까지 {pct:.0f}%에 도달하는 데 {t95:,.0f}일이 걸립니다. 몸에서 빠져나가는 양 중 "
              "{lossshare:.0f}%는 아가미로 되나가고 나머지는 자라면서 희석됩니다{met}."},
    "plain_met": {"en": ", with {p:.0f}% broken down by the liver", "ko": ", 그중 {p:.0f}%는 간에서 분해됩니다"},
    "plain_more": {"en": "Switch Detail to Expert for the whole 866-structure library, the comparison against "
                         "the published models, and every setting.",
                   "ko": "보기 수준을 전문가로 바꾸면 866종 전체, 기존 모델과의 비교, 모든 설정이 나옵니다."},
}


def t(key: str, lang: str = "en", **fmt) -> str:
    """The string for this key, formatted. A missing key shows itself rather than hiding."""
    entry = T.get(key)
    if entry is None:
        return f"⟨{key}⟩"
    s = entry.get(lang) or entry.get("en") or f"⟨{key}⟩"
    return s.format(**fmt) if fmt else s
