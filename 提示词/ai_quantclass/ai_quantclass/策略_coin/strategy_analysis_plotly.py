#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化策略全面分析脚本 - Plotly交互式版本
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from scipy import stats
import warnings
import os

warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
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

# 清洗涨跌幅列
for df in [df_monthly, df_quarterly, df_yearly]:
    if df['涨跌幅'].dtype == 'object':
        df['涨跌幅'] = df['涨跌幅'].str.rstrip('%').astype(float) / 100

# 基本信息
print(f"\n回测时间: {df_curve['candle_begin_time'].min()} ~ {df_curve['candle_begin_time'].max()}")
print(f"数据点数: {len(df_curve):,} 条（小时级）")
print(f"最终净值: {df_curve['净值'].iloc[-1]:.2f}")

# ============================================================
# 计算统计指标
# ============================================================
cumulative_return = (df_curve['净值'].iloc[-1] - 1) * 100
annual_return = float(str(df_eval.loc['年化收益', '0']).rstrip('%'))
max_drawdown = float(str(df_eval.loc['最大回撤', '0']).rstrip('%'))
return_dd_ratio = float(df_eval.loc['年化收益/回撤比', '0'])
monthly_returns = df_monthly['涨跌幅'].values
monthly_mean = np.mean(monthly_returns) * 100
monthly_std = np.std(monthly_returns) * 100
win_rate_monthly = (monthly_returns > 0).sum() / len(monthly_returns) * 100

# 风险调整收益
sharpe_ratio = annual_return / (monthly_std * np.sqrt(12)) if monthly_std > 0 else 0
negative_months = monthly_returns[monthly_returns < 0]
downside_std = np.std(negative_months) * 100 if len(negative_months) > 0 else 0
sortino_ratio = annual_return / (downside_std * np.sqrt(12)) if downside_std > 0 else 0

print(f"\n【核心指标】")
print(f"  累计收益: {cumulative_return:.2f}% | 年化收益: {annual_return:.2f}%")
print(f"  最大回撤: {max_drawdown}% | 收益回撤比: {return_dd_ratio:.2f}")
print(f"  夏普比率: {sharpe_ratio:.2f} | 月度胜率: {win_rate_monthly:.1f}%")

# ============================================================
# 第二步：生成12图综合仪表板 (Plotly)
# ============================================================
print("\n" + "=" * 70)
print("第二步：生成Plotly交互式仪表板")
print("=" * 70)

