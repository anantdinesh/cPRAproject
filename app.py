import streamlit as st
import re

# --- CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="OPTN/UNOS cPRA Simulator",
    page_icon="🧮",
    layout="wide"
)

# Custom CSS to mimic the polished UI of the React app
st.markdown("""
<style>
    .big-font { font-size: 80px !important; font-weight: 900; line-height: 1; }
    .metric-label { font-size: 14px; font-weight: bold; color: #888; letter-spacing: 1px; text-transform: uppercase; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
    .priority-badge { background-color: #f3e8ff; color: #6b21a8; padding: 4px 12px; border-radius: 99px; font-weight: bold; font-size: 12px; border: 1px solid #d8b4fe; }
    .standard-badge { background-color: #f0fdf4; color: #15803d; padding: 4px 12px; border-radius: 99px; font-weight: bold; font-size: 12px; border: 1px solid #bbf7d0; }
    .high-badge { background-color: #fef2f2; color: #b91c1c; padding: 4px 12px; border-radius: 99px; font-weight: bold; font-size: 12px; border: 1px solid #fecaca; }
    .strategy-card { background-color: #1f2937; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #374151; }
</style>
""", unsafe_allow_html=True)

# --- DATASET (NMDP 2023 FREQUENCIES) ---
HLA_DATASET = {
    # --- HLA-A ---
    'A1': 0.240, 'A2': 0.479, 'A3': 0.220, 'A11': 0.100, 'A23': 0.070, 
    'A24': 0.174, 'A25': 0.040, 'A26': 0.080, 'A29': 0.070, 'A30': 0.080,
    'A31': 0.050, 'A32': 0.050, 'A33': 0.053, 'A34': 0.010, 'A36': 0.020,
    'A43': 0.001, 'A66': 0.030, 'A68': 0.110, 'A69': 0.005, 'A74': 0.020,
    'A80': 0.001,
    # --- HLA-B ---
    'B7': 0.214, 'B8': 0.170, 'B13': 0.040, 'B18': 0.090, 'B27': 0.070,
    'B35': 0.180, 'B37': 0.020, 'B38': 0.030, 'B39': 0.050, 'B41': 0.020,
    'B42': 0.020, 'B44': 0.240, 'B45': 0.030, 'B46': 0.001, 'B47': 0.010,
    'B48': 0.010, 'B49': 0.030, 'B50': 0.030, 'B51': 0.120, 'B52': 0.040,
    'B53': 0.060, 'B54': 0.010, 'B55': 0.040, 'B56': 0.020, 'B57': 0.060,
    'B58': 0.040, 'B59': 0.002, 'B60': 0.050, 'B61': 0.040, 'B62': 0.090,
    'B63': 0.010, 'B64': 0.010, 'B65': 0.010, 'B67': 0.001, 'B70': 0.001,
    'B71': 0.002, 'B72': 0.001, 'B73': 0.001, 'B75': 0.005, 'B76': 0.002,
    'B77': 0.001, 'B81': 0.010, 'B82': 0.001,
    # --- HLA-C ---
    'C1': 0.080, 'C2': 0.040, 'C3': 0.150, 'C4': 0.250, 'C5': 0.160,
    'C6': 0.190, 'C7': 0.490, 'C8': 0.080, 'C9': 0.060, 'C10': 0.100,
    'C12': 0.070, 'C14': 0.020, 'C15': 0.050, 'C16': 0.070, 'C17': 0.030,
    'C18': 0.010,
    # --- HLA-DRB1 ---
    'DR1': 0.180, 'DR3': 0.230, 'DR4': 0.320, 'DR7': 0.260, 'DR8': 0.060,
    'DR9': 0.020, 'DR10': 0.010, 'DR11': 0.180, 'DR12': 0.040, 'DR13': 0.220,
    'DR14': 0.050, 'DR15': 0.250, 'DR16': 0.020, 'DR17': 0.150, 'DR18': 0.010,
    # --- HLA-DR Associations ---
    'DR51': 0.270, 'DR52': 0.450, 'DR53': 0.350,
    # --- HLA-DQB1 ---
    'DQ2': 0.350, 'DQ3': 0.500, 'DQ4': 0.050, 'DQ5': 0.150, 'DQ6': 0.400,
    'DQ7': 0.300, 'DQ8': 0.200, 'DQ9': 0.100,
    'DQB1*02': 0.350, 'DQB1*03': 0.500, 'DQB1*04': 0.050, 'DQB1*05': 0.150, 
    'DQB1*06': 0.400,
    # --- HLA-DQA1 ---
    'DQA1*01': 0.350, 'DQA1*02': 0.080, 'DQA1*03': 0.300, 
    'DQA1*04': 0.150, 'DQA1*05': 0.400, 'DQA1*06': 0.020,
    # --- HLA-DPB1 ---
    'DPB1*01': 0.050, 'DPB1*02': 0.150, 'DPB1*03': 0.080, 'DPB1*04': 0.450,
    'DPB1*05': 0.050, 'DPB1*06': 0.020,
    # --- HLA-DPA1 ---
    'DPA1*01': 0.850, 'DPA1*02': 0.140, 'DPA1*03': 0.010,
}

