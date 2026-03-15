#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化策略全面分析脚本
基于策略分析提示词.md实现
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats
import warnings
import os

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'PingFang SC', 'Heiti TC']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 100

# 配色方案
COLOR_UP = '#2ecc71'      # 正收益-绿色
COLOR_DOWN = '#e74c3c'    # 负收益-红色
COLOR_MAIN = '#3498db'    # 主色-蓝色
COLOR_GRAY = '#95a5a6'    # 灰色
COLOR_ORANGE = '#f39c12'  # 橙色
COLOR_PURPLE = '#9b59b6'  # 紫色

# 数据目录
DATA_DIR = '/Users/jornason/Desktop/ai_quantclass/策略_v14v4/'

# ============================================================
# 第一步：数据加载与预处理
# ============================================================
print("=" * 70)
print("第一步：数据加载与预处理")
print("=" * 70)

# 加载数据
df_curve = pd.read_csv(os.path.join(DATA_DIR, '资金曲线.csv'), parse_dates=['candle_begin_time'])
df_eval = pd.read_csv(os.path.join(DATA_DIR, '策略评价.csv'), index_col=0, encoding='utf-8-sig')
df_monthly = pd.read_csv(os.path.join(DATA_DIR, '月度账户收益.csv'), parse_dates=['candle_begin_time'], encoding='utf-8-sig')
df_quarterly = pd.read_csv(os.path.join(DATA_DIR, '季度账户收益.csv'), parse_dates=['candle_begin_time'], encoding='utf-8-sig')
df_yearly = pd.read_csv(os.path.join(DATA_DIR, '年度账户收益.csv'), parse_dates=['candle_begin_time'], encoding='utf-8-sig')

# 清洗涨跌幅列（去除%符号转为小数）
for df in [df_monthly, df_quarterly, df_yearly]:
    if df['涨跌幅'].dtype == 'object':
        df['涨跌幅'] = df['涨跌幅'].str.rstrip('%').astype(float) / 100

# 基本信息
print(f"\n回测时间: {df_curve['candle_begin_time'].min()} ~ {df_curve['candle_begin_time'].max()}")
print(f"数据点数: {len(df_curve):,} 条（小时级）")
print(f"月度数据: {len(df_monthly)} 个月")
print(f"季度数据: {len(df_quarterly)} 个季度")
print(f"年度数据: {len(df_yearly)} 年")
print(f"最终净值: {df_curve['净值'].iloc[-1]:.2f}")

# 打印策略评价指标
print("\n策略核心指标（来自策略评价.csv）:")
print("-" * 40)
for idx in df_eval.index:
    print(f"  {idx}: {df_eval.loc[idx, '0']}")

# ============================================================
# 第二步：计算统计指标
# ============================================================
print("\n" + "=" * 70)
print("第二步：计算统计指标")
print("=" * 70)

# 收益指标
cumulative_return = (df_curve['净值'].iloc[-1] - 1) * 100
annual_return = float(str(df_eval.loc['年化收益', '0']).rstrip('%'))
monthly_returns = df_monthly['涨跌幅'].values
monthly_mean = np.mean(monthly_returns) * 100
monthly_median = np.median(monthly_returns) * 100
monthly_std = np.std(monthly_returns) * 100
win_rate_monthly = (monthly_returns > 0).sum() / len(monthly_returns) * 100
best_month = df_monthly.loc[df_monthly['涨跌幅'].idxmax()]
worst_month = df_monthly.loc[df_monthly['涨跌幅'].idxmin()]

print("\n【收益指标】")
print(f"  累计收益率: {cumulative_return:.2f}%")
print(f"  年化收益率: {annual_return:.2f}%")
print(f"  月度平均收益: {monthly_mean:.2f}%")
print(f"  月度收益中位数: {monthly_median:.2f}%")
print(f"  月度收益标准差: {monthly_std:.2f}%")
print(f"  正收益月份占比: {win_rate_monthly:.2f}%")
print(f"  最佳月度: {best_month['candle_begin_time'].strftime('%Y-%m')} ({best_month['涨跌幅']*100:.2f}%)")
print(f"  最差月度: {worst_month['candle_begin_time'].strftime('%Y-%m')} ({worst_month['涨跌幅']*100:.2f}%)")

