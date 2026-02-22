import pandas as pd

def signal(df, params, factor_name):
    """
    计算择时信号 (Moving Average)
    
    参数:
        df (pd.DataFrame): 包含OHLCV数据的原始DataFrame
        params (dict): 策略参数，必须包含 'n'
        factor_name (str): 因子/信号的列名 (factor_name)
    
    返回:
        pd.DataFrame: 包含新计算因子列的DataFrame
    """
    df = df.copy()
    n = params.get('n', 20)
    
    # 简单的均线策略：收盘价 > 均线
    df['ma'] = df['close'].rolling(window=n).mean()
    
    # 信号生成: 1 (多), -1 (空), 0 (空仓/观望)
    df[factor_name] = 0
    df.loc[df['close'] > df['ma'], factor_name] = 1
    df.loc[df['close'] < df['ma'], factor_name] = -1
    
    return df
