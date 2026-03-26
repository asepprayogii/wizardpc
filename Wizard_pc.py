import streamlit as st
import pandas as pd
import re

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PC Wizard Pro", layout="wide")

# --- CSS CUSTOM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

    .block-container {
        padding: 1rem 1rem 2rem 1rem !important;
        max-width: 100% !important;
    }

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

    /* ================================================================
       PART CARD — menggantikan .part-row berbasis st.columns
       Seluruh baris komponen (info + tombol) dibungkus dalam satu div
       ================================================================ */
    .part-card {
        border: 1px solid #eef2f7;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        background: #fafbff;
    }
    .part-card-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 6px;
    }
    .part-info { flex: 1; min-width: 0; }
    .category-label {
        font-size: 10px;
        color: #888;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    .part-name {
        font-size: 13px;
        font-weight: 500;
        color: #1a1a2e;
        word-break: break-word;
    }
    .part-right {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-shrink: 0;
    }
    .part-price {
        font-size: 13px;
        color: #1E88E5;
        font-weight: 600;
        white-space: nowrap;
    }
    /* Tombol aksi inline di dalam HTML card */
    .btn-action {
        border: none;
        border-radius: 6px;
        padding: 5px 11px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        white-space: nowrap;
        font-family: 'Space Grotesk', sans-serif;
        transition: all 0.15s ease;
    }
    .btn-ganti {
        background: #E3F2FD;
        color: #1565C0;
    }
    .btn-ganti:hover { background: #BBDEFB; }
    .btn-hapus {
        background: #FFEBEE;
        color: #C62828;
    }
    .btn-hapus:hover { background: #FFCDD2; }

    /* ================================================================
       ANCHOR TRICK — tombol HTML memanggil Streamlit button tersembunyi
       ================================================================ */
    .hidden-btn { display: none; }

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

    .ganti-header {
        background: #f0f4ff;
        border: 1px solid #c5d3f0;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 12px;
        font-weight: 700;
        color: #1565C0;
    }
    .out-of-range {
        font-size: 11px;
        color: #e53935;
        margin-top: 4px;
    }

    /* Sembunyikan label kosong di atas tombol Streamlit */
    div[data-testid="stVerticalBlock"] .stButton > button {
        border-radius: 8px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
    }

    /* Tombol Ganti & Hapus — ukuran konsisten di semua layar */
    .action-col .stButton > button {
        width: 100% !important;
        padding: 6px 10px !important;
        font-size: 12px !important;
        min-height: 36px !important;
    }

    @media (max-width: 640px) {
        .block-container {
            padding: 0.5rem 0.5rem 1.5rem 0.5rem !important;
        }
        .summary-box { padding: 14px; }
        .total-price { font-size: 20px; }
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNGSI HELPER
# ============================================================

def extract_ram_gb(name):
    name = name.upper()
    match = re.search(r'(\d+)\s*GB', name)
    return int(match.group(1)) if match else 0


def extract_ddr_type(name):
    name = name.upper()
    match = re.search(r'DDR(\d)', name)
    return f"DDR{match.group(1)}" if match else None


def get_cpu_info(name):
    name = name.upper()
    info = {"brand": "INTEL", "gen": None, "socket": None,
            "is_f_type": False, "is_tray": False, "tier": None}

    if "RYZEN" in name or "AMD" in name:
        info["brand"] = "AMD"
        if any(x in name for x in ["7000","8000","9000","9500","9600","9700","9900"]) or "AM5" in name:
            info["socket"] = "AM5"
        else:
            info["socket"] = "AM4"
        if "TRAY" in name or "NO FAN" in name:
            info["is_tray"] = True
        return info

    if "ULTRA" in name:
        info["gen"] = "ULTRA"
        info["tier"] = "ULTRA"
        info["is_f_type"] = True
        if "TRAY" in name or "NO FAN" in name:
            info["is_tray"] = True
        return info

    tier_match = re.search(r'\bI([3579])\b', name)
    if tier_match:
        info["tier"] = f"I{int(tier_match.group(1))}"

    gen_match = re.search(r'I[3579]-(\d{2,2})\d{2,3}', name)
    if gen_match:
        info["gen"] = int(gen_match.group(1))
    else:
        model_match = re.search(r'\b(1[0-9])(\d{3})\b', name)
        if model_match:
            info["gen"] = int(model_match.group(1))

    if re.search(r'\d{3,4}F\b', name):
        info["is_f_type"] = True
    if "TRAY" in name or "NO FAN" in name:
        info["is_tray"] = True

    return info


def is_mobo_compatible(cpu_info, mobo_series):
    gen = cpu_info["gen"]
    socket = cpu_info["socket"]
    brand = cpu_info["brand"]
    if brand == "AMD":
        if socket == "AM4": return mobo_series in ["A520","B450","B550"]
        if socket == "AM5": return mobo_series in ["A620","B650","B840","B850","X870"]
        return True
    if gen == 10: return mobo_series in ["H410","H510"]
    if gen == 11: return mobo_series in ["H510"]
    if gen in [12,13,14]: return mobo_series in ["H610","B660","B760","Z790"]
    if gen == "ULTRA": return mobo_series in ["H810","B860","Z890"]
    return True


def get_mobo_series(name):
    name = name.upper()
    for s in ["H410","H510","H610","H810","B660","B760","B860","Z790","Z890",
              "A520","A620","B450","B550","B650","B840","B850","X870"]:
        if s in name:
            return s
    return None


def get_mobo_category(series, price):
    cats = {"office": False, "standar": False, "advance": False}
    if series in ["H410","H510","H610","H810","A520","A620"]:
        cats["office"] = True
    elif series in ["B660","B760","B860"]:
        cats["standar" if price < 2_000_000 else "advance"] = True
    elif series in ["Z790","Z890"]:
        cats["advance"] = True
    elif series in ["B450","B550","B650","B840","B850"]:
        cats["standar"] = True; cats["advance"] = True
    elif series in ["X870"]:
        cats["advance"] = True
    return cats


def get_vga_category(name):
    name = name.upper()
    cats = {"office": False, "standar": False, "advance": False}
    if any(s in name for s in ["GT710","GT730"]):
        cats["office"] = True; return cats
    if any(s in name for s in ["RTX5060TI","RTX5060 TI","RTX5070TI","RTX5070 TI","RTX5080","RTX5090"]):
        cats["advance"] = True; return cats
    if "RTX5060" in name and "TI" not in name:
        cats["advance"] = True; return cats
    if "RTX5070" in name and "TI" not in name:
        cats["advance"] = True; return cats
    if any(s in name for s in ["GT1030","GTX1650","RTX3050","RTX3060","RTX5050","RTX4060"]):
        cats["standar"] = True; return cats
    if re.search(r'RTX\s*\d*[56]0\b', name):
        cats["standar"] = True; return cats
    if re.search(r'RTX\s*\d*[789]\d\b', name):
        cats["advance"] = True; return cats
    cats["standar"] = True
    return cats


# ============================================================
# PROSES DATA
# ============================================================

def process_data(df):
    df = df.copy()
    df['Web'] = pd.to_numeric(df['Web'], errors='coerce').fillna(0)
    df = df[df['Stock Total'] > 0].copy()
    df = df[df['Web'] > 0].copy()
    df['Nama Accurate'] = df['Nama Accurate'].fillna('').astype(str)
    df['Kategori'] = df['Kategori'].fillna('').astype(str)

    for col in ['cat_office','cat_standar','cat_advance']:
        df[col] = False
    for col in ['need_vga','has_psu','need_cooler']:
        df[col] = 0
    for col in ['cpu_gen','cpu_socket','cpu_brand','cpu_tier','mobo_series','mobo_ddr','ram_ddr']:
        df[col] = None
    df['cpu_is_f'] = False
    df['cpu_is_tray'] = False

    # Processor
    for idx in df[df['Kategori'] == 'Processor'].index:
        cpu = get_cpu_info(df.at[idx, 'Nama Accurate'])
        df.at[idx, 'cpu_brand'] = cpu['brand']
        df.at[idx, 'cpu_gen'] = cpu['gen']
        df.at[idx, 'cpu_socket'] = cpu['socket']
        df.at[idx, 'cpu_tier'] = cpu['tier']
        df.at[idx, 'cpu_is_f'] = cpu['is_f_type']
        df.at[idx, 'cpu_is_tray'] = cpu['is_tray']
        df.at[idx, 'need_vga'] = 1 if cpu['is_f_type'] else 0
        df.at[idx, 'need_cooler'] = 1 if cpu['is_tray'] else 0
        tier, is_f, brand = cpu['tier'], cpu['is_f_type'], cpu['brand']
        if brand == "INTEL":
            if tier in ["I3","I5"] and not is_f: df.at[idx,'cat_office'] = True
            if tier in ["I3","I5"] and is_f:     df.at[idx,'cat_standar'] = True
            if tier in ["I7","I9"] and is_f:     df.at[idx,'cat_advance'] = True
            if tier == "ULTRA":                  df.at[idx,'cat_advance'] = True
        if brand == "AMD":
            df.at[idx,'cat_office'] = df.at[idx,'cat_standar'] = df.at[idx,'cat_advance'] = True

    # Motherboard
    for idx in df[df['Kategori'] == 'Motherboard'].index:
        name = df.at[idx, 'Nama Accurate'].upper()
        series = get_mobo_series(name)
        df.at[idx, 'mobo_series'] = series
        if series:
            cats = get_mobo_category(series, df.at[idx,'Web'])
            df.at[idx,'cat_office'] = cats['office']
            df.at[idx,'cat_standar'] = cats['standar']
            df.at[idx,'cat_advance'] = cats['advance']
        else:
            df.at[idx,'cat_office'] = df.at[idx,'cat_standar'] = df.at[idx,'cat_advance'] = True
        df.at[idx, 'mobo_ddr'] = extract_ddr_type(name)

    # RAM
    ram_mask = df['Kategori'] == 'Memory RAM'
    sodimm = df['Nama Accurate'].str.upper().str.contains('SODIMM', na=False)
    df = df[~(ram_mask & sodimm)].copy()
    for idx in df[df['Kategori'] == 'Memory RAM'].index:
        name = df.at[idx, 'Nama Accurate']
        gb = extract_ram_gb(name)
        df.at[idx,'ram_ddr'] = extract_ddr_type(name)
        if 8 <= gb <= 16:  df.at[idx,'cat_office'] = True
        if 16 <= gb <= 32: df.at[idx,'cat_standar'] = True
        if 32 <= gb <= 64: df.at[idx,'cat_advance'] = True
        if gb == 0:
            df.at[idx,'cat_office'] = df.at[idx,'cat_standar'] = df.at[idx,'cat_advance'] = True

    # SSD
    ssd_mask = df['Kategori'] == 'SSD Internal'
    excl = df['Nama Accurate'].str.upper().str.contains('WDS120G2GOB', na=False)
    df = df[~(ssd_mask & excl)].copy()
    for idx in df[df['Kategori'] == 'SSD Internal'].index:
        name = df.at[idx,'Nama Accurate'].upper()
        df.at[idx,'cat_office'] = df.at[idx,'cat_standar'] = True
        if 'NVME' in name or 'M.2' in name or 'M2' in name:
            df.at[idx,'cat_advance'] = True

    # VGA
    for idx in df[df['Kategori'] == 'VGA'].index:
        cats = get_vga_category(df.at[idx,'Nama Accurate'])
        df.at[idx,'cat_office'] = cats['office']
        df.at[idx,'cat_standar'] = cats['standar']
        df.at[idx,'cat_advance'] = cats['advance']

    # Casing
    casing_mask = df['Kategori'] == 'Casing PC'
    arm = df['Nama Accurate'].str.upper().str.contains('ARMAGEDDON', na=False)
    df = df[~(casing_mask & arm)].copy()
    for idx in df[df['Kategori'] == 'Casing PC'].index:
        name = df.at[idx,'Nama Accurate'].upper()
        df.at[idx,'cat_office'] = df.at[idx,'cat_standar'] = df.at[idx,'cat_advance'] = True
        if 'PSU' in name or 'VALCAS' in name:
            df.at[idx,'has_psu'] = 1

    # PSU
    for idx in df[df['Kategori'] == 'Power Supply'].index:
        price = df.at[idx,'Web']
        name = df.at[idx,'Nama Accurate'].upper()
        if price < 500_000: df.at[idx,'cat_office'] = True
        if price >= 500_000: df.at[idx,'cat_standar'] = True
        if any(l in name for l in ['BRONZE','GOLD','PLATINUM']): df.at[idx,'cat_advance'] = True

    # Cooler
    for idx in df[df['Kategori'] == 'CPU Cooler'].index:
        price = df.at[idx,'Web']
        if price < 300_000: df.at[idx,'cat_office'] = True
        if 250_000 <= price <= 1_000_000: df.at[idx,'cat_standar'] = True
        if price > 500_000: df.at[idx,'cat_advance'] = True

    return df


# ============================================================
# BUNDLING
# ============================================================

def sorted_items(items, mode, branch_col):
    if items.empty: return items
    if mode == 'stok_terbanyak': return items.sort_values(branch_col, ascending=False)
    if mode == 'harga_termurah': return items.sort_values('Web', ascending=True)
    if mode == 'smart_pick':
        lo = items['Web'].min()
        return items[items['Web'] <= lo + 100_000].sort_values(branch_col, ascending=False)
    return items


def build_bundle(available, branch_col, mode, variant_idx):
    def pick(items):
        ranked = sorted_items(items, mode, branch_col)
        if ranked.empty: return None
        return ranked.iloc[min(variant_idx, len(ranked)-1)]

    bundle = {}
    proc = pick(available[available['Kategori'] == 'Processor'])
    if proc is None: return None
    bundle['Processor'] = proc

    cpu_info = {'brand': proc.get('cpu_brand','INTEL'), 'gen': proc.get('cpu_gen'), 'socket': proc.get('cpu_socket')}
    mobos = available[available['Kategori'] == 'Motherboard']
    mobo = pick(mobos[mobos['mobo_series'].apply(lambda s: is_mobo_compatible(cpu_info, s))])
    if mobo is None: return None
    bundle['Motherboard'] = mobo

    rams = available[available['Kategori'] == 'Memory RAM']
    if mobo.get('mobo_ddr'):
        c = rams[rams['ram_ddr'] == mobo.get('mobo_ddr')]
        if not c.empty: rams = c
    ram = pick(rams)
    if ram is not None: bundle['Memory RAM'] = ram

    ssd = pick(available[available['Kategori'] == 'SSD Internal'])
    if ssd is not None: bundle['SSD Internal'] = ssd

    if proc.get('need_vga', 0) == 1:
        vga = pick(available[available['Kategori'] == 'VGA'])
        if vga is not None: bundle['VGA'] = vga

    casing = pick(available[available['Kategori'] == 'Casing PC'])
    if casing is not None: bundle['Casing PC'] = casing

    if not (casing is not None and casing.get('has_psu', 0) == 1):
        psu = pick(available[available['Kategori'] == 'Power Supply'])
        if psu is not None: bundle['Power Supply'] = psu

    if proc.get('need_cooler', 0) == 1:
        cooler = pick(available[available['Kategori'] == 'CPU Cooler'])
        if cooler is not None: bundle['CPU Cooler'] = cooler

    return {"parts": bundle, "total": sum(i['Web'] for i in bundle.values())}


def rebuild_from_processor(proc, available, branch_col):
    def p1(items):
        s = sorted_items(items, 'harga_termurah', branch_col)
        return s.iloc[0] if not s.empty else None
    bundle = {'Processor': proc}
    cpu_info = {'brand': proc.get('cpu_brand','INTEL'), 'gen': proc.get('cpu_gen'), 'socket': proc.get('cpu_socket')}
    mobos = available[available['Kategori'] == 'Motherboard']
    mobo = p1(mobos[mobos['mobo_series'].apply(lambda s: is_mobo_compatible(cpu_info, s))])
    if mobo is None: return None
    bundle['Motherboard'] = mobo
    rams = available[available['Kategori'] == 'Memory RAM']
    if mobo.get('mobo_ddr'):
        c = rams[rams['ram_ddr'] == mobo.get('mobo_ddr')]
        if not c.empty: rams = c
    ram = p1(rams)
    if ram is not None: bundle['Memory RAM'] = ram
    ssd = p1(available[available['Kategori'] == 'SSD Internal'])
    if ssd is not None: bundle['SSD Internal'] = ssd
    if proc.get('need_vga',0) == 1:
        vga = p1(available[available['Kategori'] == 'VGA'])
        if vga is not None: bundle['VGA'] = vga
    casing = p1(available[available['Kategori'] == 'Casing PC'])
    if casing is not None: bundle['Casing PC'] = casing
    if not (casing is not None and casing.get('has_psu',0) == 1):
        psu = p1(available[available['Kategori'] == 'Power Supply'])
        if psu is not None: bundle['Power Supply'] = psu
    if proc.get('need_cooler',0) == 1:
        cooler = p1(available[available['Kategori'] == 'CPU Cooler'])
        if cooler is not None: bundle['CPU Cooler'] = cooler
    return bundle


def rebuild_from_mobo(mobo, current_bundle, available, branch_col):
    bundle = dict(current_bundle)
    bundle['Motherboard'] = mobo
    rams = available[available['Kategori'] == 'Memory RAM']
    if mobo.get('mobo_ddr'):
        c = rams[rams['ram_ddr'] == mobo.get('mobo_ddr')]
        if not c.empty: rams = c
    if not rams.empty:
        bundle['Memory RAM'] = rams.sort_values('Web').iloc[0]
    return bundle


def rebuild_from_casing(casing, current_bundle, available, branch_col):
    bundle = dict(current_bundle)
    bundle['Casing PC'] = casing
    if casing.get('has_psu',0) == 1:
        bundle.pop('Power Supply', None)
    else:
        if 'Power Supply' not in bundle:
            psus = available[available['Kategori'] == 'Power Supply']
            if not psus.empty:
                bundle['Power Supply'] = psus.sort_values('Web').iloc[0]
    return bundle


def generate_bundles(df, branch_col, cat_col, price_min=0, price_max=0):
    available = df[(df[branch_col] > 0) & (df[cat_col] == True)].copy()
    use_filter = not (price_min == 0 and price_max == 0)
    modes = [
        {"key":"stok_terbanyak","label":"Stok Terbanyak","desc":"Produk dengan stok terbanyak dari setiap kategori","badge":"badge-stock","variants":["Stok Tertinggi","Stok Tinggi","Stok Cukup"]},
        {"key":"harga_termurah","label":"Harga Termurah","desc":"Produk dengan harga termurah dari setiap kategori","badge":"badge-price","variants":["Termurah","Budget","Ekonomis"]},
        {"key":"smart_pick","label":"Smart Pick","desc":"Harga termurah + range 100rb, stok terbanyak dalam range","badge":"badge-smart","variants":["Smart 1","Smart 2","Smart 3"]},
    ]
    grouped = []
    for m in modes:
        group = {"label":m["label"],"desc":m["desc"],"badge":m["badge"],"cards":[]}
        for v in range(3):
            bundle = build_bundle(available, branch_col, m["key"], v)
            if bundle:
                in_range = (not use_filter) or (price_min <= bundle["total"] <= price_max)
                group["cards"].append({"name":m["variants"][v],"badge":m["badge"],"in_range":in_range,**bundle})
        grouped.append(group)
    return grouped


# ============================================================
# MAIN APP
# ============================================================

st.title("PC Wizard Pro")
st.caption("Sistem Rekomendasi Bundling PC Otomatis")

for key, val in [('view','main'),('selected_bundle',None),('ganti_cat',None),('hapus_cat',None)]:
    if key not in st.session_state:
        st.session_state[key] = val

uploaded_file = st.file_uploader("Upload Data Portal (CSV atau XLSX)", type=["csv","xlsx"])

if uploaded_file:
    with st.spinner("Memproses data..."):
        raw_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        data = process_data(raw_df)

    # SIDEBAR
    st.sidebar.header("Konfigurasi")
    branch_map = {
        "Surabaya":["Stock A - ITC","Stock B","Stock Y - SBY"],
        "Jakarta":["Stock C6"],"Semarang":["Stock D - SMG"],
        "Jogja":["Stock E - JOG"],"Malang":["Stock F - MLG"],"Bali":["Stock H - BALI"],
    }
    selected_branch = st.sidebar.selectbox("Cabang", list(branch_map.keys()), index=0)
    branch_cols = branch_map[selected_branch]
    data['_stock_branch'] = data[branch_cols].sum(axis=1) if selected_branch == "Surabaya" else data[branch_cols[0]]
    branch_col = '_stock_branch'

    usage_options = {"Office":"cat_office","Standar":"cat_standar","Advance":"cat_advance"}
    usage_label = st.sidebar.radio("Kategori Penggunaan", list(usage_options.keys()),
        format_func=lambda x: {"Office":"Office (< 10 jt)","Standar":"Standar (10 - 20 jt)","Advance":"Advance (> 20 jt)"}[x])
    cat_col = usage_options[usage_label]
    assembly_fee = {"Office":100_000,"Standar":150_000,"Advance":200_000}[usage_label]
    default_min, default_max = {"Office":(0,10_000_000),"Standar":(10_000_000,20_000_000),"Advance":(20_000_000,100_000_000)}[usage_label]
    st.sidebar.divider()
    price_min = st.sidebar.number_input("Harga Min (Rp)", min_value=0, value=default_min, step=500_000)
    price_max = st.sidebar.number_input("Harga Max (Rp)", min_value=0, value=default_max, step=500_000)

    # ============================================================
    # VIEW: MAIN
    # ============================================================
    if st.session_state.view == 'main':
        st.subheader(f"Rekomendasi Bundling — {usage_label} | {selected_branch}")
        grouped = generate_bundles(data, branch_col, cat_col, price_min, price_max)

        if not any(len(g["cards"]) > 0 for g in grouped):
            st.warning("Tidak ada bundling yang bisa dibuat. Pastikan data sudah diupload dan filter sesuai.")

        btn_counter = 0
        for group in grouped:
            st.markdown(f"""
            <div style="margin:20px 0 6px 0;">
                <span style="font-size:17px;font-weight:700;color:#1a1a2e;">{group['label']}</span>
                <span style="font-size:12px;color:#888;margin-left:10px;">{group['desc']}</span>
            </div>""", unsafe_allow_html=True)

            cards = group["cards"]
            if not cards:
                st.caption("Tidak ada bundle tersedia untuk mode ini.")
                continue

            cols = st.columns(3)
            for j, card in enumerate(cards):
                with cols[j]:
                    bc = "#e0e0e0" if card["in_range"] else "#ffcdd2"
                    op = "1" if card["in_range"] else "0.65"
                    note = "" if card["in_range"] else '<div class="out-of-range">Di luar rentang harga</div>'
                    st.markdown(f"""
                    <div class="bundle-card" style="border-color:{bc};opacity:{op};">
                        <span class="badge {card['badge']}">{card['name']}</span>
                        <div class="price-text">Rp {card['total']:,.0f}</div>
                        <div style="font-size:11px;color:#888;">{len(card['parts'])} komponen</div>
                        {note}
                    </div>""", unsafe_allow_html=True)

                    if st.button("Pilih & Sesuaikan", key=f"btn_{btn_counter}", use_container_width=True):
                        st.session_state.selected_bundle = {
                            "name": f"{group['label']} — {card['name']}",
                            "parts": dict(card["parts"]),
                            "total": card["total"],
                        }
                        st.session_state.view = 'detail'
                        st.session_state.ganti_cat = None
                        st.rerun()
                    btn_counter += 1

            st.markdown("<hr style='border:none;border-top:1px solid #f0f0f0;margin:8px 0 4px 0;'>", unsafe_allow_html=True)

        with st.expander("Info Filter Produk Aktif"):
            st.markdown("""
            - **Processor**: Hanya Intel (AMD sebagai fallback)
            - **RAM**: Produk SODIMM dihapus
            - **SSD**: Produk WDS120G2GOB dihapus
            - **Casing**: Produk Armageddon dihapus
            - **VGA**: Muncul hanya jika Processor tipe F
            - **PSU**: Dihapus jika Casing sudah include PSU/VALCAS
            - **CPU Cooler**: Muncul hanya jika Processor tipe Tray
            """)

    # ============================================================
    # VIEW: DETAIL
    # ============================================================
    elif st.session_state.view == 'detail':
        bundle = st.session_state.selected_bundle

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
        display_order = ['Processor','Motherboard','Memory RAM','SSD Internal','VGA','Casing PC','Power Supply','CPU Cooler']

        with col_parts:
            st.markdown("#### Komponen Terpilih")
            updated_parts = {}

            # --- Proses hapus dari session state ---
            if st.session_state.hapus_cat:
                cat_to_del = st.session_state.hapus_cat
                st.session_state.hapus_cat = None
                # Biarkan cat_to_del tidak masuk updated_parts nanti

            for cat in display_order:
                if cat not in bundle['parts']:
                    continue

                # Skip jika sedang dihapus
                if st.session_state.get('_pending_delete') == cat:
                    st.session_state['_pending_delete'] = None
                    continue

                item = bundle['parts'][cat]

                # -----------------------------------------------
                # PART CARD — seluruh baris dalam satu container
                # Tombol Ganti & Hapus ada di dalam card,
                # di bawah info produk agar tidak overflow di HP
                # -----------------------------------------------
                with st.container():
                    # Baris atas: info produk + harga
                    st.markdown(f"""
                    <div class="part-card">
                        <div class="part-card-top">
                            <div class="part-info">
                                <div class="category-label">{cat}</div>
                                <div class="part-name">{item['Nama Accurate']}</div>
                            </div>
                            <div class="part-price">Rp {item['Web']:,.0f}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Baris tombol — 2 kolom sama lebar, responsif
                    col_g, col_h = st.columns(2)
                    with col_g:
                        label_g = "Tutup" if st.session_state.ganti_cat == cat else "Ganti"
                        if st.button(label_g, key=f"ganti_{cat}", use_container_width=True):
                            st.session_state.ganti_cat = None if st.session_state.ganti_cat == cat else cat
                            st.rerun()
                    with col_h:
                        if st.button("Hapus", key=f"del_{cat}", use_container_width=True):
                            # Hapus langsung: jangan masukkan ke updated_parts
                            bundle['parts'].pop(cat, None)
                            if st.session_state.ganti_cat == cat:
                                st.session_state.ganti_cat = None
                            st.session_state.selected_bundle['parts'] = {
                                k: v for k, v in bundle['parts'].items()
                            }
                            st.rerun()

                # updated_parts dikumpulkan setelah tombol hapus diproses
                updated_parts[cat] = item

                # Panel ganti produk
                if st.session_state.ganti_cat == cat:
                    available_all = data[(data[branch_col] > 0) & (data[cat_col] == True)].copy()
                    alternatif = available_all[available_all['Kategori'] == cat].sort_values('Web', ascending=True)

                    if cat == 'Memory RAM' and 'Motherboard' in bundle['parts']:
                        mobo_ddr = bundle['parts']['Motherboard'].get('mobo_ddr')
                        if mobo_ddr:
                            alt_ddr = alternatif[alternatif['ram_ddr'] == mobo_ddr]
                            if not alt_ddr.empty: alternatif = alt_ddr

                    if alternatif.empty:
                        st.caption("Tidak ada produk lain tersedia untuk kategori ini.")
                    else:
                        st.markdown(f'<div class="ganti-header">Pilih pengganti untuk {cat}</div>', unsafe_allow_html=True)
                        for _, alt_row in alternatif.iterrows():
                            is_current = alt_row['Nama Accurate'] == item['Nama Accurate']
                            label = f"{'[Terpilih]  ' if is_current else ''}{alt_row['Nama Accurate']}  —  Rp {alt_row['Web']:,.0f}  |  Stok: {int(alt_row[branch_col])}"
                            if st.button(label, key=f"pilih_{cat}_{alt_row.name}", disabled=is_current, use_container_width=True):
                                alt_dict = alt_row.to_dict()
                                if cat == 'Processor':
                                    new_parts = rebuild_from_processor(alt_dict, available_all, branch_col)
                                    if new_parts: st.session_state.selected_bundle['parts'] = new_parts
                                elif cat == 'Motherboard':
                                    st.session_state.selected_bundle['parts'] = rebuild_from_mobo(alt_dict, bundle['parts'], available_all, branch_col)
                                elif cat == 'Casing PC':
                                    st.session_state.selected_bundle['parts'] = rebuild_from_casing(alt_dict, bundle['parts'], available_all, branch_col)
                                else:
                                    st.session_state.selected_bundle['parts'][cat] = alt_dict
                                st.session_state.ganti_cat = None
                                st.rerun()

            # Simpan updated_parts ke session state
            st.session_state.selected_bundle['parts'] = updated_parts

        # SUMMARY
        with col_summary:
            total_items = sum(item['Web'] for item in updated_parts.values())
            is_assembled = st.checkbox("Tambah Jasa Rakit", value=False,
                help=f"Biaya jasa rakit {usage_label}: Rp {assembly_fee:,.0f}")
            grand_total = total_items + (assembly_fee if is_assembled else 0)

            parts_html = "".join(
                f'<div style="font-size:12px;margin:3px 0;opacity:0.9;">- {item["Nama Accurate"][:28]}...</div>'
                for item in updated_parts.values()
            )
            if is_assembled:
                parts_html += f'<div style="font-size:12px;margin:3px 0;opacity:0.9;">- Jasa Rakit {usage_label}</div>'

            st.markdown(f"""
            <div class="summary-box">
                <div style="font-size:12px;opacity:0.85;margin-bottom:6px;font-weight:700;letter-spacing:0.5px;">RINGKASAN</div>
                {parts_html}
                <hr style="border-color:rgba(255,255,255,0.3);margin:10px 0;">
                <div style="font-size:12px;opacity:0.85;">Total Harga</div>
                <div class="total-price">Rp {grand_total:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

            st.write("")
            if st.button("Konfirmasi Bundling", use_container_width=True, type="primary"):
                st.balloons()
                st.success(f"Bundle dikonfirmasi! Total: Rp {grand_total:,.0f}")