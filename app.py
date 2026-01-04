import streamlit as st
import re
from itertools import combinations

st.set_page_config(
    page_title="OPTN / UNOS cPRA Simulator",
    layout="wide",
)

# =========================================================
# HLA FREQUENCY DATA (NMDP 2023 – Approximate)
# =========================================================
HLA_DATASET = {
    # HLA-A
    "A1": 0.240, "A2": 0.479, "A3": 0.220, "A11": 0.100, "A23": 0.070,
    "A24": 0.174, "A25": 0.040, "A26": 0.080, "A29": 0.070, "A30": 0.080,
    "A31": 0.050, "A32": 0.050, "A33": 0.053, "A34": 0.010, "A36": 0.020,
    "A43": 0.001, "A66": 0.030, "A68": 0.110, "A69": 0.005, "A74": 0.020,
    "A80": 0.001,

    # HLA-B
    "B7": 0.214, "B8": 0.170, "B13": 0.040, "B18": 0.090, "B27": 0.070,
    "B35": 0.180, "B37": 0.020, "B38": 0.030, "B39": 0.050, "B41": 0.020,
    "B42": 0.020, "B44": 0.240, "B45": 0.030, "B46": 0.001, "B47": 0.010,
    "B48": 0.010, "B49": 0.030, "B50": 0.030, "B51": 0.120, "B52": 0.040,
    "B53": 0.060, "B54": 0.010, "B55": 0.040, "B56": 0.020, "B57": 0.060,
    "B58": 0.040, "B59": 0.002, "B60": 0.050, "B61": 0.040, "B62": 0.090,

    # HLA-C
    "C1": 0.080, "C2": 0.040, "C3": 0.150, "C4": 0.250, "C5": 0.160,
    "C6": 0.190, "C7": 0.490, "C8": 0.080, "C9": 0.060, "C10": 0.100,

    # DR
    "DR1": 0.180, "DR3": 0.230, "DR4": 0.320, "DR7": 0.260,
    "DR11": 0.180, "DR13": 0.220, "DR15": 0.250,

    "DR51": 0.270, "DR52": 0.450, "DR53": 0.350,

    # DQ
    "DQ2": 0.350, "DQ3": 0.500, "DQ4": 0.050, "DQ5": 0.150, "DQ6": 0.400,
    "DQ7": 0.300, "DQ8": 0.200,
}

# =========================================================
# Helper Functions
# =========================================================
def normalize_antigen(ag):
    ag = ag.strip().upper()
    if "*" in ag:
        locus, num = ag.split("*", 1)
        num = num.split(":")[0]
        return f"{locus}{int(num)}"
    return ag

def calculate_cpra(unacceptable):
    prob_compatible = 1.0
    for ag in unacceptable:
        ag_norm = normalize_antigen(ag)
        freq = HLA_DATASET.get(ag_norm, 0.001)
        prob_compatible *= (1 - freq)
    return min(100.0, max(0.0, (1 - prob_compatible) * 100))

def parse_bulk(text):
    results = []
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z0-9]+)\s*[:\-]?\s+(.*)", line.strip())
        if not m:
            continue
        locus = m.group(1).upper()
        vals = re.split(r"[,\s;]+", m.group(2))

        if locus == "DQ":
            locus = "DQB1"
        if locus == "DP":
            locus = "DPB1"

        for v in vals:
            v = v.strip()
            if not v:
                continue
            if locus == "DR" and v in {"51", "52", "53"}:
                results.append(f"DR{v}")
            elif locus in {"A", "B", "C", "DR"}:
                results.append(v if v.startswith(locus) else f"{locus}{v}")
            else:
                results.append(f"{locus}*{v}")
    return list(set(results))

def optimizer(cpra, unacceptable):
    if cpra < 95 or cpra >= 99.5:
        return []

    current_prob = 1 - cpra / 100
    candidates = [k for k in HLA_DATASET if k not in unacceptable]
    results = []

    for ag in candidates:
        freq = HLA_DATASET[ag]
        new_cpra = (1 - current_prob * (1 - freq)) * 100
        if new_cpra >= 99.5:
            results.append(( [ag], new_cpra, new_cpra - cpra ))

    for a, b in combinations(candidates[:30], 2):
        new_cpra = (1 - current_prob * (1 - HLA_DATASET[a]) * (1 - HLA_DATASET[b])) * 100
        if new_cpra >= 99.5:
            results.append(([a, b], new_cpra, new_cpra - cpra))

    return sorted(results, key=lambda x: (len(x[0]), -x[1]))[:20]

# =========================================================
# UI
# =========================================================
st.title("🧮 OPTN / UNOS cPRA Simulator")
st.caption("Educational simulator using independent NMDP 2023 antigen frequencies")

if "unacceptable" not in st.session_state:
    st.session_state.unacceptable = ["A2", "B7"]

col1, col2 = st.columns(2)

with col1:
    st.subheader("🧾 Antigen Entry")

    mode = st.radio("Input Mode", ["Bulk Paste", "Manual Add"])

    if mode == "Bulk Paste":
        bulk = st.text_area(
            "Paste lab report",
            placeholder="B: 18 39\nDR: 15 51\nDQB1: 4 6"
        )
        if st.button("Process"):
            st.session_state.unacceptable = list(
                set(st.session_state.unacceptable + parse_bulk(bulk))
            )

    else:
        new_ag = st.text_input("Enter antigen (e.g. A2, B44, DR51, DQB1*06)")
        if st.button("Add Antigen"):
            if new_ag:
                st.session_state.unacceptable.append(new_ag.upper())

    st.markdown("### ❌ Active Unacceptable Antigens")
    for ag in sorted(set(st.session_state.unacceptable)):
        if st.button(f"Remove {ag}", key=ag):
            st.session_state.unacceptable.remove(ag)

    if st.button("Clear All"):
        st.session_state.unacceptable = []

with col2:
    cpra = calculate_cpra(st.session_state.unacceptable)

    st.subheader("📊 Estimated cPRA")
    st.metric("cPRA (%)", f"{cpra:.2f}")

    st.progress(min(cpra / 100, 1.0))

    if cpra >= 99.5:
        st.success("🏅 National Priority Eligible")
    elif cpra >= 98:
        st.warning("⚠️ Highly Sensitized")
    else:
        st.info("Standard Allocation")

    st.markdown("### ⚡ Priority Optimizer")
    opts = optimizer(cpra, st.session_state.unacceptable)

    if opts:
        for ags, new_cpra, gain in opts:
            st.write(
                f"➕ **{', '.join(ags)}** → {new_cpra:.3f}% "
                f"(+{gain:.3f}%)"
            )
            if st.button(f"Add {','.join(ags)}", key=str(ags)):
                st.session_state.unacceptable += ags
    else:
        st.caption("No optimization pathways available.")

st.markdown("---")
st.caption(
    "⚠️ Educational tool only. Does not replicate OPTN proprietary haplotype covariance model."
)
