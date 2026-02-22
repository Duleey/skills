import pandas as pd
from backtest import BacktestEngine
import numpy as np
import itertools

def optimize_dual_ma(short_range=range(5, 50, 5), long_range=range(20, 200, 10), stop_loss=0.10):
    """
    双均线策略参数优化脚本 (Grid Search)
    """
    print(f"Starting optimization for DualMA strategy...")
    print(f"Short MA range: {short_range}")
    print(f"Long MA range: {long_range}")
    print(f"Stop Loss: {stop_loss}")
    
    # 初始化引擎
    DATA_FILE = "BTC-USDT.csv"
    # 更新交易成本配置: 手续费 0.1%, 滑点 0.8%
    FEE_RATE = 0.001
    SLIPPAGE = 0.008
    
    engine = BacktestEngine(
        data_path=DATA_FILE, 
        fee_rate=FEE_RATE, 
        slippage=SLIPPAGE
    )
    engine.load_data()
    
    results = []
    
    # 生成参数组合
    # 过滤掉 short >= long 的无效组合
    param_combinations = [
        (s, l) for s in short_range for l in long_range if s < l
    ]
    
    total_combs = len(param_combinations)
    print(f"Total combinations to test: {total_combs}")
    
    for idx, (short_n, long_n) in enumerate(param_combinations):
        print(f"Testing {idx+1}/{total_combs}: Short={short_n}, Long={long_n}...", end="\r")
        
        try:
            params = {
                'short_n': short_n,
                'long_n': long_n,
                'stop_loss': stop_loss
            }
            # 运行回测
            perf = engine.run(strategy_module="DualMA", strategy_params=params, verbose=False)
            
            # 解析结果
            if perf is None: 
                continue
                
            total_return = float(perf['Total Return'].strip('%')) / 100
            sharpe = float(perf['Sharpe Ratio'])
            max_dd = float(perf['Max Drawdown'].strip('%')) / 100
            
            results.append({
                'short_n': short_n,
                'long_n': long_n,
                'Total Return': total_return,
                'Sharpe Ratio': sharpe,
                'Max Drawdown': max_dd
            })
            
        except Exception as e:
            print(f"\nError optimizing ({short_n}, {long_n}): {e}")
            
    print("\nOptimization complete.")
    
    if not results:
        print("No results generated.")
        return

    # 转换为 DataFrame
    results_df = pd.DataFrame(results)
    
    # 按 Sharpe Ratio 排序
    top_results = results_df.sort_values(by='Sharpe Ratio', ascending=False).head(10)
    
    print("-" * 60)
    print("Top 10 Parameter Sets (by Sharpe Ratio):")
    print("-" * 60)
    print(top_results.to_string(formatters={
        'Total Return': '{:,.2%}'.format,
        'Max Drawdown': '{:,.2%}'.format,
        'Sharpe Ratio': '{:.2f}'.format
    }))
    
    # 保存结果
    results_df.to_csv("dual_ma_optimization.csv", index=False)
    print("\nResults saved to 'dual_ma_optimization.csv'")

if __name__ == "__main__":
    # 扩大参数范围以应对高成本环境
    optimize_dual_ma(
        short_range=range(10, 110, 10), 
        long_range=range(100, 550, 50),
        stop_loss=0.10
    )