# 降采样以提高性能
sample_rate = max(1, len(df_curve) // 5000)
df_sampled = df_curve.iloc[::sample_rate].copy()

# 创建9子图布局（colspan合并后实际是9个子图）
fig = make_subplots(
    rows=3, cols=4,
    subplot_titles=(
        '净值曲线（对数坐标）', '回撤曲线',  # 第一行2个
        '年度收益', '季度收益热力图', '月度收益',  # 第二行3个
        '收益率分布', '杠杆比例', '多空比例', '持仓品种数'  # 第三行4个
    ),
    specs=[
        [{"colspan": 2}, None, {"colspan": 2}, None],
        [{"type": "bar"}, {"type": "heatmap"}, {"colspan": 2}, None],
        [{"type": "histogram"}, {"type": "scatter"}, {"type": "scatter"}, {"type": "scatter"}]
    ],
    vertical_spacing=0.08,
    horizontal_spacing=0.05
)

# ---- 第一行 ----
# 1. 净值曲线（对数坐标）
fig.add_trace(
    go.Scatter(
        x=df_sampled['candle_begin_time'],
        y=df_sampled['净值'],
        mode='lines',
        name='净值',
        line=dict(color=COLOR_MAIN, width=1),
        hovertemplate='时间: %{x}<br>净值: %{y:.2f}<extra></extra>'
    ),
    row=1, col=1
)

# 添加里程碑线
for milestone in [2, 5, 10, 50, 100, 200, 300]:
    if df_curve['净值'].max() >= milestone:
        fig.add_hline(y=milestone, line_dash="dot", line_color=COLOR_GRAY,
                      opacity=0.5, row=1, col=1,
                      annotation_text=f"{milestone}x", annotation_position="right")

# 2. 回撤曲线
fig.add_trace(
    go.Scatter(
        x=df_sampled['candle_begin_time'],
        y=df_sampled['净值dd2here'] * 100,
        mode='lines',
        fill='tozeroy',
        name='回撤',
        line=dict(color=COLOR_DOWN, width=1),
        fillcolor='rgba(231, 76, 60, 0.4)',
        hovertemplate='时间: %{x}<br>回撤: %{y:.2f}%<extra></extra>'
    ),
    row=1, col=3
)

# 添加回撤参考线
for level, color in [(-5, COLOR_ORANGE), (-10, COLOR_DOWN), (-15, 'darkred'), (-20, 'black')]:
    fig.add_hline(y=level, line_dash="dash", line_color=color, opacity=0.5, row=1, col=3)

# ---- 第二行 ----
# 3. 年度收益柱状图
years = df_yearly['candle_begin_time'].dt.year.values
yearly_returns = df_yearly['涨跌幅'].values * 100
colors_yearly = [COLOR_UP if r > 0 else COLOR_DOWN for r in yearly_returns]

fig.add_trace(
    go.Bar(
        x=years,
        y=yearly_returns,
        name='年度收益',
        marker_color=colors_yearly,
        text=[f'{r:.0f}%' for r in yearly_returns],
        textposition='outside',
        hovertemplate='%{x}年<br>收益: %{y:.2f}%<extra></extra>'
    ),
    row=2, col=1
)

# 4. 季度收益热力图
df_quarterly['year'] = df_quarterly['candle_begin_time'].dt.year
df_quarterly['quarter'] = df_quarterly['candle_begin_time'].dt.quarter
pivot_q = df_quarterly.pivot(index='year', columns='quarter', values='涨跌幅') * 100

fig.add_trace(
    go.Heatmap(
        z=pivot_q.values,
        x=['Q1', 'Q2', 'Q3', 'Q4'],
        y=pivot_q.index.astype(str),
        colorscale='RdYlGn',
        zmid=0,
        text=np.round(pivot_q.values, 0),
        texttemplate='%{text:.0f}%',
        textfont={"size": 10},
        hovertemplate='%{y} %{x}<br>收益: %{z:.1f}%<extra></extra>',
        colorbar=dict(title='%', len=0.3, y=0.5)
    ),
    row=2, col=2
)

# 5. 月度收益柱状图
df_monthly['month_label'] = df_monthly['candle_begin_time'].dt.strftime('%Y-%m')
monthly_rets = df_monthly['涨跌幅'].values * 100
colors_monthly = [COLOR_UP if r > 0 else COLOR_DOWN for r in monthly_rets]

fig.add_trace(
    go.Bar(
        x=df_monthly['month_label'],
        y=monthly_rets,
        name='月度收益',
        marker_color=colors_monthly,
        hovertemplate='%{x}<br>收益: %{y:.2f}%<extra></extra>'
    ),
    row=2, col=3
)

# ---- 第三行 ----
# 6. 收益率分布直方图
hourly_returns = df_curve['涨跌幅'].dropna() * 100

fig.add_trace(
    go.Histogram(
        x=hourly_returns,
        nbinsx=100,
        name='收益分布',
        marker_color=COLOR_MAIN,
        opacity=0.7,
        hovertemplate='收益区间: %{x}<br>频次: %{y}<extra></extra>'
    ),
    row=3, col=1
)

# 添加均值线
fig.add_vline(x=hourly_returns.mean(), line_dash="dash", line_color=COLOR_DOWN,
              row=3, col=1, annotation_text=f"均值:{hourly_returns.mean():.3f}%")

# 7. 杠杆比例时序图
fig.add_trace(
    go.Scatter(
        x=df_sampled['candle_begin_time'],
        y=df_sampled['leverage_ratio'],
        mode='lines',
        name='杠杆',
        line=dict(color=COLOR_PURPLE, width=1),
        hovertemplate='时间: %{x}<br>杠杆: %{y:.2f}x<extra></extra>'
    ),
    row=3, col=2
)

avg_leverage = df_curve['leverage_ratio'].mean()
fig.add_hline(y=avg_leverage, line_dash="dash", line_color=COLOR_DOWN,
              row=3, col=2, annotation_text=f"均值:{avg_leverage:.2f}x")

# 8. 多空比例时序图
fig.add_trace(
    go.Scatter(
        x=df_sampled['candle_begin_time'],
        y=df_sampled['long_short_ratio'],
        mode='lines',
        name='多空比',
        line=dict(color=COLOR_ORANGE, width=1),
        hovertemplate='时间: %{x}<br>多空比: %{y:.2f}<extra></extra>'
    ),
    row=3, col=3
)

fig.add_hline(y=1.0, line_dash="solid", line_color='black', row=3, col=3)
fig.add_hline(y=1.2, line_dash="dash", line_color=COLOR_UP, opacity=0.5, row=3, col=3)
fig.add_hline(y=0.8, line_dash="dash", line_color=COLOR_DOWN, opacity=0.5, row=3, col=3)

# 9. 持仓品种数量（使用面积图代替柱状图，避免数据点过多显示问题）
fig.add_trace(
    go.Scatter(
        x=df_sampled['candle_begin_time'],
        y=df_sampled['symbol_long_num'],
        mode='lines',
        fill='tozeroy',
        name='多头品种',
        line=dict(color=COLOR_UP, width=1),
        fillcolor='rgba(46, 204, 113, 0.5)',
        hovertemplate='时间: %{x}<br>多头: %{y}<extra></extra>'
    ),
    row=3, col=4
)

fig.add_trace(
    go.Scatter(
        x=df_sampled['candle_begin_time'],
        y=-df_sampled['symbol_short_num'],
        mode='lines',
        fill='tozeroy',
        name='空头品种',
        line=dict(color=COLOR_DOWN, width=1),
        fillcolor='rgba(231, 76, 60, 0.5)',
        hovertemplate='时间: %{x}<br>空头: %{customdata}<extra></extra>',
        customdata=df_sampled['symbol_short_num']
    ),
    row=3, col=4
)

# 更新布局
fig.update_layout(
    height=1000,
    width=1600,
    title=dict(
        text='<b>量化策略综合分析仪表板</b><br>' +
             f'<sup>累计收益: {cumulative_return:.0f}% | 年化: {annual_return:.0f}% | 最大回撤: {max_drawdown}% | 夏普: {sharpe_ratio:.2f}</sup>',
        x=0.5,
        font=dict(size=20)
    ),
    showlegend=False,
    template='plotly_white',
    hovermode='x unified'
)

# 设置净值曲线Y轴为对数坐标，自定义刻度
max_nav = df_curve['净值'].max()
tick_values = [1, 2, 5, 10, 20, 50, 100, 200, 300, 400]
tick_values = [v for v in tick_values if v <= max_nav * 1.2]
fig.update_yaxes(
    type="log",
    tickmode='array',
    tickvals=tick_values,
    ticktext=[str(v) for v in tick_values],
    range=[np.log10(0.8), np.log10(max_nav * 1.1)],
    row=1, col=1
)
fig.update_yaxes(range=[min(df_sampled['净值dd2here'] * 100) - 2, 2], row=1, col=3)
fig.update_yaxes(range=[0, min(3, df_curve['long_short_ratio'].quantile(0.99))], row=3, col=3)

# Plotly配置：启用全屏和更多工具
plotly_config = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToAdd': ['toggleSpikelines'],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': '策略分析图表',
        'height': 1200,
        'width': 1800,
        'scale': 2
    }
}