LOCUS_INPUTS = [
    {'id': 'A', 'label': 'HLA-A'}, {'id': 'B', 'label': 'HLA-B'}, {'id': 'C', 'label': 'HLA-C'},
    {'id': 'DR', 'label': 'HLA-DR'}, 
    {'id': 'DQB1', 'label': 'HLA-DQB1'}, {'id': 'DQA1', 'label': 'HLA-DQA1'},
    {'id': 'DPB1', 'label': 'HLA-DPB1'}, {'id': 'DPA1', 'label': 'HLA-DPA1'},
]

# --- SESSION STATE ---
if 'unacceptable_antigens' not in st.session_state:
    st.session_state.unacceptable_antigens = []
if 'candidate_name' not in st.session_state:
    st.session_state.candidate_name = "Candidate #1042"

# --- LOGIC FUNCTIONS ---

def calculate_cpra(antigens):
    """Calculates CPRA based on independent probability."""
    prob_compatible = 1.0
    for ua in antigens:
        freq = 0
        if ua in HLA_DATASET:
            freq = HLA_DATASET[ua]
        else:
            # Fallback parsing for molecular types not explicitly in keys
            try:
                parts = ua.split('*')
                if len(parts) > 0:
                    locus = parts[0]
                    numeric_part = parts[1].split(':')[0] if len(parts) > 1 else ua.replace(locus, '').replace(r'\D', '')
                    
                    if numeric_part and locus:
                        broad_key = f"{locus}{numeric_part}"
                        if broad_key in HLA_DATASET:
                            freq = HLA_DATASET[broad_key]
                        # Try removing leading zeros (04 -> 4)
                        elif f"{locus}{int(numeric_part)}" in HLA_DATASET:
                            freq = HLA_DATASET[f"{locus}{int(numeric_part)}"]
            except Exception:
                pass
        
        # Rare allele assumption if recognized but 0 freq
        if freq == 0: freq = 0.001
        
        prob_compatible *= (1 - freq)
    
    cpra = (1 - prob_compatible) * 100
    return min(100, max(0, cpra))

def find_strategies(current_cpra, current_uas):
    """Finds single or double antigens to boost CPRA to > 99.5%."""
    if current_cpra < 95 or current_cpra >= 99.5:
        return []
    
    potentials = []
    candidates = [k for k in HLA_DATASET.keys() if k not in current_uas]
    
    # 1. Check Singles
    for antigen in candidates:
        freq = HLA_DATASET[antigen]
        current_prob = 1 - (current_cpra / 100)
        new_prob = current_prob * (1 - freq)
        new_score = (1 - new_prob) * 100
        
        if new_score >= 99.5:
            potentials.append({
                'antigens': [antigen], 'type': 'Single', 
                'newScore': new_score, 'gain': new_score - current_cpra
            })

    # 2. Check Combinations (Top 30 most frequent to save compute)
    sorted_candidates = sorted(candidates, key=lambda k: HLA_DATASET[k], reverse=True)[:30]
    for i in range(len(sorted_candidates)):
        for j in range(i + 1, len(sorted_candidates)):
            ag1 = sorted_candidates[i]
            ag2 = sorted_candidates[j]
            
            # Simple combined probability
            freq1 = HLA_DATASET[ag1]
            freq2 = HLA_DATASET[ag2]
            
            current_prob = 1 - (current_cpra / 100)
            new_prob = current_prob * (1 - freq1) * (1 - freq2)
            new_score = (1 - new_prob) * 100
            
            if new_score >= 99.5:
                 potentials.append({
                    'antigens': [ag1, ag2], 'type': 'Combination', 
                    'newScore': new_score, 'gain': new_score - current_cpra
                })
    
    # Sort by fewest antigens, then highest score
    potentials.sort(key=lambda x: (len(x['antigens']), -x['newScore']))
    return potentials[:20]

