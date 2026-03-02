# 仓位管理回测框架 v1.3.8 - 结构与功能全景分析

> **文档版本**: v1.0
> **框架版本**: v1.3.8 (build: v1.3.8.20251023)
> **生成日期**: 2026-01-15
> **分析师**: Claude AI (资深量化分析师 & 系统架构师)

---

## 一、框架概述

### 1.1 定位与核心能力

**仓位管理回测框架 v1.3.8** 是一套面向加密货币市场的**多策略融合选币回测系统**。其核心设计目标是：

| 能力维度 | 具体实现 |
|---------|---------|
| **多策略融合** | 支持多个子策略并行运行，通过仓位管理策略（FixedRatio/Rotation）动态分配资金权重 |
| **选币而非择时** | 基于因子排名选择持仓币种，而非判断买卖时点（区别于传统股票回测框架） |
| **现货+合约双市场** | 同时支持币安现货和永续合约市场的回测模拟 |
| **高性能计算** | 核心模拟器使用 Numba JIT 编译，大幅提升回测速度 |
| **动态模块加载** | 通过 Hub 系统实现因子/策略/信号的热插拔 |

### 1.2 框架定位图示

```
┌─────────────────────────────────────────────────────────────────┐
│                    仓位管理回测框架 v1.3.8                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │   因子计算   │───▶│   选币排名   │───▶│  仓位分配   │        │
│   │  (Factors)  │    │(SelectCoin) │    │(Positions)  │        │
│   └─────────────┘    └─────────────┘    └─────────────┘        │
│          │                  │                  │                │
│          ▼                  ▼                  ▼                │
│   ┌─────────────────────────────────────────────────┐          │
│   │              高性能模拟引擎 (Simulator)           │          │
│   │        Numba JIT | 账户状态 | 调仓计算            │          │
│   └─────────────────────────────────────────────────┘          │
│                            │                                   │
│                            ▼                                   │
│   ┌─────────────────────────────────────────────────┐          │
│   │              绩效评估 & 可视化输出                 │          │
│   └─────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、目录结构详解

### 2.1 完整目录树

```
position-mgmt_v1.3.8/
│
├── 📄 backtest.py                 # 【主入口】单次完整回测流程
├── 📄 config.py                   # 【配置中心】全局参数配置
├── 📄 param_search_beta.py        # 【参数搜索】网格遍历最优参数
├── 📄 param_search_beta_for_ui.py # 【UI对接】网页版回测接口
├── 📄 check_extra_data_source.py  # 额外数据源检查工具
├── 📄 update_min_qty.py           # 最小下单量更新工具
├── 📄 requirements.txt            # 依赖包清单
├── 📄 README.md                   # 项目说明
├── 📄 更新说明.md                  # 版本更新日志
│
├── 📁 core/                       # ════ 核心引擎层 ════
│   ├── __init__.py
│   ├── version.py                 # 版本信息
│   │
│   │  ┌──────────────────────────────────────────────┐
│   │  │            数据处理 & 因子计算                 │
│   │  └──────────────────────────────────────────────┘
│   ├── data_bridge.py             # 数据桥接：加载预处理数据
│   ├── factor.py                  # 因子计算：calc_factor_vals()
│   ├── select_coin.py             # 选币逻辑：因子排名 → 选币
│   │
│   │  ┌──────────────────────────────────────────────┐
│   │  │            回测执行 & 模拟交易                 │
│   │  └──────────────────────────────────────────────┘
│   ├── backtest.py                # 回测执行引擎 (step2~step6)
│   ├── simulator.py               # 高性能模拟器 (Numba加速)
│   ├── rebalance.py               # 仓位调整计算 (Numba加速)
│   │
│   │  ┌──────────────────────────────────────────────┐
│   │  │            绩效评估 & 可视化                   │
│   │  └──────────────────────────────────────────────┘
│   ├── equity.py                  # 资金曲线计算 & 绘图
│   ├── evaluate.py                # 策略评价指标
│   ├── figure.py                  # 图表绘制工具
│   │
│   ├── 📁 model/                  # ─── 数据模型层 ───
│   │   ├── __init__.py
│   │   ├── backtest_config.py     # BacktestConfig, Factory, MultiEquity
│   │   ├── strategy_config.py     # StrategyConfig, PosStrategyConfig
│   │   ├── timing_signal.py       # TimingSignal 择时信号模型
│   │   ├── account_type.py        # 账户类型枚举
│   │   └── rebalance_mode.py      # 调仓模式枚举
│   │
│   └── 📁 utils/                  # ─── 工具函数层 ───
│       ├── __init__.py
│       ├── factor_hub.py          # FactorHub：动态加载因子
│       ├── strategy_hub.py        # StrategyHub：动态加载策略
│       ├── signal_hub.py          # SignalHub：动态加载信号
│       ├── functions.py           # 通用工具函数
│       ├── log_kit.py             # 日志工具
│       └── path_kit.py            # 路径管理工具
│
├── 📁 factors/                    # ════ 时序因子库 ════
│   └── OnlyBTC.py                 # 示例：仅选择 BTC
│
├── 📁 sections/                   # ════ 截面因子库 ════
│   └── Demo.py                    # 示例：基于 PctChange 排名
│
├── 📁 signals/                    # ════ 择时信号库 ════
│   └── MovingAverage.py           # 均线择时信号
│
├── 📁 positions/                  # ════ 仓位策略库 ════
│   ├── FixedRatioStrategy.py      # 固定比例分配策略
│   └── RotationStrategy.py        # 轮动策略
│
├── 📁 tools/                      # ════ 工具脚本库 ════
│   ├── __init__.py
│   ├── tool1_参数分析.py           # 参数分析工具
│   └── 📁 utils/
│       ├── pfunctions.py          # 参数相关函数
│       ├── tfunctions.py          # 分析相关函数
│       └── unified_tool.py        # 统一工具参数类
│
├── 📁 examples/                   # ════ 示例脚本 ════
│   └── 📁 发帖脚本/
│       ├── __init__.py
│       ├── 发帖脚本.py             # 论坛发帖模板生成
│       └── 样本模板.txt            # 发帖模板
│
└── 📁 data/                       # ════ 数据目录 ════
    └── 📁 min_qty/
        ├── 最小下单量_spot.csv     # 现货最小下单量
        └── 最小下单量_swap.csv     # 合约最小下单量
```

### 2.2 模块职责划分

| 层级 | 目录/文件 | 职责 | 依赖方向 |
|-----|----------|------|---------|
| **入口层** | `backtest.py`, `param_search_*.py` | 流程编排、参数管理 | → 配置层、核心层 |
| **配置层** | `config.py` | 全局配置中心 | → 无 |
| **核心层** | `core/` | 业务逻辑实现 | → 模型层、工具层 |
| **模型层** | `core/model/` | 数据结构定义 | → 无 |
| **工具层** | `core/utils/` | 通用工具、动态加载 | → 扩展库 |
| **扩展库** | `factors/`, `sections/`, `signals/`, `positions/` | 可插拔业务组件 | → 无 |

---

## 三、数据流向全景图

### 3.1 完整数据流

```
                            ┌─────────────────┐
                            │   config.py     │
                            │   全局配置中心    │
                            └────────┬────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         STEP 1: 配置初始化                               │
