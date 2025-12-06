# yfinance 提供的数据类型（基于官方文档）

> 按“更新频率/增量策略”分组，便于为不同数据设计独立的更新脚本。所有接口与字段均来自 yfinance 官方 README 与文档页面。

## 高频（日内/分钟级，需高频增量）
- **历史行情 `Ticker.history()` / `yfinance.download()`（分钟级）**：支持 `1m`、`2m`、`5m`、`15m`、`30m`、`60m`、`90m`、`1h` 等 `interval`。官方限制：`1m` 仅可拉取最近 7 天；`2m~90m/1h` 最长约 60 天；更长区间需使用日线以上的 `interval`。可通过 `prepost=True` 同时取盘前/盘后。适合日内/高频策略的滚动更新。
- **期权链 `Ticker.options` / `option_chain(expiry)`**：获取可用到期日列表以及对应到期日的 `calls`/`puts` 报价表（含隐含波动率、希腊值、成交量等），期权报价在交易时段内会高频变化，建议按分钟或更短周期增量拉取。
- **快速报价与元数据 `Ticker.fast_info`**：提供接近实时的最新价、成交量、前收等基础字段（字段随官方支持而变），可在分钟级任务中轻量校验最新行情。

## 中频（按日/事件更新）
- **历史行情 `history`/`download`（日线及以上）**：`1d`、`5d`、`1wk`、`1mo`、`3mo` 等区间，可回溯至 Yahoo Finance 提供的最早历史（通常覆盖多年到数十年）。适合日线批量增量；注意超过 60 天的窗口请使用日线或更高 `interval`。
- **公司行动 `dividends` / `splits` / `capitalGains`**：分红、拆并股等事件，按公告/生效日更新，历史可回溯多年。适合与日线行情一并按日刷新。
- **财报日历 `calendar` / `earnings_dates`**：财报发布日期与指引，事件驱动型数据，通常按日检查增量即可。
- **分析师观点与目标价**：`recommendations`、`recommendations_summary`、`upgrade_downgrade_history`、`analyst_price_targets`，通常在新研报发布时更新，按日批处理合适。
- **盈利与预估**：`earnings`（年度）、`quarterly_earnings`、`earnings_trend`、`revenue_forecasts`，随财报/指引更新，日度监测足够。
- **成交与流通股数据 `shares`**：包含当前及历史流通股数，日度调整即可。

## 低频（季度/年度，变动稀少）
- **财务报表**：`income_stmt`、`balance_sheet`、`cashflow` 及对应 `quarterly_*` 变体，按季度/年度公布，适合季度刷新。
- **持股信息**：`major_holders`、`institutional_holders`、`mutualfund_holders`，通常在 13F/持仓披露后更新，季度级增量即可。
- **内部人交易**：`insider_transactions`、`insider_purchases`、`insider_roster_holders`，披露频率低，可按季度或更长周期抓取。
- **可持续性与基本信息**：`sustainability`、`info`/`fast_info` 中的静态字段（行业、货币、ISIN 等），变动罕见，半年或年度刷新即可。
- **期货/其他静态映射**：`futures`（可用期货合约列表）、`isin` 等标识符，通常长期不变。

## 资产类型支持
yfinance 同一套接口支持股票、ETF、指数、外汇、加密货币等代码格式（如 `^GSPC`、`EURUSD=X`、`BTC-USD`），可按上述频率策略执行增量。

## 时间跨度与速率注意事项
- **时间跨度**：分钟级请求受官方时间窗限制（`1m` 最长 7 天、`2m/5m/15m/30m/90m/1h` 最长约 60 天）。超过该跨度请改用日线以上 `interval` 后再自行重采样。
- **节流与并发**：官方文档提示需遵守 Yahoo Finance 的访问限制，过于频繁的请求可能被临时封禁；建议使用 `yfinance.download()` 批量合并多个 ticker、开启本地缓存/会话复用，并在高频任务中控制并发与重试间隔。
- **前后复权**：可通过 `auto_adjust=True`/`actions=True` 取得复权价与公司行动数据，便于同步写入本地缓存。
