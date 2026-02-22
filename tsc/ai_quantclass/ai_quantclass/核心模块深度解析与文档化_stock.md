# 核心模块深度解析与文档化（v1.7.3）

> 最后更新：2026-01-15

## 0. 文档范围与约定
- **范围**：`core/` 目录全部核心模块 + `回测主程序.py`
- **术语约定**：
  - `conf` = `BacktestConfig` 回测配置对象
  - `runtime` = 运行缓存目录（`运行缓存/`）
  - `result` = 回测结果目录（`回测结果/`）
  - `factor_df` = 因子面板数据（日期×股票×因子值）
- **说明**：本文以"模块"为单位描述功能、核心 API、异常处理与优化建议，表格字段为"输入/输出/逻辑"。

---

## 1. 回测主程序.py

**文件位置**：`select-stock-pro_v1.7.3/回测主程序.py`

**功能描述**：回测系统入口脚本，完成版本提示、加载配置并启动全流程回测。该脚本是整个框架的启动点，负责初始化环境、加载用户配置并调度回测流程。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| 主流程（`__main__`） | 无（依赖 `config.py`） | 回测结果文件、日志输出 | 1. 设置警告过滤与 pandas 显示选项<br>2. 调用 `version_prompt()` 显示版本信息<br>3. 调用 `load_config()` 加载配置<br>4. 打印配置描述 `conf.desc()`<br>5. 调用 `run_backtest(conf)` 启动回测 |

**代码流程图**：
```
回测主程序.py
    │
    ├── warnings.filterwarnings('ignore')  # 忽略警告
    ├── pd.set_option(...)                  # 设置显示选项
    │
    └── if __name__ == '__main__':
            ├── version_prompt()            # 版本提示
            ├── conf = load_config()        # 加载配置
            ├── print(conf.desc())          # 打印配置
            └── run_backtest(conf)          # 执行回测
```

---

## 2. core/backtest.py
**功能描述**：回测流程编排器。负责按顺序调度数据准备、因子计算、选股与交易模拟。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `run_backtest(conf, require_simulate=True)` | `BacktestConfig` | 写入缓存与回测结果 | 删除旧缓存 → `prepare_data` → `calculate_factors` → `calc_cross_sections` → `select_stocks` → `concat_select_results` → `simulate_performance` |
| `run_backtest_multi(factory, boost=True)` | `BacktestConfigFactory` | 多组回测报告 | 生成合并因子配置 → 统一算因子 → 并行选股 → 逐策略模拟并汇总 |

---

## 3. core/data_center.py
**功能描述**：数据准备与缓存中心。负责股票行情预处理、复权、停牌补齐、分钟数据合并与市场透视表构建。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `prepare_data(conf, boost=True)` | `BacktestConfig` | `股票预处理数据.pkl`、`全部股票行情pivot.pkl` | 并行逐股票清洗 → 复权 & 涨跌停 → 合并指数 → 可选分钟数据 → 写入缓存 |
| `prepare_data_by_stock(conf, stock_file_path, index_data)` | 单股 CSV 路径 | 预处理后的单股 `DataFrame` | 计算涨跌幅/换手率 → 复权 → 涨跌停 → 与指数对齐 → 构造“下日_”状态字段 |
| `load_min_data(conf, df)` | 单股日线数据 | 合并分钟字段 | 根据 `min_data_level` 选择 5m/15m，缺失用收盘价填充 |
| `make_market_pivot(market_dict, rebalance_time_list)` | 全股票字典 | 透视表字典 | 将开盘/收盘/前收盘/分钟价 pivot 为“日期×代码”矩阵 |
| `merge_extra_data(df, data_name, save_cols)` | 日线数据 + 数据名 | 扩展字段的 `DataFrame` | 基于 `data_bridge.presets` 或 `外部数据/` 扩展数据 |
| `check_extra_data(data_name)` | 数据名 | `(bool, msg)` | 校验外部数据是否存在、是否可加载 |
| `clean_folder(path)` | 路径 | 无 | 清理并重建缓存目录 |

---

