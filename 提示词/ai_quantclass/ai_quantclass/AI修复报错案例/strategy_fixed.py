#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【AI修复后的策略代码】
修复：IndexError: list index out of range
"""

import pandas as pd
import numpy as np

def compute_signal(prices, lookback=20):
    """
    计算动量信号（AI修复版）

    修复方案：
    1. 添加长度检查
    2. 从第lookback个数据开始计算
    3. 前面的数据填充NaN
    """
    signals = []

    # ✅ 修复：检查数据长度
    if len(prices) < lookback:
        print(f"⚠️ 警告：数据长度({len(prices)})不足{lookback}，无法计算完整信号")

    for i in range(len(prices)):
        # ✅ 修复：只有当i >= lookback时才计算
        if i >= lookback:
            signal = prices[i] / prices[i - lookback] - 1
        else:
            signal = np.nan  # 数据不足时填充NaN

        signals.append(signal)

    return signals


def compute_ma(prices, window=20):
    """
    计算移动平均（AI修复版）

    修复方案：
    1. 前window-1个数据填充NaN
    2. 使用正确的切片范围
    """
    ma_values = []

    for i in range(len(prices)):
        # ✅ 修复：只有当i >= window-1时才计算
        if i >= window - 1:
            start_idx = i - window + 1
            ma = sum(prices[start_idx:i+1]) / window
        else:
            ma = np.nan  # 数据不足时填充NaN

        ma_values.append(ma)

    return ma_values


def compute_signal_vectorized(prices, lookback=20):
    """
    向量化版本（更优方案）
    """
    prices_series = pd.Series(prices)
    # pandas自动处理边界情况，前面填充NaN
    signals = prices_series / prices_series.shift(lookback) - 1
    return signals.tolist()


def compute_ma_vectorized(prices, window=20):
    """
    向量化版本（更优方案）
    """
    prices_series = pd.Series(prices)
    # pandas自动处理边界情况
    ma = prices_series.rolling(window=window).mean()
    return ma.tolist()


def backtest(df):
    """
    简单回测
    """
    prices = df['close'].tolist()

    print(f"数据长度: {len(prices)}")
    print(f"前5个价格: {prices[:5]}")

    # 计算信号（使用修复后的函数）
    print("\n计算动量信号...")
    signals = compute_signal(prices, lookback=20)

    print("\n计算移动平均...")
    ma = compute_ma(prices, window=20)

    return signals, ma


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("【策略回测 - AI修复版】")
    print("=" * 60)

    # 测试1：数据不足的情况（15条）
    print("\n" + "-" * 40)
    print("测试1：数据不足（15条）")
    print("-" * 40)

    df_small = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=15),
        'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                  110, 112, 111, 113, 115]
    })

    signals, ma = backtest(df_small)
    print(f"\n信号结果: {signals}")
    print(f"MA结果: {ma}")
    print("\n✅ 数据不足时不再报错，用NaN填充！")

    # 测试2：数据充足的情况（30条）
    print("\n" + "-" * 40)
    print("测试2：数据充足（30条）")
    print("-" * 40)

    df_large = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=30),
        'close': 100 + np.cumsum(np.random.randn(30))
    })

    signals2, ma2 = backtest(df_large)
    print(f"\n信号结果（前25个）: {[f'{s:.4f}' if not np.isnan(s) else 'NaN' for s in signals2[:25]]}")
    print(f"\n✅ 数据充足时正常计算！")

    # 展示修复对比
    print("\n" + "=" * 60)
    print("【修复对比】")
    print("=" * 60)
    print("""
┌─────────────────────────────────────────────────────────────┐
│  ❌ 原始代码（会报错）                                        │
├─────────────────────────────────────────────────────────────┤
│  def compute_signal(prices):                                │
│      for i in range(len(prices)):                           │
│          signal = prices[i] / prices[i - 20] - 1  # 越界！   │
│          signals.append(signal)                             │
└─────────────────────────────────────────────────────────────┘

                          ⬇️ AI修复

┌─────────────────────────────────────────────────────────────┐
│  ✅ 修复代码（安全）                                          │
├─────────────────────────────────────────────────────────────┤
│  def compute_signal(prices, lookback=20):                   │
│      for i in range(len(prices)):                           │
│          if i >= lookback:  # 添加边界检查                   │
│              signal = prices[i] / prices[i - lookback] - 1  │
│          else:                                              │
│              signal = np.nan  # 数据不足填充NaN              │
│          signals.append(signal)                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🚀 更优方案（向量化）                                        │
├─────────────────────────────────────────────────────────────┤
│  def compute_signal_vectorized(prices, lookback=20):        │
│      prices_series = pd.Series(prices)                      │
│      return (prices_series / prices_series.shift(lookback)  │
│              - 1).tolist()                                  │
└─────────────────────────────────────────────────────────────┘
""")

    print("""
📋 AI修复要点：
   1. 添加边界检查：if i >= lookback
   2. 数据不足时填充NaN而非报错
   3. 添加警告提示用户数据不足
   4. 推荐使用pandas向量化方法（自动处理边界）

🔧 预防措施：
   • 始终检查数据长度是否满足计算需求
   • 使用pandas内置函数（如shift、rolling）自动处理边界
   • 添加异常处理和日志记录
""")
