import numpy as np
import pandas as pd

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    # 量价相关性因子：收益率与成交量的相关系数
    df[factor_name] = df['close'].pct_change(1).rolling(n, min_periods=1).corr(df['volume'])
    
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
