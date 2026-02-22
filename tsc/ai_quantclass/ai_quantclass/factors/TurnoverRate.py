import numpy as np
import pandas as pd

extra_data_dict = {
    'coin-cap': ['circulating_supply']
}

def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    # 换手率因子 = 成交量 / 流通股数 (或成交额 / 流通市值)
    # 这里使用 Volume / Circulating Supply
    df['turnover'] = df['volume'] / df['circulating_supply']
    df[factor_name] = df['turnover'].rolling(n, min_periods=1).mean()
    
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