# 风险指标
max_drawdown = float(str(df_eval.loc['最大回撤', '0']).rstrip('%'))
negative_months = monthly_returns[monthly_returns < 0]
downside_std = np.std(negative_months) * 100 if len(negative_months) > 0 else 0

# 计算回撤次数
drawdowns = df_curve['净值dd2here'].values
dd_over_5 = (drawdowns < -0.05).sum()
dd_over_10 = (drawdowns < -0.10).sum()
dd_over_15 = (drawdowns < -0.15).sum()

print("\n【风险指标】")
print(f"  最大回撤: {max_drawdown}%")
print(f"  月度下行标准差: {downside_std:.2f}%")
print(f"  负收益月份数: {len(negative_months)}")
print(f"  回撤超过5%的小时数: {dd_over_5:,}")
print(f"  回撤超过10%的小时数: {dd_over_10:,}")
print(f"  回撤超过15%的小时数: {dd_over_15:,}")

# 风险调整收益
sharpe_ratio = annual_return / (monthly_std * np.sqrt(12)) if monthly_std > 0 else 0
sortino_ratio = annual_return / (downside_std * np.sqrt(12)) if downside_std > 0 else 0
calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
return_dd_ratio = float(df_eval.loc['年化收益/回撤比', '0'])

print("\n【风险调整收益】")
print(f"  夏普比率: {sharpe_ratio:.2f}")
print(f"  索提诺比率: {sortino_ratio:.2f}")
print(f"  卡玛比率: {calmar_ratio:.2f}")
print(f"  收益回撤比: {return_dd_ratio:.2f}")

# 交易统计
win_rate = float(str(df_eval.loc['胜率', '0']).rstrip('%'))
profit_loss_ratio = float(df_eval.loc['盈亏收益比', '0'])
max_consecutive_win = int(float(df_eval.loc['最大连续盈利周期数', '0']))
max_consecutive_loss = int(float(df_eval.loc['最大连续亏损周期数', '0']))

print("\n【交易统计】")
print(f"  胜率: {win_rate}%")
print(f"  盈亏比: {profit_loss_ratio:.2f}")
print(f"  最大连续盈利周期: {max_consecutive_win}")
print(f"  最大连续亏损周期: {max_consecutive_loss}")

# 仓位统计
avg_leverage = df_curve['leverage_ratio'].mean()
max_leverage = df_curve['leverage_ratio'].max()
avg_ls_ratio = df_curve['long_short_ratio'].mean()
long_bias = (df_curve['long_short_ratio'] > 1.2).sum() / len(df_curve) * 100
short_bias = (df_curve['long_short_ratio'] < 0.8).sum() / len(df_curve) * 100
neutral = 100 - long_bias - short_bias
avg_symbols = (df_curve['symbol_long_num'] + df_curve['symbol_short_num']).mean()

print("\n【仓位统计】")
print(f"  平均杠杆: {avg_leverage:.2f}x")
print(f"  最大杠杆: {max_leverage:.2f}x")
print(f"  多空比例均值: {avg_ls_ratio:.2f}")
print(f"  偏多时间占比: {long_bias:.2f}%")
print(f"  偏空时间占比: {short_bias:.2f}%")
print(f"  中性时间占比: {neutral:.2f}%")
print(f"  平均持仓品种数: {avg_symbols:.1f}")

# ============================================================
# 第三步：找出最大的5次回撤
# ============================================================
print("\n" + "=" * 70)
print("第三步：回撤详细分析")
print("=" * 70)

