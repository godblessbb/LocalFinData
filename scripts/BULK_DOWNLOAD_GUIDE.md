# 美股所有股票批量下载指南

## 📋 功能说明

`download_all_us_stocks.py` 脚本可以自动下载美股所有股票（排除 ETF 和基金）过去5年的历史数据。

### 特点

- ✅ **自动获取股票列表** - 从 S&P 500、NASDAQ、NYSE 获取所有股票代码
- ✅ **过滤 ETF 和基金** - 只下载普通股票
- ✅ **批量下载** - 一次性下载约 3000-4000 只股票
- ✅ **断点续传** - 支持中断后继续下载
- ✅ **单独保存** - 每只股票保存为单独的 CSV 文件
- ✅ **技术指标** - 自动计算 MACD, EMA, SMA, RSI, BOLL 等指标
- ✅ **进度跟踪** - 实时显示下载进度

## 🚀 快速开始

### 1. 运行脚本

```bash
python scripts/download_all_us_stocks.py
```

### 2. 确认下载

脚本会显示将要下载的股票数量和预计时间：

```
准备下载 3542 只股票的数据
每只股票将保存为单独的 CSV 文件
预计需要时间: 118.1 分钟 (假设每只2秒)

是否继续? (y/n):
```

输入 `y` 开始下载。

### 3. 等待完成

下载过程中会显示实时进度：

```
[1/3542] 下载 AAPL... ✓ 成功
[2/3542] 下载 MSFT... ✓ 成功
[3/3542] 下载 GOOGL... ✓ 成功
...
```

## 📁 数据存储

### 文件结构

```
data/
├── prices/
│   ├── AAPL.csv      # 苹果股票数据
│   ├── MSFT.csv      # 微软股票数据
│   ├── GOOGL.csv     # 谷歌股票数据
│   ├── ...           # 其他股票
│   └── (约3000-4000个文件)
└── download_progress.json  # 下载进度记录
```

### CSV 文件格式

每个 CSV 文件包含以下列：

**基础数据：**
- `date` - 日期 (YYYY-MM-DD)
- `tic` - 股票代码
- `open` - 开盘价
- `high` - 最高价
- `low` - 最低价
- `close` - 收盘价
- `volume` - 成交量

**技术指标：**
- `macd`, `macds`, `macdh` - MACD 指标
- `ema_5`, `ema_10`, `ema_20`, `ema_30`, `ema_60` - 指数移动平均
- `sma_5`, `sma_10`, `sma_20`, `sma_30`, `sma_60` - 简单移动平均
- `rsi_6`, `rsi_12`, `rsi_24` - 相对强弱指标
- `boll`, `boll_ub`, `boll_lb` - 布林带

## ⚙️ 配置选项

### 修改时间范围

编辑脚本中的 `main()` 函数：

```python
# 默认：过去5年
start_date = end_date - timedelta(days=365 * 5)

# 修改为过去3年
start_date = end_date - timedelta(days=365 * 3)

# 或指定具体日期
START_DATE = '2020-01-01'
END_DATE = '2024-12-31'
```

### 修改批次大小

```python
# 默认每批10只股票
download_all_stocks(tickers, START_DATE, END_DATE, batch_size=10)

# 修改为每批20只（更快，但可能更容易失败）
download_all_stocks(tickers, START_DATE, END_DATE, batch_size=20)

# 修改为每批5只（更慢，但更稳定）
download_all_stocks(tickers, START_DATE, END_DATE, batch_size=5)
```

### 添加更多技术指标

编辑 `download_single_stock()` 函数，在计算指标部分添加：

```python
# CCI
for period in [14, 20]:
    stock[f'cci_{period}']

# ATR
for period in [14, 21]:
    stock[f'atr_{period}']

# OBV
stock['obv']
```

## 🔄 断点续传

### 工作原理

脚本会在 `data/download_progress.json` 中保存进度：

```json
{
  "completed": ["AAPL", "MSFT", "GOOGL", ...],
  "failed": [
    {"ticker": "BADTICKER", "error": "无数据"}
  ]
}
```

### 继续下载

如果下载过程中断（Ctrl+C、网络问题等），只需再次运行脚本：

```bash
python scripts/download_all_us_stocks.py
```

脚本会自动跳过已完成的股票，继续下载剩余的。

### 重新开始

如果想重新下载所有股票：

```bash
# 删除进度文件
rm data/download_progress.json

# 重新运行
python scripts/download_all_us_stocks.py
```

## 📊 数据统计

### 预期结果

- **股票数量**: 3000-4000 只
- **每个文件大小**: 约 50-200 KB
- **总数据量**: 约 200-500 MB
- **下载时间**:
  - 网速快: 1-2 小时
  - 网速慢: 3-4 小时

### 数据质量

- **时间范围**: 5 年（约 1260 个交易日）
- **数据完整性**: 跳过数据不足 100 天的股票
- **价格精度**: 2 位小数
- **技术指标**: 自动计算，失败时保存原始数据

## 🛠️ 故障排除

### 问题 1: 无法获取股票列表

**症状：**
```
⚠ 无法获取 NASDAQ 列表: ...
⚠ 无法获取 NYSE 列表: ...
```

