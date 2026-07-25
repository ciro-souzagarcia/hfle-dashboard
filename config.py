# Configuracoes para o Dashboard Cloud (sem tokens secretos)
HMA_PERIODS = [8, 13, 21, 34, 55, 89, 116, 144, 188, 233, 377]
TIMEFRAME_MINUTES = 5

# CROSS-TF config (igual ao main.py)
CROSS_TF_ENABLED = True
CROSS_TF_FAST = [1, 1, 5, 5, 5, 5, 5, 5]
CROSS_TF_SLOW = [5, 6, 10, 15, 20, 30, 60, 120]
CROSS_TF_HMAS = [8, 13, 21, 34, 55, 89]
CROSS_TF_ALERTA_HMAS = [21, 34, 55, 89]
CROSS_TF_FREE_MODE = "PER_HMA"
MT5_HISTORY_START_DATE = "2026-04-20"

# Telegram - usar secrets do Streamlit Cloud
import os
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_TFS = [5, 6, 10, 15, 20, 30, 60, 120]
TELEGRAM_NOTIFY_ALL_HISTORY = True
