import json, os, time, urllib.request, urllib.error
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

_last_send = 0.0
_MIN_INTERVAL = 0.05
_cooldown_until = 0.0
_cooldown_until = 0.0  # 50ms entre mensagens (~20 msg/s)

def arrow(trend_or_dir):
    """▲ para UPTREND/UP, ▼ para DOWNTREND/DOWN, ● neutro."""
    t = str(trend_or_dir).upper()
    if t in ("UPTREND", "UP"):
        return "▲"
    if t in ("DOWNTREND", "DOWN"):
        return "▼"
    return "●"

PREFS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telegram_prefs.json")

def _load_prefs():
    if not os.path.exists(PREFS_FILE):
        return {}
    try:
        with open(PREFS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def tfs_activos():
    """Retorna set de timeframes que podem enviar notificacao."""
    prefs = _load_prefs()
    raw = prefs.get("tfs")
    if raw is None:
        from config import TELEGRAM_TFS
        return set(TELEGRAM_TFS)
    return set(raw)

def salvar_tfs_activos(tfs_lista):
    prefs = _load_prefs()
    prefs["tfs"] = list(tfs_lista)
    with open(PREFS_FILE, "w") as f:
        json.dump(prefs, f)

def cross_tfs_activos():
    """Retorna TFs com alerta cross-TF ativo.
    
    Se o user nunca configurou o seletor "Alerta Cross-TF" OU se
    desmarcou todas as opcoes (lista vazia), herda o filtro do 
    REVERSAL (tfs_activos). Se configurou explicitamente com TFs,
    usa essa configuracao com autonomia total.
    """
    prefs = _load_prefs()
    raw = prefs.get("cross_tfs")
    if not raw:
        return tfs_activos()
    return set(raw)

def salvar_cross_tfs_activos(tfs_lista):
    prefs = _load_prefs()
    prefs["cross_tfs"] = list(tfs_lista)
    with open(PREFS_FILE, "w") as f:
        json.dump(prefs, f)

NOTIFIED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telegram_notified.json")

def _notified():
    if not os.path.exists(NOTIFIED_FILE):
        return set()
    try:
        with open(NOTIFIED_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def _reset_notified():
    if os.path.exists(NOTIFIED_FILE):
        try:
            os.remove(NOTIFIED_FILE)
            print("  [Reset] telegram_notified.json removido")
        except Exception as e:
            print(f"  [Reset] erro ao remover telegram_notified.json: {e}")

def _marcar_notificado(keys):
    """Marca um conjunto de chaves como notificadas.
    
    Aceita str (chave única) ou set (lote)."""
    if isinstance(keys, str):
        keys = {keys}
    n = _notified()
    n |= keys
    import time
    for attempt in range(10):
        try:
            with open(NOTIFIED_FILE, "w") as f:
                json.dump(sorted(n), f)
            return
        except PermissionError:
            if attempt < 9:
                time.sleep(1)

def notificar_reversoes_csv():
    """Varre OUTPUT_M*.csv e notifica REVERSALS conforme TELEGRAM_NOTIFY_ALL_HISTORY.
    Retorna lista de eventos (dt_str, msg_lines, key) para envio sincronizado."""
    import glob, pandas as pd
    from config import MT5_HISTORY_START_DATE, TELEGRAM_NOTIFY_ALL_HISTORY
    BASE = os.path.dirname(os.path.abspath(__file__))
    ativos = tfs_activos()
    ja_notificados = _notified()
    inicio = MT5_HISTORY_START_DATE if TELEGRAM_NOTIFY_ALL_HISTORY else datetime.now().strftime("%Y-%m-%d")
    fila = []
    for fp in sorted(glob.glob(os.path.join(BASE, "OUTPUT_M*.csv"))):
        import re
        m = re.search(r"OUTPUT_M(\d+)", fp)
        if not m:
            continue
        tf = int(m.group(1))
        if tf not in ativos:
            continue
        df = pd.read_csv(fp, sep=";", decimal=",", low_memory=False)
        if "event" not in df.columns:
            continue
        mask = df["event"].astype(str).str.contains("REVERSAL", na=False)
        df_rev = df[mask]
        if df_rev.empty:
            continue
        if "datetime" in df_rev.columns:
            str_dt = df_rev["datetime"].astype(str)
            df_rev_filt = df_rev[str_dt >= inicio]
        else:
            df_rev_filt = df_rev
        for _, row in df_rev_filt.iterrows():
            raw_dt = str(row["datetime"])
            trend = str(row.get("trend", "?"))
            ev = str(row.get("event", "") or "")
            key = f"M{tf}_{raw_dt}_{ev}"
            if key not in ja_notificados:
                fila.append((raw_dt, [f"🔄 {arrow(trend)} M{tf} - {trend}", _fmt_dt(raw_dt), ev], key))
    fila.sort(key=lambda x: x[0])
    if not fila:
        print(f"  [Telegram] nenhuma reversao desde {inicio} pendente nos CSVs")
    else:
        print(f"  [Telegram] {len(fila)} reversoes desde {inicio} coletadas")
    return fila

def _fmt_dt(dt):
    """Formata datetime(ou string ISO) para DD-MM-YYYY -- HH:MM"""
    if hasattr(dt, "strftime"):
        return dt.strftime("%d-%m-%Y -- %H:%M")
    try:
        from datetime import datetime
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M", "%d-%m-%Y -- %H:%M"):
            try:
                return datetime.strptime(str(dt), fmt).strftime("%d-%m-%Y -- %H:%M")
            except ValueError:
                continue
    except Exception:
        pass
    return str(dt)

def send_telegram(message, silent=False):
    global _last_send, _cooldown_until
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        if not silent:
            print("  [Telegram] Token ou Chat_ID nao configurados (defina no .env)")
        return False

    agora = time.time()
    if agora < _cooldown_until:
        falta = int(_cooldown_until - agora)
        if not silent:
            print(f"  [Telegram] Cooldown ativo — {falta}s restantes, ignorado")
        return False

    elapsed = agora - _last_send
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }).encode()
    req = urllib.request.Request(url, data=data,
        headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        _last_send = time.time()
        if not silent:
            print(f"  [Telegram] OK — mensagem enviada ({len(message)} chars)")
        return True
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", errors="replace")
        if e.code == 429:
            import re as _re
            m = _re.search(r'"retry_after":\s*(\d+)', corpo)
            segundos = int(m.group(1)) if m else 60
            _cooldown_until = time.time() + segundos
            if not silent:
                print(f"  [Telegram] HTTP 429 — cooldown {segundos}s ativado")
            return False
        if not silent:
            print(f"  [Telegram] HTTP {e.code} ({e.reason}): {corpo[:200]}")
        return False
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        if not silent:
            print(f"  [Telegram] ERRO rede: {e}")
        return False