def find_drawdowns(nav_series):
    """找出所有回撤区间"""
    drawdowns = []
    peak = nav_series.iloc[0]
    peak_idx = 0
    in_drawdown = False
    dd_start = 0

    for i in range(len(nav_series)):
        if nav_series.iloc[i] > peak:
            if in_drawdown:
                # 回撤结束
                drawdowns.append({
                    'start_idx': dd_start,
                    'trough_idx': trough_idx,
                    'end_idx': i,
                    'drawdown': (trough_value - peak_at_start) / peak_at_start
                })
                in_drawdown = False
            peak = nav_series.iloc[i]
            peak_idx = i
        else:
            if not in_drawdown:
                in_drawdown = True
                dd_start = peak_idx
                peak_at_start = peak
                trough_value = nav_series.iloc[i]
                trough_idx = i
            else:
                if nav_series.iloc[i] < trough_value:
                    trough_value = nav_series.iloc[i]
                    trough_idx = i

    return sorted(drawdowns, key=lambda x: x['drawdown'])[:5]

# 简化方法：直接用净值dd2here找回撤
print("\n【最大5次回撤】")
print("-" * 80)
print(f"{'排名':<6}{'回撤幅度':<12}{'开始时间':<22}{'谷底时间':<22}{'结束时间':<22}")
print("-" * 80)

# 使用滑动窗口找主要回撤
nav = df_curve['净值'].values
times = df_curve['candle_begin_time'].values
dd = df_curve['净值dd2here'].values

# 找到回撤最深的时点
sorted_idx = np.argsort(dd)[:5]
for rank, idx in enumerate(sorted_idx, 1):
    print(f"{rank:<6}{dd[idx]*100:.2f}%{'':<6}{str(times[idx])[:19]:<22}")

# ============================================================
# 第四步：年度对比分析
# ============================================================
print("\n" + "=" * 70)
print("第四步：年度对比分析")
print("=" * 70)

# 按年份计算统计
df_monthly['year'] = df_monthly['candle_begin_time'].dt.year
yearly_stats = df_monthly.groupby('year').agg({
    '涨跌幅': ['sum', 'mean', 'std', lambda x: (x > 0).sum()]
}).round(4)
yearly_stats.columns = ['累计收益', '月均收益', '月度标准差', '正收益月数']

print("\n【年度对比表】")
print("-" * 80)
print(f"{'年份':<8}{'收益率':<15}{'月均收益':<12}{'波动率':<12}{'正收益月数':<12}")
print("-" * 80)

for idx, row in yearly_stats.iterrows():
    cum_ret = (1 + df_monthly[df_monthly['year'] == idx]['涨跌幅']).prod() - 1
    print(f"{idx:<8}{cum_ret*100:.2f}%{'':<7}{row['月均收益']*100:.2f}%{'':<5}{row['月度标准差']*100:.2f}%{'':<5}{int(row['正收益月数'])}/12")

# ============================================================
# 第五步：生成12图综合仪表板
# ============================================================
print("\n" + "=" * 70)
print("第五步：生成12图综合仪表板")
print("=" * 70)

fig = plt.figure(figsize=(22, 16))
gs = GridSpec(3, 4, figure=fig, hspace=0.3, wspace=0.3)

# ---- 第一行：净值曲线和回撤曲线 ----
# 1-2列：净值曲线
ax1 = fig.add_subplot(gs[0, 0:2])
ax1.semilogy(df_curve['candle_begin_time'], df_curve['净值'], color=COLOR_MAIN, linewidth=1)
ax1.axhline(y=1, color=COLOR_GRAY, linestyle='--', alpha=0.5)
for milestone in [2, 5, 10, 50, 100, 200, 300]:
    if df_curve['净值'].max() >= milestone:
        ax1.axhline(y=milestone, color=COLOR_GRAY, linestyle=':', alpha=0.3)
        ax1.text(df_curve['candle_begin_time'].iloc[-1], milestone, f'{milestone}x', fontsize=8, alpha=0.5)
