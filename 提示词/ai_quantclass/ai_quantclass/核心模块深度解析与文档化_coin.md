# 核心模块深度解析与文档化

> **框架版本**: v1.3.8
> **文档版本**: v1.0
> **生成日期**: 2026-01-15
> **分析师**: Claude AI (资深量化分析师 & 系统架构师)

---

## 目录

1. [回测主程序 (backtest.py)](#一回测主程序-backtestpy)
2. [核心回测引擎 (core/backtest.py)](#二核心回测引擎-corebacktestpy)
3. [选币逻辑模块 (core/select_coin.py)](#三选币逻辑模块-coreselect_coinpy)
4. [高性能模拟器 (core/simulator.py)](#四高性能模拟器-coresimulatorpy)
5. [资金曲线计算 (core/equity.py)](#五资金曲线计算-coreequitypy)
6. [因子计算模块 (core/factor.py)](#六因子计算模块-corefactorpy)
7. [仓位调整模块 (core/rebalance.py)](#七仓位调整模块-corerebalancepy)
8. [策略评价模块 (core/evaluate.py)](#八策略评价模块-coreevaluatepy)
9. [配置模型 (core/model/)](#九配置模型-coremodel)
10. [工具类 (core/utils/)](#十工具类-coreutils)
11. [异常处理机制总结](#十一异常处理机制总结)
12. [优化建议](#十二优化建议)

---

## 一、回测主程序 (backtest.py)

### 1.1 功能描述

**入口脚本**，负责编排整个仓位管理回测流程。它是用户运行回测的统一入口点，协调以下六个核心步骤：

```
初始化配置 → 子策略回测 → 处理资金曲线 → 计算仓位比例 → 聚合选币结果 → 模拟交易
```

### 1.2 核心执行流程

```python
# 完整执行流程
if __name__ == '__main__':
    # Step 1: 初始化
    me_conf = MultiEquityBacktestConfig()

    # Step 2: 子策略回测
    me_conf.backtest_strategies()

    # Step 3: 处理资金曲线
    me_conf.process_equities()

    # Step 4: 计算仓位比例
    pos_ratio = me_conf.calc_ratios()

    # Step 5: 聚合选币结果
    df_spot_ratio, df_swap_ratio = me_conf.agg_pos_ratio(pos_ratio)

    # Step 5.1: 应用仓位限制
    df_spot_ratio, df_swap_ratio = me_conf.apply_position_limits(...)

    # Step 6: 模拟交易
    step6_simulate_performance(...)
```

### 1.3 核心函数清单

| 步骤 | 调用函数 | 输入 | 输出 | 功能描述 |
|-----|---------|-----|------|---------|
| 1 | `MultiEquityBacktestConfig()` | config.py 配置 | `me_conf` 对象 | 初始化多策略配置，包含所有子策略参数 |
| 2 | `me_conf.backtest_strategies()` | 配置对象 | 子策略资金曲线文件 | 并行运行所有子策略回测 |
| 3 | `me_conf.process_equities()` | 子策略资金曲线 | `equity_dfs`, `ratio_dfs` | 周期转换、因子计算、数据对齐 |
| 4 | `me_conf.calc_ratios()` | `equity_dfs` | `pos_ratio` DataFrame | 根据仓位策略计算子策略权重 |
| 5 | `me_conf.agg_pos_ratio()` | `pos_ratio`, `ratio_dfs` | `df_spot_ratio`, `df_swap_ratio` | 聚合多策略选币结果 |
| 5.1 | `me_conf.apply_position_limits()` | ratio DataFrames | 限制后的 ratio | 应用单币种权重限制 |
| 6 | `step6_simulate_performance()` | 所有数据 | 回测报告 | 模拟交易并生成报告 |

### 1.4 数据流图

```
config.py
    │
    ▼
┌─────────────────────────────┐
│ MultiEquityBacktestConfig   │
│ ├── factory (配置工厂)       │
│ ├── strategy (仓位策略)      │
│ └── leverage (杠杆)          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐      ┌─────────────────────────┐
│ backtest_strategies()       │ ──▶  │ 子策略资金曲线.csv       │
│ (调用 run_backtest_multi)   │      │ df_spot_ratio.pkl       │
│                             │      │ df_swap_ratio.pkl       │
└──────────────┬──────────────┘      └─────────────────────────┘
               │
               ▼
┌─────────────────────────────┐
│ process_equities()          │
│ ├── 周期转换 (H→D/6H/...)   │
│ ├── 因子计算                 │
│ └── 数据对齐                 │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ calc_ratios()               │
│ ├── 调用仓位策略 calc_ratio │
│ ├── 平滑换仓比例            │
│ └── 叠加择时杠杆            │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ agg_pos_ratio()             │
│ └── 按权重聚合选币结果       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ step6_simulate_performance()│
│ └── 模拟交易 + 绩效评估      │
└─────────────────────────────┘
```

---

## 二、核心回测引擎 (core/backtest.py)

### 2.1 功能描述

**回测流程编排模块**，提供单策略回测和多策略回测的完整执行流程。将数据加载、因子计算、选币、聚合、模拟交易等步骤封装为标准化的函数接口。

### 2.2 核心函数清单

| 函数名 | 输入参数 | 输出结果 | 算法逻辑 |
|-------|---------|---------|---------|
| `step2_load_data(conf)` | `BacktestConfig` | 无（数据存入缓存） | 调用 `load_spot_and_swap_data()` 读取预处理数据 |
| `step3_calc_factors(conf)` | `BacktestConfig` | 无（数据存入缓存） | 串行调用 `calc_factors()` 和 `calc_cross_sections()` |
| `step4_select_coins(conf)` | `BacktestConfig` | 无（选币结果存入文件） | 调用 `select_coins()` 执行选币逻辑 |
| `step5_aggregate_select_results(conf)` | `BacktestConfig` | `(df_spot_ratio, df_swap_ratio)` | 聚合多策略选币结果 |
| `step6_simulate_performance(...)` | 配置+数据+比例 | `report` DataFrame | 模拟交易并计算绩效 |
| `run_backtest(conf)` | `BacktestConfig` | 无 | 单策略完整回测流程 |
| `run_backtest_multi(factory)` | `BacktestConfigFactory` | `report_list` | 多策略并行回测流程 |
| `simu_timing(...)` | 配置+数据 | `(account_df, rtn, year_return)` | 择时信号回测 |

### 2.3 关键函数详解

#### 2.3.1 `run_backtest_multi(factory)`

```python
def run_backtest_multi(factory: BacktestConfigFactory):
    """
    多策略并行回测主函数

    执行流程:
    1. 准备工作: 删除缓存、创建结果目录
    2. 读取数据: 生成全因子配置，读取现货+合约K线
    3. 计算因子: 时序因子 + 截面因子
    4. 选币: 遍历策略池并行选币
    5. 聚合 + 模拟: 串行执行每个策略的聚合和模拟

    返回: 所有策略的回测报告列表
    """
```

**算法复杂度分析**：
- 因子计算: O(N_symbols × N_factors × N_bars)
- 选币: O(N_strategies × N_bars × N_symbols × log(N_symbols))
- 模拟: O(N_bars × N_symbols)

#### 2.3.2 `step6_simulate_performance(...)`

```python
def step6_simulate_performance(conf, df_spot_ratio, df_swap_ratio,
                               pivot_dict_spot, pivot_dict_swap, ...):
    """
    模拟交易并生成回测报告

    核心流程:
    1. 调用 calc_equity() 计算资金曲线
    2. 保存回测结果到 CSV
    3. 如果配置了择时信号，执行再择时回测
    4. 绘制资金曲线图表
    """
```

### 2.4 异常处理机制

```python
# 1. 数据长度校验
if len(report_list) > 65535:
    logger.debug(f'回测报表数量为 {len(report_list)}，超过 65535，后续可能会占用海量内存')

# 2. 择时信号实现检查
if conf.timing.impl_flags.get('dynamic_leverage_for_dataframe', False):
    leverages = conf.timing.get_dynamic_leverage_for_dataframe(account_df)
elif conf.timing.impl_flags.get('dynamic_leverage', False):
    leverages = conf.timing.get_dynamic_leverage(account_df['equity'])
else:
    raise NotImplementedError(f'择时信号 {conf.timing.name} 必须实现 dynamic_leverage...')

# 3. 选币异常捕获
for future in tqdm(as_completed(futures), ...):
    try:
        future.result()
    except Exception as e:
        logger.exception(e)
        exit(1)  # 选币异常直接退出
```

---

## 三、选币逻辑模块 (core/select_coin.py)

### 3.1 功能描述

**选币核心引擎**，实现从原始K线数据到选币结果的完整转换流程。包括：
- 时序因子计算
- 截面因子计算
- 因子排名选币
- 多策略聚合

### 3.2 核心函数清单

| 函数名 | 输入参数 | 输出结果 | 算法逻辑 |
|-------|---------|---------|---------|
| `calc_factors(conf)` | `BacktestConfig` | 无（分片存储到cache） | 多进程计算时序因子，分片存储节省内存 |
| `calc_cross_sections(conf)` | `BacktestConfig` | 无（存储到cache） | 加载面板数据，计算截面因子 |
| `select_coins(confs)` | `BacktestConfig` 或列表 | 无（存储到文件） | 遍历策略并行选币 |
| `select_coins_by_strategy(factor_df, stg_conf)` | DataFrame + 策略配置 | 选币结果 DataFrame | 单策略选币核心逻辑 |
| `calc_select_factor_rank(df, factor_column, ascending)` | DataFrame + 因子列名 | 添加 rank 列的 DataFrame | 计算因子排名 |
| `select_long_and_short_coin(strategy, long_df, short_df)` | 策略配置 + 多空数据 | 选币结果 DataFrame | 多空选币 + 权重分配 |
| `concat_select_results(conf)` | `BacktestConfig` | 无（存储到文件） | 合并多策略选币结果 |
| `process_select_results(conf)` | `BacktestConfig` | 选币结果 DataFrame | 现货→合约转换处理 |
| `agg_multi_strategy_ratio(conf, df_select)` | 配置 + 选币结果 | `(df_spot_ratio, df_swap_ratio)` | 多offset + 多策略权重聚合 |

### 3.3 关键函数详解

#### 3.3.1 `calc_factors(conf)` - 时序因子计算

```python
def calc_factors(conf: BacktestConfig):
    """
    时序因子计算（分片 + 多进程）

    算法流程:
    1. 读取 all_candle_df_list（所有币种K线）
    2. 按 factor_col_limit 分片计算因子
    3. 每片使用 ProcessPoolExecutor 并行计算
    4. 分片存储到 data/cache/factor_{name}.pkl

    内存优化:
    - 分片计算: factor_col_limit (默认64) 个因子一组
    - 分片存储: K线数据和因子数据分开存储
    - 及时 gc.collect() 释放内存
    """
    candle_df_list = pd.read_pickle(...)
    factor_col_count = len(conf.factor_col_name_list)
    shards = range(0, factor_col_count, factor_col_limit)

    for shard_index in shards:
        factor_col_name_list = conf.factor_col_name_list[shard_index:shard_index + factor_col_limit]

        # 多进程计算
        with ProcessPoolExecutor(max_workers=job_num) as executor:
            futures = [executor.submit(process_candle_df, ...) for ...]
            for future in tqdm(as_completed(futures), ...):
                idx, factor_df = future.result()
                all_factor_df_list[idx] = factor_df

        # 分片存储
        for factor_col_name in factor_col_name_list:
            cut_factors_df[factor_col_name].to_pickle(...)

        gc.collect()
```

**性能分析**：
- 时间复杂度: O(N_symbols × N_factors × N_bars / N_workers)
- 空间复杂度: O(factor_col_limit × N_bars × N_symbols)

#### 3.3.2 `select_coins_by_strategy(...)` - 单策略选币

```python
def select_coins_by_strategy(factor_df, stg_conf: StrategyConfig):
    """
    单策略选币核心逻辑

    执行步骤:
    4.1 数据预处理 (预留)
    4.2 计算目标选币因子 (calc_select_factor)
    4.3 前置过滤筛选 (filter_before_select)
    4.4 根据因子排名选币 (select_long_and_short_coin)
    4.5 后置过滤筛选 (filter_after_select)
    4.6 调整多空权重 (long_ratio / short_ratio)
    """
    # 4.2 计算因子
    result_df = stg_conf.calc_select_factor(factor_df)

    # 4.3 前置过滤
    long_df, short_df = stg_conf.filter_before_select(factor_df)
    short_df = short_df[short_df['symbol_swap'] != '']  # 空头必须有合约

    # 4.4 多空选币
    factor_df = select_long_and_short_coin(stg_conf, long_df, short_df)

    # 4.5 后置过滤
    factor_df = stg_conf.filter_after_select(factor_df)

    # 4.6 调整权重
    long_ratio = stg_conf.long_cap_weight / (stg_conf.long_cap_weight + stg_conf.short_cap_weight)
    factor_df.loc[factor_df['方向'] == 1, 'target_alloc_ratio'] *= long_ratio
    factor_df.loc[factor_df['方向'] == -1, 'target_alloc_ratio'] *= (1 - long_ratio)

    return factor_df[[*KLINE_COLS, '方向', 'target_alloc_ratio']]
```

#### 3.3.3 `agg_multi_strategy_ratio(...)` - 多策略权重聚合

```python
def agg_multi_strategy_ratio(conf: BacktestConfig, df_select: pd.DataFrame):
    """
    聚合多offset、多策略的选币权重

    两阶段聚合:
    1. 针对每个策略的多offset进行rolling聚合
    2. 针对多策略进行pivot_table聚合

    输出格式:
    - index: candle_begin_time (小时级)
    - columns: symbol (币种)
    - values: target_alloc_ratio (聚合后的权重)
    """
    # 阶段1: 每个策略的offset聚合
    for strategy in conf.strategy_list:
        _spot_select_long = agg_strategy_offsets(df_select_spot[...], strategy)
        df_spot_select_list.append(_spot_select_long)
        # ... 其他多空组合

    # 阶段2: 多策略聚合
    df_spot_ratio = to_ratio_pivot(df_spot_select, candle_begin_times, 'symbol')
    df_swap_ratio = to_ratio_pivot(df_swap_select, candle_begin_times, 'symbol')

    return df_spot_ratio, df_swap_ratio
```

### 3.4 异常处理机制

```python
# 1. 空选币结果处理
if result_df.empty:
    pd.DataFrame(columns=SELECT_RES_COLS).to_pickle(stg_select_result)
    return

# 2. 因子缺失处理
factor_df.dropna(subset=stg_conf.factor_columns, inplace=True)
factor_df.dropna(subset=['symbol'], how='any', inplace=True)

# 3. 合约数据合并异常
failed_merge_select_coin = spot_select_coin[spot_select_coin['close_2'].isna()][select_coin.columns].copy()
# 保留无法合并的数据，使用原现货逻辑

# 4. 策略选币文件不存在
if not os.path.exists(stg_select_result):
    continue  # 跳过不存在的文件

# 5. 下架币处理
if last_end_time >= end_time:
    continue  # 未下架，跳过
# 否则清除下架前的持仓权重
df_ratio.loc[second_last_end_time:, symbol] = 0
```

---

## 四、高性能模拟器 (core/simulator.py)

### 4.1 功能描述

**Numba JIT 加速的交易模拟器**，模拟完整的交易周期：开盘 → 调仓 → 收盘。核心特点：
- 使用 `@jitclass` 装饰器实现纯 LLVM 编译
- 精确模拟资金费、手续费、最小下单量
- 支持多币种并行持仓管理

### 4.2 核心类：`Simulator`

```python
@jitclass
class Simulator:
    """
    高性能交易模拟器

    属性:
    - equity: float           # 账户权益 (USDT)
    - fee_rate: float         # 手续费率
    - min_order_limit: float  # 最小下单金额
    - lot_sizes: nb.float64[:]    # 每手币数（最小下单量）
    - lots: nb.int64[:]           # 当前持仓手数
    - target_lots: nb.int64[:]    # 目标持仓手数
    - last_prices: nb.float64[:]  # 最新价格（用于结算）
    """
```

### 4.3 核心方法清单

| 方法名 | 输入参数 | 输出结果 | 算法逻辑 |
|-------|---------|---------|---------|
| `__init__(...)` | 初始资金、每手币数、费率等 | `Simulator` 对象 | 初始化账户状态和持仓数组 |
| `set_target_lots(target_lots)` | 目标持仓数组 | 无 | 设置下一周期的目标持仓 |
| `fill_last_prices(prices)` | 价格数组 | 无 | 更新最新价格（用于后续结算） |
| `settle_equity(prices)` | 价格数组 | 无 | 结算持仓盈亏到权益 |
| `on_open(open_prices, funding_rates, mark_prices)` | 开盘价、资金费率、标记价 | `(equity, funding_fee, pos_val)` | 模拟开盘时刻 |
| `on_execution(exec_prices)` | 执行价格 | `(equity, turnover, fee)` | 模拟调仓时刻 |
| `on_close(close_prices)` | 收盘价 | `(equity, pos_val)` | 模拟收盘时刻 |

### 4.4 关键方法详解

#### 4.4.1 `settle_equity(prices)` - 结算持仓盈亏

```python
def settle_equity(self, prices):
    """
    结算当前账户权益

    公式:
    equity_delta = Σ[(最新价格 - 前最新价) × 每手币数 × 持仓手数]

    实现细节:
    1. mask 过滤掉无持仓或价格为NaN的币种
    2. 向量化计算所有币种的盈亏
    3. 累加到账户权益
    """
    mask = np.logical_and(self.lots != 0, np.logical_not(np.isnan(prices)))
    equity_delta = np.sum(
        (prices[mask] - self.last_prices[mask]) * self.lot_sizes[mask] * self.lots[mask]
    )
    self.equity += equity_delta
```

#### 4.4.2 `on_execution(exec_prices)` - 调仓执行

```python
def on_execution(self, exec_prices):
    """
    模拟调仓时刻

    执行流程:
    1. 根据执行价结算当前权益
    2. 计算调仓手数: delta = target_lots - lots
    3. 计算成交额: turnover = |delta| × lot_sizes × prices
    4. 过滤小于最小下单量的调仓
    5. 扣除手续费
    6. 更新持仓

    返回:
    - equity: 调仓后权益
    - turnover: 总成交额
    - fee: 总手续费
    """
    self.settle_equity(exec_prices)

    delta = self.target_lots - self.lots
    mask = np.logical_and(delta != 0, np.logical_not(np.isnan(exec_prices)))

    # 计算成交额
    turnover = np.zeros(len(self.lot_sizes), dtype=np.float64)
    turnover[mask] = np.abs(delta[mask]) * self.lot_sizes[mask] * exec_prices[mask]

    # 过滤最小下单量
    mask = np.logical_and(mask, turnover >= self.min_order_limit)
    turnover_total = turnover[mask].sum()

    # 扣除手续费
    fee = turnover_total * self.fee_rate
    self.equity -= fee

    # 更新持仓
    self.lots[mask] = self.target_lots[mask]

    return self.equity, turnover_total, fee
```

### 4.5 切片赋值技巧说明

```python
# 关键语法: self.target_lots[:] = target_lots
#
# 这种写法是修改数组内容而非替换引用
#
# 好处:
# 1. 保持所有引用同步更新
# 2. Numba JIT 兼容性更好
# 3. 避免内存重新分配
#
# 示例:
# a = [1, 2, 3]
# b = a
# a[:] = [4, 5, 6]  # a 和 b 都变成 [4, 5, 6]
```

### 4.6 异常处理机制

```python
# 1. NaN 价格过滤
mask = np.logical_and(delta != 0, np.logical_not(np.isnan(exec_prices)))

# 2. 成交额校验
if np.isnan(turnover_total):
    raise RuntimeError('Turnover is nan')

# 3. 零值保护
# lot_sizes 和 prices 为 0 会导致除零错误
mask = np.logical_and(np.abs(target_equity) > 0.01,
                      np.logical_and(prices != 0, lot_sizes != 0))
```

---

## 五、资金曲线计算 (core/equity.py)

### 5.1 功能描述

**资金曲线计算与回测结果输出模块**，核心功能：
- 调用 Simulator 执行模拟交易
- 计算资金曲线和绩效指标
- 生成回测报告和图表

### 5.2 核心函数清单

| 函数名 | 输入参数 | 输出结果 | 算法逻辑 |
|-------|---------|---------|---------|
| `calc_equity(conf, pivot_dict_*, df_*_ratio, leverage)` | 配置+行情+比例 | `(account_df, rtn, year_return, month_return, quarter_return)` | 完整模拟交易流程 |
| `start_simulation(...)` | 所有模拟参数 | 多个结果数组 | Numba JIT 加速的模拟主循环 |
| `show_plot_performance(...)` | 配置+资金曲线 | 无（生成图表） | 绘制资金曲线图 |
| `read_lot_sizes(path, symbols)` | 路径+币种列表 | `pd.Series` | 读取最小下单量 |
| `align_pivot_dimensions(...)` | 数据字典+维度 | 对齐后的数据字典 | 对齐行情数据维度 |

### 5.3 关键函数详解

#### 5.3.1 `calc_equity(...)` - 资金曲线计算主函数

```python
def calc_equity(conf: BacktestConfig,
                pivot_dict_spot: dict,
                pivot_dict_swap: dict,
                df_spot_ratio: pd.DataFrame,
                df_swap_ratio: pd.DataFrame,
                leverage: float | pd.Series = None):
    """
    计算回测资金曲线

    执行流程:
    1. 数据预检和对齐
       - 校验现货/合约数据长度一致性
       - 对齐价格数据维度
       - 读取最小下单量

    2. 开始模拟交易
       - 调用 start_simulation() Numba 函数
       - 返回 equities, turnovers, fees 等数组

    3. 结果汇总
       - 构建 account_df
       - 计算净值、涨跌幅、爆仓标记
       - 调用 strategy_evaluate() 计算绩效指标
    """
```

#### 5.3.2 `start_simulation(...)` - Numba 模拟主循环

```python
@nb.jit(nopython=True, boundscheck=True)
def start_simulation(...):
    """
    Numba JIT 加速的模拟交易主循环

    每根K线循环 (n_bars 次):

    1. on_open: 开盘时刻
       - 根据开盘价结算权益
       - 计算资金费盈亏
       - 更新最新价格

    2. 检查爆仓
       - 计算保证金率 = equity / position_value
       - 若 < min_margin_rate 则终止回测

    3. on_execution: 调仓时刻
       - 根据调仓价结算权益
       - 执行调仓（扣除手续费）
       - 更新持仓

    4. on_close: 收盘时刻
       - 根据收盘价结算权益
       - 记录多空持仓价值

    5. 计算目标持仓
       - 若 require_rebalance[i] == 1
       - 调用 pos_calc.calc_lots() 计算目标手数
       - 设置下一周期目标

    返回:
    - equities: 每周期权益
    - turnovers: 每周期成交额
    - fees: 每周期手续费
    - funding_fees: 每周期资金费
    - margin_rates: 每周期保证金率
    - long_pos_values: 每周期多头持仓价值
    - short_pos_values: 每周期空头持仓价值
    """
```

### 5.4 异常处理机制

```python
# 1. 数据长度校验
if len(df_spot_ratio) != len(df_swap_ratio) or (df_swap_ratio.index != df_spot_ratio.index).any():
    raise RuntimeError(f'数据长度不一致，现货数据长度：{len(df_spot_ratio)}, 永续合约数据长度：{len(df_swap_ratio)}')

# 2. 爆仓检测
if margin_rate < min_margin_rate:
    margin_rates[i] = margin_rate
    break  # 终止回测

# 3. 爆仓标记
account_df.loc[account_df['marginRatio'] < conf.margin_rate, '是否爆仓'] = 1
account_df['是否爆仓'].fillna(method='ffill', inplace=True)

# 4. 分母为零保护
account_df['long_short_ratio'] = account_df['long_pos_value'] / (account_df['short_pos_value'] + 1e-8)
```

---

## 六、因子计算模块 (core/factor.py)

### 6.1 功能描述

**因子值计算统一接口**，支持两种因子写法：
- 新写法: `signal_multi_params()` - 批量计算多参数
- 老写法: `signal()` - 单参数计算

### 6.2 核心函数

```python
def calc_factor_vals(candle_df, factor_name, factor_param_list, shift=0) -> Dict[str, np.ndarray]:
    """
    计算因子值

    输入:
    - candle_df: 单币种K线 DataFrame（只读）
    - factor_name: 因子名称
    - factor_param_list: 参数列表 [n1, n2, ...]
    - shift: 偏移量（默认0）

    输出:
    - {f'{factor_name}_{param}': np.ndarray} 因子值字典

    执行流程:
    1. 通过 FactorHub 获取因子模块
    2. 如果有外部数据依赖，通过 merge_data 加载
    3. 优先使用 signal_multi_params() 批量计算
    4. 兜底使用 signal() 单参数计算
    5. 应用 shift 偏移
    """
```

### 6.3 两种因子写法对比

| 特性 | 新写法 `signal_multi_params` | 老写法 `signal` |
|-----|---------------------------|----------------|
| 函数签名 | `(df, param_list) -> dict` | `(df, n, factor_name) -> DataFrame` |
| 返回格式 | `{param: pd.Series}` | 添加列后的 DataFrame |
| 性能 | 高（批量计算） | 低（逐参数计算） |
| 推荐场景 | 新因子开发 | 兼容旧代码 |

### 6.4 异常处理机制

```python
# 外部数据加载
if hasattr(factor, 'extra_data_dict') and factor.extra_data_dict:
    for data_name in factor.extra_data_dict.keys():
        extra_data_dict = merge_data(candle_df, data_name, factor.extra_data_dict[data_name])
        for extra_data_name, extra_data_series in extra_data_dict.items():
            candle_df[extra_data_name] = extra_data_series.shift(shift).values
```

---

## 七、仓位调整模块 (core/rebalance.py)

### 7.1 功能描述

**Numba JIT 加速的仓位调整计算模块**，提供三种调仓模式：
- `RebAlways`: 每周期都调仓
- `RebByEquityRatio`: 调仓金额 > 总权益百分比才调仓
- `RebByPositionRatio`: 调仓金额 > 标的分配资金百分比才调仓

### 7.2 核心函数清单

| 函数名 | 输入参数 | 输出结果 | 算法逻辑 |
|-------|---------|---------|---------|
| `calc_target_lots_by_ratio(...)` | 权益、价格、比例、每手币数 | 目标手数数组 | `target = equity × ratio / price / lot_size` |
| `calc_delta_lots_amount(...)` | 目标/当前手数、价格 | `(delta_lots, delta_amount)` | 计算调仓手数和金额 |
| `filter_deltas(...)` | 手数、金额、最小限制 | 过滤后的 delta_lots | 过滤小于最小下单量的调仓 |

### 7.3 调仓模式类详解

#### 7.3.1 `RebAlways` - 默认模式

```python
@jitclass
class RebAlways:
    """
    默认 Rebalance 模式

    calc_lots():
    1. 检测是否为纯多模式（合约权重 < 1e-6）
    2. 纯多模式: equity *= 0.97（留缓冲）
    3. 直接计算目标手数
    """
    def calc_lots(self, equity, spot_prices, spot_lots, spot_ratios,
                  swap_prices, swap_lots, swap_ratios):
        is_spot_only = np.sum(np.abs(swap_ratios)) < 1e-6
        if is_spot_only:
            equity *= LONG_ONLY_EQUITY_RATIO  # 0.97

        spot_target_lots = calc_target_lots_by_ratio(...)
        swap_target_lots = calc_target_lots_by_ratio(...) if not is_spot_only else zeros

        return spot_target_lots, swap_target_lots
```

#### 7.3.2 `RebByEquityRatio` - 按总权益比例过滤

```python
@jitclass
class RebByEquityRatio:
    """
    预计调仓金额 > 总权益 × min_order_usdt_ratio 才调仓

    _calc():
    1. 计算目标手数
    2. 计算最小调仓金额 = equity × min_order_usdt_ratio
    3. 计算调仓手数和金额
    4. 过滤小额调仓（建仓/清仓除外）
    5. 返回过滤后的目标手数
    """
```

#### 7.3.3 `RebByPositionRatio` - 按持仓价值比例过滤

```python
@jitclass
class RebByPositionRatio:
    """
    预计调仓金额 > 当前持仓价值 × min_order_usdt_ratio 才调仓

    与 RebByEquityRatio 的区别:
    - 最小调仓金额 = 当前持仓价值 × min_order_usdt_ratio
    - 而非总权益
    """
```

### 7.4 关键算法：目标手数计算

```python
@nb.njit
def calc_target_lots_by_ratio(equity, prices, ratios, lot_sizes):
    """
    根据目标比例计算目标持仓手数

    公式:
    target_lots = (equity × ratios) / prices / lot_sizes

    极值处理:
    - 检测 int64 溢出（极大/极小值）
    - 发现极值强制设为 0
    - 打印警告信息
    """
    target_lots = np.zeros(len(lot_sizes), dtype=np.int64)
    target_equity = equity * ratios

    # 过滤无效数据
    mask = np.logical_and(
        np.abs(target_equity) > 0.01,
        np.logical_and(prices != 0, lot_sizes != 0)
    )

    # 计算目标手数
    target_lots[mask] = (target_equity[mask] / prices[mask] / lot_sizes[mask]).astype(np.int64)

    # 极值检测和修正
    int64_max = np.iinfo(np.int64).max
    int64_min = np.iinfo(np.int64).min
    extreme_value_mask = (target_lots == int64_max) | (target_lots == int64_min)
    if np.any(extreme_value_mask):
        print(f"警告：发现 {len(extreme_indices)} 个int64极值，已强制设置为0")
        target_lots[extreme_value_mask] = 0

    return target_lots
```

### 7.5 异常处理机制

```python
# 1. 除零保护
mask = np.logical_and(prices != 0, lot_sizes != 0)

# 2. 极值检测
int64_max = np.iinfo(np.int64).max
extreme_value_mask = (target_lots == int64_max) | (target_lots == int64_min)
target_lots[extreme_value_mask] = 0

# 3. 纯多模式检测
if np.sum(np.abs(swap_ratios)) < 1e-6:
    is_spot_only = True
    equity *= 0.97  # 留缓冲
```

---

## 八、策略评价模块 (core/evaluate.py)

### 8.1 功能描述

**策略绩效评价模块**，计算标准化的量化回测指标。

### 8.2 核心函数

```python
def strategy_evaluate(equity, net_col='多空资金曲线', pct_col='本周期多空涨跌幅'):
    """
    回测评价函数

    输入:
    - equity: 资金曲线 DataFrame
    - net_col: 净值列名
    - pct_col: 周期涨跌幅列名

    输出:
    - results.T: 评价指标 DataFrame
    - year_return: 年度收益
    - month_return: 月度收益
    - quarter_return: 季度收益
    """
```

### 8.3 评价指标清单

| 指标名称 | 计算公式 | 说明 |
|---------|---------|------|
| 累积净值 | `equity[net_col].iloc[-1]` | 最终净值 |
| 年化收益 | `(净值)^(365/天数) - 1` | 复利年化 |
| 最大回撤 | `min(净值/历史最高 - 1)` | 最大跌幅 |
| 最大回撤开始时间 | 回撤前最高点时间 | - |
| 最大回撤结束时间 | 最低点时间 | - |
| 年化收益/回撤比 | `年化收益 / |最大回撤|` | 卡尔玛比率 |
| 盈利周期数 | `count(pct > 0)` | - |
| 亏损周期数 | `count(pct <= 0)` | - |
| 胜率 | `盈利周期数 / 总周期数` | - |
| 每周期平均收益 | `mean(pct)` | - |
| 盈亏收益比 | `mean(盈利周期) / |mean(亏损周期)|` | - |
| 单周期最大盈利 | `max(pct)` | - |
| 单周期最大亏损 | `min(pct)` | - |
| 最大连续盈利周期数 | `max(连续盈利长度)` | - |
| 最大连续亏损周期数 | `max(连续亏损长度)` | - |
| 收益率标准差 | `std(pct)` | 波动率 |

### 8.4 异常处理机制

```python
# 爆仓情况下盈亏比设为0
if 1 in equity['是否爆仓'].to_list():
    results.loc[0, '盈亏收益比'] = 0
```

---

## 九、配置模型 (core/model/)

### 9.1 BacktestConfig - 回测配置类

```python
class BacktestConfig:
    """
    单账户回测配置

    核心属性:
    - name: 策略名称
    - start_date, end_date: 回测时间范围
    - leverage: 杠杆倍数
    - strategy_list: 策略配置列表
    - factor_params_dict: 因子参数字典
    - timing: 择时信号配置

    核心方法:
    - load_strategy_config(): 加载策略配置
    - get_result_folder(): 获取结果目录
    - save(): 保存配置到文件
    """
```

### 9.2 BacktestConfigFactory - 配置工厂类

```python
class BacktestConfigFactory:
    """
    多策略配置生成工厂

    核心方法:
    - generate_configs_by_strategies(): 根据策略列表生成配置
    - generate_all_factor_config(): 生成全因子配置
    - get_name_params_sheet(): 生成参数总表
    """
```

### 9.3 MultiEquityBacktestConfig - 仓位管理配置类

```python
class MultiEquityBacktestConfig:
    """
    仓位管理回测配置

    核心属性:
    - strategy: PosStrategyConfig (仓位管理策略)
    - factory: BacktestConfigFactory (配置工厂)
    - equity_dfs: 子策略资金曲线列表
    - ratio_dfs: 子策略选币比例列表

    核心方法:
    - backtest_strategies(): 运行子策略回测
    - process_equities(): 处理资金曲线
    - calc_ratios(): 计算仓位比例
    - agg_pos_ratio(): 聚合选币结果
    - apply_position_limits(): 应用仓位限制
    """
```

### 9.4 StrategyConfig - 子策略配置类

```python
@dataclass
class StrategyConfig:
    """
    子策略配置

    核心属性:
    - name: 策略名称
    - hold_period: 持仓周期 ('1H', '6H', '1D', ...)
    - market: 选币市场 ('spot_spot', 'swap_swap', 'mix_spot', ...)
    - long_select_coin_num: 多头选币数量
    - short_select_coin_num: 空头选币数量
    - long_factor_list: 多头因子列表
    - short_factor_list: 空头因子列表
    - long_filter_list: 多头过滤因子列表
    - short_filter_list: 空头过滤因子列表

    核心方法:
    - calc_select_factor(): 计算选币因子
    - filter_before_select(): 前置过滤
    - filter_after_select(): 后置过滤
    - select_by_coin_num(): 按数量选币
    """
```

### 9.5 PosStrategyConfig - 仓位策略配置类

```python
@dataclass
class PosStrategyConfig:
    """
    仓位管理策略配置

    核心属性:
    - name: 策略名称 ('FixedRatioStrategy', 'RotationStrategy', ...)
    - hold_period: 持仓周期
    - params: 策略参数
    - rebalance_cap_step: 单次调仓最大比例
    - symbol_ratio_limit: 单币种权重限制

    核心方法:
    - load(): 加载策略实现
    - calc_ratios(): 计算子策略权重
    """
```

---

## 十、工具类 (core/utils/)

### 10.1 FactorHub - 因子动态加载器

```python
class FactorHub:
    """
    因子动态加载器

    特点:
    - 静态缓存: _factor_cache 避免重复加载
    - 双目录搜索: 先 factors/，后 sections/
    - 自动标记: is_cross = True 表示截面因子

    get_by_name(factor_name) -> DummyFactor:
        1. 检查缓存
        2. 尝试从 factors/ 导入
        3. 尝试从 sections/ 导入
        4. 创建因子实例并缓存
    """
```

### 10.2 DummyFactor - 因子接口抽象

```python
class DummyFactor:
    """
    因子接口抽象（仅用于代码提示）

    属性:
    - extra_data_dict: dict  # 外部数据依赖
    - is_cross: bool  # 是否截面因子

    方法:
    - signal(df, n, factor_name) -> DataFrame
    - signal_multi_params(df, param_list) -> dict
    - get_factor_list(n) -> list  # 截面因子依赖
    """
```

---

## 十一、异常处理机制总结

### 11.1 数据校验类

| 位置 | 异常类型 | 处理方式 |
|-----|---------|---------|
| `calc_equity()` | 数据长度不一致 | `raise RuntimeError` |
| `select_coins_by_strategy()` | 空选币结果 | 保存空 DataFrame，返回 |
| `process_candle_df()` | 因子计算 NaN | 保留（后续过滤） |
| `simu_timing()` | 择时信号未实现 | `raise NotImplementedError` |

### 11.2 计算异常类

| 位置 | 异常类型 | 处理方式 |
|-----|---------|---------|
| `Simulator.on_execution()` | 成交额为 NaN | `raise RuntimeError` |
| `calc_target_lots_by_ratio()` | int64 溢出 | 强制设为 0，打印警告 |
| `start_simulation()` | 爆仓 | 终止循环，记录 margin_rate |
| `strategy_evaluate()` | 爆仓导致盈亏比异常 | 设为 0 |

### 11.3 文件/数据类

| 位置 | 异常类型 | 处理方式 |
|-----|---------|---------|
| `concat_select_results()` | 选币文件不存在 | `continue` 跳过 |
| `process_select_results()` | 选币文件不存在 | 返回空 DataFrame |
| `FactorHub.get_by_name()` | 因子模块不存在 | `raise ValueError` |
| `select_coins()` | 多进程异常 | `logger.exception` + `exit(1)` |

### 11.4 防御性编程实践

```python
# 1. 分母加小常数
account_df['long_short_ratio'] = long_val / (short_val + 1e-8)

# 2. NaN 填充
account_df['是否爆仓'].fillna(method='ffill', inplace=True)
account_df['是否爆仓'].fillna(value=0, inplace=True)

# 3. 边界条件检查
if result_df.empty:
    pd.DataFrame(columns=SELECT_RES_COLS).to_pickle(path)
    return

# 4. 类型转换保护
select_result_df['方向'] = result_df['方向'].astype('int8').values

# 5. 权重精度控制
pos_ratio_precision = 9  # 仓位比例精度
df_ratio = df_ratio.round(self.pos_ratio_precision)
```

---

## 十二、优化建议

### 12.1 性能优化建议

#### A. 因子计算优化

| 优化点 | 当前实现 | 优化建议 | 预期提升 |
|-------|---------|---------|---------|
| 因子分片 | `factor_col_limit=64` | 根据内存动态调整 | 内存效率 +20% |
| 多进程 | `ProcessPoolExecutor` | 考虑使用 `joblib` 或 `ray` | 并行效率 +30% |
| 因子缓存 | 文件缓存 `.pkl` | 使用内存映射 `np.memmap` | I/O 效率 +50% |
| 截面因子 | 逐参数计算 | 批量计算 + 向量化 | 计算效率 +40% |

```python
# 优化示例：内存映射因子缓存
import numpy as np

def save_factor_memmap(factor_values, path):
    mmap = np.memmap(path, dtype='float64', mode='w+', shape=factor_values.shape)
    mmap[:] = factor_values
    mmap.flush()

def load_factor_memmap(path, shape):
    return np.memmap(path, dtype='float64', mode='r', shape=shape)
```

#### B. 选币优化

| 优化点 | 当前实现 | 优化建议 | 预期提升 |
|-------|---------|---------|---------|
| 排名计算 | `df.groupby().rank()` | 使用 `numba` 排序 | 计算效率 +60% |
| 数据过滤 | 多次 `df[condition]` | 一次性布尔索引 | 内存效率 +30% |
| 权重聚合 | `pivot_table` + `rolling` | 向量化聚合 | 计算效率 +40% |

```python
# 优化示例：Numba 加速排名计算
@nb.njit
def fast_rank(values, ascending=True):
    n = len(values)
    sorted_indices = np.argsort(values)
    if not ascending:
        sorted_indices = sorted_indices[::-1]
    ranks = np.empty(n, dtype=np.int64)
    for i, idx in enumerate(sorted_indices):
        ranks[idx] = i + 1
    return ranks
```

#### C. 模拟器优化

| 优化点 | 当前实现 | 优化建议 | 预期提升 |
|-------|---------|---------|---------|
| 主循环 | Python `for` + Numba 函数 | 整个循环 Numba 化 | 已实现 ✓ |
| 数据结构 | 多个独立数组 | 结构化数组 | 缓存效率 +20% |
| 分支预测 | 多个 `if` 判断 | 位运算合并 | 执行效率 +10% |

### 12.2 量化逻辑优化建议

#### A. 未来函数检测

**问题描述**：当前框架未内置未来函数检测机制，可能导致回测结果过于乐观。

**优化建议**：

```python
def detect_lookahead_bias(df, factor_col, target_col='next_close'):
    """
    检测未来函数

    原理:
    - 计算因子与未来收益的相关性
    - 若相关性显著高于随机基准，可能存在未来函数
    """
    # 计算因子与未来收益的相关性
    corr = df[factor_col].corr(df[target_col])

    # 随机打乱因子计算基准相关性
    shuffled_corrs = []
    for _ in range(100):
        shuffled = df[factor_col].sample(frac=1).values
        shuffled_corrs.append(np.corrcoef(shuffled, df[target_col])[0, 1])

    baseline_std = np.std(shuffled_corrs)
    z_score = (corr - np.mean(shuffled_corrs)) / baseline_std

    if z_score > 3:
        logger.warning(f'因子 {factor_col} 可能存在未来函数！z_score={z_score:.2f}')

    return z_score
```

#### B. 滑点模拟优化

**问题描述**：当前使用 `avg_price_1m` 作为执行价格，可能低估实际滑点。

**优化建议**：

```python
def calc_slippage(order_size, volume, avg_price, impact_factor=0.1):
    """
    计算冲击成本

    公式:
    slippage = impact_factor × sqrt(order_size / volume) × avg_price

    参数:
    - impact_factor: 冲击系数 (经验值 0.05-0.2)
    """
    if volume == 0:
        return avg_price * 0.01  # 默认1%滑点

    market_impact = impact_factor * np.sqrt(order_size / volume)
    return avg_price * market_impact

def apply_slippage(exec_price, order_size, volume, direction):
    """
    应用滑点到执行价格

    - 买入: 价格上浮
    - 卖出: 价格下浮
    """
    slippage = calc_slippage(order_size, volume, exec_price)
    return exec_price + direction * slippage
```

#### C. 风险控制增强

**优化建议**：

```python
# 1. 最大回撤止损
def check_max_drawdown_stop(equity_curve, threshold=-0.2):
    """
    检测是否触发最大回撤止损
    """
    peak = equity_curve.expanding().max()
    drawdown = equity_curve / peak - 1
    return drawdown.iloc[-1] < threshold

# 2. 波动率调整仓位
def calc_vol_adjusted_weight(returns, target_vol=0.15, lookback=30):
    """
    根据历史波动率调整仓位
    """
    realized_vol = returns.rolling(lookback).std() * np.sqrt(252 * 24)
    vol_scalar = target_vol / realized_vol.clip(lower=0.01)
    return vol_scalar.clip(upper=2.0)  # 最大2倍

# 3. 相关性监控
def monitor_correlation(equity_curves_dict, threshold=0.8):
    """
    监控子策略相关性
    """
    df = pd.DataFrame(equity_curves_dict)
    corr_matrix = df.pct_change().corr()
    high_corr_pairs = []
    for i in range(len(corr_matrix)):
        for j in range(i + 1, len(corr_matrix)):
            if corr_matrix.iloc[i, j] > threshold:
                high_corr_pairs.append((
                    corr_matrix.index[i],
                    corr_matrix.columns[j],
                    corr_matrix.iloc[i, j]
                ))
    return high_corr_pairs
```

#### D. 过拟合检测

**优化建议**：

```python
def walk_forward_validation(conf, n_splits=5):
    """
    走步向前验证

    将回测期分为 n_splits 段:
    - 训练集: 前 (i-1) 段
    - 测试集: 第 i 段
    - 比较训练集和测试集的绩效差异
    """
    results = []
    date_range = pd.date_range(conf.start_date, conf.end_date, periods=n_splits + 1)

    for i in range(1, n_splits + 1):
        # 训练集回测
        train_conf = copy.deepcopy(conf)
        train_conf.end_date = date_range[i]
        train_metrics = run_backtest(train_conf)

        # 测试集回测
        test_conf = copy.deepcopy(conf)
        test_conf.start_date = date_range[i]
        test_conf.end_date = date_range[i + 1] if i < n_splits else conf.end_date
        test_metrics = run_backtest(test_conf)

        results.append({
            'train_sharpe': train_metrics['sharpe'],
            'test_sharpe': test_metrics['sharpe'],
            'degradation': (train_metrics['sharpe'] - test_metrics['sharpe']) / train_metrics['sharpe']
        })

    avg_degradation = np.mean([r['degradation'] for r in results])
    if avg_degradation > 0.5:
        logger.warning(f'可能存在过拟合！平均绩效衰减: {avg_degradation:.1%}')

    return results
```

### 12.3 代码质量优化建议

#### A. 类型标注增强

```python
from typing import Dict, List, Tuple, Optional, Union
import pandas as pd
import numpy as np

def calc_factors(
    conf: BacktestConfig
) -> None:
    """计算时序因子（结果存入缓存）"""
    ...

def select_coins_by_strategy(
    factor_df: pd.DataFrame,
    stg_conf: StrategyConfig
) -> pd.DataFrame:
    """单策略选币"""
    ...
```

#### B. 单元测试框架

```python
import pytest

class TestSimulator:
    def test_settle_equity(self):
        """测试权益结算"""
        sim = Simulator(10000, np.array([0.001]), 0.0005, np.zeros(1), 5)
        sim.lots[:] = np.array([100])
        sim.last_prices[:] = np.array([100.0])

        sim.settle_equity(np.array([110.0]))

        # 预期盈利: (110 - 100) * 0.001 * 100 = 1.0
        assert sim.equity == 10001.0

    def test_on_execution_fee(self):
        """测试手续费扣除"""
        sim = Simulator(10000, np.array([0.001]), 0.0005, np.zeros(1), 5)
        sim.target_lots[:] = np.array([1000])
        sim.last_prices[:] = np.array([100.0])

        equity, turnover, fee = sim.on_execution(np.array([100.0]))

        # 成交额: 1000 * 0.001 * 100 = 100
        # 手续费: 100 * 0.0005 = 0.05
        assert turnover == 100.0
        assert fee == 0.05
```

#### C. 日志分级规范

```python
# 建议的日志分级:
# - DEBUG: 详细调试信息（内存占用、耗时）
# - INFO: 关键步骤开始/完成
# - WARNING: 异常但可恢复的情况
# - ERROR: 错误但不致命
# - CRITICAL: 致命错误，需要退出

logger.debug(f'💾 因子分片存储，大小: {df.memory_usage().sum() / 1e6:.2f} MB')
logger.info(f'开始计算 {len(strategies)} 个策略的选币...')
logger.warning(f'策略 {name} 的选币结果为空，跳过')
logger.error(f'因子 {factor_name} 计算失败: {e}')
logger.critical(f'数据长度不一致，无法继续回测')
```

---

## 附录：模块依赖关系图

```
                              ┌─────────────────────────────────┐
                              │         backtest.py (入口)       │
                              └────────────────┬────────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
    ┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
    │ core/backtest.py      │  │ core/model/           │  │ config.py             │
    │ (回测流程编排)         │  │ backtest_config.py    │  │ (全局配置)            │
    └───────────┬───────────┘  └───────────────────────┘  └───────────────────────┘
                │
    ┌───────────┼───────────┬───────────────────────────┐
    │           │           │                           │
    ▼           ▼           ▼                           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────────┐
│ select_   │ │ factor.py │ │ equity.py │ │ core/model/       │
│ coin.py   │ │           │ │           │ │ strategy_config.py│
│           │ │           │ │           │ │                   │
└─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └───────────────────┘
      │             │             │
      │             │             │
      ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│                    core/utils/                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ factor_hub  │  │ strategy_hub│  │ signal_hub  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
      │  factors/   │ │ positions/  │ │  signals/   │
      │  sections/  │ │             │ │             │
      └─────────────┘ └─────────────┘ └─────────────┘

Numba 加速模块:
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ simulator.py│  │ rebalance.py│  │ equity.py   │          │
│  │ (Simulator) │  │ (RebAlways) │  │ (start_simu)│          │
│  │ @jitclass   │  │ @jitclass   │  │ @nb.jit     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

*文档生成于 2026-01-15 | Claude AI 资深量化分析师 & 系统架构师*
