"""
邢不行™️ 策略分享会
仓位管理框架

版权所有 ©️ 邢不行
微信: xbx6660

本代码仅供个人学习使用，未经授权不得复制、修改或用于商业用途。

Author: 邢不行
"""
import numpy as np


def signal(*args):
    df = args[0]
    n = args[1]
    factor_name = args[2]

    df['money_flow'] = np.where(df['close'] >= df['open'], df['quote_volume'], -df['quote_volume'])
    df['money_flow_sum'] = df['money_flow'].rolling(n, min_periods=1).sum()
    df[factor_name] = df['money_flow_sum']
    df[factor_name] = df[factor_name].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df
