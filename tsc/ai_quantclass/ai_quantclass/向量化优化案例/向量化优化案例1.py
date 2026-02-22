#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【代码优化演示】for循环 vs 向量化
用于直播演示：AI帮你提升代码效率
"""

import pandas as pd
import numpy as np
import time

# ============================================================
# 生成模拟数据：100万行K线数据
# ============================================================
print("=" * 60)
print("生成模拟数据：100万行K线数据...")
print("=" * 60)

np.random.seed(42)
n_rows = 1_000_000  # 100万行

df = pd.DataFrame({
    'open': np.random.uniform(100, 200, n_rows),
    'high': np.random.uniform(100, 200, n_rows),
    'low': np.random.uniform(100, 200, n_rows),
    'close': np.random.uniform(100, 200, n_rows),
    'volume': np.random.uniform(1000, 10000, n_rows)
})

# 确保high >= open,close >= low
df['high'] = df[['open', 'high', 'close']].max(axis=1)
df['low'] = df[['open', 'low', 'close']].min(axis=1)

print(f"数据形状: {df.shape}")
print(f"数据预览:\n{df.head()}")

# ============================================================
# 任务：计算多个技术因子
# 1. 涨跌幅 = (close - open) / open
# 2. 振幅 = (high - low) / low
# 3. 量价因子 = 涨跌幅 * volume
# 4. 上影线 = (high - max(open, close)) / close
# 5. 下影线 = (min(open, close) - low) / close
# ============================================================

print("\n" + "=" * 60)
print("任务：计算5个技术因子")
print("=" * 60)

# ============================================================
# 方法1：原始for循环（慢）
# ============================================================
def calculate_factors_slow(df):
    """使用for循环计算因子（初学者写法）"""
    n = len(df)
    pct_change = []
    amplitude = []
    volume_price = []
    upper_shadow = []
    lower_shadow = []

    for i in range(n):
        row = df.iloc[i]

        # 涨跌幅
        pct = (row['close'] - row['open']) / row['open']
        pct_change.append(pct)

        # 振幅
        amp = (row['high'] - row['low']) / row['low']
        amplitude.append(amp)

        # 量价因子
        vp = pct * row['volume']
        volume_price.append(vp)

        # 上影线
        upper = (row['high'] - max(row['open'], row['close'])) / row['close']
        upper_shadow.append(upper)

        # 下影线
        lower = (min(row['open'], row['close']) - row['low']) / row['close']
        lower_shadow.append(lower)

    result = pd.DataFrame({
        'pct_change': pct_change,
        'amplitude': amplitude,
        'volume_price': volume_price,
        'upper_shadow': upper_shadow,
        'lower_shadow': lower_shadow
    })
    return result


# ============================================================
# 方法2：向量化计算（快）- AI优化后
# ============================================================
# def calculate_factors_fast(df):
