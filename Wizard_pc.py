import streamlit as st
import pandas as pd
import re

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PC Wizard Pro", layout="wide", page_icon="🖥️")

# --- CSS GLOBAL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
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
        box-shadow: 0 8px 24px rgba(30,136,229,0.15);
        border-color: #1E88E5;
        transform: translateY(-4px);
    }
    .price-text { color:#1565C0; font-size:20px; font-weight:700; margin:8px 0 4px 0; }
    .badge { padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700;
             display:inline-block; margin-bottom:8px; letter-spacing:0.5px; }
    .badge-stock { background:#E3F2FD; color:#1565C0; }
    .badge-price { background:#E8F5E9; color:#2E7D32; }
    .badge-smart  { background:#FFF3E0; color:#E65100; }
    .part-row { border:1px solid #eef2f7; border-radius:10px; padding:12px 16px;
                margin-bottom:8px; background:#fafbff; display:flex;
                align-items:center; justify-content:space-between; }
    .category-label { font-size:11px; color:#888; font-weight:600;
                      text-transform:uppercase; letter-spacing:0.5px; }
    .part-name  { font-size:14px; font-weight:500; color:#1a1a2e; }
    .part-price { font-size:13px; color:#1E88E5; font-weight:600; }
    .summary-box { background:linear-gradient(135deg,#1565C0,#1E88E5);
                   border-radius:14px; padding:20px; color:white; }
    .total-price { font-size:26px; font-weight:700; margin-top:10px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_ram_gb(name):
    m = re.search(r'(\d+)\s*GB', name.upper())
    return int(m.group(1)) if m else 0

def extract_ddr_type(name):
    m = re.search(r'DDR(\d)', name.upper())
    return f"DDR{m.group(1)}" if m else None

def get_cpu_info(name):
    name = name.upper()
    info = {"brand":"INTEL","gen":None,"socket":None,"is_f_type":False,"is_tray":False,"tier":None}
    if "ULTRA" in name:
        info.update({"gen":"ULTRA","tier":"ULTRA","is_f_type":True})
        if "TRAY" in name or "NO FAN" in name: info["is_tray"] = True
        return info
    m = re.search(r'\bI([3579])\b', name)
    if m: info["tier"] = f"I{m.group(1)}"
    m2 = re.search(r'I[3579]-(\d{2,2})\d{2,3}', name)
    if m2: info["gen"] = int(m2.group(1))
    else:
        m3 = re.search(r'\b(1[0-9])(\d{3})\b', name)
        if m3: info["gen"] = int(m3.group(1))
    if re.search(r'\d{3,4}F\b', name): info["is_f_type"] = True
    if "TRAY" in name or "NO FAN" in name: info["is_tray"] = True
    return info

def is_mobo_compatible(cpu_info, mobo_series):
    gen = cpu_info["gen"]
    if gen == 10: return mobo_series in ["H410","H510"]
    if gen == 11: return mobo_series in ["H510"]
    if gen in [12,13,14]: return mobo_series in ["H610","B660","B760","Z790"]
    if gen == "ULTRA": return mobo_series in ["H810","B860","Z890"]
    return True

def get_mobo_series(name):
    for s in ["H410","H510","H610","H810","B660","B760","B860","Z790","Z890",
              "A520","A620","B450","B550","B650","B840","B850","X870"]:
        if s in name.upper(): return s
    return None

def get_mobo_category(series, price):
    cats = {"office":False,"standar":False,"advance":False}
    h = ["H410","H510","H610","H810"]
    aa = ["A520","A620"]
    bi = ["B660","B760","B860"]
    zi = ["Z790","Z890"]
    ba = ["B450","B550","B650","B840","B850"]
    xa = ["X870"]
    if series in h:  cats["office"] = True
    elif series in aa: cats["office"] = True
    elif series in bi:
        if price < 2_000_000: cats["standar"] = True
        else: cats["advance"] = True
    elif series in zi: cats["advance"] = True
    elif series in ba: cats["standar"] = cats["advance"] = True
    elif series in xa: cats["advance"] = True
    return cats

def get_vga_category(name):
    name = name.upper()
    cats = {"office":False,"standar":False,"advance":False}
    if any(s in name for s in ["GT710","GT730"]): cats["office"] = True; return cats
    if any(s in name for s in ["RTX5060TI","RTX5060 TI","RTX5070TI","RTX5070 TI","RTX5080","RTX5090"]):
        cats["advance"] = True; return cats
    if "RTX5060" in name and "TI" not in name: cats["advance"] = True; return cats
    if "RTX5070" in name and "TI" not in name: cats["advance"] = True; return cats
    if any(s in name for s in ["GT1030","GTX1650","RTX3050","RTX3060","RTX5050","RTX4060"]):
        cats["standar"] = True; return cats
    if re.search(r'RTX\s*\d*[56]0\b', name): cats["standar"] = True; return cats
    if re.search(r'RTX\s*\d*[789]\d\b', name): cats["advance"] = True; return cats
    cats["standar"] = True; return cats


# ============================================================
# PROCESS DATA
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
    df['cpu_is_f'] = df['cpu_is_tray'] = False

    # Processor — Intel Only
    for idx in df[df['Kategori']=='Processor'].index:
        name = df.at[idx,'Nama Accurate'].upper()
        if "RYZEN" in name or ("AMD" in name and "INTEL" not in name): continue
        cpu = get_cpu_info(name)
        df.at[idx,'cpu_brand']   = cpu['brand']
        df.at[idx,'cpu_gen']     = cpu['gen']
        df.at[idx,'cpu_socket']  = cpu['socket']
        df.at[idx,'cpu_tier']    = cpu['tier']
        df.at[idx,'cpu_is_f']    = cpu['is_f_type']
        df.at[idx,'cpu_is_tray'] = cpu['is_tray']
        df.at[idx,'need_vga']    = 1 if cpu['is_f_type'] else 0
        df.at[idx,'need_cooler'] = 1 if cpu['is_tray'] else 0
        t, f = cpu['tier'], cpu['is_f_type']
        if t in ["I3","I5"] and not f: df.at[idx,'cat_office']  = True
        if t in ["I3","I5"] and f:     df.at[idx,'cat_standar'] = True
        if t in ["I7","I9"] and f:     df.at[idx,'cat_advance'] = True
        if t == "ULTRA":               df.at[idx,'cat_advance'] = True

    # Motherboard
    for idx in df[df['Kategori']=='Motherboard'].index:
        name   = df.at[idx,'Nama Accurate'].upper()
        series = get_mobo_series(name)
        price  = df.at[idx,'Web']
        df.at[idx,'mobo_series'] = series
        if series:
            c = get_mobo_category(series, price)
            df.at[idx,'cat_office']  = c['office']
            df.at[idx,'cat_standar'] = c['standar']
            df.at[idx,'cat_advance'] = c['advance']
        else:
            df.at[idx,'cat_office'] = df.at[idx,'cat_standar'] = df.at[idx,'cat_advance'] = True
        df.at[idx,'mobo_ddr'] = extract_ddr_type(name)

    # RAM — exclude SODIMM
    rm = df['Kategori']=='Memory RAM'
    df = df[~(rm & df['Nama Accurate'].str.upper().str.contains('SODIMM', na=False))].copy()
    for idx in df[df['Kategori']=='Memory RAM'].index:
        name = df.at[idx,'Nama Accurate']
        gb   = extract_ram_gb(name)
        df.at[idx,'ram_ddr'] = extract_ddr_type(name)
        if 8  <= gb <= 16: df.at[idx,'cat_office']  = True
        if 16 <= gb <= 32: df.at[idx,'cat_standar'] = True
        if 32 <= gb <= 64: df.at[idx,'cat_advance'] = True
        if gb == 0: df.at[idx,'cat_office'] = df.at[idx,'cat_standar'] = df.at[idx,'cat_advance'] = True

    # SSD — exclude WDS120G2GOB
    sm = df['Kategori']=='SSD Internal'
    df = df[~(sm & df['Nama Accurate'].str.upper().str.contains('WDS120G2GOB', na=False))].copy()
    for idx in df[df['Kategori']=='SSD Internal'].index:
        name = df.at[idx,'Nama Accurate'].upper()
        df.at[idx,'cat_office'] = df.at[idx,'cat_standar'] = True
        if 'NVME' in name or 'M.2' in name or 'M2' in name:
            df.at[idx,'cat_advance'] = True

    # VGA
    for idx in df[df['Kategori']=='VGA'].index:
        c = get_vga_category(df.at[idx,'Nama Accurate'])
        df.at[idx,'cat_office']  = c['office']
        df.at[idx,'cat_standar'] = c['standar']
        df.at[idx,'cat_advance'] = c['advance']

    # Casing — exclude Armageddon, advance > 600rb
    cm = df['Kategori']=='Casing PC'
    df = df[~(cm & df['Nama Accurate'].str.upper().str.contains('ARMAGEDDON', na=False))].copy()
    for idx in df[df['Kategori']=='Casing PC'].index:
        name  = df.at[idx,'Nama Accurate'].upper()
        price = df.at[idx,'Web']
        df.at[idx,'cat_office']  = True
        df.at[idx,'cat_standar'] = True
        df.at[idx,'cat_advance'] = price > 600_000
        if 'PSU' in name or 'VALCAS' in name:
            df.at[idx,'has_psu'] = 1

    # PSU
    for idx in df[df['Kategori']=='Power Supply'].index:
        price = df.at[idx,'Web']
        name  = df.at[idx,'Nama Accurate'].upper()
        if price < 500_000:  df.at[idx,'cat_office']  = True
        if price >= 500_000: df.at[idx,'cat_standar'] = True
        if any(l in name for l in ['BRONZE','GOLD','PLATINUM']): df.at[idx,'cat_advance'] = True

    # CPU Cooler
    for idx in df[df['Kategori']=='CPU Cooler'].index:
        price = df.at[idx,'Web']
        if price < 300_000:                df.at[idx,'cat_office']  = True
        if 250_000 <= price <= 1_000_000:  df.at[idx,'cat_standar'] = True
        if price > 500_000:                df.at[idx,'cat_advance'] = True

    return df


# ============================================================
# BUNDLING
# ============================================================

def sorted_items(items, mode, branch_col):
    if items.empty: return items
    if mode == 'stok_terbanyak': return items.sort_values(branch_col, ascending=False)
    if mode == 'harga_termurah': return items.sort_values('Web', ascending=True)
    if mode == 'smart_pick':
        mn = items['Web'].min()
        r  = items[items['Web'] <= mn + 100_000]
        return r.sort_values(branch_col, ascending=False)
    return items

def build_bundle(available, branch_col, mode, variant_idx):
    def pick(items):
        r = sorted_items(items, mode, branch_col)
        if r.empty: return None
        return r.iloc[min(variant_idx, len(r)-1)]

    bundle = {}
    proc = pick(available[available['Kategori']=='Processor'])
    if proc is None: return None
    bundle['Processor'] = proc

    cpu_info = {'brand': proc.get('cpu_brand','INTEL'), 'gen': proc.get('cpu_gen',None), 'socket': proc.get('cpu_socket',None)}
    mobos = available[available['Kategori']=='Motherboard']
    compat = mobos[mobos['mobo_series'].apply(lambda s: is_mobo_compatible(cpu_info, s))]
    mobo = pick(compat)
    if mobo is None: return None
    bundle['Motherboard'] = mobo

    rams = available[available['Kategori']=='Memory RAM']
    ddr  = mobo.get('mobo_ddr', None)
    if ddr:
        rc = rams[rams['ram_ddr']==ddr]
        if not rc.empty: rams = rc
    ram = pick(rams)
    if ram is not None: bundle['Memory RAM'] = ram

    ssd = pick(available[available['Kategori']=='SSD Internal'])
    if ssd is not None: bundle['SSD Internal'] = ssd

    if proc.get('need_vga',0)==1:
        vga = pick(available[available['Kategori']=='VGA'])
        if vga is not None: bundle['VGA'] = vga

    casing = pick(available[available['Kategori']=='Casing PC'])
    if casing is not None: bundle['Casing PC'] = casing

    if not (casing is not None and casing.get('has_psu',0)==1):
        psu = pick(available[available['Kategori']=='Power Supply'])
        if psu is not None: bundle['Power Supply'] = psu

    if proc.get('need_cooler',0)==1:
        cooler = pick(available[available['Kategori']=='CPU Cooler'])
        if cooler is not None: bundle['CPU Cooler'] = cooler

    return {"parts": bundle, "total": sum(i['Web'] for i in bundle.values())}

def rebuild_from_processor(proc, available, branch_col):
    def pf(items): return sorted_items(items,'harga_termurah',branch_col).iloc[0] if not items.empty else None
    bundle = {'Processor': proc}
    cpu_info = {'brand': proc.get('cpu_brand','INTEL'), 'gen': proc.get('cpu_gen',None), 'socket': proc.get('cpu_socket',None)}
    compat = available[available['Kategori']=='Motherboard']
    compat = compat[compat['mobo_series'].apply(lambda s: is_mobo_compatible(cpu_info, s))]
    mobo = pf(compat)
    if mobo is None: return None
    bundle['Motherboard'] = mobo
    rams = available[available['Kategori']=='Memory RAM']
    ddr  = mobo.get('mobo_ddr', None)
    if ddr:
        rc = rams[rams['ram_ddr']==ddr]
        if not rc.empty: rams = rc
    ram = pf(rams)
    if ram is not None: bundle['Memory RAM'] = ram
    ssd = pf(available[available['Kategori']=='SSD Internal'])
    if ssd is not None: bundle['SSD Internal'] = ssd
    if proc.get('need_vga',0)==1:
        vga = pf(available[available['Kategori']=='VGA'])
        if vga is not None: bundle['VGA'] = vga
    casing = pf(available[available['Kategori']=='Casing PC'])
    if casing is not None: bundle['Casing PC'] = casing
    if not (casing is not None and casing.get('has_psu',0)==1):
        psu = pf(available[available['Kategori']=='Power Supply'])
        if psu is not None: bundle['Power Supply'] = psu
    if proc.get('need_cooler',0)==1:
        cooler = pf(available[available['Kategori']=='CPU Cooler'])
        if cooler is not None: bundle['CPU Cooler'] = cooler
    return bundle

def rebuild_from_mobo(mobo, current_bundle, available, branch_col):
    bundle = dict(current_bundle)
    bundle['Motherboard'] = mobo
    rams = available[available['Kategori']=='Memory RAM']
    ddr  = mobo.get('mobo_ddr', None)
    if ddr:
        rc = rams[rams['ram_ddr']==ddr]
        if not rc.empty: rams = rc
    if not rams.empty: bundle['Memory RAM'] = rams.sort_values('Web').iloc[0]
    return bundle

def rebuild_from_casing(casing, current_bundle, available, branch_col):
    bundle = dict(current_bundle)
    bundle['Casing PC'] = casing
    if casing.get('has_psu',0)==1:
        bundle.pop('Power Supply', None)
    else:
        if 'Power Supply' not in bundle:
            psus = available[available['Kategori']=='Power Supply']
            if not psus.empty: bundle['Power Supply'] = psus.sort_values('Web').iloc[0]
    return bundle

def generate_bundles(df, branch_col, cat_col, price_min=0, price_max=0):
    available = df[(df[branch_col]>0) & (df[cat_col]==True)].copy()
    use_filter = not (price_min==0 and price_max==0)
    modes = [
        {"key":"stok_terbanyak","label":"Stok Terbanyak","desc":"Produk stok terbanyak","badge":"badge-stock",
         "variants":["#1 Stok Tertinggi","#2 Stok Tinggi","#3 Stok Cukup"]},
        {"key":"harga_termurah","label":"Harga Termurah","desc":"Produk harga termurah","badge":"badge-price",
         "variants":["#1 Termurah","#2 Budget","#3 Ekonomis"]},
        {"key":"smart_pick","label":"Smart Pick","desc":"Termurah + range 100rb, stok terbanyak","badge":"badge-smart",
         "variants":["#1 Smart","#2 Smart","#3 Smart"]},
    ]
    grouped = []
    for m in modes:
        group = {"label":m["label"],"desc":m["desc"],"badge":m["badge"],"cards":[]}
        for vi in range(3):
            b = build_bundle(available, branch_col, m["key"], vi)
            if b:
                in_range = (price_min <= b["total"] <= price_max) if use_filter else True
                group["cards"].append({"name":m["variants"][vi],"badge":m["badge"],"in_range":in_range,**b})
        grouped.append(group)
    return grouped


# ============================================================
# CHAT AGENT — STATE MACHINE
# ============================================================

BRANCH_MAP = {
    "Surabaya": ["Stock A - ITC","Stock B","Stock Y - SBY"],
    "Jakarta":  ["Stock C6"],
    "Semarang": ["Stock D - SMG"],
    "Jogja":    ["Stock E - JOG"],
    "Malang":   ["Stock F - MLG"],
    "Bali":     ["Stock H - BALI"],
}

def chat_init():
    defaults = {
        'chat_messages': [],
        'chat_step': 0,
        'chat_data': {},
        'chat_open': False,
        'chat_result_bundle': None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def chat_add(role, text, choices=None, input_type=None, is_result=False):
    st.session_state.chat_messages.append({
        "role": role, "text": text,
        "choices": choices or [],
        "input_type": input_type,
        "is_result": is_result,
    })

def chat_start():
    st.session_state.chat_messages = []
    st.session_state.chat_step     = 1
    st.session_state.chat_data     = {}
    st.session_state.chat_result_bundle = None
    chat_add("agent",
        "Halo! Saya **PC Wizard** 👋\n\nKomputer ini untuk kebutuhan apa?",
        choices=["🖥️ Office — Kerja & dokumen","🎮 Standar — Gaming ringan & editing","⚡ Advance — Gaming berat & rendering"]
    )

def build_best_bundle_for_budget(cat_col, branch, budget):
    """
    Generate semua variasi bundle (3 mode x 3 variant = 9),
    lalu kembalikan yang totalnya paling mendekati budget dari bawah.
    Jika semua melebihi budget, kembalikan yang paling murah.
    """
    df_raw = st.session_state.get("processed_data", None)
    if df_raw is None:
        return None, None

    df_work = df_raw.copy()
    bcols   = BRANCH_MAP[branch]
    df_work["_cs"] = df_work[bcols].sum(axis=1) if branch == "Surabaya" else df_work[bcols[0]]
    available = df_work[(df_work["_cs"] > 0) & (df_work[cat_col] == True)].copy()

    candidates = []
    for mode in ["smart_pick", "harga_termurah", "stok_terbanyak"]:
        for vi in range(3):
            b = build_bundle(available, "_cs", mode, vi)
            if b:
                candidates.append(b)

    if not candidates:
        return None, None

    # Pisah: dalam budget vs melebihi budget
    within  = [b for b in candidates if b["total"] <= budget]
    over    = [b for b in candidates if b["total"] >  budget]

    # Duplikat bisa ada — ambil unik berdasarkan total
    seen = set()
    unique = []
    for b in candidates:
        key = tuple(sorted(b["parts"].keys())) + (round(b["total"]),)
        if key not in seen:
            seen.add(key)
            unique.append(b)

    within = [b for b in unique if b["total"] <= budget]
    over   = [b for b in unique if b["total"] >  budget]

    if within:
        # Paling mendekati budget dari bawah
        best = max(within, key=lambda b: b["total"])
    else:
        # Semua melebihi — pilih yang paling murah
        best = min(over, key=lambda b: b["total"])

    return best, available


def chat_process(choice):
    step = st.session_state.chat_step
    chat_add("user", choice)

    # ── STEP 1: Pilih kategori ──────────────────────────────
    if step == 1:
        if "Office" in choice:
            st.session_state.chat_data.update({"kategori": "Office", "cat_col": "cat_office"})
        elif "Standar" in choice:
            st.session_state.chat_data.update({"kategori": "Standar", "cat_col": "cat_standar"})
        else:
            st.session_state.chat_data.update({"kategori": "Advance", "cat_col": "cat_advance"})

        kat    = st.session_state.chat_data["kategori"]
        ranges = {"Office": "< Rp 10 juta", "Standar": "Rp 10–20 juta", "Advance": "> Rp 20 juta"}
        chat_add("agent",
            f"Oke, **{kat}** ({ranges[kat]}) 👍\n\nBerapa **budget** kamu?\n*(Ketik angka, contoh: 8000000)*",
            input_type="number"
        )
        st.session_state.chat_step = 2

    # ── STEP 2: Input budget ────────────────────────────────
    elif step == 2:
        try:
            budget = int(re.sub(r"[^\d]", "", choice))
            st.session_state.chat_data["budget"] = budget
            chat_add("agent",
                f"Budget **Rp {budget:,.0f}** ✅\n\nDari cabang mana?",
                choices=list(BRANCH_MAP.keys())
            )
            st.session_state.chat_step = 3
        except:
            chat_add("agent",
                "⚠️ Angka tidak valid. Ketik angka saja, contoh: **8000000**",
                input_type="number"
            )

    # ── STEP 3: Pilih cabang → langsung generate ────────────
    elif step == 3:
        branch = next((b for b in BRANCH_MAP if b in choice), "Surabaya")
        st.session_state.chat_data["branch"] = branch
        cd     = st.session_state.chat_data

        if st.session_state.get("processed_data") is None:
            chat_add("agent", "⚠️ Data belum diupload. Upload file dulu ya!", choices=["🔄 Mulai Ulang"])
            st.session_state.chat_step = 4
            return

        bundle, _ = build_best_bundle_for_budget(cd["cat_col"], branch, cd["budget"])

        if bundle is None:
            chat_add("agent",
                f"😔 Tidak ada bundle untuk **{cd['kategori']}** di **{branch}**. Stok mungkin kosong.",
                choices=["🔄 Mulai Ulang"]
            )
            st.session_state.chat_step = 4
            return

        st.session_state.chat_result_bundle = bundle
        total  = bundle["total"]
        budget = cd["budget"]

        lines = []
        for cat, item in bundle["parts"].items():
            n = item["Nama Accurate"]
            n = n[:40] + "…" if len(n) > 40 else n
            lines.append(f"• **{cat}**: {n}\n  Rp {item['Web']:,.0f}")

        note = (f"✅ Sisa budget **Rp {budget - total:,.0f}**"
                if total <= budget else
                f"⚠️ Melebihi budget **Rp {total - budget:,.0f}**")

        chat_add("agent",
            f"🎉 **Bundle terbaik untuk budget kamu!**\n\n" +
            "\n\n".join(lines) +
            f"\n\n💰 **Total: Rp {total:,.0f}**\n{note}",
            choices=["✅ Lihat Detail & Sesuaikan", "🔄 Mulai Ulang"],
            is_result=True
        )
        st.session_state.chat_step = 4

    # ── STEP 4: Aksi setelah hasil ──────────────────────────
    elif step == 4:
        if "Lihat Detail" in choice:
            b  = st.session_state.chat_result_bundle
            cd = st.session_state.chat_data
            if b:
                st.session_state.selected_bundle = {
                    "name":  f"Chat Wizard — {cd['kategori']} ({cd['branch']})",
                    "parts": dict(b["parts"]),
                    "total": b["total"],
                }
                st.session_state.view      = "detail"
                st.session_state.chat_open = False
        elif "Mulai Ulang" in choice:
            chat_start()


# ============================================================
# CHAT UI RENDERER — proper chat bubble style
# ============================================================

def render_chat():
    """
    Chat bubble kiri (agent) / kanan (user) menggunakan
    st.components.v1.html agar HTML+CSS bisa render penuh
    tanpa disanitasi Streamlit. Interaksi (tombol, input)
    tetap pakai widget Streamlit native di luar iframe.
    """
    import streamlit.components.v1 as components

    msgs = st.session_state.chat_messages

    # ── Bangun HTML seluruh percakapan ───────────────────
    bubbles_html = ""
    for msg in msgs:
        txt = msg["text"]
        # Konversi markdown sederhana → HTML
        txt = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", txt)
        txt = txt.replace("\n", "<br>")

        if msg["role"] == "agent":
            bubbles_html += f"""
            <div style="display:flex;align-items:flex-end;gap:8px;margin:6px 0;">
              <div style="width:30px;height:30px;border-radius:50%;flex-shrink:0;
                          background:linear-gradient(135deg,#1565C0,#42A5F5);
                          display:flex;align-items:center;justify-content:center;
                          font-size:14px;box-shadow:0 2px 6px rgba(21,101,192,.35);">🤖</div>
              <div style="background:#fff;border:1px solid #e2e8f6;
                          border-radius:4px 16px 16px 16px;
                          padding:10px 14px;max-width:76%;
                          font-size:13px;line-height:1.65;color:#1a1a2e;
                          box-shadow:0 2px 8px rgba(0,0,0,.07);">{txt}</div>
            </div>"""
        else:
            bubbles_html += f"""
            <div style="display:flex;justify-content:flex-end;margin:6px 0;">
              <div style="background:linear-gradient(135deg,#1565C0,#1976D2);
                          color:#fff;border-radius:16px 4px 16px 16px;
                          padding:10px 14px;max-width:72%;
                          font-size:13px;line-height:1.65;
                          box-shadow:0 2px 8px rgba(21,101,192,.4);">{txt}</div>
            </div>"""

    full_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Segoe UI',sans-serif; background:#f0f4fb; }}

  /* ── Header ── */
  .header {{
    background:linear-gradient(135deg,#0d47a1,#1976D2);
    padding:12px 18px;
    display:flex; align-items:center; gap:10px;
    border-radius:14px 14px 0 0;
  }}
  .header .av {{
    width:36px;height:36px;border-radius:50%;
    background:rgba(255,255,255,.2);
    display:flex;align-items:center;justify-content:center;font-size:18px;
  }}
  .header .nm  {{ color:#fff;font-weight:700;font-size:14px; }}
  .header .sub {{ color:rgba(255,255,255,.72);font-size:11px;margin-top:1px; }}

  /* ── Scroll area ── */
  .msgs {{
    padding:14px 14px 10px;
    overflow-y:auto;
    min-height:240px;
    max-height:360px;
    background:#f0f4fb;
  }}

  /* ── Footer hint ── */
  .footer {{
    background:#fff;border-top:1px solid #e2e8f6;
    padding:8px 16px;border-radius:0 0 14px 14px;
    font-size:11px;color:#aaa;
  }}
</style>
</head>
<body>
<div style="border:1.5px solid #dde8ff;border-radius:14px;
            box-shadow:0 6px 24px rgba(21,101,192,.14);overflow:hidden;">

  <div class="header">
    <div class="av">🤖</div>
    <div>
      <div class="nm">PC Wizard</div>
      <div class="sub">Asisten Rekomendasi Bundling PC</div>
    </div>
  </div>

  <div class="msgs" id="chatbox">
    {bubbles_html if bubbles_html else
     '<div style="text-align:center;padding:40px 0;color:#aaa;font-size:13px;">Mulai percakapan...</div>'}
  </div>

  <div class="footer">💡 Pilih salah satu opsi di bawah untuk melanjutkan</div>
</div>

<script>
  // Auto-scroll ke bawah setiap load
  var cb = document.getElementById("chatbox");
  if(cb) cb.scrollTop = cb.scrollHeight;
</script>
</body>
</html>"""

    # Hitung tinggi dinamis: ~60px per pesan, min 340, max 560
    height = min(max(340, len(msgs) * 62 + 120), 560)
    components.html(full_html, height=height, scrolling=False)

    # ── Interaksi: tombol + input (di luar iframe) ───────
    last_agent = next((m for m in reversed(msgs) if m["role"] == "agent"), None)
    if last_agent:
        choices    = last_agent.get("choices", [])
        input_type = last_agent.get("input_type")

        if choices:
            n    = len(choices)
            cols = st.columns(min(n, 3))
            for ci, ch in enumerate(choices):
                with cols[ci % len(cols)]:
                    if st.button(ch, key=f"ch_{len(msgs)}_{ci}", use_container_width=True):
                        chat_process(ch)
                        st.rerun()

        if input_type == "number":
            col_in, col_send = st.columns([5, 1])
            with col_in:
                val = st.text_input(
                    "Budget", label_visibility="collapsed",
                    placeholder="Contoh: 8000000",
                    key=f"num_in_{len(msgs)}"
                )
            with col_send:
                if st.button("Kirim ➤", key=f"send_{len(msgs)}", use_container_width=True):
                    if val.strip():
                        chat_process(val.strip())
                        st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("🔄 Reset", key="reset_chat_btn", use_container_width=True):
        chat_start()
        st.rerun()



# ============================================================
# MAIN APP
# ============================================================

st.title("🖥️ PC Wizard Pro")
st.caption("Sistem Rekomendasi Bundling PC Otomatis")

chat_init()

if 'view' not in st.session_state:             st.session_state.view = 'main'
if 'selected_bundle' not in st.session_state:  st.session_state.selected_bundle = None
if 'prev_usage_label' not in st.session_state: st.session_state.prev_usage_label = None

uploaded_file = st.file_uploader("Upload Data Portal (CSV atau XLSX)", type=["csv","xlsx"])

if uploaded_file:
    with st.spinner("Memproses data..."):
        raw_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        data   = process_data(raw_df)
        st.session_state.processed_data = data

    # ── SIDEBAR ───────────────────────────────────────────
    st.sidebar.header("Konfigurasi")

    selected_branch = st.sidebar.selectbox("Cabang", list(BRANCH_MAP.keys()), index=0)
    bcols = BRANCH_MAP[selected_branch]
    data['_stock_branch'] = data[bcols].sum(axis=1) if selected_branch=="Surabaya" else data[bcols[0]]
    branch_col = '_stock_branch'

    usage_options = {"Office":"cat_office","Standar":"cat_standar","Advance":"cat_advance"}
    usage_label   = st.sidebar.radio(
        "Kategori Penggunaan", list(usage_options.keys()),
        format_func=lambda x: {"Office":"Office (< 10 jt)","Standar":"Standar (10-20 jt)","Advance":"Advance (> 20 jt)"}[x]
    )

    _info = {
        "Office": (
            "**Cocok untuk:** kerja harian, browsing, dokumen\n\n"
            "- Rentang bundle: **Rp 0 – 10 juta**\n"
            "- CPU: Intel i3/i5 Non-F (ada iGPU, tanpa VGA)\n"
            "- RAM: 8–16 GB\n"
            "- Jasa rakit: Rp 100.000\n\n"
            "⚠️ Bundle di luar Rp 10 jt tetap tampil dengan tanda *di luar rentang*."
        ),
        "Standar": (
            "**Cocok untuk:** gaming ringan, desain grafis, multitasking\n\n"
            "- Rentang bundle: **Rp 10 – 20 juta**\n"
            "- CPU: Intel i3/i5 tipe F + VGA mid-range\n"
            "- RAM: 16–32 GB\n"
            "- Jasa rakit: Rp 150.000\n\n"
            "⚠️ Bundle di luar rentang tetap tampil dengan tanda *di luar rentang*."
        ),
        "Advance": (
            "**Cocok untuk:** gaming berat, rendering, video editing\n\n"
            "- Rentang bundle: **> Rp 20 juta**\n"
            "- CPU: Intel i7/i9 tipe F atau Intel Ultra\n"
            "- RAM: 32–64 GB · VGA high-end\n"
            "- Jasa rakit: Rp 200.000\n\n"
            "⚠️ Bundle di bawah Rp 20 jt tetap tampil dengan tanda *di luar rentang*."
        ),
    }
    with st.sidebar.expander(f"ℹ️ Info kategori {usage_label}", expanded=False):
        st.markdown(_info[usage_label])

    if st.session_state.prev_usage_label and st.session_state.prev_usage_label != usage_label:
        st.session_state.view = 'main'
        st.session_state.selected_bundle = None
        st.session_state.pop('ganti_cat', None)
    st.session_state.prev_usage_label = usage_label

    cat_col      = usage_options[usage_label]
    assembly_fee = {"Office":100_000,"Standar":150_000,"Advance":200_000}[usage_label]

    pr_map = {"Office":(0,10_000_000),"Standar":(10_000_000,20_000_000),"Advance":(20_000_000,100_000_000)}
    dmin, dmax = pr_map[usage_label]
    st.sidebar.divider()
    price_min = st.sidebar.number_input("Harga Min (Rp)", min_value=0, value=dmin, step=500_000)
    price_max = st.sidebar.number_input("Harga Max (Rp)", min_value=0, value=dmax, step=500_000)

    # ── MAIN VIEW ─────────────────────────────────────────
    if st.session_state.view == 'main':

        # ── CHAT PANEL (collapsible, di atas bundling) ────
        st.markdown("---")
        col_lbl, col_toggle = st.columns([5,1])
        with col_lbl:
            if st.session_state.chat_open:
                st.markdown("#### 💬 PC Wizard — Chat Advisor")
        with col_toggle:
            btn_label = "✕ Tutup" if st.session_state.chat_open else "💬 Chat"
            if st.button(btn_label, use_container_width=True):
                st.session_state.chat_open = not st.session_state.chat_open
                if st.session_state.chat_open and not st.session_state.chat_messages:
                    chat_start()
                st.rerun()

        if st.session_state.chat_open:
            with st.container(border=True):
                render_chat()

        st.markdown("---")
        st.subheader(f"Rekomendasi Bundling — {usage_label} | {selected_branch}")

        grouped  = generate_bundles(data, branch_col, cat_col, price_min, price_max)
        any_card = any(len(g["cards"])>0 for g in grouped)
        if not any_card:
            st.warning("Tidak ada bundling. Pastikan data sudah diupload dan filter sesuai.")

        btn_counter = 0
        for group in grouped:
            st.markdown(f"""
            <div style="margin:20px 0 6px 0;">
                <span style="font-size:17px;font-weight:700;color:#1a1a2e;">{group['label']}</span>
                <span style="font-size:12px;color:#888;margin-left:10px;">{group['desc']}</span>
            </div>""", unsafe_allow_html=True)

            if not group["cards"]:
                st.caption("Tidak ada bundle untuk mode ini.")
                continue

            cols = st.columns(3)
            for j, card in enumerate(group["cards"]):
                with cols[j]:
                    bc  = "#e0e0e0" if card["in_range"] else "#ffcdd2"
                    op  = "1" if card["in_range"] else "0.65"
                    orn = "" if card["in_range"] else '<div style="font-size:11px;color:#e53935;margin-top:4px;">Di luar rentang harga</div>'
                    st.markdown(f"""
                    <div class="bundle-card" style="border-color:{bc};opacity:{op};">
                        <span class="badge {card['badge']}">{card['name']}</span>
                        <div class="price-text">Rp {card['total']:,.0f}</div>
                        <div style="font-size:11px;color:#888;">{len(card['parts'])} komponen</div>
                        {orn}
                    </div>""", unsafe_allow_html=True)
                    if st.button("Pilih & Sesuaikan", key=f"btn_{btn_counter}", use_container_width=True):
                        st.session_state.selected_bundle = {
                            "name": f"{group['label']} — {card['name']}",
                            "parts": dict(card["parts"]),
                            "total": card["total"],
                        }
                        st.session_state.view = 'detail'
                        st.rerun()
                    btn_counter += 1

            st.markdown("<hr style='border:none;border-top:1px solid #f0f0f0;margin:8px 0 4px 0;'>",
                        unsafe_allow_html=True)

        with st.expander("Info Filter Produk Aktif"):
            st.markdown("""
            - **Processor**: Hanya Intel (AMD tidak digunakan)
            - **RAM**: SODIMM dihapus
            - **SSD**: WDS120G2GOB dihapus
            - **Casing**: Armageddon dihapus; Advance hanya > Rp 600.000
            - **VGA**: Muncul hanya jika Processor tipe F
            - **PSU**: Dihapus jika Casing include PSU/VALCAS
            - **CPU Cooler**: Muncul hanya jika Processor Tray
            """)

    # ── DETAIL VIEW ───────────────────────────────────────
    elif st.session_state.view == 'detail':
        bundle = st.session_state.selected_bundle

        if 'ganti_cat' not in st.session_state:
            st.session_state.ganti_cat = None

        c1, c2 = st.columns([1,8])
        with c1:
            if st.button("← Kembali"):
                st.session_state.view      = 'main'
                st.session_state.ganti_cat = None
                st.rerun()
        with c2:
            st.subheader(bundle['name'])

        st.divider()
        col_parts, col_sum = st.columns([3,1])
        display_order = ['Processor','Motherboard','Memory RAM','SSD Internal','VGA','Casing PC','Power Supply','CPU Cooler']

        with col_parts:
            st.markdown("#### Komponen Terpilih")
            updated_parts = {}

            for cat in display_order:
                if cat not in bundle['parts']: continue
                item = bundle['parts'][cat]

                ci, cg, ch = st.columns([8,1,1])
                with ci:
                    st.markdown(f"""
                    <div class="part-row">
                        <div>
                            <div class="category-label">{cat}</div>
                            <div class="part-name">{item['Nama Accurate']}</div>
                        </div>
                        <div class="part-price">Rp {item['Web']:,.0f}</div>
                    </div>""", unsafe_allow_html=True)
                with cg:
                    st.write("")
                    if st.button("♻️", key=f"ganti_{cat}", help=f"Ganti {cat}"):
                        st.session_state.ganti_cat = None if st.session_state.ganti_cat==cat else cat
                        st.rerun()
                with ch:
                    st.write("")
                    if not st.button("—", key=f"del_{cat}", help=f"Hapus {cat}"):
                        updated_parts[cat] = item

                if st.session_state.ganti_cat == cat:
                    avail_all = data[(data[branch_col]>0) & (data[cat_col]==True)].copy()
                    alts      = avail_all[avail_all['Kategori']==cat].sort_values('Web')

                    if cat=='Memory RAM' and 'Motherboard' in bundle['parts']:
                        ddr = bundle['parts']['Motherboard'].get('mobo_ddr', None)
                        if ddr:
                            ad = alts[alts['ram_ddr']==ddr]
                            if not ad.empty: alts = ad

                    if alts.empty:
                        st.caption("Tidak ada produk lain tersedia.")
                    else:
                        st.markdown(f"""
                        <div style="background:#f0f4ff;border:1px solid #c5d3f0;border-radius:10px;
                                    padding:10px 14px;margin-bottom:8px;">
                            <div style="font-size:12px;font-weight:700;color:#1565C0;">
                                Pilih pengganti untuk {cat}
                            </div>
                        </div>""", unsafe_allow_html=True)

                        for _, ar in alts.iterrows():
                            ic  = ar['Nama Accurate'] == item['Nama Accurate']
                            lbl = f"{'[Terpilih] ' if ic else ''}{ar['Nama Accurate']}  —  Rp {ar['Web']:,.0f}  |  Stok: {int(ar[branch_col])}"
                            if st.button(lbl, key=f"pilih_{cat}_{ar.name}", disabled=ic, use_container_width=True):
                                ad = ar.to_dict()
                                if cat=='Processor':
                                    np = rebuild_from_processor(ad, avail_all, branch_col)
                                    if np: st.session_state.selected_bundle['parts'] = np
                                elif cat=='Motherboard':
                                    np = rebuild_from_mobo(ad, bundle['parts'], avail_all, branch_col)
                                    st.session_state.selected_bundle['parts'] = np
                                elif cat=='Casing PC':
                                    np = rebuild_from_casing(ad, bundle['parts'], avail_all, branch_col)
                                    st.session_state.selected_bundle['parts'] = np
                                else:
                                    st.session_state.selected_bundle['parts'][cat] = ad
                                st.session_state.ganti_cat = None
                                st.rerun()

            st.session_state.selected_bundle['parts'] = updated_parts

        with col_sum:
            total_items  = sum(i['Web'] for i in updated_parts.values())
            is_assembled = st.checkbox("Tambah Jasa Rakit", value=False,
                                       help=f"Biaya jasa rakit: Rp {assembly_fee:,.0f}")
            grand_total  = total_items + (assembly_fee if is_assembled else 0)

            ph = ""
            for i in updated_parts.values():
                ph += f'<div style="font-size:12px;margin:3px 0;opacity:0.9;">• {i["Nama Accurate"][:28]}…</div>'
            if is_assembled:
                ph += f'<div style="font-size:12px;margin:3px 0;opacity:0.9;">• Jasa Rakit {usage_label}</div>'

            st.markdown(f"""
            <div class="summary-box">
                <div style="font-size:13px;opacity:0.85;margin-bottom:6px;">RINGKASAN</div>
                {ph}
                <hr style="border-color:rgba(255,255,255,0.3);margin:10px 0;">
                <div style="font-size:13px;opacity:0.85;">Total Harga</div>
                <div class="total-price">Rp {grand_total:,.0f}</div>
            </div>""", unsafe_allow_html=True)

            st.write("")
            if st.button("Konfirmasi Bundling", use_container_width=True, type="primary"):
                st.balloons()
                st.success(f"Bundle dikonfirmasi! Total: Rp {grand_total:,.0f}")