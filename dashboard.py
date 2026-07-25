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
  div[data-testid="stHorizontalBlock"] { gap: 4px !important; flex-wrap: wrap; }

  .tf-dot {
    display: inline-flex; align-items: center; justify-content: center;
    width: 40px; height: 40px; border-radius: 50%;
    font-size: 18px; font-weight: 700;
    margin: 2px; flex-shrink: 0;
  }
  .tf-dot-label { text-align: center; font-size: 9px; color: #aaa; margin-top: -2px; }
  .tf-dot-wrap { display: flex; flex-direction: column; align-items: center; margin: 0 2px; }
  .tf-row { display: flex; overflow-x: auto; gap: 2px; padding: 2px 0; flex-wrap: nowrap; }

  .ev { display: flex; align-items: center; padding: 3px 0; border-bottom: 1px solid #222; font-size: 12px; gap: 4px; }
  .ev-time { color: #888; min-width: 78px; font-size: 11px; }
  .ev-tag-r { background:#2196F3; color:#000; border-radius: 3px; padding: 0 4px; font-size: 9px; font-weight: 700; }
  .ev-tag-a { background:#FF9800; color:#000; border-radius: 3px; padding: 0 4px; font-size: 9px; font-weight: 700; }
  .ev-tf { font-weight: 600; min-width: 30px; text-align: center; font-size: 11px; }
  .ev-dir { min-width: 14px; font-weight: 700; }
  .ev-desc { color: #aaa; font-size: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .bottom-bar {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: #0e1117; border-top: 1px solid #333;
    padding: 4px 8px; display: flex; align-items: center; gap: 6px;
    z-index: 999;
  }
  .bottom-bar select, .bottom-bar input { font-size: 12px; }

  body { padding-bottom: 50px; }
  [data-testid="stDateInput"] { min-width: 100px; }
  [data-testid="stDateInput"] input { font-size: 12px; padding: 2px 6px; }
  .stButton button { font-size: 11px; padding: 2px 8px; min-height: 0; }

  .config-popup { background:#1a1d23; border:1px solid #444; border-radius:8px; padding:8px; margin:4px 0; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def carregar_output(tf):
    fp = os.path.join(BASE, f"OUTPUT_M{tf}.csv")
    if not os.path.exists(fp):
        return None
    try:
        df = pd.read_csv(fp, sep=";", decimal=",", low_memory=False,
                         usecols=lambda c: c in ["datetime", "event", "trend"])
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        return df
    except:
        return None

@st.cache_data(ttl=600)
def carregar_cross_tf(tfs_filtro, data_ts):
    import glob, re
    partes = []
    for fp in sorted(glob.glob(os.path.join(BASE, "CROSS_TF_M*_VS_M*.csv"))):
        fn = os.path.basename(fp)
        m = re.search(r"_VS_M(\d+)\.csv$", fn)
        if not m or int(m.group(1)) not in tfs_filtro:
            continue
        try:
            cdf = pd.read_csv(fp, sep=";", decimal=",", low_memory=False,
                              usecols=["datetime", "slow_tf", "period", "direction"])
            cdf["datetime"] = pd.to_datetime(cdf["datetime"], errors="coerce")
            cdf = cdf[cdf["datetime"] >= data_ts]
            if cdf.empty:
                continue
            cdf["slow_tf"] = cdf["slow_tf"].astype(int)
            partes.append(cdf)
        except:
            pass
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()

def seta(trend):
    if trend == "UPTREND":
        return "▲", "#2196F3"
    if trend == "DOWNTREND":
        return "▼", "#FF9800"
    return "●", "#9E9E9E"

# ── state ──
if "show_config" not in st.session_state:
    st.session_state.show_config = False

# ═══ HEADER ═══
st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:2px 0;">'
    f'<span style="font-weight:700;font-size:16px;">▎HFLE</span>'
    f'<span style="color:#888;font-size:11px;">{datetime.now():%H:%M}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ═══ TF ROW ═══
tfs_html = '<div class="tf-row">'
for tf in TFS:
    df = carregar_output(tf)
    if df is None or len(df) == 0:
        sym, cor = "●", "#555"
    else:
        trend = str(df.iloc[-1].get("trend", "NEUTRAL"))
        sym, cor = seta(trend)
    borda = cor
    tfs_html += (
        f'<div class="tf-dot-wrap">'
        f'<div class="tf-dot" style="background:{cor}20;border:2px solid {borda}80;color:{cor};">{sym}</div>'
        f'<div class="tf-dot-label">M{tf}</div>'
        f'</div>'
    )
tfs_html += '</div>'
st.markdown(tfs_html, unsafe_allow_html=True)

# ═══ DATE + FILTER BAR (flutuante no topo) ═══
col_data, col_conf, _ = st.columns([1.5, 1, 1])
with col_data:
    data_ini = st.date_input(
        "📅", value=datetime.strptime(MT5_HISTORY_START_DATE, "%Y-%m-%d").date(),
        key="data_picker", label_visibility="collapsed",
    )
with col_conf:
    if st.button("⚙️", help="Configurar notificações Telegram"):
        st.session_state.show_config = not st.session_state.show_config

data_ts = pd.Timestamp(data_ini)

# ── config popup ──
if st.session_state.show_config:
    with st.container():
        st.markdown('<div class="config-popup">', unsafe_allow_html=True)
        from notifier import tfs_activos, salvar_tfs_activos, send_telegram, cross_tfs_activos, salvar_cross_tfs_activos
        st.markdown('<span style="font-weight:600;font-size:12px;">🔔 REVERSAL</span>', unsafe_allow_html=True)
        atuais = tfs_activos()
        cols_r = st.columns(8)
        novos = []
        for i, tf in enumerate(sorted(TFS)):
            with cols_r[i % 8]:
                if st.checkbox(f"M{tf}", value=tf in atuais, key=f"r_{tf}"):
                    novos.append(tf)
        if set(novos) != atuais:
            salvar_tfs_activos(novos)

        st.markdown('<span style="font-weight:600;font-size:12px;">⚠️ ALERTA</span>', unsafe_allow_html=True)
        cross_atuais = cross_tfs_activos()
        cols_a = st.columns(8)
        cross_novos = []
        for i, tf in enumerate(sorted(TFS)):
            with cols_a[i % 8]:
                if st.checkbox(f"M{tf}", value=tf in cross_atuais, key=f"a_{tf}"):
                    cross_novos.append(tf)
        if set(cross_novos) != cross_atuais:
            salvar_cross_tfs_activos(cross_novos)

        ct, t1, t2 = st.columns([1, 1, 1])
        with t1:
            if st.button("🔔 Testar Reversal", use_container_width=True):
                send_telegram("<b>HFLE</b>\nReversal OK ✅")
        with t2:
            if st.button("⚠️ Testar Alerta", use_container_width=True):
                send_telegram("<b>HFLE</b>\nAlerta OK ✅")
        with ct:
            if st.button("✕ Fechar", use_container_width=True):
                st.session_state.show_config = False
        st.markdown('</div>', unsafe_allow_html=True)

# ═══ EVENTOS ═══
st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:2px 0;margin-top:2px;">'
    f'<span style="font-size:13px;font-weight:600;">Eventos</span>'
    f'<span style="color:#888;font-size:10px;">{data_ini}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

tfs_filtro = TFS
eventos = []
try:
    for tf in tfs_filtro:
        df = carregar_output(tf)
        if df is None:
            continue
        ev = df[df["datetime"] >= data_ts]
        ev = ev[ev["event"].notna() & (ev["event"] != "")]
        for _, r in ev.iterrows():
            eventos.append({
                "tipo": "R", "data": r["datetime"], "tf": f"M{tf}",
                "desc": r.get("event", ""), "dir": r.get("trend", ""),
            })

    cross_df = carregar_cross_tf(tuple(tfs_filtro), data_ts)
    if not cross_df.empty:
        for _, r in cross_df.iterrows():
            direction = str(r.get("direction", "")).upper()
            arrow = "▲" if direction == "UP" else "▼"
            eventos.append({
                "tipo": "A", "data": r["datetime"], "tf": f"M{int(r['slow_tf'])}",
                "desc": f'HMA{r["period"]}', "dir": arrow,
            })

    if eventos:
        ev_df = pd.DataFrame(eventos)
        ev_df = ev_df.sort_values("data", ascending=False).head(60)
        for _, r in ev_df.iterrows():
            d = r["data"]
            dt_str = d.strftime("%d/%m %H:%M") if hasattr(d, "strftime") else str(d)
            dir_cls = "color:#2196F3" if r["dir"] == "▲" else "color:#FF9800" if r["dir"] == "▼" else ""
            tag = "ev-tag-r" if r["tipo"] == "R" else "ev-tag-a"
            tag_txt = "R" if r["tipo"] == "R" else "A"
            st.markdown(
                f'<div class="ev">'
                f'<span class="ev-time">{dt_str}</span>'
                f'<span class="{tag}">{tag_txt}</span>'
                f'<span class="ev-tf">{r["tf"]}</span>'
                f'<span class="ev-dir" style="{dir_cls}">{r["dir"]}</span>'
                f'<span class="ev-desc">{r["desc"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Nenhum evento")
except Exception as e:
    st.error(str(e))
