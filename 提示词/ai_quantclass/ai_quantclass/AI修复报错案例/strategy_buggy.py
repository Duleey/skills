#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【有Bug的策略代码】
演示场景：IndexError: list index out of range
"""

import pandas as pd
import numpy as np

def compute_signal(prices):
    """
    计算20日动量信号
    信号 = 当前价格 / 20天前价格 - 1
    """
    signals = []

    for i in range(len(prices)):
        # ❌ Bug: 当i<20时，prices[i-20]会访问负索引
        # 例如 i=5 时，prices[5-20] = prices[-15] 可能越界
        signal = prices[i] / prices[i - 20] - 1
        signals.append(signal)

    return signals


def compute_ma(prices, window=20):
    """
    计算移动平均
    """
    ma_values = []

    for i in range(len(prices)):
        # ❌ Bug: 当i<window时，切片起始位置为负数
        start_idx = i - window + 1
        ma = sum(prices[start_idx:i+1]) / window
        ma_values.append(ma)

    return ma_values


def backtest(df):
    """
    简单回测
    """
    # 获取收盘价列表
    prices = df['close'].tolist()

    print(f"数据长度: {len(prices)}")
    print(f"前5个价格: {prices[:5]}")

    # 计算信号
    print("\n计算动量信号...")
    signals = compute_signal(prices)

    print("\n计算移动平均...")
    ma = compute_ma(prices)

    return signals, ma


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("【策略回测】")
    print("=" * 60)

    # 模拟数据：只有15条数据（不足20条）
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=15),
        'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                  110, 112, 111, 113, 115]
    })

    print(f"\n数据预览:\n{df}")

    # 运行回测 -> 会报错！
    signals, ma = backtest(df)

    print("\n回测完成！")