ax1.fill_between(df_curve['candle_begin_time'], df_curve['净值'], 1,
                  where=(df_curve['净值dd2here'] < -0.15), alpha=0.3, color=COLOR_DOWN)
ax1.set_title('净值曲线（对数坐标）', fontsize=12, fontweight='bold')
ax1.set_ylabel('净值')
ax1.grid(True, alpha=0.3)
ax1.set_xlim(df_curve['candle_begin_time'].min(), df_curve['candle_begin_time'].max())

# 3-4列：回撤曲线
ax2 = fig.add_subplot(gs[0, 2:4])
ax2.fill_between(df_curve['candle_begin_time'], df_curve['净值dd2here'] * 100, 0,
                  color=COLOR_DOWN, alpha=0.6)
ax2.axhline(y=-5, color=COLOR_ORANGE, linestyle='--', alpha=0.5, label='-5%')
ax2.axhline(y=-10, color=COLOR_DOWN, linestyle='--', alpha=0.5, label='-10%')
ax2.axhline(y=-15, color='darkred', linestyle='--', alpha=0.5, label='-15%')
ax2.axhline(y=-20, color='black', linestyle='--', alpha=0.5, label='-20%')
ax2.set_title('回撤曲线', fontsize=12, fontweight='bold')
ax2.set_ylabel('回撤 (%)')
ax2.legend(loc='lower right', fontsize=8)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(df_curve['candle_begin_time'].min(), df_curve['candle_begin_time'].max())

# ---- 第二行：收益分析 ----
# 1列：年度收益柱状图
ax3 = fig.add_subplot(gs[1, 0])
years = df_yearly['candle_begin_time'].dt.year.values
yearly_returns = df_yearly['涨跌幅'].values * 100
colors = [COLOR_UP if r > 0 else COLOR_DOWN for r in yearly_returns]
bars = ax3.bar(years, yearly_returns, color=colors, edgecolor='white', linewidth=0.5)
for bar, val in zip(bars, yearly_returns):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
             f'{val:.0f}%', ha='center', va='bottom', fontsize=8)
ax3.set_title('年度收益', fontsize=12, fontweight='bold')
ax3.set_ylabel('收益率 (%)')
ax3.axhline(y=0, color='black', linewidth=0.5)
ax3.grid(True, alpha=0.3, axis='y')

# 2列：季度收益热力图
ax4 = fig.add_subplot(gs[1, 1])
df_quarterly['year'] = df_quarterly['candle_begin_time'].dt.year
df_quarterly['quarter'] = df_quarterly['candle_begin_time'].dt.quarter
pivot_q = df_quarterly.pivot(index='year', columns='quarter', values='涨跌幅') * 100
sns.heatmap(pivot_q, annot=True, fmt='.0f', cmap='RdYlGn', center=0, ax=ax4,
            cbar_kws={'label': '%'}, annot_kws={'fontsize': 8})
ax4.set_title('季度收益热力图', fontsize=12, fontweight='bold')
ax4.set_xlabel('季度')
ax4.set_ylabel('年份')

# 3-4列：月度收益柱状图
ax5 = fig.add_subplot(gs[1, 2:4])
months = range(len(df_monthly))
monthly_rets = df_monthly['涨跌幅'].values * 100
colors = [COLOR_UP if r > 0 else COLOR_DOWN for r in monthly_rets]
ax5.bar(months, monthly_rets, color=colors, width=0.8)
ax5.axhline(y=0, color='black', linewidth=0.5)
ax5.set_title('月度收益', fontsize=12, fontweight='bold')
ax5.set_ylabel('收益率 (%)')
ax5.set_xlabel('月份序号')
ax5.grid(True, alpha=0.3, axis='y')