├──────────────────────────────────────────────────────────────────────────┤
│  MultiEquityBacktestConfig                                               │
│  ├── strategy_pool[]        # 子策略池                                   │
│  ├── strategy_config{}      # 仓位策略配置                                │
│  └── simulator_config{}     # 模拟器参数                                  │
│                                     │                                    │
│  BacktestConfigFactory              │                                    │
│  └── 为每个子策略生成 BacktestConfig   │                                    │
└──────────────────────────────────────┼───────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         STEP 2: 数据加载                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    预处理数据目录 (pre_data_path)                                         │
│    ┌─────────────────────────────────────────────────────────┐           │
│    │  spot_dict.pkl    →    {symbol: DataFrame}   现货K线     │           │
│    │  swap_dict.pkl    →    {symbol: DataFrame}   合约K线     │           │
│    │  min_qty/*.csv    →    最小下单量数据                     │           │
│    └─────────────────────────────────────────────────────────┘           │
│                              │                                           │
│                   data_bridge.py                                         │
│                   └── 数据加载、预处理、格式转换                            │
│                              │                                           │
│                              ▼                                           │
│    ┌─────────────────────────────────────────────────────────┐           │
│    │  all_symbol_candle_df_dict                               │           │
│    │  {                                                       │           │
│    │    'BTC-USDT': DataFrame[candle_begin_time, open, high,  │           │
│    │                          low, close, volume, ...]        │           │
│    │    'ETH-USDT': DataFrame[...],                           │           │
│    │    ...                                                   │           │
│    │  }                                                       │           │
│    └─────────────────────────────────────────────────────────┘           │
└──────────────────────────────────────┼───────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         STEP 3: 因子计算                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    FactorHub (core/utils/factor_hub.py)                                  │
│    └── 动态加载 factors/ 和 sections/ 中的因子模块                         │
│                              │                                           │
│              ┌───────────────┼───────────────┐                           │
│              ▼               ▼               ▼                           │
│    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │
│    │  时序因子    │  │  截面因子    │  │ 外部数据因子  │                    │
│    │ factors/    │  │ sections/   │  │extra_data   │                    │
│    │             │  │             │  │             │                    │
│    │ signal()    │  │ signal()    │  │ 预加载数据   │                    │
│    │ signal_     │  │ is_cross=   │  │             │                    │
│    │ multi_      │  │   True      │  │             │                    │
│    │ params()    │  │ get_factor_ │  │             │                    │
│    │             │  │   list()    │  │             │                    │
│    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                    │
│           │                │                │                            │
│           └────────────────┼────────────────┘                            │
│                            ▼                                             │
│    factor.py::calc_factor_vals()                                         │
│    └── 为每个币种的 DataFrame 添加因子列                                   │
│                            │                                             │
│                            ▼                                             │
│    ┌─────────────────────────────────────────────────────────┐           │
│    │  all_symbol_candle_df_dict (含因子列)                     │           │
│    │  {                                                       │           │
│    │    'BTC-USDT': DataFrame[..., factor1, factor2, ...]     │           │
│    │    'ETH-USDT': DataFrame[..., factor1, factor2, ...]     │           │
│    │  }                                                       │           │
│    └─────────────────────────────────────────────────────────┘           │
└──────────────────────────────────────┼───────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         STEP 4: 选币排名                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    select_coin.py::select_coins()                                        │
│    ┌─────────────────────────────────────────────────────────┐           │
│    │  输入:                                                   │           │
│    │  ├── all_symbol_candle_df_dict (含因子)                  │           │
│    │  ├── factor_list: [('Factor1', is_asc, n, select_num)]  │           │
│    │  ├── filter_list: [(filter_factor, threshold, op)]      │           │
│    │  └── hold_period: '1H' / '4H' / '1D'                    │           │
│    │                                                          │           │
│    │  处理流程:                                                │           │
│    │  1. 按因子值排序 (ascending 或 descending)                │           │
│    │  2. 应用过滤条件 (filter_list)                           │           │
│    │  3. 选取 Top N 币种 (select_num)                         │           │
│    │  4. 生成选币结果和权重                                    │           │
│    │                                                          │           │
│    │  输出:                                                   │           │
│    │  └── select_result_df                                   │           │
│    └─────────────────────────────────────────────────────────┘           │
│                            │                                             │
│                            ▼                                             │
│    ┌─────────────────────────────────────────────────────────┐           │
│    │  select_result_df (选币结果)                              │           │
│    │  ┌────────────────┬─────────┬────────┬───────┬───────┐  │           │
│    │  │candle_begin_   │ symbol  │ weight │ is_   │target │  │           │
│    │  │time            │         │        │ spot  │_ratio │  │           │
│    │  ├────────────────┼─────────┼────────┼───────┼───────┤  │           │
│    │  │2024-01-01 00:00│ BTC-USDT│  0.333 │ False │ 0.333 │  │           │
│    │  │2024-01-01 00:00│ ETH-USDT│  0.333 │ False │ 0.333 │  │           │
│    │  │2024-01-01 00:00│ SOL-USDT│  0.334 │ False │ 0.334 │  │           │
│    │  │2024-01-01 01:00│ BTC-USDT│  0.333 │ False │ 0.333 │  │           │
│    │  │...             │ ...     │  ...   │ ...   │ ...   │  │           │
│    │  └────────────────┴─────────┴────────┴───────┴───────┘  │           │
│    └─────────────────────────────────────────────────────────┘           │
└──────────────────────────────────────┼───────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         STEP 5: 多策略聚合                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    【子策略A的选币结果】  【子策略B的选币结果】  【子策略C的选币结果】          │
│           │                    │                    │                    │
│           └────────────────────┼────────────────────┘                    │
│                                ▼                                         │
│    select_coin.py::concat_select_results()                               │
│    └── 合并多个子策略的选币结果                                            │
│                                │                                         │
│                                ▼                                         │
│    StrategyHub (core/utils/strategy_hub.py)                              │
│    └── 动态加载 positions/ 中的仓位策略                                    │
│                                │                                         │
│              ┌─────────────────┴─────────────────┐                       │
│              ▼                                   ▼                       │
│    ┌─────────────────┐              ┌─────────────────┐                 │
│    │FixedRatio      │              │Rotation        │                 │
│    │Strategy        │              │Strategy        │                 │
│    │                │              │                │                 │
│    │按固定比例分配   │              │根据因子轮动    │                 │
│    │cap_ratios:     │              │factor_list:    │                 │
│    │[1/3, 1/3, 1/3] │              │[(...)]         │                 │
│    └────────┬───────┘              └────────┬───────┘                 │
│             │                               │                          │
│             └───────────────┬───────────────┘                          │
│                             ▼                                          │
│    calc_ratio() → strategy_weight_df                                   │
│    ┌────────────────┬───────────┬───────────┬───────────┐              │
│    │candle_begin_   │ Strategy_A│ Strategy_B│ Strategy_C│              │
│    │time            │ (权重)     │ (权重)     │ (权重)     │              │
│    ├────────────────┼───────────┼───────────┼───────────┤              │
│    │2024-01-01 00:00│   0.333   │   0.333   │   0.334   │              │
│    │2024-01-01 01:00│   0.333   │   0.333   │   0.334   │              │
│    │...             │   ...     │   ...     │   ...     │              │
│    └────────────────┴───────────┴───────────┴───────────┘              │
│                             │                                          │
│                             ▼                                          │
│    agg_multi_strategy_ratio()                                          │
│    └── 按策略权重聚合选币结果，生成最终持仓比例                             │
│                             │                                          │
│                             ▼                                          │
│    ┌─────────────────────────────────────────────────────────┐         │
│    │  final_select_df (最终选币结果)                           │         │
│    │  ┌────────────────┬─────────┬────────┬───────┐          │         │
│    │  │candle_begin_   │ symbol  │target_ │ is_   │          │         │
│    │  │time            │         │ratio   │ spot  │          │         │
│    │  ├────────────────┼─────────┼────────┼───────┤          │         │
│    │  │2024-01-01 00:00│ BTC-USDT│  0.40  │ False │          │         │
│    │  │2024-01-01 00:00│ ETH-USDT│  0.35  │ False │          │         │
│    │  │2024-01-01 00:00│ SOL-USDT│  0.25  │ True  │          │         │
│    │  │...             │ ...     │  ...   │ ...   │          │         │
│    │  └────────────────┴─────────┴────────┴───────┘          │         │
│    └─────────────────────────────────────────────────────────┘         │
└──────────────────────────────────────┼───────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                   STEP 5.5: 择时信号调整 (可选)                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    SignalHub (core/utils/signal_hub.py)                                  │
│    └── 动态加载 signals/ 中的择时信号                                      │
│                                │                                         │
│                                ▼                                         │
│    ┌─────────────────────────────────────────────────────────┐           │
│    │  MovingAverage.py::dynamic_leverage(equity, n)          │           │
│    │                                                          │           │
│    │  输入: 资金曲线 equity (pd.Series)                         │           │
│    │  输出: 杠杆倍数序列 (0 = 空仓, 1 = 满仓, 2 = 2倍杠杆...)    │           │
│    │                                                          │           │
│    │  逻辑: 当资金曲线 > MA(n) 时满仓，否则空仓                  │           │
│    └─────────────────────────────────────────────────────────┘           │
│                                │                                         │
│                                ▼                                         │
│    target_ratio × leverage_ratio = adjusted_target_ratio                 │
│                                                                          │
└──────────────────────────────────────┼───────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         STEP 6: 模拟交易                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    simulator.py::Simulator (Numba JIT 加速)                              │
│    ┌─────────────────────────────────────────────────────────┐           │
│    │                                                          │           │
│    │  初始化状态:                                              │           │
│    │  ├── equity = initial_usdt (初始资金)                    │           │
│    │  ├── lots = {} (持仓数量)                                │           │
│    │  └── target_lots = {} (目标持仓)                         │           │
│    │                                                          │           │
│    │  每根K线循环:                                             │           │
│    │  ┌──────────────────────────────────────────────────┐   │           │
│    │  │ 1. 读取当前选币结果和目标比例                        │   │           │
│    │  │    selected_symbols, target_ratios               │   │           │
│    │  │                                                  │   │           │
│    │  │ 2. 计算目标持仓 (rebalance.py)                    │   │           │
│    │  │    calc_target_lots_by_ratio()                   │   │           │
│    │  │    └── target_lots = equity × ratio / price      │   │           │
│    │  │                                                  │   │           │
│    │  │ 3. 计算调仓差额                                   │   │           │
│    │  │    calc_delta_lots_amount()                      │   │           │
│    │  │    └── delta = target_lots - current_lots        │   │           │
│    │  │                                                  │   │           │
│    │  │ 4. 过滤最小下单量                                 │   │           │
│    │  │    filter_deltas()                               │   │           │
│    │  │    └── 过滤掉小于最小下单量的调仓                   │   │           │
│    │  │                                                  │   │           │
│    │  │ 5. 执行交易                                       │   │           │
│    │  │    ├── 先平仓 (delta < 0)                        │   │           │
│    │  │    └── 后开仓 (delta > 0)                        │   │           │
│    │  │                                                  │   │           │
│    │  │ 6. 计算手续费                                     │   │           │
│    │  │    ├── swap_c_rate: 合约手续费 (0.05%)           │   │           │
│    │  │    └── spot_c_rate: 现货手续费 (0.1%)            │   │           │
│    │  │                                                  │   │           │
│    │  │ 7. 更新账户状态                                   │   │           │
│    │  │    ├── lots = new_lots                          │   │           │
│    │  │    ├── equity = new_equity                      │   │           │
│    │  │    └── 检查爆仓 (margin_rate)                    │   │           │
│    │  │                                                  │   │           │
│    │  │ 8. 记录资金曲线点                                 │   │           │
│    │  └──────────────────────────────────────────────────┘   │           │
│    │                                                          │           │
│    └─────────────────────────────────────────────────────────┘           │
│                                │                                         │
│                                ▼                                         │
│    ┌─────────────────────────────────────────────────────────┐           │
│    │  equity_curve (资金曲线)                                  │           │
│    │  ┌────────────────┬───────────┬────────────┐            │           │
│    │  │candle_begin_   │  equity   │ benchmark  │            │           │
│    │  │time            │           │            │            │           │
│    │  ├────────────────┼───────────┼────────────┤            │           │
│    │  │2024-01-01 00:00│  10000.00 │  10000.00  │            │           │
│    │  │2024-01-01 01:00│  10050.25 │  10012.50  │            │           │
│    │  │2024-01-01 02:00│  10120.80 │  10025.00  │            │           │
│    │  │...             │  ...      │  ...       │            │           │
│    │  └────────────────┴───────────┴────────────┘            │           │
│    └─────────────────────────────────────────────────────────┘           │
└──────────────────────────────────────┼───────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       STEP 7: 绩效评估 & 输出                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│    equity.py::calc_equity()                                              │
│    └── 计算资金曲线、净值曲线                                              │
│                                                                          │
│    evaluate.py                                                           │
│    ┌─────────────────────────────────────────────────────────┐           │
│    │  绩效指标计算:                                            │           │
│    │  ├── 年化收益率 (Annual Return)                          │           │
│    │  ├── 夏普比率 (Sharpe Ratio)                             │           │
│    │  ├── 最大回撤 (Max Drawdown)                             │           │
│    │  ├── 卡尔玛比率 (Calmar Ratio)                           │           │
│    │  ├── 胜率 (Win Rate)                                    │           │
│    │  ├── 盈亏比 (Profit/Loss Ratio)                         │           │
│    │  └── ...                                                │           │
│    └─────────────────────────────────────────────────────────┘           │
│                                │                                         │
│    figure.py                   │                                         │
│    └── 绑图绑制                 │                                         │
│                                ▼                                         │
│                                                                          │
│    ┌──────────────────────────────────────────────────────────────┐      │
│    │                        输出文件                               │      │
│    │  ├── 资金曲线.csv         # 完整资金曲线数据                    │      │
│    │  ├── 策略评价.csv         # 绩效指标汇总                       │      │
│    │  ├── 选币结果.csv         # 每期选币明细                       │      │
│    │  └── 绩效图表.png         # 可视化图表                         │      │
│    └──────────────────────────────────────────────────────────────┘      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据流简化视图

```
外部数据                  框架处理                    输出结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ K线预处理数据  │  ──▶ │   因子计算     │  ──▶ │   选币排名     │
│ spot_dict.pkl │      │   factor.py   │      │ select_coin.py│
│ swap_dict.pkl │      │               │      │               │
└───────────────┘      └───────────────┘      └───────┬───────┘
                                                      │
                                                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   配置参数     │  ──▶ │   仓位聚合     │  ◀── │  多策略选币    │
│   config.py   │      │ agg_ratio()   │      │   结果合并     │
│               │      │               │      │               │
└───────────────┘      └───────┬───────┘      └───────────────┘
                               │
                               ▼
                       ┌───────────────┐      ┌───────────────┐
                       │   模拟交易     │  ──▶ │   绩效评估     │
                       │ simulator.py  │      │ evaluate.py   │
                       │               │      │               │
                       └───────────────┘      └───────┬───────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │   输出文件     │
                                              │ CSV / PNG     │
                                              │               │
                                              └───────────────┘
```

---

## 四、模块耦合关系

### 4.1 依赖关系图

```
                              ┌─────────────────────────────────┐
                              │         config.py               │
                              │        (全局配置中心)            │
                              └────────────────┬────────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
           ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
           │  backtest.py  │          │param_search_  │          │param_search_  │
           │  (单次回测)    │          │beta.py       │          │beta_for_ui.py │
           │               │          │(参数搜索)     │          │(UI接口)       │
           └───────┬───────┘          └───────┬───────┘          └───────┬───────┘
                   │                          │                          │
                   └──────────────────────────┼──────────────────────────┘
                                              │
                                              ▼
                              ┌─────────────────────────────────┐
                              │          core/backtest.py       │
                              │         (回测执行引擎)           │
                              └────────────────┬────────────────┘
                                               │
              ┌────────────────────────────────┼────────────────────────────────┐
              │                                │                                │
              ▼                                ▼                                ▼
    ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
    │ core/factor.py  │              │core/select_coin │              │ core/simulator  │
    │   (因子计算)     │              │.py (选币逻辑)   │              │.py (模拟器)     │
    └────────┬────────┘              └────────┬────────┘              └────────┬────────┘
             │                                │                                │
             │                                │                                │
             ▼                                ▼                                ▼
    ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
    │utils/factor_hub │              │utils/strategy_  │              │ core/rebalance  │
    │.py (因子加载器)  │              │hub.py (策略加载)│              │.py (调仓计算)   │
    └────────┬────────┘              └────────┬────────┘              └─────────────────┘
             │                                │
             │                                │
             ▼                                ▼
    ┌─────────────────┐              ┌─────────────────┐
    │  factors/       │              │  positions/     │
    │  sections/      │              │                 │
    │ (因子库)        │              │ (仓位策略库)    │
    └─────────────────┘              └─────────────────┘



              ┌─────────────────────────────────────────────────────┐
              │                    core/model/                      │
              │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
              │  │ backtest_   │  │ strategy_   │  │ timing_     │  │
              │  │ config.py   │  │ config.py   │  │ signal.py   │  │
              │  └─────────────┘  └─────────────┘  └─────────────┘  │
              │         ▲                ▲                ▲         │
              └─────────┼────────────────┼────────────────┼─────────┘
                        │                │                │
                        └────────────────┴────────────────┘
                                         │
                             被上层模块广泛引用
```

### 4.2 模块耦合矩阵

| 模块 \ 依赖 | config | core/backtest | core/select_coin | core/simulator | core/model | factors/ | positions/ | signals/ |
|------------|--------|---------------|------------------|----------------|------------|----------|------------|----------|
| **backtest.py** | ● | ● | ○ | ○ | ● | ○ | ○ | ○ |
| **param_search_*.py** | ● | ● | ○ | ○ | ● | ○ | ○ | ○ |
| **core/backtest.py** | ○ | - | ● | ● | ● | ○ | ○ | ○ |
| **core/select_coin.py** | ○ | ○ | - | ○ | ● | ○ | ○ | ○ |
| **core/simulator.py** | ○ | ○ | ○ | - | ● | ○ | ○ | ○ |
| **core/factor.py** | ○ | ○ | ○ | ○ | ○ | ● | ○ | ○ |
| **utils/factor_hub.py** | ○ | ○ | ○ | ○ | ○ | ● | ○ | ○ |
| **utils/strategy_hub.py** | ○ | ○ | ○ | ○ | ○ | ○ | ● | ○ |
| **utils/signal_hub.py** | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ● |

> ● = 强依赖 (直接导入)
> ○ = 无依赖或间接依赖

### 4.3 关键耦合点分析

#### 4.3.1 Hub 系统：松耦合设计

框架采用 **Hub 模式** 实现扩展模块的动态加载，这是一种典型的**依赖倒置**设计：

```python
# core/utils/factor_hub.py
class FactorHub:
    """因子动态加载器"""

    def __init__(self, factor_dirs=['factors', 'sections']):
        self.factor_dirs = factor_dirs
        self._cache = {}

    def get_factor_func(self, factor_name: str):
        """动态加载因子模块并返回 signal 函数"""
        if factor_name in self._cache:
            return self._cache[factor_name]

        for dir_path in self.factor_dirs:
            module_path = f"{dir_path}/{factor_name}.py"
            if os.path.exists(module_path):
                module = importlib.import_module(f"{dir_path}.{factor_name}")
                self._cache[factor_name] = module.signal
                return module.signal

        raise ValueError(f"Factor not found: {factor_name}")
```

**优势**：
- 核心代码不需要知道具体因子实现
- 新增因子只需在 `factors/` 或 `sections/` 目录下添加文件
- 支持热插拔，无需修改核心代码

#### 4.3.2 配置驱动：中心化配置

`config.py` 作为全局配置中心，集中管理所有可配置项：

```python
# config.py 结构示意
# ═══════════════════════════════════════════════════════════

# 1. 数据路径配置
pre_data_path = r'D:\历史数据\binance_spot_swap_preprocess_1h'

# 2. 时间窗口配置
start_date = '2021-01-01 00:00:00'
end_date = '2025-01-07'

# 3. 策略池配置 (核心)
strategy_pool = [
    dict(
        strategy_list=[{...}, {...}],     # 子策略列表
        re_timing={'name': '...', 'params': [...]}  # 择时配置
    ),
    ...
]

# 4. 仓位管理策略配置
strategy_config = {
    'name': 'FixedRatioStrategy',
    'params': {'cap_ratios': [1/3, 1/3, 1/3]}
}

# 5. 模拟器参数配置
simulator_config = {...}

# 6. 过滤列表配置
black_list = []
white_list = []
stable_symbol = [...]
```

**配置流向**：

```
config.py
    │
    ├──▶ MultiEquityBacktestConfig (聚合配置)
    │         │
    │         ├──▶ BacktestConfigFactory (配置工厂)
    │         │         │
    │         │         └──▶ BacktestConfig × N (子策略配置)
    │         │
    │         └──▶ PosStrategyConfig (仓位策略配置)
    │
    └──▶ simulator_config (模拟器参数)
```

#### 4.3.3 数据模型层：类型安全

`core/model/` 提供类型化的数据结构，确保数据在模块间传递时的一致性：

```python
# core/model/backtest_config.py
@dataclass
class BacktestConfig:
    """单账户回测配置"""
    strategy_name: str
    hold_period: str
    factor_list: List[Tuple[str, bool, int, int]]
    filter_list: List[Tuple[str, float, str]]
    is_use_spot: bool
    cap_weight: float
    offset: int
    # ...

@dataclass
class StrategyConfig:
    """策略参数配置"""
    select_coin_num: int
    hold_period: str
    factor_list: List[Tuple]
    filter_list: List[Tuple]
    # ...
```

---

## 五、核心模块详解

### 5.1 回测执行引擎 (`core/backtest.py`)

#### 5.1.1 执行步骤划分

```python
# 回测执行流程（简化）
def run_backtest(multi_config: MultiEquityBacktestConfig):
    """
    完整回测执行流程
    """
    # Step 2: 加载预处理数据
    all_candle_dict = step2_load_data(multi_config)

    # Step 3: 计算因子
    all_candle_dict = step3_calc_factors(all_candle_dict, multi_config)

    # Step 4: 选币
    select_results = step4_select_coins(all_candle_dict, multi_config)

    # Step 5: 聚合多策略选币结果
    final_select_df = step5_aggregate_select_results(select_results, multi_config)

    # Step 6: 模拟交易并计算绩效
    equity_df, evaluate_df = step6_simulate_performance(
        all_candle_dict, final_select_df, multi_config
    )

    return equity_df, evaluate_df
```

#### 5.1.2 步骤详解

| 步骤 | 函数 | 输入 | 输出 | 核心逻辑 |
|-----|------|-----|------|---------|
| Step 2 | `step2_load_data()` | 配置 | K线字典 | 加载 pickle 预处理数据 |
| Step 3 | `step3_calc_factors()` | K线字典, 配置 | K线字典(含因子) | 调用 FactorHub 计算因子 |
| Step 4 | `step4_select_coins()` | K线字典, 配置 | 选币结果列表 | 按因子排序选币 |
| Step 5 | `step5_aggregate_select_results()` | 选币结果, 配置 | 最终选币DF | 多策略权重聚合 |
| Step 6 | `step6_simulate_performance()` | K线字典, 选币DF, 配置 | 资金曲线, 评价 | Numba模拟器执行 |

### 5.2 选币逻辑 (`core/select_coin.py`)

#### 5.2.1 核心函数

```python
def calc_factors(all_candle_dict: dict, factor_list: list, factor_hub: FactorHub):
    """
    计算因子值

    Args:
        all_candle_dict: {symbol: DataFrame} K线数据字典
        factor_list: [(因子名, 是否升序, 参数n, 选币数量), ...]
        factor_hub: 因子加载器

    Returns:
        all_candle_dict: 添加了因子列的K线字典
    """
    for symbol, df in all_candle_dict.items():
        for factor_name, is_asc, n, select_num in factor_list:
            factor_func = factor_hub.get_factor_func(factor_name)
            df[f'{factor_name}_{n}'] = factor_func(df, n)
    return all_candle_dict


def select_coins(all_candle_dict: dict, factor_list: list,
                 filter_list: list, hold_period: str):
    """
    基于因子排名选币

    Args:
        all_candle_dict: 含因子列的K线字典
        factor_list: 因子配置
        filter_list: 过滤条件
        hold_period: 持仓周期 ('1H', '4H', '1D')

    Returns:
        select_result_df: 选币结果DataFrame
    """
    # 1. 合并所有币种数据到一个大表
    all_df = pd.concat([
        df.assign(symbol=symbol)
        for symbol, df in all_candle_dict.items()
    ])

    # 2. 按时间分组，在每个时间点对所有币种排名
    result_list = []
    for candle_time, group_df in all_df.groupby('candle_begin_time'):
        # 2.1 应用过滤条件
        filtered_df = apply_filters(group_df, filter_list)

        # 2.2 按因子值排序
        for factor_name, is_asc, n, select_num in factor_list:
            factor_col = f'{factor_name}_{n}'
            sorted_df = filtered_df.sort_values(factor_col, ascending=is_asc)

            # 2.3 选取 Top N
            selected_df = sorted_df.head(select_num)
            selected_df['weight'] = 1.0 / select_num
            result_list.append(selected_df)

    return pd.concat(result_list)


def agg_multi_strategy_ratio(select_results: list, strategy_weights: pd.DataFrame):
    """
    聚合多策略选币结果

    Args:
        select_results: [子策略A选币DF, 子策略B选币DF, ...]
        strategy_weights: 策略权重时间序列

    Returns:
        final_select_df: 最终选币结果（含聚合后的 target_ratio）
    """
    # 合并所有子策略结果
    all_results = pd.concat(select_results)

    # 按时间和币种分组，加权求和
    final_df = all_results.groupby(['candle_begin_time', 'symbol']).apply(
        lambda g: (g['weight'] * g['strategy_weight']).sum()
    ).reset_index(name='target_ratio')

    return final_df
```

#### 5.2.2 选币流程图

```
全市场K线数据
      │
      ▼
┌─────────────────────────────────────────┐
│           因子计算                       │
│  每个币种的 DataFrame 添加因子列          │
│  df['momentum_20'] = calc_momentum(...)  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           时间切片                       │
│  按 candle_begin_time 分组               │
│  每个时间点包含所有币种的因子值           │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           过滤条件                       │
│  filter_list: [(factor, threshold, op)] │
│  例: [('volume_20', 1000000, '>')]      │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           因子排名                       │
│  sort_values(factor_col, ascending=?)   │
│  升序: 因子值小的排前面                  │
│  降序: 因子值大的排前面                  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           选取 Top N                     │
│  head(select_num)                       │
│  分配等权重: weight = 1/N               │
└─────────────────┬───────────────────────┘
                  │
                  ▼
           选币结果 DataFrame
```

### 5.3 高性能模拟器 (`core/simulator.py`)

#### 5.3.1 Numba 加速设计

```python
from numba import jit, types
from numba.experimental import jitclass

# 账户状态结构（Numba 兼容）
account_spec = [
    ('equity', types.float64),
    ('margin', types.float64),
    ('unrealized_pnl', types.float64),
    ('realized_pnl', types.float64),
]

@jitclass(account_spec)
class AccountState:
    """账户状态（Numba JIT 编译）"""
    def __init__(self, initial_equity):
        self.equity = initial_equity
        self.margin = 0.0
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0


@jit(nopython=True)
def simulate_step(account: AccountState,
                  current_lots: np.ndarray,
                  target_lots: np.ndarray,
                  prices: np.ndarray,
                  is_spot: np.ndarray,
                  swap_c_rate: float,
                  spot_c_rate: float):
    """
    单步模拟（Numba JIT 编译）

    核心性能优化点：
    1. nopython 模式确保纯 LLVM 编译
    2. 使用 numpy 数组而非 Python 列表
    3. 避免 Python 对象操作
    """
    # 计算调仓差额
    delta_lots = target_lots - current_lots

    # 先平仓（释放保证金）
    close_mask = delta_lots < 0
    close_amount = np.abs(delta_lots[close_mask] * prices[close_mask])
    close_fee = np.sum(close_amount * np.where(is_spot[close_mask], spot_c_rate, swap_c_rate))

    # 后开仓
    open_mask = delta_lots > 0
    open_amount = np.abs(delta_lots[open_mask] * prices[open_mask])
    open_fee = np.sum(open_amount * np.where(is_spot[open_mask], spot_c_rate, swap_c_rate))

    # 更新账户状态
    total_fee = close_fee + open_fee
    account.equity -= total_fee

    return target_lots, total_fee
```

#### 5.3.2 模拟器执行流程

```
初始化账户状态
equity = 10000 USDT
lots = {} (空仓)
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│                      K线循环开始                              │
│  for t in candle_begin_time_range:                           │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 1. 读取当前选币结果                                      │  │
│  │    selected = select_df[select_df['time'] == t]        │  │
│  │    symbols = selected['symbol'].tolist()               │  │
│  │    target_ratios = selected['target_ratio'].values     │  │
│  └────────────────────────────────────────────────────────┘  │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 2. 获取当前价格                                         │  │
│  │    prices = {sym: candle_dict[sym].loc[t, 'close']     │  │
│  │              for sym in symbols}                       │  │
│  └────────────────────────────────────────────────────────┘  │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 3. 计算目标持仓 (rebalance.py)                         │  │
│  │    target_lots[sym] = equity × target_ratio / price    │  │
│  └────────────────────────────────────────────────────────┘  │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 4. 计算调仓差额                                         │  │
│  │    delta_lots = target_lots - current_lots             │  │
│  │    过滤最小下单量 (swap_min=5, spot_min=10)            │  │
│  └────────────────────────────────────────────────────────┘  │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 5. 执行交易                                             │  │
│  │    先平仓 (delta < 0) → 释放保证金                      │  │
│  │    后开仓 (delta > 0) → 占用保证金                      │  │
│  │    计算手续费 (swap: 0.05%, spot: 0.1%)               │  │
│  └────────────────────────────────────────────────────────┘  │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 6. 更新账户状态                                         │  │
│  │    lots = new_lots                                     │  │
│  │    unrealized_pnl = Σ(lots × (current_price - entry))  │  │
│  │    equity = initial + realized_pnl + unrealized_pnl    │  │
│  └────────────────────────────────────────────────────────┘  │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 7. 检查爆仓                                             │  │
│  │    if margin / equity > margin_rate:                   │  │
│  │        强制平仓所有持仓                                  │  │
│  └────────────────────────────────────────────────────────┘  │
│      │                                                       │
│      ▼                                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 8. 记录资金曲线点                                       │  │
│  │    equity_curve.append((t, equity))                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
      │
      ▼
输出资金曲线 DataFrame
```

### 5.4 仓位调整 (`core/rebalance.py`)

#### 5.4.1 核心计算逻辑

```python
@jit(nopython=True)
def calc_target_lots_by_ratio(equity: float,
                               target_ratios: np.ndarray,
                               prices: np.ndarray,
                               leverage: float = 1.0):
    """
    根据目标比例计算目标持仓手数

    公式: target_lots = (equity × ratio × leverage) / price

    Args:
        equity: 当前权益
        target_ratios: 目标仓位比例数组 [0.3, 0.3, 0.4]
        prices: 当前价格数组
        leverage: 杠杆倍数

    Returns:
        target_lots: 目标持仓手数数组
    """
    return (equity * target_ratios * leverage) / prices


@jit(nopython=True)
def calc_delta_lots_amount(current_lots: np.ndarray,
                            target_lots: np.ndarray,
                            prices: np.ndarray):
    """
    计算调仓差额和金额

    Returns:
        delta_lots: 调仓手数 (正=开仓, 负=平仓)
        delta_amount: 调仓金额
    """
    delta_lots = target_lots - current_lots
    delta_amount = np.abs(delta_lots * prices)
    return delta_lots, delta_amount


@jit(nopython=True)
def filter_deltas(delta_lots: np.ndarray,
                  delta_amount: np.ndarray,
                  is_spot: np.ndarray,
                  swap_min: float = 5.0,
                  spot_min: float = 10.0):
    """
    过滤小于最小下单量的调仓

    规则:
    - 合约最小下单量: $5
    - 现货最小下单量: $10

    Returns:
        filtered_delta_lots: 过滤后的调仓手数
    """
    min_amounts = np.where(is_spot, spot_min, swap_min)
    mask = delta_amount >= min_amounts
    return np.where(mask, delta_lots, 0.0)
```

#### 5.4.2 调仓模式

```python
# core/model/rebalance_mode.py
from enum import Enum

class RebalanceMode(Enum):
    """调仓模式枚举"""

    REB_ALWAYS = 'always'      # 每根K线都调仓
    REB_SIGNAL = 'signal'      # 仅在信号变化时调仓
    REB_PERIOD = 'period'      # 固定周期调仓 (1H/4H/1D)
```

### 5.5 因子接口规范

#### 5.5.1 时序因子 (`factors/`)

```python
# factors/Momentum.py - 时序因子示例

def signal(df: pd.DataFrame, n: int, factor_name: str = None):
    """
    单参数因子计算

    Args:
        df: 单币种K线DataFrame，必含列: open, high, low, close, volume
        n: 因子参数（通常是周期数）
        factor_name: 因子名称（可选，用于列命名）

    Returns:
        pd.Series: 因子值序列，索引与 df 对齐
    """
    return df['close'].pct_change(n)


def signal_multi_params(df: pd.DataFrame, param_list: list):
    """
    多参数因子计算（性能优化写法）

    Args:
        df: 单币种K线DataFrame
        param_list: [(n1, factor_name1), (n2, factor_name2), ...]

    Returns:
        dict: {param: pd.Series} 因子值字典
    """
    result = {}
    for n, factor_name in param_list:
        result[(n, factor_name)] = df['close'].pct_change(n)
    return result
```

#### 5.5.2 截面因子 (`sections/`)

```python
# sections/RelativeStrength.py - 截面因子示例

is_cross = True  # 标记为截面因子（必需）

def get_factor_list(n: int):
    """
    返回依赖的基础因子列表

    截面因子需要先计算基础因子，再在全市场范围内比较

    Returns:
        list: 依赖因子列表 [(factor_name, n), ...]
    """
    return [('PctChange', n)]


def signal(all_df: pd.DataFrame, n: int, factor_name: str = None):
    """
    截面因子计算

    与时序因子不同：
    - 输入是合并后的全市场DataFrame（含 symbol 列）
    - 在每个时间点对所有币种进行比较

    Args:
        all_df: 全市场K线DataFrame，含 symbol 列
        n: 因子参数

    Returns:
        pd.Series: 截面排名/分数
    """
    base_factor = f'PctChange_{n}'

    # 按时间分组，计算截面排名
    return all_df.groupby('candle_begin_time')[base_factor].rank(pct=True)
```

### 5.6 仓位策略接口规范

#### 5.6.1 固定比例策略 (`positions/FixedRatioStrategy.py`)

```python
def calc_ratio(equity_dfs: list, stg_conf: PosStrategyConfig) -> pd.DataFrame:
    """
    固定比例仓位分配

    Args:
        equity_dfs: [子策略A资金曲线DF, 子策略B资金曲线DF, ...]
        stg_conf: 策略配置，包含:
            - cap_ratios: [0.33, 0.33, 0.34] 固定分配比例

    Returns:
        pd.DataFrame: 时间 × 策略 的权重矩阵
            columns: [candle_begin_time, Strategy_A, Strategy_B, Strategy_C]
            每行各策略权重之和为 1.0

    示例输出:
        candle_begin_time    Strategy_A  Strategy_B  Strategy_C
        2024-01-01 00:00:00     0.333       0.333       0.334
        2024-01-01 01:00:00     0.333       0.333       0.334
        ...
    """
    cap_ratios = stg_conf.params.get('cap_ratios', [1.0 / len(equity_dfs)] * len(equity_dfs))

    # 获取时间索引
    time_index = equity_dfs[0]['candle_begin_time']

    # 构建权重DataFrame
    result = pd.DataFrame({'candle_begin_time': time_index})
    for i, (equity_df, ratio) in enumerate(zip(equity_dfs, cap_ratios)):
        result[f'Strategy_{i}'] = ratio

    return result
```

#### 5.6.2 轮动策略 (`positions/RotationStrategy.py`)

```python
def calc_ratio(equity_dfs: list, stg_conf: PosStrategyConfig) -> pd.DataFrame:
    """
    轮动仓位分配

    根据子策略的历史表现动态调整权重

    Args:
        equity_dfs: 子策略资金曲线列表
        stg_conf: 策略配置，包含:
            - factor_list: [('momentum', n), ...] 轮动因子
            - lookback: 回溯周期

    Returns:
        pd.DataFrame: 动态权重矩阵

    逻辑:
        1. 计算各子策略近期表现（momentum/sharpe/...）
        2. 按表现排名分配权重（表现好的权重高）
    """
    factor_list = stg_conf.params.get('factor_list', [])
    lookback = stg_conf.params.get('lookback', 30 * 24)  # 默认30天

    # 计算各策略表现
    performances = []
    for equity_df in equity_dfs:
        equity = equity_df['equity']
        perf = equity.pct_change(lookback).fillna(0)
        performances.append(perf)

    # 归一化为权重
    perf_df = pd.concat(performances, axis=1)
    perf_df = perf_df.clip(lower=0)  # 负表现设为0
    weight_df = perf_df.div(perf_df.sum(axis=1), axis=0).fillna(1.0 / len(equity_dfs))

    # 构建结果
    result = pd.DataFrame({'candle_begin_time': equity_dfs[0]['candle_begin_time']})
    for i in range(len(equity_dfs)):
        result[f'Strategy_{i}'] = weight_df.iloc[:, i].values

    return result
```

### 5.7 择时信号接口规范

```python
# signals/MovingAverage.py

def dynamic_leverage(equity: pd.Series, n: int) -> pd.Series:
    """
    均线择时信号

    Args:
        equity: 资金曲线 (pd.Series, index=candle_begin_time)
        n: 均线周期

    Returns:
        pd.Series: 杠杆倍数序列
            0 = 空仓
            1 = 满仓
            2 = 2倍杠杆
            ...

    逻辑:
        equity > MA(equity, n) → 满仓 (leverage=1)
        equity < MA(equity, n) → 空仓 (leverage=0)
    """
    ma = equity.rolling(n).mean()
    leverage = (equity > ma).astype(float)
    return leverage
```

---

## 六、配置体系详解

### 6.1 配置层级结构

```
config.py (全局配置)
│
├── 数据配置
│   ├── pre_data_path      # 预处理数据路径
│   ├── start_date         # 回测开始时间
│   ├── end_date           # 回测结束时间
│   └── min_kline_num      # 最少K线数量要求
│
├── 策略池配置 (strategy_pool)
│   └── [策略组1, 策略组2, ...]
│       └── 策略组结构:
│           ├── strategy_list[]   # 子策略列表
│           │   └── 子策略配置:
│           │       ├── strategy    # 策略名称
│           │       ├── offset_list # 偏移量列表
│           │       ├── hold_period # 持仓周期
│           │       ├── is_use_spot # 是否使用现货
│           │       ├── cap_weight  # 资金权重
│           │       ├── factor_list # 因子列表
│           │       └── filter_list # 过滤条件
│           │
│           └── re_timing{}       # 择时配置
│               ├── name          # 择时信号名称
│               └── params        # 择时参数
│
├── 仓位策略配置 (strategy_config)
│   ├── name               # 策略名称
│   ├── hold_period        # 持仓周期
│   └── params             # 策略参数
│       └── cap_ratios / factor_list / ...
│
├── 模拟器配置 (simulator_config)
│   ├── account_type       # 账户类型
│   ├── initial_usdt       # 初始资金
│   ├── margin_rate        # 保证金率
│   ├── swap_c_rate        # 合约手续费
│   ├── spot_c_rate        # 现货手续费
│   ├── swap_min_order_limit  # 合约最小下单量
│   ├── spot_min_order_limit  # 现货最小下单量
│   └── avg_price_col      # 均价列名
│
└── 过滤配置
    ├── black_list         # 黑名单
    ├── white_list         # 白名单
    └── stable_symbol      # 稳定币列表
```

### 6.2 配置示例详解

```python
# config.py 完整示例

# ═══════════════════════════════════════════════════════════
#                        数据配置
# ═══════════════════════════════════════════════════════════

# 预处理数据路径（包含 spot_dict.pkl 和 swap_dict.pkl）
pre_data_path = r'D:\历史数据\binance_spot_swap_preprocess_1h'

# 回测时间窗口
start_date = '2021-01-01 00:00:00'
end_date = '2025-01-07 00:00:00'

# 最少K线数量（用于过滤新上市币种）
min_kline_num = 168  # 168小时 = 7天

# ═══════════════════════════════════════════════════════════
#                        策略池配置
# ═══════════════════════════════════════════════════════════

strategy_pool = [
    # ─────────────────────────────────────────────
    # 策略组 1: BTC 单币策略（保守组）
    # ─────────────────────────────────────────────
    dict(
        strategy_list=[
            {
                "strategy": "Strategy_BTC",         # 策略名称
                "offset_list": [0],                 # 换仓偏移量
                "hold_period": "1H",                # 持仓周期
                "is_use_spot": True,                # 使用现货
                "cap_weight": 1,                    # 资金权重
                "factor_list": [
                    # (因子名, 是否升序, 参数n, 选币数量)
                    ('OnlyBTC', False, 1, 1),       # 仅选BTC
                ],
                "filter_list": [],                  # 无过滤条件
            }
        ],
        re_timing={                                 # 择时配置
            'name': 'MovingAverage',
            'params': [34 * 24]                     # 34天均线
        }
    ),

    # ─────────────────────────────────────────────
    # 策略组 2: 动量选币策略（激进组）
    # ─────────────────────────────────────────────
    dict(
        strategy_list=[
            {
                "strategy": "Strategy_Momentum",
                "offset_list": [0, 4, 8],           # 3个换仓偏移
                "hold_period": "4H",                # 4小时周期
                "is_use_spot": False,               # 使用合约
                "cap_weight": 1,
                "factor_list": [
                    ('Momentum', True, 20, 5),      # 20周期动量，选5个
                ],
                "filter_list": [
                    ('Volume', 1000000, '>'),       # 成交量 > 100万
                    ('Volatility', 0.1, '<'),       # 波动率 < 10%
                ],
            }
        ],
        re_timing=None                              # 不使用择时
    ),

    # ─────────────────────────────────────────────
    # 策略组 3: 截面因子策略
    # ─────────────────────────────────────────────
    dict(
        strategy_list=[
            {
                "strategy": "Strategy_CrossSection",
                "offset_list": [0],
                "hold_period": "1D",                # 日线周期
                "is_use_spot": False,
                "cap_weight": 1,
                "factor_list": [
                    ('Demo', False, 5, 10),         # 截面因子，选10个
                ],
                "filter_list": [],
            }
        ],
        re_timing={
            'name': 'MovingAverage',
            'params': [20 * 24]                     # 20天均线
        }
    ),
]

# ═══════════════════════════════════════════════════════════
#                     仓位管理策略配置
# ═══════════════════════════════════════════════════════════

strategy_config = {
    'name': 'FixedRatioStrategy',                   # 固定比例策略
    'hold_period': '1H',
    'params': {
        'cap_ratios': [0.4, 0.3, 0.3]               # 40%/30%/30% 分配
    }
}

# 轮动策略示例（注释）
# strategy_config = {
#     'name': 'RotationStrategy',
#     'hold_period': '1D',
#     'params': {
#         'factor_list': [('momentum', 30*24)],     # 30天动量轮动
#         'lookback': 30 * 24
#     }
# }

# ═══════════════════════════════════════════════════════════
#                       模拟器配置
# ═══════════════════════════════════════════════════════════

simulator_config = dict(
    # 账户类型
    account_type='普通账户',                         # '普通账户' / '统一账户'

    # 初始资金
    initial_usdt=10000,

    # 保证金设置
    margin_rate=0.05,                               # 5% 保证金率

    # 手续费设置
    swap_c_rate=5 / 10000,                          # 合约手续费 0.05%
    spot_c_rate=1 / 1000,                           # 现货手续费 0.1%

    # 最小下单量
    swap_min_order_limit=5,                         # 合约最小 $5
    spot_min_order_limit=10,                        # 现货最小 $10

    # 均价列名（用于滑点模拟）
    avg_price_col='avg_price_1m',                   # 1分钟均价
)

# ═══════════════════════════════════════════════════════════
#                        过滤配置
# ═══════════════════════════════════════════════════════════

# 黑名单（禁止交易）
black_list = [
    'LUNA-USDT',
    'UST-USDT',
]

# 白名单（仅交易这些）- 留空表示不限制
white_list = []

# 稳定币列表（自动排除）
stable_symbol = [
    'USDC', 'BUSD', 'USDT', 'DAI', 'TUSD',
    'USDP', 'GUSD', 'FRAX', 'LUSD', 'USDD',
]

# ═══════════════════════════════════════════════════════════
#                       性能配置
# ═══════════════════════════════════════════════════════════

import os

# 并行进程数
job_num = max(os.cpu_count() - 1, 1)

# 内存优化：因子列数限制
factor_col_limit = 64

# 缓存控制
reserved_cache = ('select',)                        # 保留选币结果缓存
```

---

## 七、扩展开发指南

### 7.1 添加新因子

#### 7.1.1 时序因子

```python
# 文件: factors/MyMomentum.py

"""
自定义动量因子

因子逻辑：计算过去 n 周期的收益率
"""

def signal(df, n, factor_name=None):
    """
    单参数因子计算

    Args:
        df: 单币种K线DataFrame
        n: 周期参数
        factor_name: 因子名（可选）

    Returns:
        pd.Series: 因子值
    """
    return df['close'].pct_change(n)


def signal_multi_params(df, param_list):
    """
    多参数批量计算（可选，性能优化）

    Args:
        param_list: [(n1, name1), (n2, name2), ...]

    Returns:
        dict: {(n, name): pd.Series}
    """
    result = {}
    for n, factor_name in param_list:
        result[(n, factor_name)] = df['close'].pct_change(n)
    return result
```

**使用方法**：
```python
# config.py
factor_list = [
    ('MyMomentum', True, 20, 5),   # 20周期动量，升序，选5个
]
```

#### 7.1.2 截面因子

```python
# 文件: sections/MyRelativeStrength.py

"""
相对强度截面因子

因子逻辑：在每个时间点，计算各币种收益率相对于市场平均的强度
"""

is_cross = True  # 必需：标记为截面因子

def get_factor_list(n):
    """
    返回依赖的基础因子

    截面因子需要先计算基础时序因子，
    然后在 signal 函数中进行跨币种比较
    """
    return [('PctChange', n)]  # 依赖 PctChange 因子


def signal(all_df, n, factor_name=None):
    """
    截面因子计算

    Args:
        all_df: 全市场合并DataFrame（含 symbol 列）
        n: 参数

    Returns:
        pd.Series: 截面排名分数
    """
    base_col = f'PctChange_{n}'

    # 按时间分组，计算截面排名（百分位）
    return all_df.groupby('candle_begin_time')[base_col].rank(pct=True)
```

### 7.2 添加新仓位策略

```python
# 文件: positions/MyDynamicStrategy.py

"""
动态权重分配策略

策略逻辑：根据各子策略的波动率倒数分配权重（风险平价）
"""

import pandas as pd
import numpy as np

def calc_ratio(equity_dfs, stg_conf):
    """
    计算仓位比例

    Args:
        equity_dfs: 子策略资金曲线列表
        stg_conf: PosStrategyConfig 配置对象

    Returns:
        pd.DataFrame: 权重矩阵
    """
    lookback = stg_conf.params.get('lookback', 30 * 24)

    # 计算各策略波动率
    volatilities = []
    for equity_df in equity_dfs:
        returns = equity_df['equity'].pct_change()
        vol = returns.rolling(lookback).std()
        volatilities.append(vol)

    # 波动率倒数作为权重
    vol_df = pd.concat(volatilities, axis=1)
    inv_vol = 1.0 / vol_df.replace(0, np.inf)
    weights = inv_vol.div(inv_vol.sum(axis=1), axis=0).fillna(1.0 / len(equity_dfs))

    # 构建结果DataFrame
    result = pd.DataFrame({'candle_begin_time': equity_dfs[0]['candle_begin_time']})
    for i in range(len(equity_dfs)):
        result[f'Strategy_{i}'] = weights.iloc[:, i].values

    return result
```

**使用方法**：
```python
# config.py
strategy_config = {
    'name': 'MyDynamicStrategy',
    'hold_period': '1D',
    'params': {
        'lookback': 30 * 24  # 30天回溯期
    }
}
```

### 7.3 添加新择时信号

```python
# 文件: signals/MyVolatilitySignal.py

"""
波动率择时信号

信号逻辑：波动率高于阈值时降低仓位
"""

import pandas as pd

def dynamic_leverage(equity, vol_threshold=0.02, lookback=24*7):
    """
    波动率择时

    Args:
        equity: 资金曲线 pd.Series
        vol_threshold: 波动率阈值
        lookback: 回溯周期

    Returns:
        pd.Series: 杠杆倍数 (0~1)
    """
    returns = equity.pct_change()
    volatility = returns.rolling(lookback).std()

    # 波动率低于阈值时满仓，高于阈值时减仓
    leverage = (volatility < vol_threshold).astype(float)

    return leverage
```

**使用方法**：
```python
# config.py
re_timing = {
    'name': 'MyVolatilitySignal',
    'params': [0.02, 24*7]  # 阈值=2%, 回溯=7天
}
```

---

## 八、性能优化要点

### 8.1 Numba JIT 编译

框架在以下模块使用 Numba 加速：

| 模块 | 加速函数 | 性能提升 |
|------|---------|---------|
| `simulator.py` | `simulate_step()` | ~10-50x |
| `rebalance.py` | `calc_target_lots_by_ratio()` | ~5-20x |
| `rebalance.py` | `calc_delta_lots_amount()` | ~5-20x |

**Numba 使用注意事项**：
```python
# ✓ 正确：使用 numpy 数组
@jit(nopython=True)
def fast_calc(arr: np.ndarray) -> np.ndarray:
    return arr * 2

# ✗ 错误：使用 Python 列表/字典
@jit(nopython=True)  # 会报错
def slow_calc(lst: list) -> list:
    return [x * 2 for x in lst]
```

### 8.2 并行计算

```python
# config.py
import os

# 并行进程数（留1核给系统）
job_num = max(os.cpu_count() - 1, 1)
```

并行点：
- 因子计算：各币种独立计算
- 参数搜索：各参数组合独立回测

### 8.3 内存优化

```python
# config.py

# 限制因子列数（减少内存占用）
factor_col_limit = 64

# 缓存控制（仅保留必要缓存）
reserved_cache = ('select',)  # 仅保留选币结果
```

---

## 九、常见问题与解决方案

### 9.1 因子计算相关

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 因子值全为 NaN | 参数 n 大于数据长度 | 检查 `min_kline_num` 配置 |
| 截面因子未生效 | 缺少 `is_cross = True` | 在因子文件中添加标记 |
| 因子加载失败 | 文件名与引用不匹配 | 检查 `factor_list` 中的因子名 |

### 9.2 模拟相关

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 频繁爆仓 | 保证金率过高 | 降低 `margin_rate` |
| 调仓过于频繁 | 无最小下单量过滤 | 检查 `min_order_limit` |
| 手续费过高 | 费率配置错误 | 检查 `c_rate` 配置 |

### 9.3 性能相关

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| 内存溢出 | 因子列过多 | 降低 `factor_col_limit` |
| 回测过慢 | 单线程计算 | 增加 `job_num` |
| Numba 编译慢 | 首次运行 JIT 编译 | 正常现象，后续会缓存 |

---

## 十、版本更新记录

| 版本 | 日期 | 主要更新 |
|------|-----|---------|
| v1.3.8 | 2025-10-23 | 网页版回测支持 (`param_search_beta_for_ui.py`) |
| v1.3.7 | 2025-09-30 | 三期船队功能、SYRUP 币种修复 |
| v1.3.6 | 2025-08-26 | MultiRotationStrategy 遍历支持 |
| v1.3.5 | 2025-07-22 | 超限仓位填充策略 |
| v1.3.4 | 2025-07-14 | 单币权重限制、Top3 币种显示 |

---

## 十一、附录

### A. 文件统计

| 分类 | 文件数 | 代码行数 |
|------|-------|---------|
| 核心引擎 (`core/`) | 23 | ~5,438 |
| 因子库 (`factors/`, `sections/`) | 2 | ~50 |
| 策略库 (`positions/`) | 2 | ~100 |
| 信号库 (`signals/`) | 1 | ~30 |
| 工具脚本 (`tools/`) | 5 | ~200 |
| 入口脚本 | 4 | ~500 |
| **合计** | **~42** | **~6,400** |

### B. 依赖包清单

```
# requirements.txt
pandas>=1.5.0
numpy>=1.23.0
numba>=0.56.0
matplotlib>=3.6.0
xbx-py11>=1.0.0
```

### C. 目录快速索引

| 功能需求 | 对应文件 |
|---------|---------|
| 添加新因子 | `factors/*.py` 或 `sections/*.py` |
| 添加新仓位策略 | `positions/*.py` |
| 添加新择时信号 | `signals/*.py` |
| 修改回测参数 | `config.py` |
| 理解执行流程 | `core/backtest.py` |
| 理解选币逻辑 | `core/select_coin.py` |
| 理解模拟交易 | `core/simulator.py` |
| 理解仓位调整 | `core/rebalance.py` |

---

*文档生成于 2026-01-15 | Claude AI 资深量化分析师 & 系统架构师*