## 4. core/data_bridge.py
**功能描述**：外部数据接入层。提供预置数据源读取函数与映射表。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `auto_load_data(file_path, candle_df, save_cols)` | 路径 + 日线 + 列名 | 合并后的 `DataFrame` | 读取同名 CSV 并按交易日合并 |
| `load_hk_stock(file_path, candle_df, save_cols)` | 港股路径 | 合并后的 `DataFrame` | 合并港股行情 + 汇率数据，构造港股复权价格 |
| `load_dividend_delivery(file_path, candle_df, save_cols)` | 分红路径 | 合并后的 `DataFrame` | 计算分红率与统计特征，并按日期补齐 |
| `load_15min_data/ load_5min_data` | 分钟行情路径 | 合并后的 `DataFrame` | 读取分钟收盘价并与日线合并 |
| `load_stock_notices_title` | 公告路径 | 合并后的 `DataFrame` | 合并公告标题与数量统计 |
| `presets` | 无 | 数据源映射字典 | 预置数据源名称 → (读取函数, 路径) |

---

## 5. core/select_stock.py
**功能描述**：因子计算、选股与权重生成的核心模块，支持时序/截面因子、择时与分批进场。

### 5.1 因子计算相关
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `cal_strategy_factors(conf, stock_code, candle_df, fin_data, factor_col_name_list)` | 单股 K 线 + 财务数据 | 含因子的 `DataFrame` | 动态加载因子文件 → 逐参数计算 → 校验行数 → 裁切回测区间 |
| `process_by_stock(conf, candle_df, factor_col_name_list, idx)` | 单股 K 线 | `(idx, factor_df)` | 合并财务/外部数据 → 调用 `cal_strategy_factors` |
| `calculate_factors(conf, boost=True)` | `BacktestConfig` | `all_factors_kline.pkl` + `factor_*.pkl` | 分片并行计算因子 → 分列落盘 → 内存回收 |
| `load_all_factors(conf)` | `BacktestConfig` | 全因子面板 | 读取基础行情 + 并行读取各因子列 |
| `calc_cross_sections(conf)` | `BacktestConfig` | `factor_*.pkl` | 对截面因子执行 `add_factor`，并落盘 |

### 5.2 选股与权重相关
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `select_stocks(confs, boost=True)` | `BacktestConfig` 或列表 | 选股结果文件 | 单策略或多策略并行选股 |
| `select_stock_by_conf(conf, boost=True, silent=False)` | `BacktestConfig` | `DataFrame` | 加载因子面板 → 按策略迭代选股 |
| `select_stocks_by_strategy(strategy, factor_df_path, result_folder, period_offset)` | 单策略配置 | 单策略选股结果 | 前置过滤 → 复合因子 → 择时/临时调仓 → 排名筛选 → 后置过滤 → 分批进场 |
| `select_by_factor(period_df, select_num, factor_name)` | 因子面板 | 选股 `DataFrame` | 按排名筛选 Top-N 或百分比并分配权重 |
| `calc_select_factor_rank(df, factor_column, ascending)` | 因子面板 | 加入排名列的 `DataFrame` | 按交易日排序并计算排名 |
| `concat_select_results(conf)` | `BacktestConfig` | 综合选股 `DataFrame` | 合并各策略选股结果并保存 CSV/Pickle |
| `agg_ratios_by_period(conf, select_results)` | 选股结果 | `period_ratio_df` | 按策略/周期/换仓时间聚合权重 |

### 5.3 分批进场与临时调仓
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `calc_scalein_pos(strategy, result_df, override_pos_dict, select_dates_dict)` | 选股结果 + 临时调仓信号 | 带“分批进场仓位”的结果 | 各 offset 独立构建开仓信号 → 合成目标仓位 |
| `apply_override_pos(result_df, override_pos, use_cum=True)` | 原始选股结果 | 增加临时调仓信号 | 插入临时调仓日并重算信号 |
| `fill_scalein_targets(strategy, offset_signal_df)` | offset 信号矩阵 | 分批进场仓位序列 | 根据目标总仓位与信号状态生成仓位路径 |

---

