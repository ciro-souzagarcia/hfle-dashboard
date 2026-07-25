import os, time, pandas as pd, streamlit as st
from datetime import datetime
from config import CROSS_TF_SLOW, MT5_HISTORY_START_DATE

BASE = os.path.dirname(os.path.abspath(__file__))
CORES = {"UPTREND": "#2196F3", "DOWNTREND": "#FF9800", "NEUTRAL": "#9E9E9E"}
TFS = sorted(int(m) for m in CROSS_TF_SLOW if int(m) > 1)

st.set_page_config(page_title="HFLE Dashboard", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
@media (max-width: 768px) {
  div[data-testid="stSidebarNav"] { display: none; }
  .stApp header { display: none; }
  .card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
}
@media (min-width: 769px) {
  .card-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
}
.event-row {
  display: flex; align-items: center; gap: 4px; flex-wrap: wrap;
  padding: 3px 0; border-bottom: 1px solid #333; font-size: 13px;
}
.event-time { color: #aaa; min-width: 80px; }
.event-tf { font-weight: 600; min-width: 36px; text-align: center; }
.event-dir-up { color: #2196F3; font-weight: 700; }
.event-dir-down { color: #FF9800; font-weight: 700; }
.event-tag-up { background:#2196F3; color:#000; border-radius:4px; padding:1px 5px; font-size:10px; }
.event-tag-down { background:#FF9800; color:#000; border-radius:4px; padding:1px 5px; font-size:10px; }
div[data-testid="stVerticalBlock"] { gap: 4px; }
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

# ═══════════ SIDEBAR (desktop) ═══════════
st.sidebar.title("HFLE Dashboard")
modo = st.sidebar.radio("Modo", ["Histórico", "Online"], index=0)
tf_sel = st.sidebar.selectbox("TF", ["Todos"] + [f"M{t}" for t in TFS], index=0)
tf_all = tf_sel == "Todos"
tf_num = None if tf_all else int(tf_sel.replace("M", ""))
if modo == "Online":
    intervalo = st.sidebar.slider("Auto refresh (s)", 1, 60, 5)

with st.sidebar.expander("Telegram (REVERSAL)", expanded=False):
    from notifier import tfs_activos, salvar_tfs_activos, send_telegram, cross_tfs_activos, salvar_cross_tfs_activos
    atuais = tfs_activos()
    novos = []
    for tf in sorted(TFS):
        ligado = st.checkbox(f"M{tf}", value=tf in atuais, key=f"tel_{tf}")
        if ligado:
            novos.append(tf)
    if set(novos) != atuais:
        salvar_tfs_activos(novos)
    if st.button("🔔 Testar"):
        ok = send_telegram("<b>HFLE Dashboard</b>\nTeste OK ✅")
        st.success("Enviada!") if ok else st.error("Falha")

with st.sidebar.expander("⚠️ Alerta Cross-TF", expanded=False):
    cross_atuais = cross_tfs_activos()
    cross_novos = []
    for tf in sorted(TFS):
        ligado = st.checkbox(f"M{tf}", value=tf in cross_atuais, key=f"cross_{tf}")
        if ligado:
            cross_novos.append(tf)
    if set(cross_novos) != cross_atuais:
        salvar_cross_tfs_activos(cross_novos)
    if st.button("🔔 Testar Cross"):
        ok = send_telegram("<b>HFLE Dashboard</b>\n⚠ Teste Cross OK ✅")
        st.success("Enviada!") if ok else st.error("Falha")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Última atualização:** {datetime.now():%H:%M:%S}")

# ═══════════ ESTADO DOS TIMEFRAMES ═══════════
st.subheader("Estado")
def seta(trend):
    if trend == "UPTREND":
        return "▲", "#2196F3"
    if trend == "DOWNTREND":
        return "▼", "#FF9800"
    return "●", "#9E9E9E"

cards = []
for tf in TFS:
    df = carregar_output(tf)
    if df is None or len(df) == 0:
        continue
    fp = os.path.join(BASE, f"OUTPUT_M{tf}.csv")
    mtime = os.path.getmtime(fp)
    idade_min = (time.time() - mtime) / 60
    trend = str(df.iloc[-1].get("trend", "NEUTRAL"))
    sym, cor = seta(trend)
    cards.append((tf, cor, sym, idade_min))

st.markdown('<div class="card-grid">', unsafe_allow_html=True)
for tf, cor, sym, idade_min in cards:
    if idade_min < 2:
        rodape = f'<span style="color:#9E9E9E">✓</span>'
    elif idade_min < 30:
        rodape = f'<span style="color:#888">{int(idade_min)}\'</span>'
    else:
        rodape = f'<span style="color:#FF9800">⚠ {int(idade_min)}\'</span>'
    st.markdown(
        f'<div style="background:{cor}15;border:1.5px solid {cor}60;'
        f'padding:6px 2px;border-radius:10px;text-align:center;">'
        f'<div style="font-size:24px;line-height:1.2;color:{cor};font-weight:700">{sym}</div>'
        f'<div style="font-weight:600;font-size:12px">M{tf}</div>'
        f'<div style="font-size:10px">{rodape}</div></div>',
        unsafe_allow_html=True,
    )
st.markdown('</div>', unsafe_allow_html=True)

# ═══════════ ULTIMOS EVENTOS (compacto) ═══════════
st.markdown("---")
st.subheader("Eventos")
data_ini = st.date_input(
    "De", value=datetime.strptime(MT5_HISTORY_START_DATE, "%Y-%m-%d").date(),
    key="ev_data_ini", label_visibility="collapsed",
)

tfs_filtro = [tf_num] if tf_num else TFS
data_ts = pd.Timestamp(data_ini)
total = 0

try:
    eventos = []
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
            sinal_cls = "event-dir-up" if direction == "UP" else "event-dir-down"
            eventos.append({
                "tipo": "A", "data": r["datetime"], "tf": f"M{int(r['slow_tf'])}",
                "desc": f'HMA{r["period"]}', "dir": f'{arrow}',
            })

    if eventos:
        ev_df = pd.DataFrame(eventos)
        ev_df = ev_df.sort_values("data", ascending=False).head(200)
        total = len(ev_df)
        for _, r in ev_df.iterrows():
            d = r["data"]
            if hasattr(d, "strftime"):
                dt_str = d.strftime("%d/%m %H:%M")
            else:
                dt_str = str(d)
            cls_dir = "event-dir-up" if "▲" in str(r["dir"]) else "event-dir-down" if "▼" in str(r["dir"]) else ""
            tag = f'<span class="event-tag-up">R</span>' if r["tipo"] == "R" else f'<span class="event-tag-down">A</span>'
            st.markdown(
                f'<div class="event-row">'
                f'<span class="event-time">{dt_str}</span>'
                f'{tag}'
                f'<span class="event-tf">{r["tf"]}</span>'
                f'<span class="{cls_dir}">{r["dir"]}</span>'
                f'<span style="color:#ccc">{r["desc"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.caption(f"{total} eventos desde {data_ini}")
    else:
        st.info("Nenhum evento encontrado no período.")
except Exception as e:
    st.error(f"Erro: {e}")
    import traceback
    st.code(traceback.format_exc())

# ═══════════ ONLINE ═══════════
if modo == "Online":
    time.sleep(intervalo)
    st.rerun()
