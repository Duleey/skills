  一、系统概览

  本框架采用模块化分层架构,实现了从原始行情数据到回测报告的完整量化投资流水线。核心设计理念为:
  - 数据驱动: 通过 pickle 缓存实现各阶段数据解耦
  - 并行计算: 基于 ProcessPoolExecutor 的多进程因子计算与选股
  - 配置化策略: 通过 BacktestConfig 和 StrategyConfig 实现策略参数化

  二、数据流向分析

  完整数据流管道:

  外部数据源 → 数据预处理 → 因子计算 → 选股筛选 → 交易模拟 → 回测报告
      ↓            		↓           	↓          	↓          	↓          	↓
  [CSV文件]  	[股票预处理]  [因子pkl]  [选股结果]  [资金曲线]     [策略评价]

  详细流程拆解:

  阶段1: 数据准备 (core/data_center.py::prepare_data)
  - 输入: data_center_path/{股票代码}.csv (原始日线数据)
  - 处理:
    - 读取指数数据作为交易日历基准
    - 逐股票计算复权价格 (cal_fuquan_price)
    - 计算涨跌停价格 (cal_zdt_price)
    - 合并指数数据补全停牌日 (merge_with_index_data)
    - 可选加载分钟级数据 (load_min_data)
  - 输出:
    - 运行缓存/股票预处理数据.pkl: 字典结构 {股票代码: DataFrame}
    - 运行缓存/全部股票行情pivot.pkl: 透视表 {price_type: pivot_df}

  阶段2: 因子计算 (core/select_stock.py::calculate_factors)
  - 输入: 预处理数据 + 因子库模块
  - 处理:
    - 通过 FactorHub 动态加载因子文件
    - 分批计算因子 (受 factor_col_limit 控制,默认8-12列/批)
    - 时序因子: 逐股票调用 add_factor() 方法
    - 截面因子: 基于全市场面板数据计算 (calc_cross_sections)
    - 财务因子: 通过 FinanceDataFrame 对象管理财报数据
  - 输出:
    - 运行缓存/all_factors_kline.pkl: 基础行情字段
    - 运行缓存/factor_{因子名}.pkl: 每个因子独立存储

  阶段3: 选股执行 (core/select_stock.py::select_stocks)
  - 输入: 因子数据 + StrategyConfig
  - 处理:
    - 前置过滤: filter_before_select() (如上市天数、板块过滤)
    - 复合因子计算: calc_select_factor() (多因子加权/排序)
    - 择时信号: calc_signal() (可选,如定风波信号)
    - 因子排名选股: select_by_factor() (Top-N 或百分比选股)
    - 后置过滤: filter_after_select() (如涨停、ST过滤)
    - 分批进场: calc_scalein_pos() (多offset资金分配)
  - 输出:
    - 回测结果/选股结果{策略名}.pkl: 包含 [选股日期, 股票代码, 目标资金占比, 择时信号]

  阶段4: 交易模拟 (core/equity.py::simulate_performance)
  - 输入: 选股结果 + 行情pivot数据
  - 处理:
    - 权重聚合: 按 (策略, 持仓周期, 换仓时间) 分组透视
    - Numba加速模拟: start_simulation() 逐K线模拟交易
        - 支持T+0/T+1换仓
      - 支持分钟级换仓时间点 (如09:30, 14:55)
      - 动态杠杆管理
      - 印花税/佣金计算
    - 可选再择时: simu_equity_timing() (基于资金曲线的动态杠杆)
  - 输出:
    - 回测结果/资金曲线.csv: 逐日账户状态
    - 回测结果/策略评价.csv: 收益指标汇总

  三、模块耦合关系图

  ┌─────────────────────────────────────────────────────────┐
  │                    config.py (全局配置)                   		│
  │  - 数据路径、回测区间、手续费率、并行度                    │
  └────────────────────┬────────────────────────────────────┘
                       │
           ┌───────────▼───────────┐
           │  回测主程序.py          │
           │  run_backtest()       │
           └───────────┬───────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Step 1   			│  │ Step 2   			│  │ Step 3   		      │
  │数据准备   		     │→│因子计算   		  │→ │选股执行		   │
  └──────────┘  └──────────┘  └──────────┘
        │              │              │
        │              │              ▼
        │              │        ┌──────────┐
        │              │        │ Step 4   			│
        │              └─→│交易模拟   │
        │                       └──────────┘
        │                             │
        ▼                             ▼
  ┌──────────────────┐      ┌──────────────────┐
  │  core/model/     					│      │  core/evaluate   					│
  │  - BacktestConfig					│      │  - 策略评价       					│
  │  - StrategyConfig					│      │  - 绩效指标       					│
  └──────────────────┘      └──────────────────┘
        ▲
        │
  ┌─────┴─────┬─────────┬─────────┐
  │           	│         	│         			 │
  ▼           	▼         	▼         			▼
  因子库/   	 策略库/   信号库/  		 截面因子库/

  四、关键耦合点分析

  1. 配置对象传递 (强耦合)

  - BacktestConfig 贯穿全流程,包含:
    - 数据路径 (stock_data_path, index_data_path)
    - 策略列表 (strategy_list: List[StrategyConfig])
    - 因子元数据 (factor_params_dict, fin_cols)
    - 运行时路径 (get_runtime_folder(), get_result_folder())

  2. 数据缓存机制 (松耦合)

  - 各阶段通过 pickle 文件解耦:
    - 优点: 支持断点续跑,减少重复计算
    - 缺点: 磁盘I/O开销,需手动管理缓存一致性

  3. 因子库动态加载 (插件化)

  - FactorHub 通过反射机制加载因子模块:
  factor_file = FactorHub.get_by_name(factor_name)
    factor_df = factor_file.add_factor(df, param, ...)
  - 因子文件需实现标准接口: add_factor(df, param, **kwargs)

  4. 多进程并行 (进程隔离)

  - 因子计算和选股阶段使用 ProcessPoolExecutor
  - 进程数由 n_jobs 控制 (根据 performance_mode 自动调整)
  - 注意: Windows系统限制最大61进程

  5. Numba加速核心 (性能关键)

  - equity.py::start_simulation() 使用 @nb.njit 编译
  - 要求数据结构为 Numba 兼容类型 (StockMarketData, SimuParams)

  五、扩展性设计

  可扩展点:

  1. 因子库: 在 因子库/ 下新增 .py 文件,实现 add_factor() 接口
  2. 策略库: 在 策略库/ 下配置新策略参数
  3. 信号库: 实现择时信号类 (继承 EquityTiming)
  4. 外部数据: 通过 core/data_bridge.py 注册新数据源

  约束条件:

  - 因子计算不得改变DataFrame行数
  - 选股结果必须包含 RES_COLS 字段
  - 财务数据需遵循 FinanceDataFrame 接口

---
  六、性能优化要点

  1. 内存管理: factor_col_limit 控制批次大小,避免OOM
  2. 并行度调优: performance_mode 三档 (ECO/BAL/MAX)
  3. 数据类型优化: 使用 category 类型存储股票代码/名称
  4. 计算缓存: 因子结果按列独立存储,支持增量计算

---
  总结: 该框架通过配置驱动 + 数据缓存 + 插件化因子的设计,实现了高度模块化的量化回测系统。核心耦合点集中在 BacktestConfig 对象,各计算阶段通过 pickle 文件松耦合,支持灵活的策略开发和性能调优。