# 保存HTML（带全屏支持）
dashboard_path = os.path.join(DATA_DIR, '策略分析仪表板.html')
fig.write_html(dashboard_path, config=plotly_config, full_html=True, include_plotlyjs=True)
print(f"已保存: 策略分析仪表板.html")

# ============================================================
# 第三步：回撤分析图
# ============================================================
print("\n生成回撤分析图...")

fig_dd = make_subplots(
    rows=2, cols=1,
    subplot_titles=('回撤深度分布', '回撤时序图'),
    vertical_spacing=0.12
)

# 上图：回撤深度分布
dd_values = df_curve['净值dd2here'].values * 100
dd_negative = dd_values[dd_values < 0]

fig_dd.add_trace(
    go.Histogram(
        x=dd_negative,
        nbinsx=50,
        name='回撤分布',
        marker_color=COLOR_DOWN,
        opacity=0.7
    ),
    row=1, col=1
)

for level, color, name in [(-5, COLOR_ORANGE, '-5%'), (-10, 'darkred', '-10%'), (-15, 'black', '-15%')]:
    fig_dd.add_vline(x=level, line_dash="dash", line_color=color, row=1, col=1,
                     annotation_text=name)

# 下图：回撤时序图
fig_dd.add_trace(
    go.Scatter(
        x=df_sampled['candle_begin_time'],
        y=df_sampled['净值dd2here'] * 100,
        mode='lines',
        fill='tozeroy',
        name='回撤',
        line=dict(color=COLOR_DOWN, width=1),
        fillcolor='rgba(231, 76, 60, 0.5)'
    ),
    row=2, col=1
)

