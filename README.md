# LocalFinData

本仓库提供一个轻量级的数据抓取与可视化工具集，用于定期下载金融行情、计算训练所需的技术指标，并生成 K 线图。核心流程基于 `yfinance` API 拉取行情，随后在本地补充 MACD、EMA、RSI、布林带、ADX、ATR、OBV、SAR、随机指标等字段，方便直接用于策略回测和模型训练。

## 功能概览
- 从 Yahoo Finance 一次性或批量下载指定股票的 OHLCV 数据，并本地计算指标。
- 增量抓取 yfinance 提供的所有日级/事件驱动数据（行情、分红拆并、财报日历、研报观点、流通股数等），按股票保存到 `data/ticker/*.csv`。
- 基于保存的数据生成多面板 K 线图（含均线、布林带、MACD、KDJ、RSI、ADX/ATR、成交量、OBV）。

## 快速开始
1. 安装依赖：`pip install -r requirements.txt`。
2. 下载日级/事件数据并写入本地：
   ```bash
   python scripts/download_ticker_info.py AAPL TSLA QQQ
   ```
   默认抓取最近 5 年日线及所有日度更新的事件数据，按股票保存在 `data/ticker/<TICKER>.csv`。
   若需要带指标的行情数据，可在代码中调用 `localfindata.pipeline.download_and_cache()` 指定起止日期和周期。
3. 生成 K 线图（默认读取 `data/prices/`，输出到 `data/candles/`）：
   ```bash
   python scripts/generate_candlestick_charts.py AAPL --auto-split --max-years 2
   ```

## 代码结构
- `localfindata/`：数据抓取与指标计算的核心代码。
  - `config.py`：默认目录和指标窗口配置。
  - `pipeline.py`：下载行情、补充指标、保存到本地的高阶流程。
  - `indicators.py`：使用 `ta` 库计算训练和可视化所需的技术指标。
  - `ticker_info.py`：按股票抓取日级/事件数据（行情、公司行动、研报观点、财报与流通股等）。
- `scripts/download_ticker_info.py`：命令行脚本，增量拉取日度更新的各类数据并按股票保存。
- `scripts/generate_candlestick_charts.py`：读取本地 CSV，自动切分时间段并绘制多面板 K 线图。

## 数据目录约定
- `data/` 用于存放下载得到的 CSV、图片等大体量数据，已通过 `.gitignore` 屏蔽（仅保留下载进度文件 `data/download_progress.json`）。
- 行情缓存默认写入 `data/prices/`，生成的图表默认写入 `data/candles/`，可通过脚本参数覆盖。

## 一键验证示例
要快速确认抓取脚本是否工作，可在项目根目录直接运行下面一条命令，测试标的为 AAPL、TSLA、QQQ：

```bash
python scripts/download_ticker_info.py AAPL TSLA QQQ
```

完成后在 `data/ticker/` 可看到 `AAPL.csv`、`TSLA.csv`、`QQQ.csv` 三个文件；如果此前已有同名文件，脚本会与历史数据取并集做增量更新，而不会覆盖原有包含指标的列。

## 定期抓取建议
可将 `scripts/download_ticker_info.py` 放入定时任务（如 cron、Airflow 或 CI）中，按交易日批量拉取所需标的的最新行情与事件数据并追加到 `data/ticker/`。生成的数据可直接供训练管线读取，同时可用 `generate_candlestick_charts.py` 快速检查行情与指标质量。
