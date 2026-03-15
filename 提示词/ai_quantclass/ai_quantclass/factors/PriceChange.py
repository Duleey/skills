import numpy as np
import pandas as pd

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    # 涨跌幅因子：最近 1 根 K 线的涨跌幅
    # 也可以理解为短期动量或反转因子
    df[factor_name] = df['close'].pct_change(1)
    
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
