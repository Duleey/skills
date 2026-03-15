import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import warnings
import os

warnings.filterwarnings('ignore')

# 配置项
DATA_DIR = os.path.dirname(os.path.abspath(__file__))  # 获取脚本所在目录的绝对路径
OUTPUT_FILE = 'strategy_analysis_report.html'

def load_data():
    """加载并预处理数据"""
    print("正在加载数据...")
    
    # 1. 加载资金曲线
    curve_path = os.path.join(DATA_DIR, '资金曲线.csv')
    if not os.path.exists(curve_path):
        raise FileNotFoundError(f"找不到文件: {curve_path}")
    
    df_curve = pd.read_csv(curve_path, parse_dates=['交易日期'])
    
    # 数值列清洗
    cols_to_float = ['净值', '涨跌幅', '实际杠杆', '印花税', '券商佣金', '总资产', '净值dd2here']
    for col in cols_to_float:
        if col in df_curve.columns:
            if df_curve[col].dtype == 'object':
                df_curve[col] = df_curve[col].str.rstrip('%').astype(float) / 100 if '%' in str(df_curve[col].iloc[0]) else df_curve[col].astype(float)
    
    # 2. 加载周期收益
    dfs_period = {}
    for p in ['月度', '季度', '年度']:
        fname = os.path.join(DATA_DIR, f'{p}账户收益.csv')
        if os.path.exists(fname):
            df = pd.read_csv(fname, parse_dates=['交易日期'])
            if '涨跌幅' in df.columns and df['涨跌幅'].dtype == 'object':
                df['涨跌幅'] = df['涨跌幅'].str.rstrip('%').astype(float) / 100
            dfs_period[p] = df
        else:
            print(f"Warning: {fname} not found.")
            dfs_period[p] = pd.DataFrame()

    # 3. 加载选股结果
    stock_path = os.path.join(DATA_DIR, '选股结果.csv')
    if os.path.exists(stock_path):
        df_stock = pd.read_csv(stock_path, parse_dates=['选股日期'])
    else:
        df_stock = pd.DataFrame()
        
    return df_curve, dfs_period, df_stock

