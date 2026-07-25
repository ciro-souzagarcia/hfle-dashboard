import os, time, pandas as pd, streamlit as st
from datetime import datetime
from config import CROSS_TF_SLOW, MT5_HISTORY_START_DATE

BASE = os.path.dirname(os.path.abspath(__file__))
CORES = {"UPTREND": "#2196F3", "DOWNTREND": "#FF9800", "NEUTRAL": "#9E9E9E"}

TFS = sorted(int(m) for m in CROSS_TF_SLOW if int(m) > 1)

st.set_page_config(page_title="HFLE Dashboard", layout="wide")

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
    except Exception as e:
        st.error(f"OUTPUT_M{tf}: {e}")
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
        except Exception as e:
            st.error(f"CROSS {fn}: {e}")
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()

# ── sidebar ──
st.sidebar.title("HFLE Dashboard")
modo = st.sidebar.radio("Modo", ["Histórico", "Online"], index=0)
tf_opcoes = ["Todos"] + [f"M{t}" for t in TFS]
tf_sel = st.sidebar.selectbox("Timeframe", tf_opcoes, index=0)
tf_all = tf_sel == "Todos"
tf_num = None if tf_all else int(tf_sel.replace("M", ""))

if modo == "Online":
    intervalo = st.sidebar.slider("Auto refresh (s)", 1, 60, 5)

# ── Telegram (REVERSAL) ──
with st.sidebar.expander("Telegram (REVERSAL)", expanded=False):
    from notifier import tfs_activos, salvar_tfs_activos, send_telegram
    atuais = tfs_activos()
    novos = []
    for tf in sorted(int(m) for m in CROSS_TF_SLOW if int(m) > 1):
        ligado = st.checkbox(f"M{tf}", value=tf in atuais, key=f"tel_{tf}")
        if ligado:
            novos.append(tf)
    if set(novos) != atuais:
        salvar_tfs_activos(novos)
    if st.button("🔔 Testar Telegram"):
        ok = send_telegram("<b>HFLE Dashboard</b>\nTeste de conexão OK ✅")
        if ok:
            st.sidebar.success("Mensagem enviada!")
        else:
            st.sidebar.error("Falha. Verifique .env")

# ── Alerta Cross-TF (fast x slow HMA) ──
with st.sidebar.expander("⚠️ Alerta Cross-TF", expanded=False):
    from notifier import cross_tfs_activos, salvar_cross_tfs_activos, send_telegram
    cross_atuais = cross_tfs_activos()
    cross_novos = []
    for tf in sorted(int(m) for m in CROSS_TF_SLOW if int(m) > 1):
        ligado = st.checkbox(f"M{tf}", value=tf in cross_atuais, key=f"cross_{tf}")
        if ligado:
            cross_novos.append(tf)
    if set(cross_novos) != cross_atuais:
        salvar_cross_tfs_activos(cross_novos)
    if st.button("🔔 Testar Cross-TF"):
        ok = send_telegram("<b>HFLE Dashboard</b>\n⚠ Teste de Alerta Cross-TF OK ✅")
        if ok:
            st.sidebar.success("Mensagem enviada!")
        else:
            st.sidebar.error("Falha. Verifique .env")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Última atualização:** {datetime.now():%H:%M:%S}")

# ════════════════════════════════════════════
# ESTADO DOS TIMEFRAMES
# ════════════════════════════════════════════
st.subheader("Estado dos Timeframes")

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

cols = st.columns(6)
for i, (tf, cor, sym, idade_min) in enumerate(cards):
    with cols[i % 6]:
        if idade_min < 2:
            rodape = f'<div style="font-size:9px;color:#9E9E9E;margin-top:2px">✓ agora</div>'
        elif idade_min < 30:
            rodape = f'<div style="font-size:9px;color:#888;margin-top:2px">{int(idade_min)}min</div>'
        else:
            rodape = f'<div style="font-size:9px;color:#FF9800;margin-top:2px">⚠ {int(idade_min)}min</div>'
        st.markdown(
            f'<div style="background:{cor}15;border:2px solid {cor}60;'
            f'padding:8px 4px;margin:4px 0;border-radius:10px;text-align:center">'
            f'<div style="font-size:28px;line-height:1.1;color:{cor}">{sym}</div>'
            f'<div style="font-weight:600;font-size:14px">M{tf}</div>'
            f'{rodape}</div>',
            unsafe_allow_html=True,
        )

# ════════════════════════════════════════════
# ÚLTIMOS EVENTOS
# ════════════════════════════════════════════
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("Últimos Eventos")
with col2:
    data_ini = st.date_input(
        "De", value=datetime.strptime(MT5_HISTORY_START_DATE, "%Y-%m-%d").date(),
        key="ev_data_ini", label_visibility="collapsed",
    )

tfs_filtro = [tf_num] if tf_num else TFS
data_ts = pd.Timestamp(data_ini)

try:
    # REVERSALS
    eventos = []
    for tf in tfs_filtro:
        df = carregar_output(tf)
        if df is None:
            continue
        ev = df[df["datetime"] >= data_ts]
        ev = ev[ev["event"].notna() & (ev["event"] != "")]
        for _, r in ev.iterrows():
            eventos.append({
                "Tipo": "🔄",
                "Data": r["datetime"],
                "TF": f"M{tf}",
                "Evento": r["event"],
                "Direção": r.get("trend", ""),
            })

    # ALERTAS
    cross_df = carregar_cross_tf(tuple(tfs_filtro), data_ts)
    if not cross_df.empty:
        for _, r in cross_df.iterrows():
            eventos.append({
                "Tipo": "⚠️",
                "Data": r["datetime"],
                "TF": f"M{int(r['slow_tf'])}",
                "Evento": f"ALERTA HMA{r['period']} {r['direction']}",
                "Direção": r["direction"],
            })

    if eventos:
        ev_df = pd.DataFrame(eventos)
        ev_df["Data"] = ev_df["Data"].dt.strftime("%Y-%m-%d %H:%M")

        col_sort, col_order = st.columns([1, 1])
        with col_sort:
            sort_col = st.selectbox("Ordenar por", ["Data", "Tipo", "TF", "Evento", "Direção"], index=0)
        with col_order:
            sort_asc = st.checkbox("Ascendente", value=False)
        ev_df = ev_df.sort_values(sort_col, ascending=sort_asc)

        st.caption(f"{len(ev_df)} eventos desde {data_ini}")
        st.dataframe(ev_df, use_container_width=True, height=720)
    else:
        st.info("Nenhum evento encontrado no período.")
except Exception as e:
    st.error(f"Erro ao carregar eventos: {e}")
    import traceback
    st.code(traceback.format_exc())

# ════════════════════════════════════════════
# ONLINE - auto refresh
# ════════════════════════════════════════════
if modo == "Online":
    st.sidebar.info(f"Auto refresh a cada {intervalo}s")
    time.sleep(intervalo)
    st.rerun()
