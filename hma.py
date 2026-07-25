import numpy as np
import pandas as pd

from config import (
    ADX_PERIOD,
    ATR_PERIOD,
    CHOPPINESS_PERIOD,
    FAST_CONFIRMATION_HMAS,
    HMA_PERIODS,
)


def wma(series: pd.Series, period: int) -> pd.Series:
    if len(series) < period:
        return pd.Series(np.nan, index=series.index)
    if period <= 1:
        return series.copy()
    weights = np.arange(1, period + 1)
    weights_sum = weights.sum()
    w = weights / weights_sum
    res = np.convolve(series.values, w[::-1], mode='valid')
    pad = np.full(period - 1, np.nan)
    return pd.Series(np.concatenate([pad, res]), index=series.index)


def hma(series: pd.Series, period: int) -> pd.Series:
    half_length = int(period / 2)
    sqrt_length = int(np.sqrt(period))

    wma_half = wma(series, half_length)
    wma_full = wma(series, period)

    raw_hma = 2 * wma_half - wma_full

    return wma(raw_hma, sqrt_length)


def add_hmas(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]

    for period in HMA_PERIODS:
        df[f"hma{period}"] = hma(close, period)

    previous_close = close.shift(1)
    true_range = pd.concat([
        df["high"] - df["low"],
        (df["high"] - previous_close).abs(),
        (df["low"] - previous_close).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = true_range.ewm(
        alpha=1 / ATR_PERIOD, adjust=False, min_periods=ATR_PERIOD
    ).mean()

    up_move = df["high"].diff()
    down_move = -df["low"].diff()
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=df.index,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=df.index,
    )
    # Evita infinidades quando o ATR for zero (mercado sem amplitude).
    safe_atr = df["atr"].where(df["atr"] > 0)
    plus_di = 100 * plus_dm.ewm(
        alpha=1 / ADX_PERIOD, adjust=False, min_periods=ADX_PERIOD
    ).mean() / safe_atr
    minus_di = 100 * minus_dm.ewm(
        alpha=1 / ADX_PERIOD, adjust=False, min_periods=ADX_PERIOD
    ).mean() / safe_atr
    directional_sum = (plus_di + minus_di).where((plus_di + minus_di) > 0)
    dx = 100 * (plus_di - minus_di).abs() / directional_sum
    df["adx"] = dx.ewm(
        alpha=1 / ADX_PERIOD, adjust=False, min_periods=ADX_PERIOD
    ).mean()

    tr_sum = true_range.rolling(CHOPPINESS_PERIOD).sum()
    price_range = (
        df["high"].rolling(CHOPPINESS_PERIOD).max()
        - df["low"].rolling(CHOPPINESS_PERIOD).min()
    )
    safe_price_range = price_range.where(price_range > 0)
    chop_ratio = (tr_sum / safe_price_range).where(lambda value: value > 0)
    df["choppiness"] = 100 * np.log10(chop_ratio) / np.log10(CHOPPINESS_PERIOD)

    fast_columns = [f"hma{period}" for period in FAST_CONFIRMATION_HMAS]
    df["fast_hma_spread"] = df[fast_columns].max(axis=1) - df[fast_columns].min(axis=1)
    df["fast_hma_spread_atr"] = df["fast_hma_spread"] / safe_atr

    for column in ("atr", "adx", "choppiness", "fast_hma_spread_atr"):
        df[column] = df[column].replace([np.inf, -np.inf], np.nan)

    return df
