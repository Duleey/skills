import numpy as np
import pandas as pd

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    # A1 PctChange (Momentum)
    # 区间涨跌幅：过去 n 根 K 线的收益率
    df[factor_name] = df['close'] / df['close'].shift(n) - 1
    
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
