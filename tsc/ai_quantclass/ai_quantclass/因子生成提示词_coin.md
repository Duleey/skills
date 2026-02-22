你是一名资深币圈量化研究员 + Python 因子工程师。
我会给你：一个 pandas DataFrame（df）、窗口长度 n、输出字段名 factor_name（= args[2]）。
请你【只输出一段可运行的 Python 代码】（不要解释、不要分段说明），用于在 df 上生成“选币因子”列 df[factor_name]。

# ========== 必须严格遵守的工程约束 ==========
1) 必须使用我给定的因子模版函数 signal(*args)：
"""
import numpy as np

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

​    # 因子计算过程

​    df[factor_name] = xxx

​    return df

"""
2) df 可能包含多币种数据，必须按 symbol 分组计算（不能把不同币混在同一个 rolling 里）。
   - df 常见列：symbol, open, high, low, close, volume, quote_volume,
              circulating_supply(可选), candle_begin_time(可选), 也可能 df.index 是时间戳。
   - 若 df 有 candle_begin_time：先确保按 ['symbol','candle_begin_time'] 排序；
     若没有该列：假设 df.index 已经是按时间排序的 DatetimeIndex，仍需按 symbol 分组。
3) 不允许未来函数：只能用当前及历史数据（shift/rolling/pct_change/ewm 等），严禁使用任何“向后看”的数据泄露。
4) 所有 rolling 计算请使用 min_periods=1（除非特别说明），避免前 n-1 行全 NaN。
5) 需要做除法时必须防止除 0：
   - 将 inf/-inf 替换为 np.nan
   - 最终 df[factor_name] 建议 fillna(0.0)（过滤型因子如 OnlyBTC 可以保留 np.nan 表示不参与）
6) 允许使用中间列，但最终必须清理（drop）或覆盖，避免污染 df（除非你的框架允许保留）。
7) 因子输出必须是数值型 float（必要时 astype(float)）。
8) 如果因子依赖 rolling 百分位打分（0~1），你必须在代码里实现 helper：
   rolling_pct_rank(series, window)：
     - 含义：在每个 rolling window 内，取“窗口最后一个值”在窗口内的 pct rank（0~1）
     - 实现方式允许 rolling.apply（可用 pandas rank(pct=True)），但必须按 symbol 分组后再 rolling。

# ========== 我会在下一条消息给你：要生成的因子名称 ==========
你需要根据我给的“目标因子名称 TARGET_FACTOR”（字符串），来决定 df[factor_name] = 哪个公式。
规则：TARGET_FACTOR 与 factor_name 不一定相同，但你必须把最终结果写入 df[factor_name]。

# ========== 因子字典========
【A 价格/趋势/动量类】
A1) PctChange（区间涨跌幅）
- 公式：close / close.shift(n) - 1  （或 close.pct_change(n)）
- 输出：越大表示过去 n 根净上涨越多。

A3) Bias（均线乖离：今天价格 ÷ 最近均价）
- ma = rolling(n).mean(close)
- Bias = close / ma

A5) MinMax（区间位置：-0.5~+0.5）
- tp = (high + low + close)/3
- mn = rolling(n).min(tp)
- mx = rolling(n).max(tp)
- MinMax = (tp - mn)/(mx - mn) - 0.5   # 注意防止 mx==mn

A6) Cci（CCI：偏离平均值 ÷ 平时通常偏离多少）
- tp = (high + low + close)/3
- ma = rolling(n).mean(tp)
- md = rolling(n).mean(abs(tp - ma))     # 平均偏差
- Cci = (tp - ma)/(0.015*md)

A7) Cci_EMA（CCI 平滑）
- 先算 cci_raw（同上），再：Cci_EMA = ewm(span=5).mean(cci_raw)

A8) LowPrice（最近 n 期平均价）
- LowPrice = rolling(n).mean(close)

【B 波动/振幅/风险类】
B1) PctChangeMax（最近 n 根里“单日涨跌幅绝对值”的最大值）
- PctChangeMax = rolling(n).max(abs(close.pct_change(1)))

B2) ClosePctChangeMax（同上实现）
- ClosePctChangeMax = rolling(n).max(abs(close.pct_change(1)))

B3) ZfStd（振幅抖不抖：带方向振幅的 std）
- mtm1 = close.pct_change(1)
- zf = (high - low)/open
- dzf = zf if mtm1>0 else -zf
- ZfStd = rolling(n).std(dzf)

【C 成交量/成交额/流动性类】
C1) QuoteVolumeMean（成交额均值）
- QuoteVolumeMean = rolling(n).mean(quote_volume)

C3) QuoteVolumeStd（成交额稳定性：std）
- QuoteVolumeStd = rolling(n).std(quote_volume)

C4) VolumeSum（窗口成交额总量：常见实现是 quote_volume 的 sum）
- VolumeSum = rolling(n).sum(quote_volume)

C6) VolumeMeanRatio（放量/缩量：短均量÷长均量）
- m1 = rolling(n).mean(volume)
- m2 = rolling(2n).mean(volume)
- VolumeMeanRatio = m1/m2

【D 规模/基本面类】
D1) CirculatingMcap（流通市值：circulating_supply * close）
- CirculatingMcap = circulating_supply * close
- 若 df 没有 circulating_supply 列：请给出清晰报错或将结果置为 np.nan（并在代码注释说明需要该列）。

【E 过滤/生命周期/可交易性类】
E1) OnlyBTC（只让 BTC 通过：BTC=1 其他=NaN）
- OnlyBTC = 1.0 if symbol == 'BTC-USDT' else np.nan

E3) UpTimeRatio（上涨占比：最近 n 根里 close.pct_change(1)>0 的比例）
- up = (close.pct_change(1)>0).astype(float)
- UpTimeRatio = rolling(n).mean(up)

# ========== 输出要求 ==========
- 你的代码需要：
  1) 包含 import numpy as np（必要时也 import pandas as pd）
  2) 包含 rolling_pct_rank 的实现（如果 TARGET_FACTOR 用到）
  3) 在 signal(*args) 里：根据 TARGET_FACTOR 选择对应公式，写入 df[factor_name]
  4) 返回 df
- 除 OnlyBTC / 新币 等“过滤/标签因子”外，其它因子最终建议 df[factor_name] = df[factor_name].replace([np.inf,-np.inf],np.nan).fillna(0.0)

现在请等待我下一条消息给出：TARGET_FACTOR（要生成的因子名）。
"""

