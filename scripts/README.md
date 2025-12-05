# 股票数据下载工具使用指南

## 📁 文件说明

### 1. `download_stock_data_simple.py` (推荐使用)
**独立版本**，不依赖 FinRL 模块，直接使用 yfinance 和 stockstats。

**特点：**
- ✅ 独立运行，依赖少
- ✅ 快速简洁
- ✅ 包含完整的技术指标
- ✅ 带重试机制

### 2. `download_stock_data.py`
**集成版本**，使用 FinRL 的 YahooFinanceProcessor。

**特点：**
- 使用 FinRL 的数据处理器
- 支持 VIX 和 Turbulence 风险指标（需要多股票数据）
- 需要安装完整的 FinRL 依赖

## 🚀 快速开始

### 安装依赖

```bash
# 基础依赖（独立版本）
pip install pandas numpy yfinance stockstats

# 完整依赖（如需使用 FinRL 版本）
pip install -r requirements.txt
```

### 运行脚本

```bash
# 使用独立版本（推荐）
python scripts/download_stock_data_simple.py

# 使用 FinRL 版本
python scripts/download_stock_data.py
```

## ⚙️ 配置参数

### 修改股票列表

编辑脚本中的 `TICKER_LIST`：

```python
# 单个股票
TICKER_LIST = ['AAPL']

# 多个股票
TICKER_LIST = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

# 道琼斯30成分股
TICKER_LIST = [
    'AAPL', 'MSFT', 'JNJ', 'V', 'WMT', 'JPM', 'PG', 'UNH', 'DIS', 'HD',
    'MA', 'NVDA', 'BAC', 'VZ', 'KO', 'INTC', 'PFE', 'CSCO', 'PEP', 'MRK',
    'ABT', 'CVX', 'NKE', 'ABBV', 'ADBE', 'CRM', 'TMO', 'ACN', 'COST', 'MDT'
]
```

### 修改时间范围

```python
# 方法 1: 使用年数
START_DATE, END_DATE = get_date_range(years=3)  # 过去3年
START_DATE, END_DATE = get_date_range(years=5)  # 过去5年

# 方法 2: 指定具体日期
START_DATE = '2020-01-01'
END_DATE = '2024-12-31'
```

### 修改时间间隔

```python
TIME_INTERVAL = '1d'   # 日线（推荐）
TIME_INTERVAL = '1wk'  # 周线
TIME_INTERVAL = '1mo'  # 月线
TIME_INTERVAL = '1h'   # 小时线（仅限最近60天）
TIME_INTERVAL = '5m'   # 5分钟线（仅限最近7天）
```

## 📊 包含的技术指标

### 趋势指标

| 指标 | 参数 | 说明 |
|------|------|------|
| **MACD** | - | 移动平均收敛散度 |
| **EMA** | 3, 5, 10, 20, 30, 60 | 指数移动平均 |
| **SMA** | 5, 10, 20, 30, 60 | 简单移动平均 |
| **DMA** | - | 双移动平均 |

### 动量指标

| 指标 | 参数 | 说明 |
|------|------|------|
| **RSI** | 6, 12, 24 | 相对强弱指标 |
| **CCI** | 14, 20 | 商品通道指数 |
| **DX** | - | 动向指数 |
| **WR** | - | 威廉指标 |
| **KDJ** | - | 随机指标 (K, D, J) |

### 波动率指标

| 指标 | 参数 | 说明 |
|------|------|------|
| **BOLL** | - | 布林带 (中轨, 上轨, 下轨) |
| **ATR** | 14, 21 | 真实波动幅度均值 |

### 成交量指标

| 指标 | 参数 | 说明 |
|------|------|------|
| **Volume Delta** | - | 成交量变化 |
| **VR** | - | 成交量比率 |
| **VROC** | - | 成交量变化率 |
| **CR** | - | 能量指标 |

### 其他指标

| 指标 | 参数 | 说明 |
|------|------|------|
| **TRIX** | - | 三重指数平滑平均线 |
| **OBV** | - | 能量潮 |
| **MFI** | - | 资金流量指标 |

## 📈 输出数据格式

### 文件位置
```
data/prices/AAPL_2022-11-20_2025-11-19.csv
```

### 文件命名规则
```
{TICKER}_{START_DATE}_{END_DATE}.csv
```

多股票示例：
```
AAPL_MSFT_GOOGL_2022-01-01_2024-12-31.csv
10stocks_2022-01-01_2024-12-31.csv  # 超过3个股票时
```

### 数据列说明

**基础价格数据：**
- `date`: 日期
- `tic`: 股票代码
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `adj close`: 复权收盘价
- `volume`: 成交量

**技术指标：** (70+ 列)
- `macd`, `macds`, `macdh`: MACD 指标
- `ema_3`, `ema_5`, ..., `ema_60`: 不同周期的 EMA
- `sma_5`, `sma_10`, ..., `sma_60`: 不同周期的 SMA
- `rsi_6`, `rsi_12`, `rsi_24`: 不同周期的 RSI
- `cci_14`, `cci_20`: 不同周期的 CCI
- `boll`, `boll_ub`, `boll_lb`: 布林带
- `atr_14`, `atr_21`: ATR
- 以及更多...

### 数据预览示例
```
   date       tic    open    high     low   close  volume   macd  rsi_12  cci_14
0  2022-11-20 AAPL  150.2  151.8  149.5  151.2  82.5M   -0.5    45.2    -25.3
1  2022-11-21 AAPL  151.0  152.5  150.8  152.1  75.3M   -0.3    48.1    -15.8
2  2022-11-22 AAPL  152.3  153.0  151.5  152.8  68.9M   -0.1    51.5     -8.2
...
```