# 标注最大回撤
min_dd_idx = df_curve['净值dd2here'].idxmin()
min_dd_time = df_curve.loc[min_dd_idx, 'candle_begin_time']
min_dd_value = df_curve.loc[min_dd_idx, '净值dd2here'] * 100

fig_dd.add_annotation(
    x=min_dd_time,
    y=min_dd_value,
    text=f"最大回撤<br>{min_dd_value:.2f}%",
    showarrow=True,
    arrowhead=2,
    row=2, col=1
)

fig_dd.update_layout(
    height=700,
    width=1200,
    title=dict(text='<b>回撤分析</b>', x=0.5),
    showlegend=False,
    template='plotly_white'
)

fig_dd.write_html(os.path.join(DATA_DIR, '回撤分析.html'), config=plotly_config)
print("已保存: 回撤分析.html")

# ============================================================
# 第四步：滚动分析图
# ============================================================
print("\n生成滚动分析图...")

# 计算12个月滚动指标
df_monthly_sorted = df_monthly.sort_values('candle_begin_time').reset_index(drop=True)
rolling_window = 12

rolling_returns = []
rolling_sharpe = []
rolling_max_dd = []

for i in range(rolling_window, len(df_monthly_sorted) + 1):
    window_data = df_monthly_sorted.iloc[i-rolling_window:i]
    cum_ret = (1 + window_data['涨跌幅']).prod() - 1
    rolling_returns.append(cum_ret * 100)

    mean_ret = window_data['涨跌幅'].mean()
    std_ret = window_data['涨跌幅'].std()
    sharpe = (mean_ret * 12) / (std_ret * np.sqrt(12)) if std_ret > 0 else 0
    rolling_sharpe.append(sharpe)

    cum_nav = (1 + window_data['涨跌幅']).cumprod()
    max_dd = (cum_nav / cum_nav.cummax() - 1).min() * 100
    rolling_max_dd.append(max_dd)

rolling_dates = df_monthly_sorted['candle_begin_time'].iloc[rolling_window-1:].values

fig_rolling = make_subplots(
    rows=3, cols=1,
    subplot_titles=('12个月滚动收益率', '12个月滚动夏普比率', '12个月滚动最大回撤'),
    vertical_spacing=0.1
)

# 滚动收益率
fig_rolling.add_trace(
    go.Scatter(
        x=rolling_dates,
        y=rolling_returns,
        mode='lines',
        fill='tozeroy',
        name='滚动收益',
        line=dict(color=COLOR_MAIN, width=2),
        fillcolor='rgba(52, 152, 219, 0.3)'
    ),
    row=1, col=1
)
fig_rolling.add_hline(y=0, line_color='black', row=1, col=1)
fig_rolling.add_hline(y=100, line_dash="dash", line_color=COLOR_GRAY, row=1, col=1)

# 滚动夏普
fig_rolling.add_trace(
    go.Scatter(
        x=rolling_dates,
        y=rolling_sharpe,
        mode='lines',
        name='滚动夏普',
        line=dict(color=COLOR_PURPLE, width=2)
    ),
    row=2, col=1
)
fig_rolling.add_hline(y=1.0, line_dash="dash", line_color=COLOR_ORANGE, row=2, col=1,
                       annotation_text="Sharpe=1")
fig_rolling.add_hline(y=2.0, line_dash="dash", line_color=COLOR_UP, row=2, col=1,
                       annotation_text="Sharpe=2")

# 滚动最大回撤
fig_rolling.add_trace(
    go.Scatter(
        x=rolling_dates,
        y=rolling_max_dd,
        mode='lines',
        fill='tozeroy',
        name='滚动回撤',
        line=dict(color=COLOR_DOWN, width=2),
        fillcolor='rgba(231, 76, 60, 0.4)'
    ),
    row=3, col=1
)
fig_rolling.add_hline(y=-10, line_dash="dash", line_color=COLOR_ORANGE, row=3, col=1)
fig_rolling.add_hline(y=-20, line_dash="dash", line_color='darkred', row=3, col=1)

fig_rolling.update_layout(
    height=800,
    width=1200,
    title=dict(text='<b>滚动分析（12个月窗口）</b>', x=0.5),
    showlegend=False,
    template='plotly_white'
)

