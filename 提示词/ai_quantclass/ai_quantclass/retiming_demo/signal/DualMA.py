import pandas as pd
import numpy as np

def signal(df, params, factor_name):
    """
    计算择时信号 (Dual Moving Average with Stop Loss)
    
    参数:
        df (pd.DataFrame): 包含OHLCV数据的原始DataFrame
        params (dict): 策略参数，必须包含 'short_n', 'long_n', 可选 'stop_loss' (默认0.10)
        factor_name (str): 因子/信号的列名
    
    返回:
        pd.DataFrame: 包含新计算因子列的DataFrame
    """
    df = df.copy()
    short_n = params.get('short_n', 10)
    long_n = params.get('long_n', 60)
    stop_loss = params.get('stop_loss', 0.10)
    
    # 计算均线
    df['short_ma'] = df['close'].rolling(window=short_n).mean()
    df['long_ma'] = df['close'].rolling(window=long_n).mean()
    
    # 初始化信号列
    df[factor_name] = 0
    
    # 遍历K线进行信号生成与止损逻辑
    # 状态变量
    position = 0 # 0: 空仓, 1: 持仓
    entry_price = 0.0
    
    # 将DataFrame转换为迭代器或使用索引遍历
    # 为提高效率，先计算出基础的金叉死叉信号
    # cross_signal: 1 (Golden Cross), -1 (Death Cross), 0 (None)
    # Golden Cross: short_ma > long_ma (current) AND short_ma <= long_ma (prev)
    # Death Cross: short_ma < long_ma (current) AND short_ma >= long_ma (prev)
    
    # 但由于需要处理止损，简单的向量化可能不够，这里使用遍历
    # 信号列表
    signals = [0] * len(df)
    
    closes = df['close'].values
    short_mas = df['short_ma'].values
    long_mas = df['long_ma'].values
    
    for i in range(1, len(df)):
        # 获取当前与前一时刻的数据
        curr_close = closes[i]
        curr_short = short_mas[i]
        curr_long = long_mas[i]
        prev_short = short_mas[i-1]
        prev_long = long_mas[i-1]
        
        # 检查数据有效性
        if np.isnan(curr_short) or np.isnan(curr_long):
            continue
            
        # 默认保持前一时刻的信号/仓位状态？
        # 注意：回测引擎根据 shift(1) 的 position 计算收益
        # 这里我们生成的是"当前K线结束时"的理想仓位信号
        
        # 止损逻辑
        if position == 1:
            # 检查是否触发止损
            if curr_close <= entry_price * (1 - stop_loss):
                position = 0 # 平仓
                signals[i] = 0
                continue # 本K线结束
        
        # 金叉：短期上穿长期 -> 做多
        if prev_short <= prev_long and curr_short > curr_long:
            if position == 0:
                position = 1
                entry_price = curr_close # 以收盘价作为参考入场价
        
        # 死叉：短期下穿长期 -> 平仓
        elif prev_short >= prev_long and curr_short < curr_long:
            if position == 1:
                position = 0
                entry_price = 0.0
        
        signals[i] = position
        
    df[factor_name] = signals
    
    # 清理临时列
    del df['short_ma']
    del df['long_ma']
    
    return df
