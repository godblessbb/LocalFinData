# LocalFinData

本仓库提供一个轻量级的数据抓取与可视化工具集，用于定期下载金融行情、计算训练所需的技术指标，并生成 K 线图。核心流程基于 `yfinance` API 拉取行情，随后在本地补充 MACD、EMA、RSI、布林带、ADX、ATR、OBV、SAR、随机指标等字段，方便直接用于策略回测和模型训练。

## 功能概览
- 从 Yahoo Finance 一次性或批量下载指定股票的 OHLCV 数据。
- 自动补充常见技术指标，结果保存为 `data/prices/*.csv` 方便复用。
- 基于保存的数据生成多面板 K 线图（含均线、布林带、MACD、KDJ、RSI、ADX/ATR、成交量、OBV）。

## 快速开始
1. 安装依赖：`pip install -r requirements.txt`。
2. 下载数据并写入本地：
   ```bash
   python scripts/download_prices.py AAPL MSFT --start 2022-01-01 --end 2024-01-01
   ```
   下载完成后会在 `data/prices/` 下生成含指标的 CSV 文件。
3. 生成 K 线图（在 `data` 目录运行）：
   ```bash
   python generate_candlestick_charts.py AAPL --auto-split --max-years 2
   ```

## 代码结构
- `localfindata/`：数据抓取与指标计算的核心代码。
  - `config.py`：默认目录和指标窗口配置。
  - `pipeline.py`：下载行情、补充指标、保存到本地的高阶流程。
  - `indicators.py`：使用 `ta` 库计算训练和可视化所需的技术指标。
- `scripts/download_prices.py`：命令行脚本，用于触发下载和本地缓存。
- `data/generate_candlestick_charts.py`：读取本地 CSV，自动切分时间段并绘制多面板 K 线图。

## 定期抓取建议
可将 `scripts/download_prices.py` 放入定时任务（如 cron、Airflow 或 CI）中，按交易日批量拉取所需标的的最新行情并覆盖/追加到 `data/prices/`。生成的数据可直接供训练管线读取，同时可用 `generate_candlestick_charts.py` 快速检查行情与指标质量。