## 🔧 自定义技术指标

### 添加新指标

编辑 `add_technical_indicators` 函数中的指标列表：

```python
# 添加新的 EMA 周期
for period in [3, 5, 10, 20, 30, 60, 120, 200]:  # 添加 120 和 200
    stock[f'ema_{period}']

# 添加新的 RSI 周期
for period in [6, 9, 12, 14, 24]:  # 添加 9 和 14
    stock[f'rsi_{period}']

# 添加其他 stockstats 支持的指标
stock['adx']      # 平均趋向指标
stock['willr']    # 威廉姆斯指标
stock['cci_20']   # 20周期 CCI
```

### Stockstats 指标命名规则

- **带参数的指标**：`指标名_参数`
  - `rsi_6` - 6周期 RSI
  - `ema_10` - 10周期 EMA
  - `cci_14` - 14周期 CCI

- **默认参数的指标**：直接使用名称
  - `macd` - MACD 线
  - `boll` - 布林带中轨
  - `dx` - 动向指数

## ⚠️ 常见问题

### 1. Yahoo Finance 403 错误

**问题：** `HTTP Error 403: Access denied`

**原因：**
- 网络环境限制（防火墙、代理）
- Yahoo Finance API 限流
- 请求过于频繁

**解决方案：**
```python
# 方法 1: 增加重试延迟
time.sleep(5)  # 在重试之间等待更长时间

# 方法 2: 使用代理
import yfinance as yf
ticker = yf.Ticker('AAPL', proxy="http://your-proxy:port")

# 方法 3: 分批下载大量股票
for ticker in TICKER_LIST:
    download_one_ticker(ticker)
    time.sleep(10)  # 每个股票之间等待10秒
```

### 2. NumPy 版本兼容性

**问题：** `numpy 2.0 compatibility error`

**解决方案：**
```bash
pip uninstall -y numpy
pip install "numpy<2.0"
```

### 3. 技术指标计算失败

**问题：** 某些技术指标返回 NaN

**原因：** 数据量不足（如 60 日 EMA 需要至少 60 个数据点）

**解决方案：**
```python
# 下载更长时间范围的数据
START_DATE, END_DATE = get_date_range(years=5)  # 使用5年而不是3年

# 或者使用更短周期的指标
for period in [3, 5, 10, 20]:  # 移除 60, 120 等长周期
    stock[f'ema_{period}']
```

### 4. 内存不足

**问题：** 下载大量股票时内存溢出

**解决方案：**
```python
# 分批处理
BATCH_SIZE = 10
for i in range(0, len(ALL_TICKERS), BATCH_SIZE):
    batch = ALL_TICKERS[i:i+BATCH_SIZE]
    df = download_stock_data(batch, ...)
    save_data(df, batch, ...)
```

## 📝 使用示例

### 示例 1: 下载单个股票（AAPL）过去3年数据
```python
TICKER_LIST = ['AAPL']
START_DATE, END_DATE = get_date_range(years=3)
TIME_INTERVAL = '1d'

df = main()
```

### 示例 2: 下载 FAANG 股票5年数据
```python
TICKER_LIST = ['META', 'AAPL', 'AMZN', 'NFLX', 'GOOGL']
START_DATE, END_DATE = get_date_range(years=5)
TIME_INTERVAL = '1d'

df = main()
```

### 示例 3: 下载特定时间段的周线数据
```python
TICKER_LIST = ['AAPL', 'MSFT']
START_DATE = '2020-01-01'
END_DATE = '2023-12-31'
TIME_INTERVAL = '1wk'

df = main()
```

### 示例 4: 下载最近60天的小时线数据
```python
TICKER_LIST = ['AAPL']
START_DATE, END_DATE = get_date_range(years=1)  # 实际只取最近60天
TIME_INTERVAL = '1h'

df = main()
```

## 🔍 数据质量检查

脚本会自动进行以下检查：

1. **缺失值处理**：自动清理含有 NaN 的行
2. **数据完整性**：确保所有必需列都存在
3. **时间连续性**：验证日期序列的连续性
4. **数据统计**：显示基本统计信息（均值、标准差等）

### 手动检查
```python
# 检查缺失值
df.isnull().sum()

# 检查数据范围
df.describe()

# 检查重复数据
df.duplicated().sum()

# 检查特定日期的数据
df[df['date'] == '2024-01-01']
```

## 📚 参考资料

- **Yahoo Finance API**: https://finance.yahoo.com/
- **yfinance 文档**: https://pypi.org/project/yfinance/
- **stockstats 文档**: https://github.com/jealous/stockstats
- **技术指标说明**: 参见项目根目录的 `YAHOO_FINANCE_DATA_GUIDE.md`

## 🎯 下一步

1. **验证数据**：检查下载的 CSV 文件，确保数据完整
2. **调整指标**：根据需要添加或删除技术指标
3. **扩展股票列表**：下载更多股票数据
4. **数据分析**：使用下载的数据进行策略回测和训练

## ⚙️ 环境限制说明

**注意：** 如果在沙盒环境中运行时遇到 Yahoo Finance 403 错误，这是正常的。该脚本在**本地环境**中应该能够正常工作。

在本地运行前，请确保：
1. ✅ 已安装所有依赖：`pip install pandas numpy yfinance stockstats`
2. ✅ 有稳定的网络连接
3. ✅ 如有代理/防火墙，请配置相应的网络设置