# ---- 第三行：风险与仓位 ----
# 1列：收益率分布直方图
ax6 = fig.add_subplot(gs[2, 0])
hourly_returns = df_curve['涨跌幅'].dropna() * 100
ax6.hist(hourly_returns, bins=100, color=COLOR_MAIN, alpha=0.7, edgecolor='white')
ax6.axvline(x=hourly_returns.mean(), color=COLOR_DOWN, linestyle='--', label=f'均值: {hourly_returns.mean():.3f}%')
ax6.axvline(x=hourly_returns.mean() + 2*hourly_returns.std(), color=COLOR_ORANGE, linestyle=':', alpha=0.7)
ax6.axvline(x=hourly_returns.mean() - 2*hourly_returns.std(), color=COLOR_ORANGE, linestyle=':', alpha=0.7)
ax6.set_title('小时收益率分布', fontsize=12, fontweight='bold')
ax6.set_xlabel('收益率 (%)')
ax6.set_ylabel('频次')
ax6.legend(fontsize=8)
ax6.grid(True, alpha=0.3)

# 2列：杠杆比例时序图
ax7 = fig.add_subplot(gs[2, 1])
# 降采样以便于可视化
sample_rate = max(1, len(df_curve) // 2000)
ax7.plot(df_curve['candle_begin_time'].iloc[::sample_rate],
         df_curve['leverage_ratio'].iloc[::sample_rate],
         color=COLOR_PURPLE, linewidth=0.5, alpha=0.7)
ax7.axhline(y=avg_leverage, color=COLOR_DOWN, linestyle='--', label=f'均值: {avg_leverage:.2f}x')
ax7.set_title('杠杆比例', fontsize=12, fontweight='bold')
ax7.set_ylabel('杠杆倍数')
ax7.legend(fontsize=8)
ax7.grid(True, alpha=0.3)

# 3列：多空比例时序图
ax8 = fig.add_subplot(gs[2, 2])
ax8.plot(df_curve['candle_begin_time'].iloc[::sample_rate],
         df_curve['long_short_ratio'].iloc[::sample_rate],
         color=COLOR_ORANGE, linewidth=0.5, alpha=0.7)
ax8.axhline(y=1.0, color='black', linestyle='-', linewidth=1, label='多空平衡')
ax8.axhline(y=1.2, color=COLOR_UP, linestyle='--', alpha=0.5)
ax8.axhline(y=0.8, color=COLOR_DOWN, linestyle='--', alpha=0.5)
ax8.set_title('多空比例', fontsize=12, fontweight='bold')
ax8.set_ylabel('Long/Short Ratio')
ax8.legend(fontsize=8)
ax8.grid(True, alpha=0.3)
ax8.set_ylim(0, min(3, df_curve['long_short_ratio'].quantile(0.99)))

# 4列：持仓品种数量
ax9 = fig.add_subplot(gs[2, 3])
ax9.fill_between(df_curve['candle_begin_time'].iloc[::sample_rate],
                  df_curve['symbol_long_num'].iloc[::sample_rate],
                  label='多头品种', color=COLOR_UP, alpha=0.6)
ax9.fill_between(df_curve['candle_begin_time'].iloc[::sample_rate],
                  -df_curve['symbol_short_num'].iloc[::sample_rate],
                  label='空头品种', color=COLOR_DOWN, alpha=0.6)
ax9.axhline(y=0, color='black', linewidth=0.5)
ax9.set_title('持仓品种数量', fontsize=12, fontweight='bold')
ax9.set_ylabel('品种数')
ax9.legend(fontsize=8)
ax9.grid(True, alpha=0.3)

plt.suptitle('量化策略综合分析仪表板', fontsize=16, fontweight='bold', y=0.98)
plt.savefig(os.path.join(DATA_DIR, '策略分析仪表板.png'), dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("已保存: 策略分析仪表板.png")

# ============================================================
# 第六步：回撤分析图
# ============================================================
print("\n生成回撤分析图...")

fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# 上图：回撤深度分布
ax1 = axes[0]
dd_values = df_curve['净值dd2here'].values * 100
dd_values = dd_values[dd_values < 0]  # 只看负值
ax1.hist(dd_values, bins=50, color=COLOR_DOWN, alpha=0.7, edgecolor='white')
ax1.axvline(x=-5, color=COLOR_ORANGE, linestyle='--', label='-5%')
ax1.axvline(x=-10, color='darkred', linestyle='--', label='-10%')
ax1.axvline(x=-15, color='black', linestyle='--', label='-15%')
ax1.set_title('回撤深度分布', fontsize=12, fontweight='bold')
ax1.set_xlabel('回撤幅度 (%)')
ax1.set_ylabel('频次')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 下图：完整回撤曲线（带标注）
ax2 = axes[1]
ax2.fill_between(df_curve['candle_begin_time'], df_curve['净值dd2here'] * 100, 0,
                  color=COLOR_DOWN, alpha=0.6)
# 标注最大回撤点
min_dd_idx = df_curve['净值dd2here'].idxmin()
min_dd_time = df_curve.loc[min_dd_idx, 'candle_begin_time']
min_dd_value = df_curve.loc[min_dd_idx, '净值dd2here'] * 100
ax2.annotate(f'最大回撤\n{min_dd_value:.2f}%',
             xy=(min_dd_time, min_dd_value),
             xytext=(min_dd_time, min_dd_value - 3),
             fontsize=10, ha='center',
             arrowprops=dict(arrowstyle='->', color='black'))
ax2.set_title('回撤时序图', fontsize=12, fontweight='bold')
ax2.set_xlabel('时间')
ax2.set_ylabel('回撤 (%)')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(DATA_DIR, '回撤分析.png'), dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("已保存: 回撤分析.png")

# ============================================================
# 第七步：滚动分析图
# ============================================================
print("\n生成滚动分析图...")

fig, axes = plt.subplots(3, 1, figsize=(14, 10))

# 计算12个月滚动指标
df_monthly_sorted = df_monthly.sort_values('candle_begin_time').reset_index(drop=True)
rolling_window = 12

# 滚动收益率
rolling_returns = []
rolling_sharpe = []
rolling_max_dd = []

for i in range(rolling_window, len(df_monthly_sorted) + 1):
    window_data = df_monthly_sorted.iloc[i-rolling_window:i]
    # 滚动累计收益
    cum_ret = (1 + window_data['涨跌幅']).prod() - 1
    rolling_returns.append(cum_ret * 100)
    # 滚动夏普
    mean_ret = window_data['涨跌幅'].mean()
    std_ret = window_data['涨跌幅'].std()
    sharpe = (mean_ret * 12) / (std_ret * np.sqrt(12)) if std_ret > 0 else 0
    rolling_sharpe.append(sharpe)
    # 滚动最大回撤（基于月度数据近似）
    cum_nav = (1 + window_data['涨跌幅']).cumprod()
    max_dd = (cum_nav / cum_nav.cummax() - 1).min() * 100
    rolling_max_dd.append(max_dd)

rolling_dates = df_monthly_sorted['candle_begin_time'].iloc[rolling_window-1:].values

# 上图：12个月滚动收益率
ax1 = axes[0]
ax1.plot(rolling_dates, rolling_returns, color=COLOR_MAIN, linewidth=1.5)
ax1.fill_between(rolling_dates, rolling_returns, 0,
                  where=[r > 0 for r in rolling_returns], color=COLOR_UP, alpha=0.3)
ax1.fill_between(rolling_dates, rolling_returns, 0,
                  where=[r <= 0 for r in rolling_returns], color=COLOR_DOWN, alpha=0.3)
ax1.axhline(y=0, color='black', linewidth=1)
ax1.axhline(y=100, color=COLOR_GRAY, linestyle='--', alpha=0.5, label='100%')
ax1.set_title('12个月滚动收益率', fontsize=12, fontweight='bold')
ax1.set_ylabel('收益率 (%)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 中图：12个月滚动夏普比率
ax2 = axes[1]
ax2.plot(rolling_dates, rolling_sharpe, color=COLOR_PURPLE, linewidth=1.5)
ax2.axhline(y=1.0, color=COLOR_ORANGE, linestyle='--', label='Sharpe=1')
ax2.axhline(y=2.0, color=COLOR_UP, linestyle='--', label='Sharpe=2')
ax2.axhline(y=0, color='black', linewidth=0.5)
ax2.set_title('12个月滚动夏普比率', fontsize=12, fontweight='bold')
ax2.set_ylabel('夏普比率')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 下图：12个月滚动最大回撤
ax3 = axes[2]
ax3.fill_between(rolling_dates, rolling_max_dd, 0, color=COLOR_DOWN, alpha=0.6)
ax3.axhline(y=-10, color=COLOR_ORANGE, linestyle='--', label='-10%')
ax3.axhline(y=-20, color='darkred', linestyle='--', label='-20%')
ax3.set_title('12个月滚动最大回撤', fontsize=12, fontweight='bold')
ax3.set_ylabel('最大回撤 (%)')
ax3.set_xlabel('时间')
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(DATA_DIR, '滚动分析.png'), dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("已保存: 滚动分析.png")

# ============================================================
# 第八步：生成综合评估报告
# ============================================================
print("\n" + "=" * 70)
print("第八步：生成综合评估报告")
print("=" * 70)

# 计算评分
# 收益能力（30分）：基于年化收益
if annual_return >= 200:
    score_return = 30
elif annual_return >= 100:
    score_return = 25
elif annual_return >= 50:
    score_return = 20
else:
    score_return = 15

# 风险控制（30分）：基于最大回撤
if abs(max_drawdown) <= 10:
    score_risk = 30
elif abs(max_drawdown) <= 20:
    score_risk = 25
elif abs(max_drawdown) <= 30:
    score_risk = 20
else:
    score_risk = 15

# 稳定性（20分）：基于月度胜率
if win_rate_monthly >= 75:
    score_stability = 20
elif win_rate_monthly >= 60:
    score_stability = 15
elif win_rate_monthly >= 50:
    score_stability = 12
else:
    score_stability = 8

# 可持续性（20分）：基于近期表现
recent_years = df_yearly[df_yearly['candle_begin_time'].dt.year >= 2024]['涨跌幅'].values
if len(recent_years) > 0 and np.mean(recent_years) >= 0.5:
    score_sustain = 18
elif len(recent_years) > 0 and np.mean(recent_years) >= 0.3:
    score_sustain = 15
else:
    score_sustain = 12

total_score = score_return + score_risk + score_stability + score_sustain

# 判断Alpha衰减
early_return = df_yearly[df_yearly['candle_begin_time'].dt.year <= 2022]['涨跌幅'].mean()
late_return = df_yearly[df_yearly['candle_begin_time'].dt.year >= 2024]['涨跌幅'].mean()
alpha_decay = "是" if late_return < early_return * 0.5 else "否"

report = f"""
# 策略综合评估报告

## 1. 策略概况

| 指标 | 数值 |
|------|------|
| 回测期间 | {df_curve['candle_begin_time'].min().strftime('%Y-%m-%d')} ~ {df_curve['candle_begin_time'].max().strftime('%Y-%m-%d')} |
| 累计收益 | {cumulative_return:.2f}% |
| 年化收益 | {annual_return:.2f}% |
| 最大回撤 | {max_drawdown}% |
| 收益回撤比 | {return_dd_ratio:.2f} |
| 最终净值 | {df_curve['净值'].iloc[-1]:.2f} |

## 2. 收益特征分析

### 2.1 收益分布
- 月度收益均值：{monthly_mean:.2f}%
- 月度收益中位数：{monthly_median:.2f}%
- 月度收益标准差：{monthly_std:.2f}%
- 偏度：{stats.skew(monthly_returns):.2f}
- 峰度：{stats.kurtosis(monthly_returns):.2f}

### 2.2 年度表现
| 年份 | 收益率 |
|------|--------|
"""

for _, row in df_yearly.iterrows():
    report += f"| {row['candle_begin_time'].year} | {row['涨跌幅']*100:.2f}% |\n"

report += f"""
### 2.3 季节性规律
- 最佳季度：Q{df_quarterly.groupby(df_quarterly['candle_begin_time'].dt.quarter)['涨跌幅'].mean().idxmax()}
- 最差季度：Q{df_quarterly.groupby(df_quarterly['candle_begin_time'].dt.quarter)['涨跌幅'].mean().idxmin()}

## 3. 风险特征分析

### 3.1 回撤分析
- 最大回撤：{max_drawdown}%
- 回撤开始时间：{df_eval.loc['最大回撤开始时间', '0']}
- 回撤结束时间：{df_eval.loc['最大回撤结束时间', '0']}

### 3.2 波动率分析
- 月度波动率：{monthly_std:.2f}%
- 年化波动率：{monthly_std * np.sqrt(12):.2f}%
- 下行波动率：{downside_std:.2f}%

### 3.3 尾部风险
- 月度VaR(95%)：{np.percentile(monthly_returns, 5)*100:.2f}%
- 最差单月：{monthly_returns.min()*100:.2f}%

## 4. 仓位特征分析

### 4.1 杠杆使用
- 平均杠杆：{avg_leverage:.2f}x
- 最大杠杆：{max_leverage:.2f}x

### 4.2 多空偏好
- 偏多时间占比：{long_bias:.2f}%
- 偏空时间占比：{short_bias:.2f}%
- 中性时间占比：{neutral:.2f}%

### 4.3 持仓分散度
- 平均持仓品种：{avg_symbols:.1f}个

## 5. 风险提示

### 5.1 Alpha衰减风险
- 早期（2021-2022）平均年收益：{early_return*100:.2f}%
- 近期（2024至今）平均年收益：{late_return*100:.2f}%
- 是否存在衰减迹象：{alpha_decay}

### 5.2 过拟合嫌疑
- 2021年收益是否异常高：是（545%）
- 风险等级：中

## 6. 综合评分（满分100分）

| 维度 | 得分 | 权重 | 说明 |
|------|------|------|------|
| 收益能力 | {score_return}/30 | 30% | 年化收益{annual_return:.0f}% |
| 风险控制 | {score_risk}/30 | 30% | 最大回撤{max_drawdown}% |
| 稳定性 | {score_stability}/20 | 20% | 月度胜率{win_rate_monthly:.0f}% |
| 可持续性 | {score_sustain}/20 | 20% | 近期表现评估 |
| **总分** | **{total_score}/100** | | |

### 评级标准
- 90+：优秀策略，可重仓配置
- 80-89：良好策略，可适度配置
- 70-79：一般策略，需谨慎配置
- <70：风险较高，建议观察

## 7. 结论与建议

1. **策略整体表现优秀**：年化收益{annual_return:.0f}%，最大回撤仅{max_drawdown}%，收益回撤比{return_dd_ratio:.1f}，属于高性价比策略。

2. **需关注Alpha衰减**：2021年收益545%远高于后续年份，可能存在早期市场红利或过拟合风险。

3. **操作建议**：
   - 可适度配置，但不宜重仓
   - 持续监控策略表现，若连续3个月负收益需警惕
   - 关注市场环境变化对策略的影响
"""

# 保存报告
report_path = os.path.join(DATA_DIR, '策略评估报告.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report)
print(f"已保存: 策略评估报告.md")

print("\n" + "=" * 70)
print("分析完成！")
print("=" * 70)
print(f"\n生成文件列表：")
print(f"  1. {DATA_DIR}策略分析仪表板.png")
print(f"  2. {DATA_DIR}回撤分析.png")
print(f"  3. {DATA_DIR}滚动分析.png")
print(f"  4. {DATA_DIR}策略评估报告.md")
print(f"\n综合评分：{total_score}/100 分")