def create_dashboard(df_curve, dfs_period, df_stock):
    """创建 Plotly 交互式仪表板"""
    print("正在生成图表...")
    
    # 创建子图布局
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=(
            "策略净值走势 (对数坐标)", "动态回撤深度",
            "年度收益率", "月度收益热力图",
            "收益率分布", "每日持仓股票数量",
            "交易成本堆叠图", "选股因子排名分布"
        ),
        vertical_spacing=0.08,
        horizontal_spacing=0.1,
        specs=[[{"type": "xy"}, {"type": "xy"}],
               [{"type": "xy"}, {"type": "xy"}],
               [{"type": "xy"}, {"type": "xy"}],
               [{"type": "xy"}, {"type": "xy"}]]
    )

    # ------------------------------------------------
    # 1. 净值曲线 (Row 1, Col 1)
    # ------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=df_curve['交易日期'], 
            y=df_curve['净值'],
            name='策略净值',
            line=dict(color='#0984e3', width=2),
            hovertemplate='日期: %{x}<br>净值: %{y:.3f}<extra></extra>'
        ),
        row=1, col=1
    )
    fig.update_yaxes(type="log", title="净值 (Log)", row=1, col=1)

    # ------------------------------------------------
    # 2. 回撤深度 (Row 1, Col 2)
    # ------------------------------------------------
    dd_col = '净值dd2here' if '净值dd2here' in df_curve.columns else None
    if dd_col:
        fig.add_trace(
            go.Scatter(
                x=df_curve['交易日期'], 
                y=df_curve[dd_col],
                name='回撤',
                fill='tozeroy',
                line=dict(color='#d63031', width=1),
                hovertemplate='日期: %{x}<br>回撤: %{y:.2%}<extra></extra>'
            ),
            row=1, col=2
        )
        # 添加警戒线
        fig.add_hline(y=-0.2, line_dash="dash", line_color="orange", annotation_text="-20%", row=1, col=2)

    # ------------------------------------------------
    # 3. 年度收益 (Row 2, Col 1)
    # ------------------------------------------------
    if not dfs_period['年度'].empty:
        df_y = dfs_period['年度'].copy()
        df_y['year'] = df_y['交易日期'].dt.year
        colors = ['#d63031' if x > 0 else '#00b894' for x in df_y['涨跌幅']]
        
        fig.add_trace(
            go.Bar(
                x=df_y['year'], 
                y=df_y['涨跌幅'],
                name='年度收益',
                marker_color=colors,
                text=df_y['涨跌幅'].apply(lambda x: f'{x:.1%}'),
                textposition='auto',
                hovertemplate='年份: %{x}<br>收益: %{y:.2%}<extra></extra>',
                showlegend=False
            ),
            row=2, col=1
        )

    # ------------------------------------------------
    # 4. 月度收益热力图 (Row 2, Col 2)
    # ------------------------------------------------
    if not dfs_period['月度'].empty:
        df_m = dfs_period['月度'].copy()
        df_m['year'] = df_m['交易日期'].dt.year
        df_m['month'] = df_m['交易日期'].dt.month
        pivot_m = df_m.pivot_table(index='year', columns='month', values='涨跌幅')
        
        # 补全月份
        for m in range(1, 13):
            if m not in pivot_m.columns:
                pivot_m[m] = np.nan
        pivot_m = pivot_m.sort_index(ascending=False)  # 年份倒序
        
        fig.add_trace(
            go.Heatmap(
                z=pivot_m.values,
                x=[f'{m}月' for m in range(1, 13)],
                y=pivot_m.index,
                colorscale='RdYlGn',
                zmid=0,
                text=np.round(pivot_m.values * 100, 1),
                texttemplate="%{text}%",
                hoverongaps=False,
                name='月度收益',
                showscale=False
            ),
            row=2, col=2
        )

    # ------------------------------------------------
    # 5. 收益率分布 (Row 3, Col 1)
    # ------------------------------------------------
    fig.add_trace(
        go.Histogram(
            x=df_curve['涨跌幅'],
            name='收益分布',
            marker_color='#0984e3',
            opacity=0.7,
            nbinsx=100,
            histnorm='probability',
            showlegend=False
        ),
        row=3, col=1
    )
    fig.add_vline(x=0, line_dash="dash", line_color="black", row=3, col=1)

    # ------------------------------------------------
    # 6. 每日持仓数量 (Row 3, Col 2)
    # ------------------------------------------------
    if not df_stock.empty:
        daily_counts = df_stock.groupby('选股日期')['股票代码'].nunique()
        fig.add_trace(
            go.Scatter(
                x=daily_counts.index,
                y=daily_counts.values,
                name='持仓数量',
                mode='lines',
                line=dict(color='#e17055', shape='hv'), # 阶梯线
                hovertemplate='日期: %{x}<br>持仓数: %{y}<extra></extra>'
            ),
            row=3, col=2
        )

    # ------------------------------------------------
    # 7. 交易成本堆叠图 (Row 4, Col 1)
    # ------------------------------------------------
    if '印花税' in df_curve.columns and '券商佣金' in df_curve.columns:
        df_curve['累计印花税'] = df_curve['印花税'].cumsum()
        df_curve['累计佣金'] = df_curve['券商佣金'].cumsum()
        
        fig.add_trace(
            go.Scatter(
                x=df_curve['交易日期'], 
                y=df_curve['累计印花税'],
                name='累计印花税',
                stackgroup='one',
                mode='none',
                fillcolor='rgba(189, 195, 199, 0.5)'
            ),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df_curve['交易日期'], 
                y=df_curve['累计佣金'],
                name='累计佣金',
                stackgroup='one',
                mode='none',
                fillcolor='rgba(127, 140, 141, 0.5)'
            ),
            row=4, col=1
        )

    # ------------------------------------------------
    # 8. 选股因子排名分布 (Row 4, Col 2)
    # ------------------------------------------------
    if not df_stock.empty and '选股因子排名' in df_stock.columns:
        df_stock['year'] = df_stock['选股日期'].dt.year
        fig.add_trace(
            go.Box(
                x=df_stock['year'],
                y=df_stock['选股因子排名'],
                name='因子排名',
                boxpoints=False, # 不显示离群点以保持整洁
                marker_color='#6c5ce7',
                showlegend=False
            ),
            row=4, col=2
        )
        fig.update_yaxes(autorange="reversed", title="排名 (越小越好)", row=4, col=2)

    # ------------------------------------------------
    # 布局调整
    # ------------------------------------------------
    fig.update_layout(
        title={
            'text': "A股策略回测分析报告",
            'y':0.99,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24)
        },
        height=2000,  # 增加高度以容纳更多图表
        width=1400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.005,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=50, r=50, t=100, b=50),
        template="plotly_white",
        hovermode="x unified"
    )

    return fig

def main():
    try:
        # 1. 加载数据
        df_curve, dfs_period, df_stock = load_data()
        
        # 2. 生成图表
        fig = create_dashboard(df_curve, dfs_period, df_stock)
        
        # 3. 导出HTML
        output_path = os.path.join(DATA_DIR, OUTPUT_FILE)
        fig.write_html(output_path)
        print(f"报告已生成: {os.path.abspath(output_path)}")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
