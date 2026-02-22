import numpy as np
import pandas as pd

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    # 振幅因子：(High - Low) / Open
    df['amp'] = (df['high'] - df['low']) / df['open']
    df[factor_name] = df['amp'].rolling(n, min_periods=1).mean()
    
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
