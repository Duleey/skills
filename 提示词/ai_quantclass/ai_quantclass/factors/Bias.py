import numpy as np
import pandas as pd

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    # A3 价格偏离度因子 (Bias)：收盘价 / 均线 - 1
    df['ma'] = df['close'].rolling(n, min_periods=1).mean()
    df[factor_name] = df['close'] / df['ma'] - 1
    
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
