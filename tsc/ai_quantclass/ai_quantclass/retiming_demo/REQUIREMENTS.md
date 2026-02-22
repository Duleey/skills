# 择时回测框架需求说明书 (Requirements Specification)

## 1. 项目简介 (Project Overview)
本项目旨在构建一套轻量级、高扩展性的加密货币择时策略回测框架。框架需支持现货数据（如 BTC-USDT），允许用户自定义择时信号（Signal），并支持做多（Long）与做空（Short）双向交易。系统需模拟真实交易环境，包括手续费（Commission）和滑点（Slippage）对策略表现的影响。

## 2. 系统架构 (System Architecture)

### 2.1 目录结构
建议的项目文件结构如下：
```text
/
├── BTC-USDT.csv          # 数据文件
├── backtest.py           # 回测主程序（执行引擎）
├── config.py             # (可选) 策略与回测配置
├── requirements.txt      # 依赖库说明
├── signal/               # 信号策略文件夹
│   ├── __init__.py
│   └── MovingAverage.py  # 均线策略实现示例
└── README.md             # 说明文档
```

## 3. 数据模块 (Data Module)

### 3.1 数据源
- **文件格式**: CSV
- **文件名示例**: `BTC-USDT.csv`
- **必需字段**:
    - `candle_begin_time`: K线开始时间 (时间戳或字符串)
    - `open`: 开盘价
    - `high`: 最高价
    - `low`: 最低价
    - `close`: 收盘价
    - `volume`: 成交量
- **扩展字段** (框架应能兼容): `quote_volume`, `trade_num`, `taker_buy_base_asset_volume`, `taker_buy_quote_asset_volume`, `Spread`, `avg_price_1m` 等。

### 3.2 数据处理要求
- 加载 CSV 时需自动解析 `candle_begin_time` 为 datetime 对象并设为索引。
- 需处理可能存在的缺失值（Forward Fill 或 Drop）。

## 4. 信号模块 (Signal Module)

### 4.1 接口规范
所有的择时策略代码应放置在 `signal/` 文件夹下。每个策略文件必须包含一个名为 `signal` 的入口函数。

**函数签名**:
```python
def signal(df, params, factor_name):
    """
    计算择时信号
    
    参数:
        df (pd.DataFrame): 包含OHLCV数据的原始DataFrame
        params (dict): 策略参数字典 (如 {'n': 20} 或 {'short_n': 10, 'long_n': 60})
        factor_name (str): 因子/信号的列名 (factor_name)
    
    返回:
        pd.DataFrame: 包含新计算因子列的DataFrame
    """
    # 策略逻辑实现
    # ...
    return df
```

### 4.2 信号逻辑示例

#### 4.2.1 均线策略 (MovingAverage.py)
- 计算 N 日移动平均线。
- 当收盘价 > N日均线时，看多 (Signal 1)。
- 当收盘价 < N日均线时，看空 (Signal -1)。

#### 4.2.2 双均线策略 (DualMA.py)
- **参数**: `short_n` (短期周期), `long_n` (长期周期), `stop_loss` (止损比例)。
- **金叉 (Golden Cross)**: 短期均线 > 长期均线，且前一时刻短期 <= 长期 -> **做多 (Signal 1)**。
- **死叉 (Death Cross)**: 短期均线 < 长期均线，且前一时刻短期 >= 长期 -> **平仓 (Signal 0)**。
- **止损 (Stop Loss)**: 持仓期间若收盘价跌破 `Entry Price * (1 - stop_loss)` -> **平仓 (Signal 0)**。

## 5. 回测引擎 (`backtest.py`) 核心逻辑

### 5.1 配置项 (Configuration)
回测脚本支持显式配置以下参数（在 `__main__` 块中定义）：
- `DATA_FILE`: 数据文件路径。
- `INITIAL_CAPITAL`: 初始资金 (如 10000.0)。
- `FEE_RATE`: 手续费率 (如 0.001，即 0.1%)。
- `SLIPPAGE`: 滑点率 (如 0.008，即 0.8%)。

### 5.2 核心流程
1.  **数据加载**: 读取 CSV 数据，支持 GBK/UTF-8 自动识别。
2.  **信号计算**: 
    - 动态导入策略模块。
    - 调用 `signal(df, params, factor_name)` 计算因子。
3.  **仓位生成**: 根据因子列生成仓位信号 `position`，并处理时间滞后 (`shift(1)`).
4.  **资金曲线计算**: 计算单期收益、扣除交易成本（手续费+滑点）、计算净值曲线。
5.  **绩效评估**: 计算累计收益、年化收益、最大回撤、夏普比率等。

## 6. 绩效评估 (Performance Evaluation)
... (保持不变)

## 7. 输出交付物 (Deliverables)
... (保持不变)

## 8. 参数优化模块 (Parameter Optimization)

### 8.1 功能目标
编写独立的寻参脚本 `optimize.py`，支持多参数网格搜索。

### 8.2 核心逻辑
1.  **参数空间定义**: 支持定义多个参数的范围 (如 `short_range`, `long_range`)。
2.  **网格搜索**: 使用 `itertools.product` 或嵌套循环遍历所有合法参数组合。
3.  **回测执行**: 调用 `BacktestEngine.run(..., verbose=False)` 获取每组参数的绩效。
4.  **结果输出**: 打印 Top N 参数组合，并保存完整结果到 CSV (`dual_ma_optimization.csv` 等)。

## 9. 开发计划
1.  **阶段一**: [已完成] 完成 `backtest.py` 框架搭建，实现数据加载与简单的 Buy & Hold 逻辑验证数据流。
2.  **阶段二**: [已完成] 实现 `signal/MovingAverage.py` 并在回测中集成。
3.  **阶段三**: [已完成] 完善资金管理逻辑（支持做空、杠杆处理）及成本计算。
4.  **阶段四**: [已完成] 开发绩效评估模块与可视化 (Plotly)。
5.  **阶段五**: [已完成] 实现 `optimize.py` 寻参脚本，支持双均线策略参数优化。
6.  **阶段六**: (可选) 进一步扩展策略库或优化回测性能。

## 10. 架构示意图

1-系统架构总览图

  用途：展示框架整体结构和模块关系

![1-系统架构总览图](http://geekree-md.oss-cn-shanghai.aliyuncs.com/2026-01-25-071748.png)

2-数据处理流程图

  用途：详细展示从原始CSV到可回测DataFrame的转换过程

![2-数据处理流程图](http://geekree-md.oss-cn-shanghai.aliyuncs.com/2026-01-25-071809.png)

3-策略信号接口规范图

  用途：展示策略模块的标准接口，便于理解如何扩展新策略

![3-策略信号接口规范图](http://geekree-md.oss-cn-shanghai.aliyuncs.com/2026-01-25-071822.png)

4-回测引擎类结构图

  用途：展示BacktestEngine的内部结构

![4-回测引擎类结构图](http://geekree-md.oss-cn-shanghai.aliyuncs.com/2026-01-25-071900.png)



