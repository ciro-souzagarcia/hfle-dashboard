import os, time, pandas as pd, streamlit as st
from datetime import datetime
from config import CROSS_TF_SLOW, MT5_HISTORY_START_DATE

BASE = os.path.dirname(os.path.abspath(__file__))
TFS = sorted(int(m) for m in CROSS_TF_SLOW if int(m) > 1)

st.set_page_config(page_title="HFLE", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
  .stApp { padding: 4px 8px !important; }
  .stApp header, #MainMenu, footer { display: none !important; }
  div[data-testid="stVerticalBlock"] { gap: 2px !important; }

  .tf-dot { display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:50%;font-size:18px;font-weight:700;margin:2px;flex-shrink:0; }
  .tf-dot-label { text-align:center;font-size:9px;color:#aaa;margin-top:-2px; }
  .tf-dot-wrap { display:flex;flex-direction:column;align-items:center;margin:0 2px; }
  .tf-row { display:flex;overflow-x:auto;gap:2px;padding:2px 0;flex-wrap:nowrap; }

  .ev { display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #333;font-size:15px;gap:8px; }
  .ev-time { color:#aaa;min-width:100px;font-size:14px; }
  .ev-tag-r { background:#2196F3;color:#000;border-radius:4px;padding:1px 8px;font-size:12px;font-weight:700; }
  .ev-tag-a { background:#FF9800;color:#000;border-radius:4px;padding:1px 8px;font-size:12px;font-weight:700; }
  .ev-tf { font-weight:700;min-width:40px;text-align:center;font-size:14px;color:#fff; }
  .ev-hma { color:#ddd;font-size:14px; }

  [data-testid="stDateInput"] { min-width:100px; }
  [data-testid="stDateInput"] input { font-size:12px;padding:2px 6px; }
  .stButton button { font-size:11px;padding:2px 8px;min-height:0; }
  .config-box { background:#1a1d23;border:1px solid #444;border-radius:8px;padding:8px;margin:4px 0; }
  .stTabs [data-baseweb="tab"] { font-size:14px;padding:4px 12px; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:2px 0;">'
    f'<span style="font-weight:700;font-size:16px;">▎HFLE</span>'
    f'<span style="color:#888;font-size:11px;">{datetime.now():%H:%M}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── listar ficheiros (debug) ──
arqs = [f for f in os.listdir(BASE) if f.endswith(".csv")]
if len(arqs) == 0:
    st.error("Nenhum CSV encontrado em " + BASE)
else:
    st.caption(f"{len(arqs)} CSVs carregados")

# ── TF ROW ──
tfs_html = '<div class="tf-row">'
for tf in TFS:
    fp = os.path.join(BASE, f"OUTPUT_M{tf}.csv")
    try:
        df = pd.read_csv(fp, sep=";", decimal=",", nrows=1)
        trend = str(df.iloc[-1].get("trend", "NEUTRAL"))
        sym, cor = ("▲", "#2196F3") if trend == "UPTREND" else ("▼", "#FF9800") if trend == "DOWNTREND" else ("●", "#9E9E9E")
    except:
        sym, cor = "●", "#555"
    tfs_html += f'<div class="tf-dot-wrap"><div class="tf-dot" style="background:{cor}20;border:2px solid {cor}80;color:{cor};">{sym}</div><div class="tf-dot-label">M{tf}</div></div>'
tfs_html += '</div>'
st.markdown(tfs_html, unsafe_allow_html=True)

# ── DATE BAR ──
col_data, col_conf = st.columns([3, 1])
with col_data:
    data_ini = st.date_input("📅", value=datetime.strptime(MT5_HISTORY_START_DATE, "%Y-%m-%d").date(), label_visibility="collapsed")
with col_conf:
    mostra_config = st.checkbox("⚙️", label_visibility="collapsed")

data_ts = pd.Timestamp(data_ini)

# ── CONFIG ──
if mostra_config:
    with st.container():
        st.markdown('<div class="config-box">', unsafe_allow_html=True)
        from notifier import tfs_activos, salvar_tfs_activos, send_telegram, cross_tfs_activos, salvar_cross_tfs_activos
        atuais = tfs_activos()
        cross_atuais = cross_tfs_activos()
        c1, c2 = st.columns(2)
        with c1:
            rev_on = st.checkbox("🔔 REVERSAL", value=len(atuais) > 0)
            if rev_on and len(atuais) == 0: salvar_tfs_activos(TFS)
            elif not rev_on and len(atuais) > 0: salvar_tfs_activos([])
        with c2:
            al_on = st.checkbox("⚠️ ALERTA", value=len(cross_atuais) > 0)
            if al_on and len(cross_atuais) == 0: salvar_cross_tfs_activos(TFS)
            elif not al_on and len(cross_atuais) > 0: salvar_cross_tfs_activos([])
        t1, t2 = st.columns(2)
        with t1:
            if st.button("🔔 Testar REVERSAL", use_container_width=True): send_telegram("<b>HFLE</b>\nReversal OK ✅")
        with t2:
            if st.button("⚠️ Testar ALERTA", use_container_width=True): send_telegram("<b>HFLE</b>\nAlerta OK ✅")
        st.markdown('</div>', unsafe_allow_html=True)

# ── CARREGAR EVENTOS ──
reversais = []
alertas = []
for tf in TFS:
    fp = os.path.join(BASE, f"OUTPUT_M{tf}.csv")
    if not os.path.exists(fp):
        continue
    try:
        df = pd.read_csv(fp, sep=";", decimal=",", usecols=["datetime","event","trend"])
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df[df["datetime"] >= data_ts]
        df = df[df["event"].notna() & (df["event"] != "")]
        for _, r in df.iterrows():
            reversais.append({"data": r["datetime"], "tf": f"M{tf}", "hma": str(r.get("event",""))})
    except Exception as e:
        st.warning(f"M{tf}: {e}")

import glob, re
for fp in sorted(glob.glob(os.path.join(BASE, "CROSS_TF_M*_VS_M*.csv"))):
    fn = os.path.basename(fp)
    m = re.search(r"_VS_M(\d+)\.csv$", fn)
    if not m:
        continue
    try:
        cdf = pd.read_csv(fp, sep=";", decimal=",", usecols=["datetime","slow_tf","period","direction"])
        cdf["datetime"] = pd.to_datetime(cdf["datetime"], errors="coerce")
        cdf = cdf[cdf["datetime"] >= data_ts]
        if cdf.empty:
            continue
        for _, r in cdf.iterrows():
            alertas.append({"data": r["datetime"], "tf": f"M{int(r['slow_tf'])}", "hma": f'HMA{r["period"]}'})
    except Exception as e:
        st.warning(f"{fn}: {e}")

st.caption(f"{len(reversais)} reversais, {len(alertas)} alertas")

# ── ABAS ──
aba_rev, aba_al = st.tabs(["🔄 REVERSAL", "⚠️ ALERTA"])

with aba_rev:
    if reversais:
        df_r = pd.DataFrame(reversais).sort_values("data", ascending=False)
        for _, r in df_r.iterrows():
            ts = r["data"].strftime("%d/%m %H:%M") if hasattr(r["data"], "strftime") else str(r["data"])
            st.markdown(f'<div class="ev"><span class="ev-time">{ts}</span><span class="ev-tag-r">R</span><span class="ev-tf">{r["tf"]}</span><span class="ev-hma">{r["hma"]}</span></div>', unsafe_allow_html=True)
    else:
        st.info("Nenhum")

with aba_al:
    if alertas:
        df_a = pd.DataFrame(alertas).sort_values("data", ascending=False)
        for _, r in df_a.iterrows():
            ts = r["data"].strftime("%d/%m %H:%M") if hasattr(r["data"], "strftime") else str(r["data"])
            st.markdown(f'<div class="ev"><span class="ev-time">{ts}</span><span class="ev-tag-a">A</span><span class="ev-tf">{r["tf"]}</span><span class="ev-hma">{r["hma"]}</span></div>', unsafe_allow_html=True)
    else:
        st.info("Nenhum")