**解决方案：**
- 检查网络连接
- 检查防火墙设置
- 尝试使用 VPN

### 问题 2: 下载失败率高

**症状：**
```
失败: 1245
成功: 1856
```

**解决方案：**
1. 减小批次大小：`batch_size=5`
2. 增加重试次数（修改脚本）
3. 分时段下载（避开高峰期）

### 问题 3: 技术指标计算失败

**症状：**
```
⚠ AAPL 技术指标计算失败: ...
```

**影响：** 仍会保存原始价格数据，只是缺少技术指标

**解决方案：** 可以后续使用其他脚本补充计算技术指标

### 问题 4: 内存不足

**症状：** 程序崩溃或变慢

**解决方案：**
1. 减小批次大小：`batch_size=5`
2. 关闭其他程序释放内存
3. 分批下载（手动修改股票列表）

## 📈 使用下载的数据

### 读取单个股票

```python
import pandas as pd

# 读取苹果股票数据
aapl = pd.read_csv('data/prices/AAPL.csv')
print(aapl.head())
```

### 读取所有股票

```python
import pandas as pd
import glob

# 读取所有 CSV 文件
all_files = glob.glob('data/prices/*.csv')

# 合并所有股票
all_stocks = pd.concat([pd.read_csv(f) for f in all_files], ignore_index=True)

print(f"总共 {len(all_stocks)} 行数据")
print(f"包含 {all_stocks['tic'].nunique()} 只股票")
```

### 筛选特定股票

```python
# 只读取科技股
tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA']
tech_data = pd.concat([
    pd.read_csv(f'data/prices/{ticker}.csv')
    for ticker in tech_stocks
    if os.path.exists(f'data/prices/{ticker}.csv')
], ignore_index=True)
```

### 数据分析示例

```python
import pandas as pd
import matplotlib.pyplot as plt

# 读取数据
aapl = pd.read_csv('data/prices/AAPL.csv', parse_dates=['date'])

# 绘制价格走势
plt.figure(figsize=(12, 6))
plt.plot(aapl['date'], aapl['close'], label='Close Price')
plt.plot(aapl['date'], aapl['ema_20'], label='EMA 20')
plt.plot(aapl['date'], aapl['sma_60'], label='SMA 60')
plt.xlabel('Date')
plt.ylabel('Price ($)')
plt.title('AAPL Stock Price')
plt.legend()
plt.grid(True)
plt.show()
```

## ⚡ 性能优化

### 提高下载速度

1. **增加批次大小**
   ```python
   batch_size=20  # 从默认的10增加到20
   ```

2. **减少暂停时间**
   ```python
   time.sleep(0.5)  # 从1秒减少到0.5秒
   ```

3. **并行下载**（高级）
   使用多线程或多进程（需要修改脚本）

### 减少磁盘空间

1. **只保存必要列**
   ```python
   # 只保存价格数据，不保存技术指标
   result_df = df[['date', 'tic', 'open', 'high', 'low', 'close', 'volume']]
   ```

2. **压缩 CSV 文件**
   ```python
   result_df.to_csv(filepath, index=False, compression='gzip')
   # 保存为 .csv.gz 文件，节省 70-80% 空间
   ```

## 📝 常见问题

### Q1: 为什么有些知名股票没有下载？

**A:** 可能的原因：
- 是 ETF（如 SPY、QQQ）被过滤掉了
- 股票代码包含特殊字符被过滤
- 下载失败（查看 `download_progress.json`）

**解决：** 手动添加到股票列表

### Q2: 可以下载其他国家的股票吗？

**A:** 可以，但需要修改获取股票列表的部分。例如港股、A股需要不同的数据源。

### Q3: 数据会自动更新吗？

**A:** 不会。需要定期手动运行脚本更新数据。建议：
- 每周运行一次更新最新数据
- 或使用 cron job 自动定时运行

### Q4: 如何只下载特定行业的股票？

**A:** 修改 `get_all_us_stocks()` 函数，添加行业过滤逻辑，或手动创建股票列表。

## 🔗 相关脚本

- `download_stock_data_minimal.py` - 单个或少量股票下载（推荐用于测试）
- `download_stock_data_standalone.py` - 备用下载方案
- `download_stock_data_simple.py` - 原始版本

## ⚠️ 注意事项

1. **网络稳定性** - 下载大量股票需要稳定的网络连接
2. **Yahoo Finance 限制** - 避免过于频繁的请求，可能被临时封禁
3. **磁盘空间** - 确保有至少 1GB 可用空间
4. **数据准确性** - Yahoo Finance 数据仅供参考，重要决策请使用付费数据源
5. **法律合规** - 遵守 Yahoo Finance 使用条款，仅用于个人研究

## 💡 最佳实践

1. **分时段下载** - 避开市场开盘时间，选择晚上或周末下载
2. **定期备份** - 下载完成后备份 `data/prices/` 文件夹
3. **验证数据** - 随机抽查几只股票的数据完整性
4. **增量更新** - 首次全量下载后，后续只更新新数据
5. **错误处理** - 保存失败列表，后续单独处理

---

**祝您下载顺利！** 🎉