## 6. core/equity.py
**功能描述**：交易模拟与资金曲线生成，引入 `numba` 加速，支持 T+0/T+1 与分钟级换仓。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `parse_rebalance_time(reb_time)` | 换仓时点字符串 | `(sell_idx, buy_idx)` | 将 `open/close/0930` 等映射到价格索引 |
| `get_stock_market(pivot_dict_stock, trading_dates, symbols, symbol_types)` | 行情透视表 | `StockMarketData` | 组装 JIT 友好的行情结构 |
| `get_adjust_ratios(df_stock_ratio, start_date, end_date, symbols, reb_time)` | 持仓权重表 | `AdjustRatios` | 权重对齐交易日并转换为数组 |
| `calc_equity(conf, pivot_dict_stock, period_ratio_df, symbols, leverage)` | 配置 + 权重 + 行情 | 资金曲线与统计 | 组装 `SimuParams` + `AdjustRatios` → `start_simulation` |
| `start_simulation(market, simu_params, adj_ratios, leverages, pos_calc)` | 市场数据 + 策略权重 | `cashes/pos_values/fees` | `numba` 循环模拟逐日交易、费用与仓位更新 |
| `simu_equity_timing(conf, pivot_dict_stock, period_ratio_df, symbols)` | 资金曲线 + 动态杠杆 | 再择时资金曲线 | 依据 `EquityTiming` 动态调整仓位 |
| `simulate_performance(conf, show_plot=True, extra_equities=None)` | `BacktestConfig` | 资金曲线与评价 | 聚合权重 → 调用 `calc_equity` → 保存结果 + 可选绘图 |

---

## 7. core/simulator.py
**功能描述**：低层级交易模拟器，处理调仓、费用与现金/仓位更新（`numba` JIT）。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `Simulator` | 初始资金、费率、仓位 | 账户状态对象 | 管理现金、仓位价值、最新价格 |
| `adjust_positions(exec_prices, target_pos)` | 调仓价 + 目标持仓 | 税费 | 按目标持仓更新仓位，计算佣金/印花税 |
| `sell_all(exec_prices)` | 卖出价 | 税费 | 将仓位清零并计算费用 |

---

## 8. core/rebalance.py
**功能描述**：换仓目标仓位计算（以资金比例转为手数），支持市场规则与限制。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `calc_target_lots_by_ratio(equity, prices, ratios, types)` | 资金/价格/权重 | 目标手数 | 资金分配 → 按交易所规则对手数取整 |
| `RebAlways.calc_lots(...)` | 资金/价格/权重 | 目标手数 | 使用 `LONG_ONLY_EQUITY_RATIO` 保留现金缓冲 |
| `RebAlwaysSimple.calc_lots(...)` | 资金/价格/权重 | 目标手数 | 不做手数约束的简化版本 |

---

## 9. core/evaluate.py
**功能描述**：回测绩效指标计算（收益、回撤、胜率、分年/月/季度收益）。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `strategy_evaluate(equity, net_col, pct_col)` | 资金曲线 | 指标表 + 分期收益 | 计算年化/回撤/胜率/盈亏比/分年收益 |

---

## 10. core/figure.py
**功能描述**：回测图表与报告输出（Plotly + HTML）。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `draw_equity_curve_plotly(...)` | 资金曲线 | Plotly Figure | 主图净值 + 回撤 + 叠加仓位子图 |
| `draw_table(table_df, ...)` | 表格数据 | Plotly Table | 将统计表格渲染为图表 |
| `save_performance(conf, **kwargs)` | 多个 `DataFrame` | CSV 文件 | 统一写入回测结果文件夹 |
| `show_performance_plot(conf, select_results, equity_df, rtn, year_return, ...)` | 数据 + 指标 | `资金曲线.html` | 叠加指数曲线、回撤、统计图表 |

---

## 11. core/market_essentials.py
**功能描述**：行情预处理工具集，包括复权、涨跌停、指数导入、交易日历校验。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `cal_fuquan_price(df, fuquan_type, method)` | 日线行情 | 复权字段 | 计算复权因子与复权价 |
| `import_index_data(path, date_range, max_param)` | 指数 CSV | 指数涨跌幅 | 计算指数涨跌幅并按区间截取 |
| `merge_with_index_data(df, index_data, fill_0_list)` | 个股 + 指数 | 对齐后的行情 | 交易日补齐、停牌填充、退市剔除 |
| `cal_zdt_price(df)` | 日线行情 | 涨跌停字段 | 分板块规则计算涨跌停与一字涨跌停 |
| `download_period_offset(path)` | 文件路径 | 交易日历 | 从远端下载交易日历 |
| `check_period_offset(path)` | 文件路径 | 校验结果 | 校验哈希并必要时更新 |

---

## 12. core/fin_essentials.py
**功能描述**：财务数据处理与因子衍生（单季/TTM/同比/环比）。

