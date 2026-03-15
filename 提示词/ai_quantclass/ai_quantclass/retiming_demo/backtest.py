import pandas as pd
import numpy as np
import os
import sys
import importlib
import plotly.graph_objects as go

class BacktestEngine:
    def __init__(self, data_path, symbol='BTC-USDT', initial_capital=10000.0, fee_rate=0.0005, slippage=0.0001):
        self.data_path = data_path
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage = slippage
        self.data = None
        self.results = {}
        
    def load_data(self):
        """
        加载 CSV 数据并进行预处理
        """
        print(f"Loading data from {self.data_path}...")
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"File not found: {self.data_path}")
            
        try:
            # Skip the first row (garbage metadata) and try GBK encoding
            try:
                self.data = pd.read_csv(self.data_path, skiprows=1, encoding='utf-8')
            except UnicodeDecodeError:
                print("UTF-8 failed, trying GBK...")
                self.data = pd.read_csv(self.data_path, skiprows=1, encoding='gbk')
            
            # 检查必需字段
            required_cols = ['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in self.data.columns for col in required_cols):
                raise ValueError(f"Missing required columns. Found: {self.data.columns}")
                
            # 时间解析与索引设置
            self.data['candle_begin_time'] = pd.to_datetime(self.data['candle_begin_time'])
            self.data.set_index('candle_begin_time', inplace=True)
            self.data.sort_index(inplace=True)
            
            # 简单的数据清洗
            self.data.ffill(inplace=True)
            
            print(f"Data loaded successfully. Rows: {len(self.data)}")
            print(f"Time range: {self.data.index[0]} to {self.data.index[-1]}")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise

    def calculate_equity(self, factor_name='signal'):
        """
        计算资金曲线
        """
        df = self.data.copy()
        
        # 1. 仓位生成
        # 信号通常在收盘时产生，只能在下一根K线执行
        # position: 1 (long), -1 (short), 0 (flat)
        df['position'] = df[factor_name].shift(1).fillna(0)
        
        # 2. 计算单期收益率 (简单收益率)
        df['pct_change'] = df['close'].pct_change().fillna(0)
        
        # 3. 策略毛收益
        df['strategy_return'] = df['position'] * df['pct_change']
        
        # 4. 成本扣除 (手续费 + 滑点)
        # 当仓位发生变化时产生交易成本
        # position_change: 0 -> 1 (1), 1 -> -1 (2), -1 -> 0 (1)
        df['position_change'] = df['position'].diff().abs().fillna(0)
        
        # 交易成本 = 仓位变化量 * (手续费率 + 滑点)
        # 注意：这里简化处理，假设全仓进出，按本金比例扣除
        df['cost'] = df['position_change'] * (self.fee_rate + self.slippage)
        
        # 5. 净收益率
        df['net_return'] = df['strategy_return'] - df['cost']
        
        # 6. 资金曲线 (累乘)
        df['equity_curve'] = (1 + df['net_return']).cumprod() * self.initial_capital
        
        # 7. 净值 (Net Value)
        df['net_value'] = (1 + df['net_return']).cumprod()
        
        self.data = df
        return df

    def calculate_performance(self):
        """
        计算绩效指标
        """
        if 'net_value' not in self.data.columns:
            return None
            
        df = self.data
        net_values = df['net_value']
        returns = df['net_return']
        
        # 1. 累计收益率
        total_return = net_values.iloc[-1] - 1
        
        # 2. 年化收益率 (假设数据为小时线，每年 24*365 = 8760 小时)
        # 实际应根据数据频率自动推断，这里简单处理
        days = (df.index[-1] - df.index[0]).days
        if days > 0:
            annualized_return = (net_values.iloc[-1]) ** (365 / days) - 1
        else:
            annualized_return = 0
            
        # 3. 最大回撤
        running_max = net_values.cummax()
        drawdown = (net_values - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 4. 夏普比率 (假设无风险利率为0)
        # 年化夏普 = sqrt(periods_per_year) * mean(returns) / std(returns)
        # 假设小时数据
        periods_per_year = 365 * 24
        if returns.std() != 0:
            sharpe_ratio = np.sqrt(periods_per_year) * (returns.mean() / returns.std())
        else:
            sharpe_ratio = 0
            
        # 5. 交易次数
        trade_count = df['position_change'].sum() # 每次变动算一次"单位"交易，如果 1->-1 算2单位
        # 也可以统计开仓次数 (diff != 0)
        action_count = (df['position'] != df['position'].shift(1)).sum()
        
        # 6. 胜率 (按日或按交易统计比较复杂，这里简化为盈利K线占比，或者按持有期统计)
        # 简单版：盈利的周期数 / 总持仓周期数
        holding_periods = df[df['position'] != 0]
        if len(holding_periods) > 0:
            win_rate = (holding_periods['net_return'] > 0).sum() / len(holding_periods)
        else:
            win_rate = 0

        self.results = {
            'Total Return': f"{total_return:.2%}",
            'Annualized Return': f"{annualized_return:.2%}",
            'Max Drawdown': f"{max_drawdown:.2%}",
            'Sharpe Ratio': f"{sharpe_ratio:.2f}",
            'Trade Count': int(action_count),
            'Win Rate (Per Candle)': f"{win_rate:.2%}",
            'Final Equity': f"{df['equity_curve'].iloc[-1]:.2f}"
        }
        
        return self.results

    def plot_equity(self, filename='equity_curve.html'):
        """
        绘制资金曲线 (Plotly)
        """
        if 'equity_curve' not in self.data.columns:
            print("Equity curve not found. Please run backtest first.")
            return

        df = self.data
        
        fig = go.Figure()
        
        # 资金曲线
        fig.add_trace(go.Scatter(
            x=df.index, 
            y=df['equity_curve'], 
            mode='lines', 
            name='Equity Curve',
            line=dict(color='blue', width=1.5)
        ))
        
        # 基准曲线 (BTC Buy & Hold) - 可选
        # 归一化到初始资金
        benchmark = (df['close'] / df['close'].iloc[0]) * self.initial_capital
        fig.add_trace(go.Scatter(
            x=df.index,
            y=benchmark,
            mode='lines',
            name='Benchmark (Buy & Hold)',
            line=dict(color='gray', width=1, dash='dash')
        ))

        fig.update_layout(
            title=f'Backtest Equity Curve: {self.symbol}',
            xaxis_title='Date',
            yaxis_title='Equity',
            hovermode='x unified',
            template='plotly_white'
        )
        
        print(f"Saving plot to {filename}...")
        fig.write_html(filename)

    def run(self, strategy_module, strategy_params, factor_name='signal', verbose=True):
        """
        运行回测
        """
        if self.data is None:
            self.load_data()
            
        if verbose:
            print(f"Running strategy: {strategy_module} with params: {strategy_params}")
        
        try:
            mod = importlib.import_module(f"signal.{strategy_module}")
            if not hasattr(mod, 'signal'):
                raise AttributeError(f"Module {strategy_module} does not have a 'signal' function.")
            
            # 计算信号
            # n = strategy_params.get('n', 20)
            # Pass full params dict to signal function
            self.data = mod.signal(self.data, strategy_params, factor_name)
            
            # 计算资金曲线
            self.calculate_equity(factor_name)
            
            # 计算绩效
            perf = self.calculate_performance()
            
            if verbose:
                print("-" * 30)
                print("Backtest Results:")
                for k, v in perf.items():
                    print(f"{k}: {v}")
                print("-" * 30)
                
                # 绘制图表
                self.plot_equity()
                
                # 简单的最后几行展示
                print(self.data[['close', 'position', 'net_value']].tail())
            
            return perf
            
        except Exception as e:
            print(f"Error running strategy: {e}")
            raise

if __name__ == "__main__":
    # 基础配置
    DATA_FILE = "BTC-USDT.csv"
    INITIAL_CAPITAL = 10000.0  # 初始资金
    
    # 交易成本配置
    FEE_RATE = 0.001      # 手续费率 (0.1%)
    SLIPPAGE = 0.008      # 滑点率 (0.018%)
    
    # 初始化回测引擎
    engine = BacktestEngine(
        data_path=DATA_FILE, 
        initial_capital=INITIAL_CAPITAL,
        fee_rate=FEE_RATE, 
        slippage=SLIPPAGE
    )
    
    # 阶段一测试：加载数据
    engine.load_data()
    
    # 阶段二预演：测试信号计算 (DualMA - Optimized Params)
    # Best params from optimization: Short=35, Long=80
    strategy_settings = {
        'short_n': 80,
        'long_n': 500,
        'stop_loss': 0.10
    }
    engine.run(strategy_module="DualMA", strategy_params=strategy_settings)