def parse_input_line(line):
    """Parses text like 'B: 18 39' or 'DQB1: 04' into valid tokens."""
    new_entries = []
    # Regex to find Locus followed by values
    match = re.match(r'^([A-Za-z0-9]+)\s*[:|-]?\s+(.*)', line.strip())
    
    if match:
        locus = match.group(1).upper()
        raw_values = match.group(2)
        values = re.split(r'[\s,;]+', raw_values)
        values = [v for v in values if v] # Filter empty
        
        # Normalize locus
        if locus == 'DQ': locus = 'DQB1'
        if locus == 'DP': locus = 'DPB1'
        
        for val in values:
            formatted = val
            
            # DR Associations
            if locus == 'DR' and val in ['51', '52', '53']:
                new_entries.append(f"DR{val}")
                continue
                
            # Molecular
            if locus in ['DQB1', 'DQA1', 'DPB1', 'DPA1']:
                if '*' not in val:
                    clean_val = re.sub(r'\D', '', val)
                    padded_val = f"0{clean_val}" if len(clean_val) == 1 else clean_val
                    suffix = val if ':' in val else padded_val
                    formatted = f"{locus}*{suffix}"
                else:
                    formatted = val if val.startswith(locus) else f"{locus}{val}"
            
            # Class I and Broad DR
            elif locus in ['A', 'B', 'C', 'DR']:
                if ':' in val or '*' in val:
                    formatted = val if val.startswith(locus) else f"{locus}*{val}"
                else:
                    formatted = val if val.startswith(locus) else f"{locus}{val}"
            
            new_entries.append(formatted)
            
    return new_entries

# --- EVENT HANDLERS ---
def add_antigens(antigens):
    current = set(st.session_state.unacceptable_antigens)
    for ag in antigens:
        current.add(ag)
    st.session_state.unacceptable_antigens = list(current)

def clear_all():
    st.session_state.unacceptable_antigens = []

def process_bulk_text():
    # Use session_state to get the widget value directly
    if "bulk_input_text" in st.session_state:
        text = st.session_state.bulk_input_text
        if text:
            lines = text.split('\n')
            results = []
            for line in lines:
                results.extend(parse_input_line(line))
            add_antigens(results)
            # Safely clear the input in session state because we are inside a callback
            st.session_state.bulk_input_text = "" 

def toggle_dr_special(antigen):
    if antigen in st.session_state.unacceptable_antigens:
        st.session_state.unacceptable_antigens.remove(antigen)
    else:
        st.session_state.unacceptable_antigens.append(antigen)

# --- MAIN UI ---

# Header
col_head_1, col_head_2 = st.columns([3, 1])
with col_head_1:
    st.title("🧮 OPTN/UNOS cPRA Simulator")
    st.caption("NMDP 2023 Frequency Data • Independent Probability Model")
with col_head_2:
    st.text_input("Candidate Name", key="candidate_name")

st.divider()

# Main Layout
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    # --- INPUT SECTION ---
    tab_bulk, tab_grid = st.tabs(["📋 Bulk Paste", "⌨️ Manual Grid"])
    
    with tab_bulk:
        st.markdown("**Paste from Lab Report** (Format: `Locus: Val Val`)")
        st.text_area(
            "Bulk Input", 
            height=150, 
            placeholder="B: 18 39 41\nDR: 01:03 15\nDQB1: 4 5 6",
            key="bulk_input_text",
            label_visibility="collapsed"
        )
        # FIX: Use on_click callback to process text and clear input safely
        st.button("Process & Add", type="primary", on_click=process_bulk_text)

    with tab_grid:
        st.markdown("**Check Special Associations**")
        c1, c2, c3 = st.columns(3)
        with c1: st.checkbox("DR51", value="DR51" in st.session_state.unacceptable_antigens, on_change=toggle_dr_special, args=("DR51",))
        with c2: st.checkbox("DR52", value="DR52" in st.session_state.unacceptable_antigens, on_change=toggle_dr_special, args=("DR52",))
        with c3: st.checkbox("DR53", value="DR53" in st.session_state.unacceptable_antigens, on_change=toggle_dr_special, args=("DR53",))
        
        st.markdown("---")
        
        # Grid Inputs
        # We use a form to prevent reload on every character type
        with st.form("grid_form"):
            grid_cols = st.columns(3)
            new_grid_vals = {}
            for idx, locus in enumerate(LOCUS_INPUTS):
                with grid_cols[idx % 3]:
                    new_grid_vals[locus['id']] = st.text_input(locus['label'], placeholder="e.g. 2, 24")
            
            if st.form_submit_button("Add Grid Values"):
                batch_add = []
                for lid, val in new_grid_vals.items():
                    if val.strip():
                        # Reuse parse logic by faking the "Locus: Val" format
                        batch_add.extend(parse_input_line(f"{lid}: {val}"))
                add_antigens(batch_add)
                st.rerun() # Force update after form submit

    # --- ACTIVE EXCLUSIONS ---
    st.markdown("### Active Exclusions")
    if st.session_state.unacceptable_antigens:
        # Multiselect acts as a chip display that allows deletion
        updated_list = st.multiselect(
            "Manage Antigens",
            options=st.session_state.unacceptable_antigens,
            default=st.session_state.unacceptable_antigens,
            label_visibility="collapsed"
        )
        
        # Detect removals
        if len(updated_list) != len(st.session_state.unacceptable_antigens):
            st.session_state.unacceptable_antigens = updated_list
            st.rerun()
            
        if st.button("Clear All Antigens", type="secondary"):
            clear_all()
            st.rerun()
    else:
        st.info("No antigens entered. Use Bulk Paste or Grid to add.")