**核心函数/类清单**
| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `cal_fin_data(data, flow_fin_list, cross_fin_list, discard)` | 原始财报 | 衍生财务字段 | 计算单季/TTM/同比/环比 |
| `get_finance_data(conf, stock_code, stock_df)` | 股票代码 | 原始财报 | 读取财报 CSV 并补齐缺失列 |
| `merge_with_finance_data_new(conf, stock_df, fin_data_ins)` | 行情 + 财务对象 | 合并后的行情 | 按字段类型生成财务序列并对齐交易日 |
| `generate_fin_pivot(origin_df, candle_df, cols)` | 原始财报 + 行情 | `pivot_dict` | 生成季度/发布日透视表，用于 FinanceDataFrame |
| `prepare_fin_cols(cols)` | 字段列表 | `(flow, cross)` | 将财务指标区分为流量型/截面型 |

---

## 13. core/model（核心配置与数据结构）

### 13.1 backtest_config.py
**功能描述**：回测系统的“单一事实源”，集中管理路径、策略、因子、缓存与结果。

| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `BacktestConfig.__init__` | 配置字典 | 配置对象 | 初始化路径/费率/策略/缓存/交易日历 |
| `load_strategies(strategy_list, equity_timing)` | 策略配置 | `strategy_list` | 解析策略、聚合因子、登记分钟换仓 |
| `load_period_offset()` | 无 | 交易日历 | 读取 `period_offset.csv` 并校验 |
| `load_index_data()` | 无 | 指数行情 | 读取指数并按回测区间裁切 |
| `get_runtime_folder()/get_result_folder()` | 无 | 路径 | 统一回测缓存与结果路径 |
| `save()` | 无 | `config.json`/`config.pkl` | 保存配置快照 |
| `BacktestConfigFactory` | 参数遍历 | 多组配置 | 批量生成回测配置并统一算因子 |
| `load_config()` | 环境变量 | `BacktestConfig` | 从 `config.py` 创建配置对象 |

### 13.2 strategy_config.py
**功能描述**：策略配置与选股逻辑封装，包括过滤、复合因子、择时与临时调仓。

| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `StrategyConfig.init(...)` | 策略字典 | 策略对象 | 解析策略参数并构建因子列表 |
| `filter_before_select(df)` | 因子面板 | 过滤后面板 | 通用过滤（停牌/ST/退市等）+ 自定义过滤 |
| `calc_select_factor(df)` | 因子面板 | 复合因子 | 默认加权组合或自定义函数 |
| `calc_signal(df)` | 因子面板 | 择时信号 | 策略信号计算 + fallback 处理 |
| `calc_override_signal(df)` | 因子面板 | 临时调仓信号 | 生成分周期 override 信号 |

### 13.3 factor_config.py
**功能描述**：因子、过滤因子与截面因子配置模型。

| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `FactorConfig.parse_list` | 因子列表 | `FactorConfig[]` | 归一化权重并生成列名 |
| `FilterFactorConfig.init` | 过滤配置 | `FilterFactorConfig` | 解析 `rank/pct/val` 过滤方式 |
| `CrossSectionConfig.parse_list` | 截面因子列表 | `CrossSectionConfig[]` | 解析因子组合与参数 |
| `get_col_name(...)` | 因子参数 | 列名 | 统一列名编码规则 |

### 13.4 timing_signal.py
**功能描述**：择时/临时调仓/资金曲线再择时的信号封装。

| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `TimingSignal.init` | 配置信号 | `TimingSignal` | 解析因子与参数，并识别分钟信号 |
| `OverrideSignal.init` | 配置信号 | `OverrideSignal` | 生成临时调仓信号配置 |
| `EquityTiming.init` | 配置信号 | `EquityTiming` | 生成资金曲线择时器 |

### 13.5 finance_manager.py
**功能描述**：财务数据容器，支持原始/单季/TTM/同比/环比等派生序列。

| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `FinanceDataFrame` | 财务数据 + 交易日 | 财务数据对象 | 维护 raw/pivot 与缓存 |
| `FinanceDataSeries` | 字段名 | `Series` | 提供 `.raw/.quarter/.ttm/.yoy/.qoq` 等方法 |

### 13.6 rebalance_mode.py
**功能描述**：换仓策略封装与实例化入口。

| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `RebalanceMode.init` | 配置 | `RebalanceMode` | 解析 rebalance 模式并创建对应类 |

### 13.7 type_def.py
**功能描述**：交易模拟中使用的 `numba` 数据结构与常量。

