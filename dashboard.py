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
  .ev-dir-up { color:#2196F3;font-weight:700;min-width:18px;text-align:center;font-size:16px; }
  .ev-dir-down { color:#FF9800;font-weight:700;min-width:18px;text-align:center;font-size:16px; }

  [data-testid="stDateInput"] { min-width:100px; }
  [data-testid="stDateInput"] input { font-size:12px;padding:2px 6px; }
  .stButton button { font-size:11px;padding:2px 8px;min-height:0; }
  .stTabs [data-baseweb="tab"] { font-size:14px;padding:4px 12px; }
</style>
""", unsafe_allow_html=True)

# ═══ HEADER ═══
st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:2px 0;">'
    f'<span style="font-weight:700;font-size:16px;">▎HFLE</span>'
    f'<span style="color:#888;font-size:11px;">{datetime.now():%H:%M}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

def _arrow_dir(trend_or_dir):
    t = str(trend_or_dir).upper()
    if t in ("UPTREND", "UP"):
        return "▲"
    if t in ("DOWNTREND", "DOWN"):
        return "▼"
    return ""

# ═══ TF DOTS ═══
tfs_html = '<div class="tf-row">'
for tf in TFS:
    fp = os.path.join(BASE, f"OUTPUT_M{tf}.csv")
    try:
        df = pd.read_csv(fp, sep=";", decimal=",", low_memory=False, dtype={"trend": str})
        trend = str(df["trend"].iloc[-1]) if "trend" in df.columns and len(df) > 0 else "NEUTRAL"
        sym, cor = ("▲", "#2196F3") if trend == "UPTREND" else ("▼", "#FF9800") if trend == "DOWNTREND" else ("●", "#9E9E9E")
    except:
        sym, cor = "●", "#555"
    tfs_html += f'<div class="tf-dot-wrap"><div class="tf-dot" style="background:{cor}20;border:2px solid {cor}80;color:{cor};">{sym}</div><div class="tf-dot-label">M{tf}</div></div>'
tfs_html += '</div>'
st.markdown(tfs_html, unsafe_allow_html=True)

# ═══ DATE ═══
data_ini = st.date_input("📅", value=datetime.strptime(MT5_HISTORY_START_DATE, "%Y-%m-%d").date(), label_visibility="collapsed")
data_ts = pd.Timestamp(data_ini)

# ═══ CONFIG ═══
with st.expander("🔔 REVERSAL / ⚠️ ALERTA", expanded=True):
    from notifier import tfs_activos, salvar_tfs_activos, notify, cross_tfs_activos, salvar_cross_tfs_activos
    atuais = tfs_activos()
    cross_atuais = cross_tfs_activos()

    st.markdown('<span style="font-weight:600;font-size:13px;">🔔 REVERSAL</span>', unsafe_allow_html=True)
    cols_r = st.columns(8)
    novos_r = []
    for i, tf in enumerate(sorted(TFS)):
        with cols_r[i]:
            if st.checkbox(f"M{tf}", value=tf in atuais, key=f"rev_{tf}"):
                novos_r.append(tf)
    if set(novos_r) != atuais:
        salvar_tfs_activos(novos_r)

    st.markdown('<span style="font-weight:600;font-size:13px;">⚠️ ALERTA</span>', unsafe_allow_html=True)
    cols_a = st.columns(8)
    novos_a = []
    for i, tf in enumerate(sorted(TFS)):
        with cols_a[i]:
            if st.checkbox(f"M{tf}", value=tf in cross_atuais, key=f"al_{tf}"):
                novos_a.append(tf)
    if set(novos_a) != cross_atuais:
        salvar_cross_tfs_activos(novos_a)

    t1, t2 = st.columns(2)
    with t1:
        if st.button("🔔 Testar REVERSAL", use_container_width=True): notify("<b>HFLE</b>\nReversal OK ✅")
    with t2:
        if st.button("⚠️ Testar ALERTA", use_container_width=True): notify("<b>HFLE</b>\nAlerta OK ✅")

# ═══ CARREGAR EVENTOS ═══
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
            direcao = str(r.get("trend", "")).upper()
            seta = _arrow_dir(direcao)
            reversais.append({"data": r["datetime"], "tf": f"M{tf}", "hma": str(r.get("event","")), "seta": seta, "tipo": "R"})
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
            direcao = str(r.get("direction", "")).upper()
            seta = _arrow_dir(direcao)
            alertas.append({"data": r["datetime"], "tf": f"M{int(r['slow_tf'])}", "hma": f'HMA{r["period"]}', "seta": seta, "tipo": "A"})
    except Exception as e:
        st.warning(f"{fn}: {e}")

st.caption(f"{len(reversais)} reversais, {len(alertas)} alertas")

# ═══ ABAS ═══
combinados = sorted(reversais + alertas, key=lambda x: str(x["data"]), reverse=True)

def _render_lista(eventos):
    if not eventos:
        st.info("Nenhum")
        return
    for r in eventos:
        ts = r["data"].strftime("%d/%m %H:%M") if hasattr(r["data"], "strftime") else str(r["data"])
        e_tag = "ev-tag-r" if r["tipo"] == "R" else "ev-tag-a"
        dir_cls = "ev-dir-up" if r["seta"] == "▲" else "ev-dir-down" if r["seta"] == "▼" else ""
        st.markdown(
            f'<div class="ev">'
            f'<span class="ev-time">{ts}</span>'
            f'<span class="{e_tag}">{r["tipo"]}</span>'
            f'<span class="ev-tf">{r["tf"]}</span>'
            f'<span class="{dir_cls}">{r["seta"]}</span>'
            f'<span class="ev-hma">{r["hma"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

aba_tudo, aba_rev, aba_al = st.tabs(["📋 TODOS", "🔄 REVERSAL", "⚠️ ALERTA"])
with aba_tudo:
    _render_lista(combinados)
with aba_rev:
    _render_lista(reversais)
with aba_al:
    _render_lista(alertas)