with right_col:
    # --- DASHBOARD ---
    
    # Calculate
    cpra_val = calculate_cpra(st.session_state.unacceptable_antigens)
    
    # Visualization Container
    st.markdown('<div style="background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">', unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="metric-label" style="text-align: center;">Estimated cPRA</div>', unsafe_allow_html=True)
    
    # Big Number
    color_class = "text-red-600" if cpra_val > 98 else "text-blue-600"
    st.markdown(f'<div class="big-font" style="text-align: center; color: #111827;">{cpra_val:.1f}<span style="font-size: 40px; color: #9ca3af;">%</span></div>', unsafe_allow_html=True)
    
    # Badges
    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        badge_html = ""
        if cpra_val > 98:
            badge_html += '<span class="high-badge">Highly Sensitized</span> '
        else:
            badge_html += '<span class="standard-badge">Standard Allocation</span> '
            
        if cpra_val >= 99.5:
            badge_html += '<span class="priority-badge">⚡ National Priority</span>'
            
        st.markdown(f'<div style="text-align: center; margin-bottom: 20px;">{badge_html}</div>', unsafe_allow_html=True)

    # Progress Bar
    bar_color = "red" if cpra_val > 98 else "blue"
    st.progress(cpra_val / 100)
    st.caption(f"{cpra_val:.4f}% exact calculation.")
    
    st.markdown('</div>', unsafe_allow_html=True) # End card

    # Disclaimer
    st.warning("**EDUCATIONAL USE ONLY:** This tool uses independent probability products of 2023 NMDP Antigen Frequencies. It approximates the official OPTN calculator.")

    # --- STRATEGY ENGINE ---
    
    # Calculate strategies
    strategies = find_strategies(cpra_val, st.session_state.unacceptable_antigens)
    
    if 95 <= cpra_val < 99.5:
        st.markdown("### ⚡ Priority Optimizer")
        st.caption(f"Pathways to >99.5% National Sharing ({len(strategies)} Options)")
        
        with st.container(height=400):
            if not strategies:
                st.write("No single or double antigen combinations found to reach 99.5%.")
            
            for idx, strat in enumerate(strategies):
                # Using a container for card-like look
                with st.container():
                    cols = st.columns([3, 1])
                    
                    with cols[0]:
                        antigen_str = " + ".join(strat['antigens'])
                        st.markdown(f"**{antigen_str}**")
                        st.caption(f"New cPRA: {strat['newScore']:.4f}% (Gain: +{strat['gain']:.3f}%)")
                    
                    with cols[1]:
                        if st.button("ADD", key=f"add_{idx}"):
                            add_antigens(strat['antigens'])
                            st.rerun()
                    st.divider()
                    
    elif cpra_val >= 99.5:
        st.success("✅ **Optimization Complete.** Patient is already National Priority eligible.")
    else:
        st.markdown("""
        <div style="border: 2px dashed #e5e7eb; border-radius: 12px; padding: 2rem; text-align: center; opacity: 0.6;">
            <h4>Optimizer Inactive</h4>
            <p>Available when cPRA is between 95% and 99.5%.</p>
        </div>
        """, unsafe_allow_html=True)
