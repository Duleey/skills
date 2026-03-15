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
def calculate_factors_fast(df):
    """使用向量化计算因子（AI优化写法）"""
    result = pd.DataFrame({
        # 涨跌幅
        'pct_change': (df['close'] - df['open']) / df['open'],

        # 振幅
        'amplitude': (df['high'] - df['low']) / df['low'],

        # 量价因子
        'volume_price': (df['close'] - df['open']) / df['open'] * df['volume'],

        # 上影线
        'upper_shadow': (df['high'] - np.maximum(df['open'], df['close'])) / df['close'],

        # 下影线
        'lower_shadow': (np.minimum(df['open'], df['close']) - df['low']) / df['close']
    })
    return result


# ============================================================
# 性能对比测试
# ============================================================

# 为了演示效果，先用10万行测试for循环（100万行太慢）
print("\n" + "=" * 60)
print("【性能测试】")
print("=" * 60)

# 测试数据（for循环用10万行，否则太慢）
df_small = df.head(100_000).copy()

# 方法1：for循环（10万行）
print("\n▶ 方法1：for循环计算 (10万行数据)...")
start_time = time.time()
result_slow = calculate_factors_slow(df_small)
time_slow = time.time() - start_time
print(f"  耗时: {time_slow:.2f} 秒")

# 方法2：向量化（100万行）
print("\n▶ 方法2：向量化计算 (100万行数据)...")
start_time = time.time()
result_fast = calculate_factors_fast(df)
time_fast = time.time() - start_time
print(f"  耗时: {time_fast:.4f} 秒")

# 换算对比（估算for循环处理100万行的时间）
estimated_slow = time_slow * 10  # 10万行 * 10 = 100万行
speedup = estimated_slow / time_fast

print("\n" + "=" * 60)
print("【对比结果】")
print("=" * 60)
print(f"""
┌─────────────────────────────────────────────────────────┐
│                    性能对比结果                          │
├─────────────────────────────────────────────────────────┤
│  数据量: 100万行                                         │
├─────────────────────────────────────────────────────────┤
│  for循环（估算）:  {estimated_slow:>8.2f} 秒  (~{estimated_slow/60:.1f}分钟)          │
│  向量化:           {time_fast:>8.4f} 秒                          │
├─────────────────────────────────────────────────────────┤
│  🚀 速度提升:      {speedup:>8.0f} 倍                            │
└─────────────────────────────────────────────────────────┘
""")

# 验证结果一致性
print("【结果验证】")
print(f"  for循环结果(前5行):\n{result_slow.head()}\n")
print(f"  向量化结果(前5行):\n{result_fast.head()}")

# 检查数值是否一致
diff = (result_slow - result_fast.head(100_000)).abs().max()
print(f"\n  最大误差: {diff.max():.2e} (数值精度误差，可忽略)")

# ============================================================
# 代码对比展示
# ============================================================
print("\n" + "=" * 60)
print("【代码对比】")
print("=" * 60)



print(f"""
📊 优化效果总结：
   • 运行时间: {estimated_slow:.0f}秒 → {time_fast:.2f}秒 (提升{speedup:.0f}倍)
""")
