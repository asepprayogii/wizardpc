import streamlit as st
import pandas as pd
import re

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PC Wizard Pro", layout="wide", page_icon="🖥️")

# --- CSS CUSTOM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

    .bundle-card {
        border: 1.5px solid #e0e0e0;
        border-radius: 14px;
        padding: 18px;
        background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
        margin-bottom: 16px;
        transition: all 0.25s ease;
        height: 100%;
    }
    .bundle-card:hover {
        box-shadow: 0 8px 24px rgba(30, 136, 229, 0.15);
        border-color: #1E88E5;
        transform: translateY(-4px);
    }
    .price-text {
        color: #1565C0;
        font-size: 20px;
        font-weight: 700;
        margin: 8px 0 4px 0;
    }
    .bundle-title {
        color: #1a1a2e;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .badge {
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }
    .badge-stock { background: #E3F2FD; color: #1565C0; }
    .badge-price { background: #E8F5E9; color: #2E7D32; }
    .badge-smart { background: #FFF3E0; color: #E65100; }
    .mode-card {
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 14px 18px;
        cursor: pointer;
        transition: all 0.2s;
        text-align: center;
        background: white;
    }
    .mode-card.active {
        border-color: #1E88E5;
        background: #E3F2FD;
    }
    .part-row {
        border: 1px solid #eef2f7;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        background: #fafbff;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .category-label {
        font-size: 11px;
        color: #888;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .part-name {
        font-size: 14px;
        font-weight: 500;
        color: #1a1a2e;
    }
    .part-price {
        font-size: 13px;
        color: #1E88E5;
        font-weight: 600;
    }
    .summary-box {
        background: linear-gradient(135deg, #1565C0, #1E88E5);
        border-radius: 14px;
        padding: 20px;
        color: white;
    }
    .total-price {
        font-size: 26px;
        font-weight: 700;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNGSI HELPER
# ============================================================

def extract_ram_gb(name):
    name = name.upper()
    match = re.search(r'(\d+)\s*GB', name)
    if match:
        return int(match.group(1))
    return 0


def extract_ddr_type(name):
    name = name.upper()
    match = re.search(r'DDR(\d)', name)
    if match:
        return f"DDR{match.group(1)}"
    return None


def get_cpu_info(name):
    """Ekstrak info CPU Intel only."""
    name = name.upper()
    info = {
        "brand": "INTEL",
        "gen": None,
        "socket": None,
        "is_f_type": False,
        "is_tray": False,
        "tier": None
    }

    # Deteksi Intel Ultra
    if "ULTRA" in name:
        info["gen"] = "ULTRA"
        info["tier"] = "ULTRA"
        info["is_f_type"] = True
        if "TRAY" in name or "NO FAN" in name:
            info["is_tray"] = True
        return info

    # Tier i3/i5/i7/i9
    tier_match = re.search(r'\bI([3579])\b', name)
    if tier_match:
        info["tier"] = f"I{tier_match.group(1)}"

    # Generasi dari model number
    gen_match = re.search(r'I[3579]-(\d{2,2})\d{2,3}', name)
    if gen_match:
        info["gen"] = int(gen_match.group(1))
    else:
        model_match = re.search(r'\b(1[0-9])(\d{3})\b', name)
        if model_match:
            info["gen"] = int(model_match.group(1))

    # Tipe F (butuh VGA)
    if re.search(r'\d{3,4}F\b', name):
        info["is_f_type"] = True

    # Tray (butuh CPU Cooler)
    if "TRAY" in name or "NO FAN" in name:
        info["is_tray"] = True

    return info


def is_mobo_compatible(cpu_info, mobo_series):
    gen = cpu_info["gen"]

    if gen == 10:
        return mobo_series in ["H410", "H510"]
    if gen == 11:
        return mobo_series in ["H510"]
    if gen in [12, 13, 14]:
        return mobo_series in ["H610", "B660", "B760", "Z790"]
    if gen == "ULTRA":
        return mobo_series in ["H810", "B860", "Z890"]

    return True


def get_mobo_series(name):
    name = name.upper()
    series_list = [
        "H410", "H510", "H610", "H810",
        "B660", "B760", "B860",
        "Z790", "Z890",
        "A520", "A620",
        "B450", "B550",
        "B650", "B840", "B850",
        "X870"
    ]
    for s in series_list:
        if s in name:
            return s
    return None


def get_mobo_category(series, price):
    h_series = ["H410", "H510", "H610", "H810"]
    amd_a_series = ["A520", "A620"]
    b_series_intel = ["B660", "B760", "B860"]
    z_series_intel = ["Z790", "Z890"]
    b_series_amd = ["B450", "B550", "B650", "B840", "B850"]
    x_series_amd = ["X870"]

    cats = {"office": False, "standar": False, "advance": False}

    if series in h_series:
        cats["office"] = True
    elif series in amd_a_series:
        cats["office"] = True
    elif series in b_series_intel:
        if price < 2_000_000:
            cats["standar"] = True
        else:
            cats["advance"] = True
    elif series in z_series_intel:
        cats["advance"] = True
    elif series in b_series_amd:
        cats["standar"] = True
        cats["advance"] = True
    elif series in x_series_amd:
        cats["advance"] = True

    return cats


def get_vga_category(name):
    name = name.upper()
    cats = {"office": False, "standar": False, "advance": False}

    office_series = ["GT710", "GT730"]
    standar_series = ["GT1030", "GTX1650", "RTX3050", "RTX3060", "RTX5050", "RTX4060"]
    advance_series = ["RTX5060TI", "RTX5060 TI", "RTX5070TI", "RTX5070 TI", "RTX5080", "RTX5090"]

    if any(s in name for s in office_series):
        cats["office"] = True
        return cats

    if any(s in name for s in advance_series):
        cats["advance"] = True
        return cats

    if "RTX5060" in name and "TI" not in name:
        cats["advance"] = True
        return cats

    if "RTX5070" in name and "TI" not in name:
        cats["advance"] = True
        return cats

    if any(s in name for s in standar_series):
        cats["standar"] = True
        return cats

    if re.search(r'RTX\s*\d*[56]0\b', name):
        cats["standar"] = True
        return cats

    if re.search(r'RTX\s*\d*[789]\d\b', name):
        cats["advance"] = True
        return cats

    cats["standar"] = True
    return cats


# ============================================================
# FUNGSI PROCESS DATA UTAMA
# ============================================================

def process_data(df):
    df = df.copy()

    df['Web'] = pd.to_numeric(df['Web'], errors='coerce').fillna(0)
    df = df[df['Stock Total'] > 0].copy()
    df = df[df['Web'] > 0].copy()
    df['Nama Accurate'] = df['Nama Accurate'].fillna('').astype(str)
    df['Kategori'] = df['Kategori'].fillna('').astype(str)

    df['cat_office'] = False
    df['cat_standar'] = False
    df['cat_advance'] = False

    df['need_vga'] = 0
    df['has_psu'] = 0
    df['need_cooler'] = 0
    df['cpu_gen'] = None
    df['cpu_socket'] = None
    df['cpu_brand'] = None
    df['cpu_tier'] = None
    df['cpu_is_f'] = False
    df['cpu_is_tray'] = False
    df['mobo_series'] = None
    df['mobo_ddr'] = None
    df['ram_ddr'] = None

    # --------------------------------------------------------
    # 1. PROCESSOR — Intel Only (skip AMD)
    # --------------------------------------------------------
    proc_mask = df['Kategori'] == 'Processor'

    for idx in df[proc_mask].index:
        name = df.at[idx, 'Nama Accurate'].upper()

        # Skip AMD processor
        if "RYZEN" in name or ("AMD" in name and "INTEL" not in name):
            continue

        cpu = get_cpu_info(name)

        df.at[idx, 'cpu_brand'] = cpu['brand']
        df.at[idx, 'cpu_gen'] = cpu['gen']
        df.at[idx, 'cpu_socket'] = cpu['socket']
        df.at[idx, 'cpu_tier'] = cpu['tier']
        df.at[idx, 'cpu_is_f'] = cpu['is_f_type']
        df.at[idx, 'cpu_is_tray'] = cpu['is_tray']
        df.at[idx, 'need_vga'] = 1 if cpu['is_f_type'] else 0
        df.at[idx, 'need_cooler'] = 1 if cpu['is_tray'] else 0

        tier = cpu['tier']
        is_f = cpu['is_f_type']

        if tier in ["I3", "I5"] and not is_f:
            df.at[idx, 'cat_office'] = True
        if tier in ["I3", "I5"] and is_f:
            df.at[idx, 'cat_standar'] = True
        if tier in ["I7", "I9"] and is_f:
            df.at[idx, 'cat_advance'] = True
        if tier == "ULTRA":
            df.at[idx, 'cat_advance'] = True

    # --------------------------------------------------------
    # 2. MOTHERBOARD
    # --------------------------------------------------------
    mb_mask = df['Kategori'] == 'Motherboard'

    for idx in df[mb_mask].index:
        name = df.at[idx, 'Nama Accurate'].upper()
        series = get_mobo_series(name)
        price = df.at[idx, 'Web']
        df.at[idx, 'mobo_series'] = series

        if series:
            cats = get_mobo_category(series, price)
            df.at[idx, 'cat_office'] = cats['office']
            df.at[idx, 'cat_standar'] = cats['standar']
            df.at[idx, 'cat_advance'] = cats['advance']
        else:
            df.at[idx, 'cat_office'] = True
            df.at[idx, 'cat_standar'] = True
            df.at[idx, 'cat_advance'] = True

        ddr = extract_ddr_type(name)
        df.at[idx, 'mobo_ddr'] = ddr

    # --------------------------------------------------------
    # 3. RAM — Filter SODIMM
    # --------------------------------------------------------
    ram_mask = df['Kategori'] == 'Memory RAM'
    sodimm_mask = df['Nama Accurate'].str.upper().str.contains('SODIMM', na=False)
    df = df[~(ram_mask & sodimm_mask)].copy()

    ram_mask = df['Kategori'] == 'Memory RAM'
    for idx in df[ram_mask].index:
        name = df.at[idx, 'Nama Accurate']
        gb = extract_ram_gb(name)
        ddr = extract_ddr_type(name)
        df.at[idx, 'ram_ddr'] = ddr

        if 8 <= gb <= 16:
            df.at[idx, 'cat_office'] = True
        if 16 <= gb <= 32:
            df.at[idx, 'cat_standar'] = True
        if 32 <= gb <= 64:
            df.at[idx, 'cat_advance'] = True
        if gb == 0:
            df.at[idx, 'cat_office'] = True
            df.at[idx, 'cat_standar'] = True
            df.at[idx, 'cat_advance'] = True

    # --------------------------------------------------------
    # 4. SSD Internal
    # --------------------------------------------------------
    ssd_mask = df['Kategori'] == 'SSD Internal'
    exclude_ssd = df['Nama Accurate'].str.upper().str.contains('WDS120G2GOB', na=False)
    df = df[~(ssd_mask & exclude_ssd)].copy()

    ssd_mask = df['Kategori'] == 'SSD Internal'
    for idx in df[ssd_mask].index:
        name = df.at[idx, 'Nama Accurate'].upper()
        df.at[idx, 'cat_office'] = True
        df.at[idx, 'cat_standar'] = True
        if 'NVME' in name or 'M.2' in name or 'M2' in name:
            df.at[idx, 'cat_advance'] = True

    # --------------------------------------------------------
    # 5. VGA
    # --------------------------------------------------------
    vga_mask = df['Kategori'] == 'VGA'
    for idx in df[vga_mask].index:
        name = df.at[idx, 'Nama Accurate']
        cats = get_vga_category(name)
        df.at[idx, 'cat_office'] = cats['office']
        df.at[idx, 'cat_standar'] = cats['standar']
        df.at[idx, 'cat_advance'] = cats['advance']

    # --------------------------------------------------------
    # 6. CASING PC
    # --------------------------------------------------------
    casing_mask = df['Kategori'] == 'Casing PC'
    armageddon_mask = df['Nama Accurate'].str.upper().str.contains('ARMAGEDDON', na=False)
    df = df[~(casing_mask & armageddon_mask)].copy()

    casing_mask = df['Kategori'] == 'Casing PC'
    for idx in df[casing_mask].index:
        name = df.at[idx, 'Nama Accurate'].upper()
        df.at[idx, 'cat_office'] = True
        df.at[idx, 'cat_standar'] = True
        df.at[idx, 'cat_advance'] = True

        if 'PSU' in name or 'VALCAS' in name:
            df.at[idx, 'has_psu'] = 1

    # --------------------------------------------------------
    # 7. POWER SUPPLY
    # --------------------------------------------------------
    psu_mask = df['Kategori'] == 'Power Supply'
    for idx in df[psu_mask].index:
        price = df.at[idx, 'Web']
        name = df.at[idx, 'Nama Accurate'].upper()

        if price < 500_000:
            df.at[idx, 'cat_office'] = True
        if price >= 500_000:
            df.at[idx, 'cat_standar'] = True
        if any(label in name for label in ['BRONZE', 'GOLD', 'PLATINUM']):
            df.at[idx, 'cat_advance'] = True

    # --------------------------------------------------------
    # 8. CPU COOLER
    # --------------------------------------------------------
    cooler_mask = df['Kategori'] == 'CPU Cooler'
    for idx in df[cooler_mask].index:
        price = df.at[idx, 'Web']
        if price < 300_000:
            df.at[idx, 'cat_office'] = True
        if 250_000 <= price <= 1_000_000:
            df.at[idx, 'cat_standar'] = True
        if price > 500_000:
            df.at[idx, 'cat_advance'] = True

    return df


# ============================================================
# FUNGSI BUNDLING
# ============================================================

def sorted_items(items, mode, branch_col):
    if items.empty:
        return items
    if mode == 'stok_terbanyak':
        return items.sort_values(branch_col, ascending=False)
    elif mode == 'harga_termurah':
        return items.sort_values('Web', ascending=True)
    elif mode == 'smart_pick':
        cheapest_price = items['Web'].min()
        in_range = items[items['Web'] <= cheapest_price + 100_000]
        return in_range.sort_values(branch_col, ascending=False)
    return items


def build_bundle(available, branch_col, mode, variant_idx):
    def pick(items):
        ranked = sorted_items(items, mode, branch_col)
        if ranked.empty:
            return None
        idx = min(variant_idx, len(ranked) - 1)
        return ranked.iloc[idx]

    bundle = {}

    procs = available[available['Kategori'] == 'Processor']
    proc = pick(procs)
    if proc is None:
        return None
    bundle['Processor'] = proc

    mobos = available[available['Kategori'] == 'Motherboard']
    cpu_info = {
        'brand': proc.get('cpu_brand', 'INTEL'),
        'gen':   proc.get('cpu_gen', None),
        'socket':proc.get('cpu_socket', None),
    }
    compatible_mobos = mobos[mobos['mobo_series'].apply(
        lambda s: is_mobo_compatible(cpu_info, s)
    )]
    mobo = pick(compatible_mobos)
    if mobo is None:
        return None
    bundle['Motherboard'] = mobo

    rams = available[available['Kategori'] == 'Memory RAM']
    mobo_ddr = mobo.get('mobo_ddr', None)
    if mobo_ddr:
        rams_compatible = rams[rams['ram_ddr'] == mobo_ddr]
        if not rams_compatible.empty:
            rams = rams_compatible
    ram = pick(rams)
    if ram is not None:
        bundle['Memory RAM'] = ram

    ssds = available[available['Kategori'] == 'SSD Internal']
    ssd = pick(ssds)
    if ssd is not None:
        bundle['SSD Internal'] = ssd

    if proc.get('need_vga', 0) == 1:
        vgas = available[available['Kategori'] == 'VGA']
        vga = pick(vgas)
        if vga is not None:
            bundle['VGA'] = vga

    casings = available[available['Kategori'] == 'Casing PC']
    casing = pick(casings)
    if casing is not None:
        bundle['Casing PC'] = casing

    casing_has_psu = (casing is not None and casing.get('has_psu', 0) == 1)
    if not casing_has_psu:
        psus = available[available['Kategori'] == 'Power Supply']
        psu = pick(psus)
        if psu is not None:
            bundle['Power Supply'] = psu

    if proc.get('need_cooler', 0) == 1:
        coolers = available[available['Kategori'] == 'CPU Cooler']
        cooler = pick(coolers)
        if cooler is not None:
            bundle['CPU Cooler'] = cooler

    total = sum(item['Web'] for item in bundle.values())
    return {"parts": bundle, "total": total}


def rebuild_from_processor(proc, available, branch_col):
    def pick_first(items):
        return sorted_items(items, 'harga_termurah', branch_col).iloc[0] if not items.empty else None

    bundle = {'Processor': proc}

    mobos = available[available['Kategori'] == 'Motherboard']
    cpu_info = {'brand': proc.get('cpu_brand','INTEL'), 'gen': proc.get('cpu_gen',None), 'socket': proc.get('cpu_socket',None)}
    compatible = mobos[mobos['mobo_series'].apply(lambda s: is_mobo_compatible(cpu_info, s))]
    mobo = pick_first(compatible)
    if mobo is None:
        return None
    bundle['Motherboard'] = mobo

    rams = available[available['Kategori'] == 'Memory RAM']
    mobo_ddr = mobo.get('mobo_ddr', None)
    if mobo_ddr:
        rams_compat = rams[rams['ram_ddr'] == mobo_ddr]
        if not rams_compat.empty:
            rams = rams_compat
    ram = pick_first(rams)
    if ram is not None:
        bundle['Memory RAM'] = ram

    ssd = pick_first(available[available['Kategori'] == 'SSD Internal'])
    if ssd is not None:
        bundle['SSD Internal'] = ssd

    if proc.get('need_vga', 0) == 1:
        vga = pick_first(available[available['Kategori'] == 'VGA'])
        if vga is not None:
            bundle['VGA'] = vga

    casing = pick_first(available[available['Kategori'] == 'Casing PC'])
    if casing is not None:
        bundle['Casing PC'] = casing

    if not (casing is not None and casing.get('has_psu', 0) == 1):
        psu = pick_first(available[available['Kategori'] == 'Power Supply'])
        if psu is not None:
            bundle['Power Supply'] = psu

    if proc.get('need_cooler', 0) == 1:
        cooler = pick_first(available[available['Kategori'] == 'CPU Cooler'])
        if cooler is not None:
            bundle['CPU Cooler'] = cooler

    return bundle


def rebuild_from_mobo(mobo, current_bundle, available, branch_col):
    bundle = dict(current_bundle)
    bundle['Motherboard'] = mobo

    rams = available[available['Kategori'] == 'Memory RAM']
    mobo_ddr = mobo.get('mobo_ddr', None)
    if mobo_ddr:
        rams_compat = rams[rams['ram_ddr'] == mobo_ddr]
        if not rams_compat.empty:
            rams = rams_compat
    if not rams.empty:
        bundle['Memory RAM'] = rams.sort_values('Web').iloc[0]

    return bundle


def rebuild_from_casing(casing, current_bundle, available, branch_col):
    bundle = dict(current_bundle)
    bundle['Casing PC'] = casing

    if casing.get('has_psu', 0) == 1:
        bundle.pop('Power Supply', None)
    else:
        if 'Power Supply' not in bundle:
            psus = available[available['Kategori'] == 'Power Supply']
            if not psus.empty:
                bundle['Power Supply'] = psus.sort_values('Web').iloc[0]

    return bundle


def generate_bundles(df, branch_col, cat_col, price_min=0, price_max=0):
    available = df[(df[branch_col] > 0) & (df[cat_col] == True)].copy()
    use_price_filter = not (price_min == 0 and price_max == 0)

    modes = [
        {
            "key": "stok_terbanyak",
            "label": "Stok Terbanyak",
            "desc": "Produk dengan stok terbanyak dari setiap kategori",
            "badge": "badge-stock",
            "variants": ["#1 Stok Tertinggi", "#2 Stok Tinggi", "#3 Stok Cukup"],
        },
        {
            "key": "harga_termurah",
            "label": "Harga Termurah",
            "desc": "Produk dengan harga termurah dari setiap kategori",
            "badge": "badge-price",
            "variants": ["#1 Termurah", "#2 Budget", "#3 Ekonomis"],
        },
        {
            "key": "smart_pick",
            "label": "Smart Pick",
            "desc": "Harga termurah + range 100rb — stok terbanyak dalam range",
            "badge": "badge-smart",
            "variants": ["#1 Smart", "#2 Smart", "#3 Smart"],
        },
    ]

    grouped = []
    for m in modes:
        group = {"label": m["label"], "desc": m["desc"], "badge": m["badge"], "cards": []}
        for v_idx in range(3):
            bundle = build_bundle(available, branch_col, m["key"], v_idx)
            if bundle:
                in_range = True
                if use_price_filter:
                    in_range = price_min <= bundle["total"] <= price_max
                card = {
                    "name": m["variants"][v_idx],
                    "badge": m["badge"],
                    "in_range": in_range,
                    **bundle
                }
                group["cards"].append(card)
        grouped.append(group)

    return grouped


# ============================================================
# MAIN APP
# ============================================================

st.title("PC Wizard Pro")
st.caption("Sistem Rekomendasi Bundling PC Otomatis")

# Session state init
if 'view' not in st.session_state:
    st.session_state.view = 'main'
if 'selected_bundle' not in st.session_state:
    st.session_state.selected_bundle = None
if 'prev_usage_label' not in st.session_state:
    st.session_state.prev_usage_label = None

uploaded_file = st.file_uploader("Upload Data Portal (CSV atau XLSX)", type=["csv", "xlsx"])

if uploaded_file:
    with st.spinner("Memproses data..."):
        raw_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        data = process_data(raw_df)

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------
    st.sidebar.header("Konfigurasi")

    branch_map = {
        "Surabaya": ["Stock A - ITC", "Stock B", "Stock Y - SBY"],
        "Jakarta":  ["Stock C6"],
        "Semarang": ["Stock D - SMG"],
        "Jogja":    ["Stock E - JOG"],
        "Malang":   ["Stock F - MLG"],
        "Bali":     ["Stock H - BALI"],
    }

    selected_branch = st.sidebar.selectbox("Cabang", list(branch_map.keys()), index=0)
    branch_cols = branch_map[selected_branch]

    if selected_branch == "Surabaya":
        data['_stock_branch'] = data[branch_cols].sum(axis=1)
    else:
        data['_stock_branch'] = data[branch_cols[0]]
    branch_col = '_stock_branch'

    usage_options = {
        "Office":    "cat_office",
        "Standar":   "cat_standar",
        "Advance":   "cat_advance"
    }
    usage_label = st.sidebar.radio(
        "Kategori Penggunaan",
        list(usage_options.keys()),
        format_func=lambda x: {
            "Office":  "Office (< 10 jt)",
            "Standar": "Standar (10 - 20 jt)",
            "Advance": "Advance (> 20 jt)"
        }[x]
    )

    # FIX 1: Reset ke main view jika kategori penggunaan berubah
    if st.session_state.prev_usage_label is not None and st.session_state.prev_usage_label != usage_label:
        st.session_state.view = 'main'
        st.session_state.selected_bundle = None
        if 'ganti_cat' in st.session_state:
            st.session_state.ganti_cat = None
    st.session_state.prev_usage_label = usage_label

    cat_col = usage_options[usage_label]

    assembly_map = {"Office": 100_000, "Standar": 150_000, "Advance": 200_000}
    assembly_fee = assembly_map[usage_label]

    price_range_map = {
        "Office":  (0,          10_000_000),
        "Standar": (10_000_000, 20_000_000),
        "Advance": (20_000_000, 100_000_000),
    }
    default_min, default_max = price_range_map[usage_label]

    st.sidebar.divider()
    price_min = st.sidebar.number_input("Harga Min (Rp)", min_value=0, value=default_min, step=500_000)
    price_max = st.sidebar.number_input("Harga Max (Rp)", min_value=0, value=default_max, step=500_000)

    # --------------------------------------------------------
    # VIEW: MAIN
    # --------------------------------------------------------
    if st.session_state.view == 'main':
        st.subheader(f"Rekomendasi Bundling — {usage_label} | {selected_branch}")

        grouped = generate_bundles(data, branch_col, cat_col, price_min, price_max)

        any_card = any(len(g["cards"]) > 0 for g in grouped)
        if not any_card:
            st.warning("Tidak ada bundling yang bisa dibuat. Pastikan data sudah diupload dan filter sesuai.")

        btn_counter = 0
        for group in grouped:
            st.markdown(f"""
            <div style="margin: 20px 0 6px 0;">
                <span style="font-size:17px; font-weight:700; color:#1a1a2e;">{group['label']}</span>
                <span style="font-size:12px; color:#888; margin-left:10px;">{group['desc']}</span>
            </div>
            """, unsafe_allow_html=True)

            cards = group["cards"]
            if not cards:
                st.caption("Tidak ada bundle tersedia untuk mode ini.")
                continue

            cols = st.columns(3)
            for j, card in enumerate(cards):
                with cols[j]:
                    border_color = "#e0e0e0" if card["in_range"] else "#ffcdd2"
                    opacity = "1" if card["in_range"] else "0.65"
                    out_of_range_note = "" if card["in_range"] else '<div style="font-size:11px;color:#e53935;margin-top:4px;">Di luar rentang harga</div>'
                    st.markdown(f"""
                    <div class="bundle-card" style="border-color:{border_color}; opacity:{opacity};">
                        <span class="badge {card['badge']}">{card['name']}</span>
                        <div class="price-text">Rp {card['total']:,.0f}</div>
                        <div style="font-size:11px; color:#888;">{len(card['parts'])} komponen</div>
                        {out_of_range_note}
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("Pilih & Sesuaikan", key=f"btn_{btn_counter}", use_container_width=True):
                        st.session_state.selected_bundle = {
                            "name": f"{group['label']} — {card['name']}",
                            "parts": dict(card["parts"]),
                            "total": card["total"],
                        }
                        st.session_state.view = 'detail'
                        st.rerun()
                    btn_counter += 1

            st.markdown("<hr style='border:none;border-top:1px solid #f0f0f0;margin:8px 0 4px 0;'>", unsafe_allow_html=True)

        with st.expander("Info Filter Produk Aktif"):
            st.markdown("""
            - **Processor**: Hanya Intel (AMD tidak digunakan)
            - **RAM**: Produk SODIMM dihapus
            - **SSD**: Produk WDS120G2GOB dihapus
            - **Casing**: Produk Armageddon dihapus
            - **VGA**: Muncul hanya jika Processor tipe F
            - **PSU**: Dihapus jika Casing sudah include PSU/VALCAS
            - **CPU Cooler**: Muncul hanya jika Processor tipe Tray
            """)

    # --------------------------------------------------------
    # VIEW: DETAIL
    # --------------------------------------------------------
    elif st.session_state.view == 'detail':
        bundle = st.session_state.selected_bundle

        if 'ganti_cat' not in st.session_state:
            st.session_state.ganti_cat = None

        col_back, col_title = st.columns([1, 8])
        with col_back:
            if st.button("Kembali"):
                st.session_state.view = 'main'
                st.session_state.ganti_cat = None
                st.rerun()
        with col_title:
            st.subheader(bundle['name'])

        st.divider()

        col_parts, col_summary = st.columns([3, 1])

        display_order = ['Processor', 'Motherboard', 'Memory RAM', 'SSD Internal', 'VGA', 'Casing PC', 'Power Supply', 'CPU Cooler']

        with col_parts:
            st.markdown("#### Komponen Terpilih")
            updated_parts = {}

            for cat in display_order:
                if cat not in bundle['parts']:
                    continue
                item = bundle['parts'][cat]

                c_info, c_ganti, c_hapus = st.columns([8, 1, 1])
                with c_info:
                    st.markdown(f"""
                    <div class="part-row">
                        <div>
                            <div class="category-label">{cat}</div>
                            <div class="part-name">{item['Nama Accurate']}</div>
                        </div>
                        <div class="part-price">Rp {item['Web']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_ganti:
                    st.write("")
                    # FIX 3: Tombol Ganti diganti simbol ♻️
                    if st.button("♻️", key=f"ganti_{cat}", help=f"Ganti {cat}"):
                        if st.session_state.ganti_cat == cat:
                            st.session_state.ganti_cat = None
                        else:
                            st.session_state.ganti_cat = cat
                        st.rerun()
                with c_hapus:
                    st.write("")
                    if not st.button("—", key=f"del_{cat}", help=f"Hapus {cat}"):
                        updated_parts[cat] = item

                if st.session_state.ganti_cat == cat:
                    available_all = data[(data[branch_col] > 0) & (data[cat_col] == True)].copy()
                    alternatif = available_all[
                        available_all['Kategori'] == cat
                    ].sort_values('Web', ascending=True)

                    if cat == 'Memory RAM' and 'Motherboard' in bundle['parts']:
                        mobo_ddr = bundle['parts']['Motherboard'].get('mobo_ddr', None)
                        if mobo_ddr:
                            alt_ddr = alternatif[alternatif['ram_ddr'] == mobo_ddr]
                            if not alt_ddr.empty:
                                alternatif = alt_ddr

                    if alternatif.empty:
                        st.caption("Tidak ada produk lain tersedia untuk kategori ini.")
                    else:
                        st.markdown(f"""
                        <div style="background:#f0f4ff; border:1px solid #c5d3f0; border-radius:10px;
                                    padding:10px 14px; margin-bottom:8px;">
                            <div style="font-size:12px; font-weight:700; color:#1565C0;">
                                Pilih pengganti untuk {cat}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        for _, alt_row in alternatif.iterrows():
                            is_current = alt_row['Nama Accurate'] == item['Nama Accurate']
                            label = f"{'[Terpilih]  ' if is_current else ''}{alt_row['Nama Accurate']}  —  Rp {alt_row['Web']:,.0f}  |  Stok: {int(alt_row[branch_col])}"
                            if st.button(label, key=f"pilih_{cat}_{alt_row.name}", disabled=is_current, use_container_width=True):
                                alt_dict = alt_row.to_dict()

                                if cat == 'Processor':
                                    new_parts = rebuild_from_processor(alt_dict, available_all, branch_col)
                                    if new_parts:
                                        st.session_state.selected_bundle['parts'] = new_parts
                                elif cat == 'Motherboard':
                                    new_parts = rebuild_from_mobo(alt_dict, bundle['parts'], available_all, branch_col)
                                    st.session_state.selected_bundle['parts'] = new_parts
                                elif cat == 'Casing PC':
                                    new_parts = rebuild_from_casing(alt_dict, bundle['parts'], available_all, branch_col)
                                    st.session_state.selected_bundle['parts'] = new_parts
                                else:
                                    st.session_state.selected_bundle['parts'][cat] = alt_dict

                                st.session_state.ganti_cat = None
                                st.rerun()

            st.session_state.selected_bundle['parts'] = updated_parts

        with col_summary:
            total_items = sum(item['Web'] for item in updated_parts.values())
            is_assembled = st.checkbox(
                f"Tambah Jasa Rakit",
                value=False,
                help=f"Biaya jasa rakit {usage_label}: Rp {assembly_fee:,.0f}"
            )
            grand_total = total_items + (assembly_fee if is_assembled else 0)

            parts_html = ""
            for item in updated_parts.values():
                nama = item['Nama Accurate'][:30]
                parts_html += f'<div style="font-size:12px; margin:3px 0; opacity:0.9;">• {nama}...</div>'
            if is_assembled:
                parts_html += f'<div style="font-size:12px; margin:3px 0; opacity:0.9;">• Jasa Rakit {usage_label}</div>'

            summary_html = f"""
            <div class="summary-box">
                <div style="font-size:13px; opacity:0.85; margin-bottom:6px;">RINGKASAN</div>
                {parts_html}
                <hr style="border-color: rgba(255,255,255,0.3); margin:10px 0;">
                <div style="font-size:13px; opacity:0.85;">Total Harga</div>
                <div class="total-price">Rp {grand_total:,.0f}</div>
            </div>
            """
            st.markdown(summary_html, unsafe_allow_html=True)

            st.write("")
            if st.button("Konfirmasi Bundling", use_container_width=True, type="primary"):
                st.balloons()
                st.success(f"Bundle dikonfirmasi! Total: Rp {grand_total:,.0f}")