fig_rolling.write_html(os.path.join(DATA_DIR, '滚动分析.html'), config=plotly_config)
print("已保存: 滚动分析.html")

# ============================================================
# 第五步：年度对比详细图
# ============================================================
print("\n生成年度对比图...")

fig_yearly = make_subplots(
    rows=2, cols=2,
    subplot_titles=('年度收益对比', '季度收益热力图', '月度收益热力图', '累计净值曲线'),
    specs=[
        [{"type": "bar"}, {"type": "heatmap"}],
        [{"type": "heatmap"}, {"type": "scatter"}]
    ],
    vertical_spacing=0.12,
    horizontal_spacing=0.1
)

# 年度收益
fig_yearly.add_trace(
    go.Bar(
        x=years,
        y=yearly_returns,
        marker_color=colors_yearly,
        text=[f'{r:.0f}%' for r in yearly_returns],
        textposition='outside'
    ),
    row=1, col=1
)

# 季度热力图
fig_yearly.add_trace(
    go.Heatmap(
        z=pivot_q.values,
        x=['Q1', 'Q2', 'Q3', 'Q4'],
        y=pivot_q.index.astype(str),
        colorscale='RdYlGn',
        zmid=0,
        text=np.round(pivot_q.values, 0),
        texttemplate='%{text:.0f}%',
        showscale=False
    ),
    row=1, col=2
)

# 月度热力图
df_monthly['year'] = df_monthly['candle_begin_time'].dt.year
df_monthly['month'] = df_monthly['candle_begin_time'].dt.month
pivot_m = df_monthly.pivot(index='year', columns='month', values='涨跌幅') * 100

fig_yearly.add_trace(
    go.Heatmap(
        z=pivot_m.values,
        x=[f'{m}月' for m in range(1, 13)],
        y=pivot_m.index.astype(str),
        colorscale='RdYlGn',
        zmid=0,
        text=np.round(pivot_m.values, 0),
        texttemplate='%{text:.0f}',
        textfont={"size": 8},
        showscale=True,
        colorbar=dict(title='%', len=0.4, y=0.25)
    ),
    row=2, col=1
)

# 累计净值曲线
fig_yearly.add_trace(
    go.Scatter(
        x=df_sampled['candle_begin_time'],
        y=df_sampled['净值'],
        mode='lines',
        line=dict(color=COLOR_MAIN, width=2)
    ),
    row=2, col=2
)

fig_yearly.update_yaxes(type="log", row=2, col=2)

fig_yearly.update_layout(
    height=800,
    width=1400,
    title=dict(text='<b>年度/季度/月度收益对比</b>', x=0.5),
    showlegend=False,
    template='plotly_white'
)

fig_yearly.write_html(os.path.join(DATA_DIR, '年度对比分析.html'), config=plotly_config)
print("已保存: 年度对比分析.html")

# ============================================================
# 输出统计汇总
# ============================================================
print("\n" + "=" * 70)
print("统计指标汇总")
print("=" * 70)

print(f"""
┌─────────────────────────────────────────────────────────────────┐
│                        策略核心指标                              │
├─────────────────────────────────────────────────────────────────┤
│  累计收益率    │ {cumulative_return:>10.2f}%  │  年化收益率   │ {annual_return:>8.2f}%  │
│  最大回撤      │ {max_drawdown:>10}%  │  收益回撤比   │ {return_dd_ratio:>8.2f}   │
│  夏普比率      │ {sharpe_ratio:>10.2f}   │  索提诺比率   │ {sortino_ratio:>8.2f}   │
│  月度胜率      │ {win_rate_monthly:>10.2f}%  │  月均收益     │ {monthly_mean:>8.2f}%  │
└─────────────────────────────────────────────────────────────────┘
""")

print("\n【年度收益】")
for _, row in df_yearly.iterrows():
    year = row['candle_begin_time'].year
    ret = row['涨跌幅'] * 100
    bar = '█' * int(min(ret/10, 50))
    print(f"  {year}: {ret:>7.2f}% {bar}")

# ============================================================
# 完成
# ============================================================
print("\n" + "=" * 70)
print("分析完成！")
print("=" * 70)
print(f"""
生成的交互式HTML文件：
  1. {DATA_DIR}策略分析仪表板.html  (主仪表板)
  2. {DATA_DIR}回撤分析.html
  3. {DATA_DIR}滚动分析.html
  4. {DATA_DIR}年度对比分析.html

请在浏览器中打开查看交互式图表！
""")