| 函数/类 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `StockMarketData` | 行情数组 | JIT 可用结构 | 聚合 open/close/分钟价与品种类型 |
| `SimuParams` | 资金、费率 | 模拟参数 | 传入 `start_simulation` |
| `AdjustRatios` | 调仓日期 + 权重矩阵 | 调仓参数对象 | 记录调仓时点与买卖价格索引 |
| `get_symbol_type(symbol)` | 股票代码 | 交易所类型 | 依据代码前缀判定交易所/板块 |
| `price_array` | 常量 | 价格索引表 | 定义分钟价格的索引顺序 |

---

## 14. core/utils（通用工具）

### 14.1 factor_hub.py / strategy_hub.py / signal_hub.py
**功能描述**：插件式加载因子、策略、信号。

| 模块 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `FactorHub.get_by_name` | 因子名 | 因子对象 | `importlib` 动态加载 `因子库/` 与 `截面因子库/` |
| `get_strategy_by_name` | 策略名 | 函数字典 | 加载 `策略库/` 模块函数 |
| `get_signal_by_name` | 信号名 | 函数字典 | 加载 `信号库/` 模块函数 |

### 14.2 data_hub.py / path_kit.py / misc_kit.py / serializable_kit.py
**功能描述**：外部数据发现、路径管理、稳定拼接与配置序列化。

| 模块 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `load_ext_data` | 无 | 外部数据字典 | 扫描 `外部数据/` 并加载读取函数 |
| `get_folder_path/get_file_path` | 路径片段 | 绝对路径 | 按项目根目录拼接 |
| `pd_concat` | `DataFrame[]` | 合并结果 | 过滤空表/全 NA 并抑制警告 |
| `save_csv_safely` | `DataFrame` + 路径 | CSV + 可选 pkl | 写入前检查权限与文件占用 |
| `object_to_json` | 配置对象 | `config.json` | 基于 `config.py` 结构输出 |

### 14.3 其他辅助模块
| 模块 | 输入 | 输出 | 逻辑/算法 |
| --- | --- | --- | --- |
| `core/version.py` | 无 | 版本提示 | `version_prompt()` 输出版本与提示信息 |
| `core/utils/color_kit.py` | 无 | 颜色常量 | Plotly 图表配色 |
| `core/utils/figure_kit.py` | 图表数据 | 图表对象 | 图表辅助函数封装 |

---

## 15. 异常处理机制（跨模块）
- **路径/数据缺失**：
  - `BacktestConfig.__init__` 校验数据中心路径与交易日历，不满足时 `sys.exit()`
  - `check_extra_data` 返回 `(False, msg)`，由上层决定终止或降级
  - `merge_extra_data` 读取失败时用 `NaN`/默认值填充
- **因子计算一致性**：
  - `cal_strategy_factors` 与 `calc_cross_sections` 校验行数是否变化，变化即抛异常
- **财务数据缺失**：
  - `get_finance_data`/`merge_with_finance_data` 若无文件则补全 `NaN` 并提示
- **选股异常**：
  - 空结果自动落盘空表，避免流程中断
  - 因子列缺失会触发警告（例如最近 5 日因子全空）
- **交易模拟异常**：
  - 权重聚合为空时警告并退出或使用默认区间
  - `save_csv_safely` 捕获写入失败（如文件被占用）
- **网络/交易日历**：
  - `check_period_offset`/`download_period_offset` 使用重试并记录错误日志

---

## 16. 优化建议（性能与量化逻辑）
- **性能优化**
  - 将 `factor_*.pkl` 改为 `parquet` 或 `feather`，减少 I/O 开销并提升读取速度
  - 对 `calculate_factors` 引入“列级缓存索引”，避免重复加载 `all_factors_kline.pkl`
  - 在 `prepare_data` 和 `calculate_factors` 中使用共享内存或 Arrow Flight 降低多进程序列化成本
  - `start_simulation` 中可加入更紧凑的数组布局（结构体数组 → 数组结构）提升缓存友好度

- **量化逻辑与风控**
  - 明确“换仓时间”与“信号时间”对齐关系，避免混用 `T+0/T+1` 时出现隐性未来函数
  - 将“下日_是否交易/涨停”等字段的使用场景显式标注，确保仅用于可知信息的过滤
  - 对 `merge_with_finance_data_new` 加入“发布日期可得性”审计开关，提供未来函数检测日志
  - 为 `择时信号` 与 `临时调仓` 增加“信号生成时刻”校验与回测一致性检查

- **可维护性**
  - 在 `BacktestConfig.save` 之外增加“结果元数据索引（manifest）”，便于溯源与回滚
  - 统一“异常处理策略”：对关键步骤引入可配置的 `strict/lenient` 模式
