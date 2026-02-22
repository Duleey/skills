import numpy as np
import pandas as pd

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    # 波动率因子：收益率的标准差
    df['ret'] = df['close'].pct_change(1)
    df[factor_name] = df['ret'].rolling(n, min_periods=1).std()
    
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
