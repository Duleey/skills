# Finance Skills 说明文档

来源仓库：https://github.com/gauss314/skills

开源金融 Skill 合集，遵循 [SKILL.md](https://skills.sh) 标准，为 UCEMA 大学 AI 课程开发。许可证 MIT。

- 本地路径：`finance/skills-main/skills/`
- Skill 总数：**32 个**
- 免 API Key：**28 个**；需申请 Key：**4 个**（FRED、Alpha Vantage、Alpaca、Finnhub）
- 文档语言：多数 SKILL.md 为**西班牙语**，仅 `backtesting` 为英语

> ⚠️ 本文档内容整理自各 SKILL.md 的自述说明，**未逐个实测**。其中爬虫与逆向接口类数据源随时可能失效。

---

## 目录

- [一、全球数据源（21 个）](#一全球数据源21-个)
- [二、阿根廷本地数据（6 个）](#二阿根廷本地数据6-个)
- [三、券商交易（2 个）](#三券商交易2-个)
- [四、量化工具（3 个）](#四量化工具3-个)
- [安装方式](#安装方式)
- [使用建议与风险提示](#使用建议与风险提示)

---

## 一、全球数据源（21 个）

覆盖美国、欧洲、亚洲及全球聚合数据：行情、历史、基本面、筛选器等。

| # | Skill | 类型 | Key | 覆盖标的 |
|---|-------|------|:---:|---------|
| 1 | [fred-macro](#1-fred-macro) | 官方 API | 需要 | 宏观数据 |
| 2 | [alpha-vantage](#2-alpha-vantage) | 官方 API | 需要 | 股票、外汇、大宗、基本面 |
| 3 | [yahoo-finance](#3-yahoo-finance) | 非官方 API | 免 | 股票、外汇、期权、期货、基本面 |
| 4 | [sec-data](#4-sec-data) | 官方 API | 免 | 基本面 |
| 5 | [alpaca-data](#5-alpaca-data) | 官方 API | 需要 | 股票、期权 |
| 6 | [finnhub](#6-finnhub) | 官方 API | 需要 | 股票、外汇、基本面 |
| 7 | [finviz](#7-finviz) | 爬虫 | 免 | 股票、基本面、筛选器 |
| 8 | [macrotrends](#8-macrotrends) | 爬虫 | 免 | 股票、基本面 |
| 9 | [marketscreener](#9-marketscreener) | 爬虫 | 免 | 股票、基本面、筛选器 |
| 10 | [marketwatch](#10-marketwatch) | 爬虫 | 免 | 股票、期权、期货、基本面 |
| 11 | [companiesmarketcap](#11-companiesmarketcap) | 爬虫 | 免 | 股票、ETF |
| 12 | [simplywallst](#12-simplywallst) | 内部 API | 免 | 股票、基本面 |
| 13 | [earningswhispers](#13-earningswhispers) | 公开 API | 免 | 财报电话会 |
| 14 | [barchart](#14-barchart) | 爬虫 | 免 | 股票、期货、基本面 |
| 15 | [nasdaq-data](#15-nasdaq-data) | 内部 API | 免 | 股票、期权、基本面、ETF |
| 16 | [cboe-data](#16-cboe-data) | 公开 API | 免 | 指数、期权、期货 |
| 17 | [investing](#17-investing) | 爬虫 | 免 | 全品类 + 筛选器 |
| 18 | [morningstar](#18-morningstar) | 公开 API | 免 | 筛选器 |
| 19 | [tradingview](#19-tradingview) | 内部 API | 免 | 全品类 + 筛选器 |
| 20 | [google-finance](#20-google-finance) | 逆向 API | 免 | 股票、ETF、期权、基本面 |
| 21 | [historyofmarket](#21-historyofmarket) | 公开 API | 免 | 指数历史、板块、宏观 |

---

### 1. fred-macro

美联储圣路易斯分行 FRED 官方 API，**84 万+ 宏观经济序列**。

- **数据内容**：GDP、CPI、利率、就业、M2、VIX、国债收益率、房贷利率
- **历史深度**：1996 年至今
- **检索能力**：按名称/分类/标签/发布物搜索，支持日/月/季/年频率
- **脚本**：`fetch_series.py`、`search_series.py`、`download_multiple.py`
- **参考**：`API_REFERENCE.md`、`SERIES_REFERENCE.md`

### 2. alpha-vantage

覆盖 **20+ 全球交易所、20 万+ 标的**的老牌金融数据 API。

- **数据内容**：股票、外汇、加密货币、大宗商品（金属/能源/谷物）
- **接口**：TIME_SERIES_INTRADAY/DAILY/WEEKLY/MONTHLY、**50+ 技术指标**、基本面概览、汇率、加密评级
- **限制**：免费版仅 **25 次调用/天**
- **脚本**：`download_timeseries.py`、`download_quotes.py`
- **参考**：`indicators.md`

### 3. yahoo-finance

Yahoo 自 2017 年起无官方 API，本 skill 直接发 HTTP 请求，**不依赖 `yfinance` 等封装库**。

- **数据内容**：股票、ETF、加密、外汇、债券、指数、期权、基本面、新闻
- **核心端点**：
  - `v8/finance/chart` — 历史 OHLCV（免鉴权）
  - `v7/finance/quote` — 实时报价（需 crumb）
  - `v10/finance/quoteSummary` — 基本面，**33 个模块**
  - `v7/finance/options` — 期权链
- **鉴权**：部分端点需 cookie + crumb（CSRF token），skill 内提供 `yahoo_session()` 实现
- **国际后缀**：`.BA` 阿根廷、`.SA` 巴西、`.MX` 墨西哥、`-USD` 加密、`=X` 外汇、`^` 指数
- **速率限制**：约 2 req/s 安全，3-5 req/s 易触发 429，>10 req/s 会被临时封 IP
- **脚本**：`batch_fetch.py`（令牌桶限流 + 线程池，推荐）、`fetch_all.py`、`fetch_quote.py`、`download_historical.py`

### 4. sec-data

美国证监会 EDGAR 官方数据，从 XBRL facts 提取结构化财报。

- **覆盖范围**：所有向 SEC 提交备案的公司（10K/10Q/8K），含使用 IFRS 的国际公司
- **历史深度**：近 5 年以上，含季报与年报
- **输出**：利润表、资产负债表、现金流量表，JSON/CSV
- **特色**：同时支持 US-GAAP 与 IFRS，自动做会计科目映射
- **脚本**：`fetch_financials.py`
- **参考**：`FINANCIALS_REFERENCE.md`

### 5. alpaca-data

Alpaca 券商的行情数据 API，**5000+ 美股**及加密、期权。

- **数据内容**：快照、K 线（OHLCV）、逐笔成交、报价
- **数据源**：IEX feed
- **特色**：多资产类别统一符号规范化；历史数据免费额度充足，实时数据有限制
- **脚本**：`download_stock_bars.py`、`download_crypto_bars.py`、`download_options.py`
- **参考**：`options_reference.md`

### 6. finnhub

**32 个免费 REST 端点**，覆盖美股/欧股/英股 + 外汇 + 加密。

- **数据内容**：报价、公司概况、财报、财报日历、分析师评级趋势、目标价、内部交易、同业对比、ESG 评分、新闻、经济数据
- **实时**：支持 WebSocket
- **限制**：免费版 **60 次/分钟**
- **脚本**：`finnhub_client.py`、`finnhub_cli.py`、`download_multiple.py`
- **参考**：`ENDPOINTS.md`

### 7. finviz

Finviz 网站爬虫，**8K+ 美股**（NYSE/NASDAQ/AMEX）+ 加拿大。

- **基本面**：P/E、EPS、PEG、利润率
- **技术面**：RSI、MACD、SMA、ATR
- **其他**：内部交易、机构持股、新闻
- **筛选器**：支持市值、P/E、行业、涨跌幅等条件在线筛选
- **脚本**：`fetch_quote.py`
- **参考**：`QUOTE_REFERENCE.md`

### 8. macrotrends

**约 6500 个标的**，含来自 30+ 国家的国际 ADR。

- **数据内容**：三大报表、财务比率、员工数
- **历史深度**：**15+ 年**（报表 5-30 年）
- **细分**：盈利能力、负债、利润率、每股数据、分部数据
- **脚本**：`fetch_financials.py`
- **参考**：`STATEMENTS_REFERENCE.md`、`MARKETS_REFERENCE.md`

### 9. marketscreener

数据源自 S&P Capital IQ，**2 万+ 全球股票**含 ADR。

- **数据内容**：报价、公司概况、三大报表、估值、分析师共识、新闻
- **特色**：**财报电话会记录列表**、内部交易、股东名册、公司治理、财报日历、持股结构
- **脚本**：`marketscreener_client.py`、`marketscreener_cli.py`
- **参考**：`ENDPOINTS.md`

### 10. marketwatch

美股及全球 ADR。

- **数据内容**：报价、三大报表、SEC 备案、分析师预估、期权链、历史 OHLCV
- **特色**：可比公司面板、按分类的筛选器、**期货数据**（指数/大宗/利率/货币）
- **脚本**：`fetch_marketwatch.py`
- **参考**：`REFERENCE.md`

### 11. companiesmarketcap

全球财务排行榜，使用站点原生 CSV 下载能力。

- **排名维度**：市值、盈利、营收、员工数、P/E、利润率、资产、负债、现金
- **其他**：股票历史市值、ETF 持仓
- **脚本**：`fetch_cmc.py`
- **参考**：`REFERENCE.md`

### 12. simplywallst

**12 万+ 全球股票，106 个交易所**，走网站前端的内部 REST API。

- **雪花评分**（1-5 星）：估值、收益、健康、过往、未来、管理层
- **数据内容**：同业估值对比、**19+ 年股息历史**及预测、财务健康分、内部交易、目标价、P/E / P/B / ROE 分析
- **脚本**：`fetch_sws.py`
- **参考**：`REFERENCE.md`；资产：`26-06-04-ticker-snapshot.csv`

### 13. earningswhispers

**3.35 万+ 全球股票**的财报电话会数据，公开 API 无需鉴权。

- **核心能力**：**完整财报电话会记录**（含管理层陈述 + 分析师问答）
- **优势**：无反爬机制、无激进限流
- **元数据**：日期、财季、参与人
- **测试情况**：作者称在 60+ 标的上验证通过（AAPL、MSFT、GGAL、SHEL、TM、VALE 等）
- **脚本**：`ew_client.py`、`ew_cli.py`
- **参考**：`REFERENCES.md`

### 14. barchart

**3 万+ 美股及全球 ADR**，外加期货。

- **数据内容**：延迟报价（15-20 分钟）、基本面、内部交易汇总、分析师评级、财报预估、三大报表明细、公司概况
- **期货**：指数、大宗商品、货币、利率
- **脚本**：`fetch_barchart.py`
- **参考**：`API.md`、`REFERENCE.md`

### 15. nasdaq-data

Nasdaq.com 的内部 REST API。

- **数据内容**：报价、**做空兴趣**（半月度）、财报、**13F 机构持仓**、内部交易、期权链、股息、财报日历、新闻
- **特色**：可查询将该股列为前十大持仓的 ETF
- **脚本**：`fetch_nasdaq.py`
- **参考**：`REFERENCE.md`

### 16. cboe-data

芝加哥期权交易所公开 API。

- **指数**：VIX、SPX、DJ、RUT
- **期货**：VX（VIX 期货链）、债券期货（IBHY、IBIG）、方差（VA）
- **期权**：含希腊字母
- **行情**：**1 分钟盘中 K 线**、各交易所市场汇总（BZX/BYX/EDGX/EDGA）、最活跃股票与期权、符号查询、历史 HV/IV
- **脚本**：`fetch_cboe.py`
- **参考**：`REFERENCE.md`

### 17. investing

Investing.com HTML 爬虫，全球覆盖。

- **覆盖规模**：8.1 万+ 股票、1 万+ 指数、2400 货币、344 大宗、3 万+ ETF、4000+ 加密
- **数据内容**：报价、历史 OHLCV、基本面（利润表/资产负债表/现金流/比率）、股息、财报、公司概况
- **延迟**：15-20 分钟
- **依赖**：需 `curl_cffi` 绕过 Cloudflare
- **脚本**：`fetch_investing.py`
- **参考**：`REFERENCE.md`

### 18. morningstar

晨星筛选器公开 JSON API，无需鉴权。

- **覆盖规模**：**53 个 universe、10.2 万+ 标的、39 个国家**
- **主要市场**：NYSE (2343)、Nasdaq (3741)、法兰克福 (1.4万+)、东京 (3989)、上海 (2365)、深圳 (2934)、香港 (2757)、印度 (5000+)、韩国 (2877)、巴西 (2070)、墨西哥 (2233)、伦敦 (1333)，以及阿根廷 CEDEAR (469) 等 30+ 市场
- **每标的 33 个字段**：价格、市值、比率、**1d/1w/1m/3m/6m/12m/36m/60m/120m 多周期收益**、负债、股息率、板块、行业
- **特色**：多币种、多国家、多语言
- **脚本**：`fetch_morningstar.py`
- **参考**：`REFERENCE.md`；资产：`DATA_POINTS.md`、`UNIVERSES.md`

### 19. tradingview

内部公开 API，无需鉴权，**全球覆盖**。

- **覆盖规模**：10 万+ 股票、5 万+ 加密、指数、外汇、债券
- **Scanner API**：**约 300 列**——报价、预计算技术指标（RSI/MACD/EMA/SMA/枢轴点）、聚合买卖评级、估值、财务、财报及预测、分析师目标价、股息、持股、做空兴趣、收益率
- **Symbol Search v3**：支持 ISIN/CUSIP/**CIK**（可与 SEC EDGAR 关联）
- **新闻**：每股约 200 条（道琼斯/路透/MarketBeat）
- **HTML 抓取**：16+ 子页（技术面、三大报表、期权链、预测、观点）
- **筛选器**：SQL 式大批量筛选，支持过滤 + 排序 + 分页
- **规模**：**24 个 CLI 模式**，4 个独立 HTTP 端点
- **脚本**：`fetch_tradingview.py`
- **参考**：8 份文档（COOKBOOK、SCANNER_COLUMNS、SCANNER_FILTERS、MARKETS_EXCHANGES、NEWS_API、SYMBOL_SEARCH、HTML_SCRAPING、REFERENCE）

### 20. google-finance

通过逆向工程发现的内部 RPC API（`batchexecute`），**无需 Key、无需鉴权**。

- **规模**：**19 个 CLI 模式**，覆盖 14+ 个 RPC ID
- **数据内容**：报价（美股 + 阿根廷 BCBA）、财报（约 22KB 多期三大报表）、财报历史、技术评级、公司描述、同业、带缩略图的新闻
- **独有优势**：
  - **免费 1 分钟与 5 分钟盘中 OHLC**（其他免费源普遍不提供）
  - **分析师推荐逐家明细**（如高盛，含机构名 + 目标价 + 日期）
  - 公司**实际办公地址** + 员工数
  - **一次调用取全球指数**（道指、标普、纳指、VIX、DAX、富时、日经、恒生、IBEX、CAC）
  - 板块热力图
- **风险**：⚠️ 非官方 API，生产使用前必读 `LIMITATIONS_TROUBLESHOOTING.md`
- **脚本**：`fetch_gfinance.py`
- **参考**：5 份文档 + 3 个 JSON 资产（`rpc_ids.json`、`chunk_layouts.json`、`consent_cookies.json`）

### 21. historyofmarket

来自 historyofmarket.com 的 **88 个预生成历史数据集**（CC BY 4.0，无需 Key）。

- **标普 500**：**追溯至 1871 年**——Shiller CAPE、EPS、带成因标注的回撤、前瞻 PE、驱动因素分解、成分股及变更、板块
- **纳斯达克**：综合指数（1971→）、纳斯达克 100（1985→）——价格、波动率、VXN、回撤、滚动 5 年
- **其他指数**：道琼斯（1914→）、SOX 半导体（1994→，含 30 只成分股与 SMH 持仓）
- **板块 ETF**：XLK、XLF，含 2018/2023 年 GICS 重分类与持仓
- **Magnificent 7**：集中度、相关性、AI 资本开支、**AI 估值对比互联网泡沫**
- **宏观**：NBER 衰退期、收益率曲线、AIAE 股票配置比例
- **脚本**：`reconstitute_sp500.py`、`reconstitute_ndx.py`（重建历史成分股）、`sector_rotation.py`
- **参考**：7 份文档（SP500/NASDAQ_100 方法论、回撤波动率、Mag7、板块 ETF、估值指标、大盘）

---

## 二、阿根廷本地数据（6 个）

针对阿根廷市场，中国用户一般用不上，列出备查。

### 1. bcra-macro

阿根廷央行货币统计 API v4.0，**638 条国家级序列**（总计 1220 条）。

- 汇率（官方/批发/MEP/CCL）、储备、货币政策利率、BADLAR、CER、UVA、LELIQ
- 基础货币、M1/M2/M3、存款、贷款、通胀
- 数据自 **1996 年**起
- **参考**：`VARIABLES.md`

### 2. data912

阿根廷市场实时行情。

- 本地股票、CEDEAR、债券、票据、期权、MEP、CCL；美股实时与波动率
- **刷新频率 20 秒**，限流 120 req/min
- 历史 OHLCV、筛选器、阿根廷公司基本面
- **脚本**：`download_historical.py`
- **参考**：股票/债券/CEDEAR 三份标的清单

### 3. mae

阿根廷电子公开市场（批发），**17 个端点**。

- 固定收益：LECAP、BONCAP、BOPREAL、硬美元债、企业债
- 回购（CAARS 比索 / CAUSD 美元，按期限）、REPO、掉期、FORWORD
- 批发外汇、美元远期合约（DDF）、ARS-MAE 指数、一级招标、机构公告、用于 TIR/MD 曲线的资金流
- **脚本**：`fetch_mae.py`

### 4. byma

阿根廷证券交易所，**9 个端点**。

- 权益：主板股票、CEDEAR
- 固收：主权债、LECAP/BONCAP、企业债、回购
- 衍生品：期权、SENEBI
- 指数历史 OHLCV（MERVAL、BURCAP）、**债券技术说明书含摊还计划**
- **脚本**：`fetch_byma.py`

### 5. cafci

阿根廷共同基金商会数据。

- 截至 2026-06：**1152 只基金、4615 个份额类别**
- 分类：货币市场、固收、权益、混合、中小企业、总回报、基建、封闭式、ASG、RG900
- 四类数据：JSON 目录（费率/ID/元数据）、每日 XLSX 快照（净值/规模/市占/变动）、个基 markdown 说明（各期 TNA 收益）、持仓构成
- **脚本**：`fetch_cafci.py`

### 6. indec

阿根廷国家统计局官方时间序列 API（`apis.datos.gob.ar/series`）。

- **约 4250 条序列**，来自 INDEC、BCRA、经济部、劳工部、DGEYC
- **无需 Key、无鉴权、无验证码**
- **作者称是本仓库最稳定、文档最完善的 API**：有官方文档、开源代码、不破坏 ABI 的政策
- 覆盖：全国 CPI（总体/核心/管制价/分章节分地区）、EMAE 经济活动指数、制造业 IPI、建筑业 ISAC、分地区失业率、贫困线、出口、RIPTE 工资、最低工资、汇率、储备、REM 市场预期
- **独有能力**：
  - 服务端 **7 种内置变换**（`percent_change_a_year_ago` = 同比通胀、`percent_change_since_beginning_of_year` = 年初至今）
  - **6 种时间聚合**（日→月→年，支持均值/求和/期末/最小/最大）
  - 单次请求取多条序列
- **规模**：19 个 CLI 模式，9 个指标快捷方式（`ipc`、`emae`、`salarios`、`dolar`、`reservas` 等）
- **脚本**：`fetch_indec.py`
- **参考**：10 份文档（含 30+ 配方的 COOKBOOK）+ 5 个 JSON 资产

---

## 三、券商交易（2 个）

> 🚨 **高风险**：这两个 skill 可以**下真实订单、动用真实资金**。使用前务必确认处于模拟盘环境。

### 1. alpaca-trading

Alpaca 券商 REST API，美国。

- **模式**：paper trading（模拟，免费）与 live trading（实盘）
- **标的**：美股、加密货币、期权
- **订单类型**：市价、限价、止损、追踪止损；支持**做空**、**多腿期权**
- **其他**：持仓、账户、自选列表、交易日历
- **行情**：IEX feed
- **官方 SDK**：`alpaca-py`
- **脚本**：`check_account.py`、`check_positions.py`、`place_order.py`

### 2. primary

阿根廷 Matba ROFEX 衍生品交易所 API。

- **标的**：期货（美元、大豆、玉米、小麦）、期货期权、股票、债券、CEDEAR
- **鉴权**：Token 制，有效期 24 小时
- **接口**：REST + **WebSocket**（实时行情、报单/撤单、成交回报）
- **风控 API**：HTTP Basic Auth，查询持仓与账户报告
- **无 SDK**：直接用 `requests` 发 HTTP
- **脚本**：`check_account.py`、`check_positions.py`、`instruments.py`、`market_data.py`、`place_order.py`、`websocket_md.py`、`websocket_orders.py`、`websocket_send_order.py`

---

## 四、量化工具（3 个）

本合集最有价值的部分。**全部只依赖 numpy / pandas / scipy**，不需要 Riskfolio-Lib、PyPortfolioOpt、cvxpy 等重型金融库。

### 1. option-pricing

扁平 Python + numpy 向量化的期权定价库，**9 种方法**覆盖香草期权、波动率微笑与尾部风险。

| 方法 | 类型 | 适用 |
|------|------|------|
| Black-Scholes | 解析解 | 欧式 |
| Binomial CRR | 二叉树 | 美式 + 欧式 |
| Trinomial Boyle | 三叉树 | 美式 + 欧式 |
| Monte Carlo（对偶变量） | 模拟 | 欧式 |
| Longstaff-Schwartz | 模拟 | 美式 |
| Bjerksund-Stensland 2002 / BAW | 解析解 | 美式 |
| Heston 1993 | 随机波动率 | 波动率微笑（傅里叶积分） |
| Bates 1996 | Heston + Merton 跳跃 | 微笑 + **崩盘风险** |

- **附加能力**：解析希腊字母（delta/gamma/vega/theta/rho）、二分法求隐含波动率、风险中性 P(ITM) 与 P(Profit)
- **CLI**：15 个模式，含 `validate` 与 `bench`
- **性能**（作者实测，Python 3.14 + numpy 2.4.4）：BS 2.4 µs/次（41.9 万次/秒）、P(ITM) 1.1 µs/次、Heston 398 µs/次、Bates 6.2 ms/次、二叉树 N=500 5.6 ms/次
- **验证**：对照 Hull 教材第 9 版例题 15.6 与 21.1，及看跌看涨平价，声称 15/15 通过
- **脚本**：`option_pricing.py`
- **参考**：`REFERENCE.md`、`theory.md`；资产：`defaults.json`、`validation_cases.json`

### 2. backtesting

面向量化研究的学术级回测框架。

- **30+ 风险绩效比率**：Sharpe、Sortino、Calmar、Kelly、MaxDD、Ulcer、Recovery Factor、Rachev A/B/C、Common Sense Ratio、Payoff Ratio、Profit Factor、盈亏比、VaR（经验/正态/Johnson SU）、cVaR、跟踪误差、信息比率
- **10 类指标**：趋势跟踪、振荡器、逆势、资金流、组合、离散计数、季节性、统计、参照、基本面
- **事件驱动引擎**：8 个内置策略（SMA 交叉、RSI 均值回归、MACD、布林带逆势、ADX 趋势、动量、成长+动量组合）
- **Markowitz**：有效前沿 + 随机组合抽样 + 蒙特卡洛模拟
- **前瞻模拟**：Johnson SU 边际分布 + t/高斯 Copula + 漂移项 + 扇形图投影
- **Walk-forward 交叉验证**：扩展窗口 + 样本内外间隔
- **压力测试**：参数化情景冲击
- **基本面分析**：Altman Z 破产预测、Piotroski F 九项质量评分、杜邦五因子 ROE 分解
- **验证套件**：`py scripts/validate.py`，31 项检查分 4 个层级（CLI 模式、数学一致性、边界情况、回归）
- **脚本**：`engine.py`、`backtesting.py`、`ratios.py`、`indicators.py`、`simulations.py`、`copulas.py`、`distributions.py`、`forward.py`、`fundamental_ratios.py`、`validate.py`
- **测试**：`tests/test_ratios.py`
- **参考**：6 份文档（BACKTESTING_THEORY、RATIOS、SIMULATIONS、FEATURES、OTHER_FEATURES、VALIDATION）
- **资产**：标普 500 价格/收益率、多资产价格、多组策略收益基准 CSV

### 3. portfolio

组合构建与优化，源自课程材料（MPT、NCO、Black-Litterman）。

**三条技术路线：**

1. **Markowitz 均值方差**
   - `scipy.optimize` 凸优化，或蒙特卡洛模拟
   - 有效前沿 + CML 资本市场线
   - CML 支持**杠杆与去杠杆**（如 60% 切线组合 + 40% 无风险，Sharpe 不变）

2. **Black-Litterman 完整流程**
   - 市场隐含风险厌恶系数（delta）
   - CAPM 逆推先验收益
   - 绝对观点与相对观点 + 置信度
   - Idzorek 方法构造不确定性矩阵 Ω
   - 贝叶斯后验收益与协方差 → 在后验上做 Markowitz

3. **HRP / HERC / NCO 层次方法**
   - 相关性转距离聚类（single/complete/average/ward）
   - 递归二分风险平价
   - 嵌套聚类优化：簇内 + 簇间 Markowitz
   - 支持**按标的与按资产类别的约束**

**辅助模块：**

- **风险度量**：VaR、CVaR、MAD、MSV、最大回撤、CDaR、分散化比率、风险贡献
- **协方差估计**：历史、Ledoit-Wolf、OAS、EWMA

**其他信息：**

- **CLI 12 个模式**：`markowitz`、`montecarlo`、`frontier`、`cml`、`bl-prior`、`bl`、`hrp`、`herc`、`nco`、`nco-con`、`clusters`、`risk`、`stats`
- **验证**：28 项测试，含数学一致性检查，并用真实 yfinance 数据对照 PyPortfolioOpt / Riskfolio-Lib 输出
- **脚本**：`portfolio.py`、`black_litterman.py`、`hierarchical.py`、`risk_measures.py`、`covariance.py`、`cli.py`
- **参考**：`PORTFOLIO_THEORY.md`、`BLACK_LITTERMAN.md`、`HIERARCHICAL.md`、`RISK_MEASURES.md`
- **理论出处**：Markowitz (1952)、Black-Litterman (1992)、Idzorek (2005)、Lopez de Prado (2016, 2019)、Pfitzinger & Katzke (2019)、Meucci (2006)

---

## 安装方式

```bash
# 安装单个 skill 到当前项目
npx skills add gauss314/skills --skill fred-macro

# 安装全部
npx skills add gauss314/skills --all

# 全局安装（所有项目可用）
npx skills add gauss314/skills --skill fred-macro -g
```

安装后会得到四类内容：

| 目录 | 加载时机 | 用途 |
|------|---------|------|
| `SKILL.md` | 调用 skill 时载入上下文 | 必需，快速上手说明 |
| `references/` | **按需加载** | 详细文档、目录、字段参考 |
| `scripts/` | 按需执行 | 可运行脚本 |
| `assets/` | 按需读取 | 模板、配置、样例数据 |

`references/`、`scripts/`、`assets/` 遵循**渐进式披露**原则，仅在需要时加载以节省 token。

---

## 使用建议与风险提示

### 选型建议

| 需求 | 推荐 Skill |
|------|-----------|
| 免费历史 OHLCV | yahoo-finance、alpaca-data |
| **免费 1 分钟盘中数据** | google-finance、cboe-data |
| 全球大批量筛选 | tradingview、morningstar |
| 财报原文 | earningswhispers（完整记录）、marketscreener |
| 权威财报数据 | sec-data（XBRL 官方） |
| 宏观数据 | fred-macro（美国 84 万序列） |
| 超长历史（19 世纪至今） | historyofmarket |
| 做空兴趣 / 13F | nasdaq-data |
| 期权定价与希腊字母 | option-pricing |
| 策略回测 | backtesting |
| 资产配置 | portfolio |

### 风险提示

1. **接口稳定性**：多数免费数据源是**爬虫或非官方接口**，随时可能失效。
   - Yahoo 自 2017 年起无官方 API
   - Google Finance 是逆向出的 `batchexecute` RPC
   - Investing.com 需 `curl_cffi` 绕 Cloudflare
   - 相对最稳的是官方 API：sec-data、fred-macro、indec

2. **速率限制**：Yahoo 建议 ≤2 req/s；Alpha Vantage 免费仅 25 次/天；Finnhub 60 次/分钟。批量抓取务必使用限流（yahoo-finance 的 `batch_fetch.py` 已实现令牌桶）。

3. **交易风险**：`alpaca-trading` 与 `primary` 会真实下单。Alpaca 请确认使用 paper trading 端点；Primary 无模拟环境概念，需格外谨慎。

4. **数据核对**：涉及金额、收益率、比率的计算，建议至少用一个独立数据源交叉验证，尤其注意除权除息调整、货币单位、时区与交易日边界。

5. **依赖安装**：工具类 skill 需 `numpy` / `pandas` / `scipy`；`investing` 额外需 `curl_cffi`；`alpaca-trading` 建议装 `alpaca-py`。

6. **语言**：SKILL.md 多为西班牙语，阅读时可能需要翻译。

### 未经验证的部分

本文档信息来自各 SKILL.md 与仓库 README 的**作者自述**，包括：

- 各类覆盖规模数字（标的数、序列数、交易所数）
- option-pricing 的性能基准与 Hull 教材验证结论
- backtesting 的 31 项检查、portfolio 的 28 项测试通过情况
- 各数据源当前是否仍然可用

如需在生产或投研中使用，建议先对目标 skill 做实际连通性与数据准确性测试。
