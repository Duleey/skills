import numpy as np
import pandas as pd

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    # C1 QuoteVolumeMean (成交量因子 - 使用成交额更准确反映资金量)
    df[factor_name] = df['quote_volume'].rolling(n, min_periods=1).mean()
    
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
