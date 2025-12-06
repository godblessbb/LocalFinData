# yfinance 提供的数据类型（基于官方文档）

> 依据 yfinance 官方 README 与文档列出的接口功能整理，方便在本项目中参考可抓取/查询的数据类型。

## 行情与衍生品
- **历史行情（OHLCV）**：通过 `Ticker.history()`/`download()` 获取开高低收、成交量，支持日内到月度等多种 `interval`。
- **企业行动 (corporate actions)**：分红 `dividends`、拆/并股 `splits`、资本重组 `capitalGains`。
- **期权链 (Option chains)**：`Ticker.options` 获取可用到期日；`option_chain(expiry)` 返回 `calls`、`puts` 两张期权报价表。

## 基本面与报表
- **公司信息档案**：`Ticker.info`/`fast_info` 提供公司概览、行业、交易所、货币、流通股本等。
- **财报报表**：`income_stmt`、`balance_sheet`、`cashflow` 及其 `quarterly_*` 变体。
- **财报日历**：`calendar`/`earnings_dates` 提供财报发布与预告日期。
- **盈利与预估**：`earnings`（年度）、`quarterly_earnings`、`earnings_trend`、`revenue_forecasts`。
- **分析师观点**：`recommendations`、`recommendations_summary`、`upgrade_downgrade_history`、`analyst_price_targets`。
- **可持续性指标**：`sustainability`（ESG 相关数据）。

## 持股与交易相关
- **大股东/机构持股**：`major_holders`、`institutional_holders`、`mutualfund_holders`。
- **内部人交易**：`insider_transactions`、`insider_purchases`、`insider_roster_holders`。

## 价格衍生数据
- **分红/拆股时间序列**：`dividends`、`splits` 单独访问。
- **成交数据细分**：`shares`（当前/历史流通股）、`futures`（可用期货链）、`isin`（国际证券识别码）。

## 指数/外汇/加密
- yfinance 同一套接口也支持指数、外汇、加密货币等代码（通过传入相应 ticker，常见格式如 `^GSPC`、`EURUSD=X`、`BTC-USD`）。

> 更多细节可参考 yfinance 官方 README（https://github.com/ranaroussi/yfinance）和文档页面的最新说明。
