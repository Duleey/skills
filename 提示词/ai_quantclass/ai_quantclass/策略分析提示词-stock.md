# 量化策略全面分析 - AI提示词 (股票版)

## 使用说明

将下方提示词复制给AI（Claude/ChatGPT/Cursor），同时上传以下 CSV 文件（位于 `26分享会小市值组合` 文件夹）：
- `资金曲线.csv`
- `策略评价.csv`
- `月度账户收益.csv`
- `年度账户收益.csv`
- `选股结果.csv`
- `择时信号#0.小市值_基本面优化1.csv` (可选，用于择时分析)

---

## 一键完整分析提示词

```python
"""
我有一套股票量化策略的回测数据（A股小市值策略），请用 Python 进行全面分析并生成可视化报告。
请直接运行以下完整的 Python 脚本。
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# 1. 配置与预处理
# ==========================================

# 设置中文字体（兼容 Mac/Windows/Linux）
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'PingFang SC', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# A股专用配色
COLOR_UP = '#d63031'      # 涨-红
COLOR_DOWN = '#00b894'    # 跌-绿
COLOR_MAIN = '#0984e3'    # 主色-蓝
COLOR_COST = '#636e72'    # 成本-灰

def load_and_clean_data():
    # 1. 加载资金曲线
    df_curve = pd.read_csv('资金曲线.csv', parse_dates=['交易日期'])
    # 确保数值列为float
    cols_to_float = ['净值', '涨跌幅', '实际杠杆', '印花税', '券商佣金', '总资产']
    for col in cols_to_float:
        if col in df_curve.columns and df_curve[col].dtype == 'object':
             df_curve[col] = df_curve[col].str.rstrip('%').astype(float) / 100 if '%' in str(df_curve[col].iloc[0]) else df_curve[col].astype(float)
    
    # 2. 加载周期收益
    dfs_period = {}
    for p in ['月度', '季度', '年度']:
        fname = f'{p}账户收益.csv'
        try:
            df = pd.read_csv(fname, parse_dates=['交易日期'])
            if '涨跌幅' in df.columns and df['涨跌幅'].dtype == 'object':
                df['涨跌幅'] = df['涨跌幅'].str.rstrip('%').astype(float) / 100
            dfs_period[p] = df
        except FileNotFoundError:
            print(f"Warning: {fname} not found.")
            dfs_period[p] = pd.DataFrame()

    # 3. 加载选股结果
    try:
        df_stock = pd.read_csv('选股结果.csv', parse_dates=['选股日期'])
    except FileNotFoundError:
        df_stock = pd.DataFrame()
        
    # 4. 加载策略评价
    try:
        df_eval = pd.read_csv('策略评价.csv', index_col=0)
    except FileNotFoundError:
        df_eval = pd.DataFrame()

    return df_curve, dfs_period, df_stock, df_eval

df_curve, dfs_period, df_stock, df_eval = load_and_clean_data()

print("=" * 60)
print(f"策略回测区间: {df_curve['交易日期'].min().date()} ~ {df_curve['交易日期'].max().date()}")
print(f"最终净值: {df_curve['净值'].iloc[-1]:.2f}")
print("=" * 60)

# ==========================================
# 2. 核心图表绘制 (12图仪表板)
# ==========================================

fig = plt.figure(figsize=(24, 18), constrained_layout=True)
gs = GridSpec(4, 4, figure=fig)

# --- 第一行：净值与回撤 ---
# [1-2列] 净值曲线 (对数坐标)
ax1 = fig.add_subplot(gs[0, :2])
ax1.plot(df_curve['交易日期'], df_curve['净值'], color=COLOR_MAIN, linewidth=1.5, label='策略净值')
ax1.set_yscale('log')
ax1.set_title('策略净值走势 (对数坐标)', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(loc='upper left')

# 标注最大回撤区域
dd_col = '净值dd2here' if '净值dd2here' in df_curve.columns else None
if dd_col:
    # 找到回撤最深的点
    max_dd_idx = df_curve[dd_col].idxmin()
    max_dd_date = df_curve.loc[max_dd_idx, '交易日期']
    ax1.annotate(f'最大回撤\n{df_curve.loc[max_dd_idx, dd_col]:.2%}', 
                 xy=(max_dd_date, df_curve.loc[max_dd_idx, '净值']),
                 xytext=(max_dd_date, df_curve.loc[max_dd_idx, '净值']*0.6),
                 arrowprops=dict(facecolor='red', shrink=0.05))

# [3-4列] 回撤深度
ax2 = fig.add_subplot(gs[0, 2:])
if dd_col:
    ax2.fill_between(df_curve['交易日期'], df_curve[dd_col], 0, color='gray', alpha=0.3)
    ax2.plot(df_curve['交易日期'], df_curve[dd_col], color='black', linewidth=0.8)
    # 标记危险区域
    ax2.axhline(-0.2, color='red', linestyle='--', alpha=0.5, label='-20% 警戒线')
ax2.set_title('动态回撤深度', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend()

# --- 第二行：周期收益分析 ---
# [1列] 年度收益
ax3 = fig.add_subplot(gs[1, 0])
if not dfs_period['年度'].empty:
    df_y = dfs_period['年度'].copy()
    df_y['year'] = df_y['交易日期'].dt.year
    colors = [COLOR_UP if x > 0 else COLOR_DOWN for x in df_y['涨跌幅']]
    bars = ax3.bar(df_y['year'], df_y['涨跌幅'], color=colors)
    ax3.set_title('年度收益率', fontsize=14, fontweight='bold')
    ax3.bar_label(bars, fmt='%.1f%%', fontsize=9)

# [2列] 季度热力图
ax4 = fig.add_subplot(gs[1, 1])
if not dfs_period['季度'].empty:
    df_q = dfs_period['季度'].copy()
    df_q['year'] = df_q['交易日期'].dt.year
    df_q['quarter'] = df_q['交易日期'].dt.quarter
    pivot_q = df_q.pivot_table(index='year', columns='quarter', values='涨跌幅')
    sns.heatmap(pivot_q, annot=True, fmt='.1%', cmap='RdYlGn', center=0, ax=ax4, cbar=False)
    ax4.set_title('季度收益热力图', fontsize=14, fontweight='bold')

# [3-4列] 月度收益分布
ax5 = fig.add_subplot(gs[1, 2:])
if not dfs_period['月度'].empty:
    df_m = dfs_period['月度'].copy()
    colors = [COLOR_UP if x > 0 else COLOR_DOWN for x in df_m['涨跌幅']]
    ax5.bar(df_m['交易日期'], df_m['涨跌幅'], color=colors, width=20)
    ax5.set_title('月度收益分布', fontsize=14, fontweight='bold')
    ax5.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# --- 第三行：持仓与成本 ---
# [1列] 实际杠杆率/仓位
ax6 = fig.add_subplot(gs[2, 0])
if '实际杠杆' in df_curve.columns:
    ax6.plot(df_curve['交易日期'], df_curve['实际杠杆'], color='purple', linewidth=1)
    ax6.fill_between(df_curve['交易日期'], df_curve['实际杠杆'], 0, color='purple', alpha=0.1)
    ax6.set_title('实际仓位/杠杆率', fontsize=14, fontweight='bold')
    ax6.set_ylim(0, 1.1) # 假设主要是多头

# [2列] 交易成本堆叠图
ax7 = fig.add_subplot(gs[2, 1])
if '印花税' in df_curve.columns and '券商佣金' in df_curve.columns:
    df_curve['累计印花税'] = df_curve['印花税'].cumsum()
    df_curve['累计佣金'] = df_curve['券商佣金'].cumsum()
    ax7.stackplot(df_curve['交易日期'], df_curve['累计印花税'], df_curve['累计佣金'], 
                  labels=['印花税', '佣金'], colors=['#bdc3c7', '#7f8c8d'])
    ax7.set_title('累计交易成本', fontsize=14, fontweight='bold')
    ax7.legend(loc='upper left')

# [3列] 持仓数量变化 (从选股结果分析)
ax8 = fig.add_subplot(gs[2, 2])
if not df_stock.empty:
    daily_counts = df_stock.groupby('选股日期')['股票代码'].nunique()
    ax8.plot(daily_counts.index, daily_counts.values, color='orange', drawstyle='steps-post')
    ax8.set_title('每日持仓股票数量', fontsize=14, fontweight='bold')

# [4列] 子策略贡献 (如果有策略列)
ax9 = fig.add_subplot(gs[2, 3])
if not df_stock.empty and '策略' in df_stock.columns:
    strategy_counts = df_stock['策略'].value_counts()
    # 取前N个策略，其他的归为Others
    if len(strategy_counts) > 5:
        top_strats = strategy_counts[:5]
        others = pd.Series([strategy_counts[5:].sum()], index=['Others'])
        strategy_counts = pd.concat([top_strats, others])
    
    ax9.pie(strategy_counts, labels=strategy_counts.index, autopct='%1.1f%%', startangle=90)
    ax9.set_title('子策略选股占比', fontsize=14, fontweight='bold')

# --- 第四行：风险与风格 ---
# [1列] 收益分布直方图
ax10 = fig.add_subplot(gs[3, 0])
sns.histplot(df_curve['涨跌幅'].dropna(), kde=True, ax=ax10, color=COLOR_MAIN)
ax10.set_title('日收益率分布', fontsize=14, fontweight='bold')
ax10.axvline(0, color='black', linestyle='--')

# [2列] 滚动年化波动率 (20日)
ax11 = fig.add_subplot(gs[3, 1])
rolling_vol = df_curve['涨跌幅'].rolling(20).std() * np.sqrt(250)
ax11.plot(df_curve['交易日期'], rolling_vol, color='orange')
ax11.set_title('20日滚动波动率(年化)', fontsize=14, fontweight='bold')

# [3-4列] 选股因子排名分布 (如果存在)
ax12 = fig.add_subplot(gs[3, 2:])
if not df_stock.empty and '选股因子排名' in df_stock.columns:
    # 绘制箱线图看每年的排名分布变化
    df_stock['year'] = df_stock['选股日期'].dt.year
    sns.boxplot(x='year', y='选股因子排名', data=df_stock, ax=ax12, showfliers=False)
    ax12.set_title('选股因子排名年度分布 (越小越好)', fontsize=14, fontweight='bold')
    ax12.invert_yaxis() # 排名越小越好，所以在上方

plt.savefig('策略分析仪表板.png', dpi=150, bbox_inches='tight')
print("\n图表已生成：策略分析仪表板.png")

# ==========================================
# 3. 深度文本分析报告生成
# ==========================================

# 3.1 成本分析
total_tax = df_curve['印花税'].sum()
total_comm = df_curve['券商佣金'].sum()
total_cost = total_tax + total_comm
avg_asset = df_curve['总资产'].mean()
cost_impact = total_cost / avg_asset
years = (df_curve['交易日期'].max() - df_curve['交易日期'].min()).days / 365.25

# 3.2 收益统计
cagr = (df_curve['净值'].iloc[-1]) ** (1/years) - 1
daily_ret = df_curve['涨跌幅'].mean()
volatility = df_curve['涨跌幅'].std() * np.sqrt(250)
sharpe = (cagr - 0.03) / volatility

# 3.3 打印报告
print("\n" + "="*30)
print("策略深度评估报告")
print("="*30)
print(f"1. 收益与风险")
print(f"   - 年化收益率 (CAGR): {cagr:.2%}")
print(f"   - 年化波动率: {volatility:.2%}")
print(f"   - 夏普比率: {sharpe:.2f}")
print(f"   - 最大回撤: {df_curve['净值dd2here'].min():.2%}")

print(f"\n2. 交易成本分析")
print(f"   - 累计印花税: {total_tax/10000:.2f} 万元")
print(f"   - 累计佣金: {total_comm/10000:.2f} 万元")
print(f"   - 成本对净值拖累: {cost_impact/years:.2%} / 年")
print(f"     (注: 若成本拖累 > 5%/年，需警惕实盘滑点影响)")

print(f"\n3. 持仓特征")
if not df_stock.empty:
    avg_hold = daily_counts.mean()
    print(f"   - 平均每日持股: {avg_hold:.1f} 只")
    print(f"   - 子策略数量: {df_stock['策略'].nunique()} 个")
    if '股票名称' in df_stock.columns:
        top_stocks = df_stock['股票名称'].value_counts().head(5)
        print(f"   - 最常持有的股票: {', '.join(top_stocks.index.tolist())}")

print(f"\n4. 策略稳定性")
if not dfs_period['年度'].empty:
    best_year = dfs_period['年度'].loc[dfs_period['年度']['涨跌幅'].idxmax()]
    worst_year = dfs_period['年度'].loc[dfs_period['年度']['涨跌幅'].idxmin()]
    print(f"   - 最佳年份: {best_year['year']} ({best_year['涨跌幅']:.1%})")
    print(f"   - 最差年份: {worst_year['year']} ({worst_year['涨跌幅']:.1%})")
    
print("="*60)
```

---

## 进阶分析提示词 (无需代码)

### A. 隐形风险挖掘
```markdown
请结合 `策略分析仪表板.png` 和打印的指标，帮我挖掘这个策略可能存在的“隐形风险”：
1. **风格漂移**：观察选股因子排名的箱线图，近年来排名是否变大？这意味着选股能力在下降。
2. **拥挤度风险**：看每日持仓数量，2024年是否突然持仓变少？可能是在微盘股崩塌时无法卖出。
3. **成本黑洞**：如果每年成本拖累超过10%，请计算包含滑点（假设双边千分之三）后的真实收益会剩下多少。
```

### B. 牛熊市压力测试
```markdown
请将策略在以下三个特殊时期的表现单独拉出来点评：
1. **2015年股灾** (2015.06 - 2016.02)：是否成功逃顶？
2. **2018年贸易战** (全年)：是空仓躲避还是硬抗？
3. **2024年春节微盘股危机** (2024.01 - 2024.02)：回撤幅度是否超过了历史极值？
```
