import numpy as np
import pandas as pd

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    # 资金流因子：简单近似 = 成交额 * 涨跌方向
    # close > open 视为流入，close < open 视为流出
    direction = np.where(df['close'] >= df['open'], 1, -1)
    df['raw_mf'] = df['quote_volume'] * direction
    df[factor_name] = df['raw_mf'].rolling(n, min_periods=1).mean()
    
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
