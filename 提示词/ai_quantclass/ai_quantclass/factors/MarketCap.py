import numpy as np
import pandas as pd

extra_data_dict = {
    'coin-cap': ['circulating_supply']
}

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    # D1 市值因子：流通市值
    df[factor_name] = df['circulating_supply'] * df['close']
    
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
