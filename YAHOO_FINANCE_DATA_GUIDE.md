# Yahoo Finance 高级功能数据维度完整清单

## 1. 基础数据维度（OHLCV）

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| timestamp | datetime | 时间戳 | 2023-01-03 09:30:00 |
| open | float | 开盘价 | 150.25 |
| high | float | 最高价 | 152.80 |
| low | float | 最低价 | 149.50 |
| close | float | 收盘价 | 151.30 |
| volume | int | 成交量 | 85423000 |
| tic | string | 股票代码 | AAPL |

---

## 2. 支持的时间间隔

| 间隔代码 | 含义 | 数据量（1年） | 用途 |
|---------|------|--------------|------|
| 1m | 1分钟 | ~97,000 | 日内交易、高频策略 |
| 5m | 5分钟 | ~19,400 | 日内交易 |
| 15m | 15分钟 | ~6,500 | 日内交易 |
| 30m | 30分钟 | ~3,250 | 日内交易 |
| 1h | 1小时 | ~1,625 | 日内/短线 |
| 1d | 1天 | ~252 | 中长线策略 ⭐ |
| 1wk | 1周 | ~52 | 长线策略 |
| 1mo | 1月 | ~12 | 超长线策略 |

---

## 3. 技术指标维度（30+指标）

### 3.1 趋势类指标

| 指标 | 全称 | 参数 | 含义 | 交易信号 |
|------|------|------|------|---------|
| macd | Moving Average Convergence Divergence | (12,26,9) | MACD值 | >0看多，<0看空 |
| macds | MACD Signal | (12,26,9) | 信号线 | MACD上穿信号线=金叉 |
| macdh | MACD Histogram | (12,26,9) | 柱状图 | 正值增大=上涨动能强 |
| ema_5 | Exponential Moving Average | 5日 | 5日指数均线 | 价格上穿EMA=看多 |
| ema_10 | EMA | 10日 | 10日指数均线 | 短期趋势 |
| ema_20 | EMA | 20日 | 20日指数均线 | 中期趋势 |
| ema_60 | EMA | 60日 | 60日指数均线 | 长期趋势 |
| sma_5 | Simple Moving Average | 5日 | 5日简单均线 | 支撑/阻力 |
| sma_10 | SMA | 10日 | 10日简单均线 | 短期趋势 |
| sma_20 | SMA | 20日 | 20日简单均线 | 中期趋势 |
| sma_60 | SMA | 60日 | 60日简单均线 | 长期趋势 |
| dma | Dual Moving Average | - | 双均线差值 | >0多头，<0空头 |

### 3.2 动量/振荡类指标

| 指标 | 全称 | 参数 | 范围 | 交易信号 |
|------|------|------|------|---------|
| rsi_6 | Relative Strength Index | 6日 | 0-100 | >70超买，<30超卖 |
| rsi_12 | RSI | 12日 | 0-100 | >70超买，<30超卖 |
| rsi_30 | RSI | 30日 | 0-100 | >70超买，<30超卖 ⭐ |
| cci_6 | Commodity Channel Index | 6日 | ±∞ | >100超买，<-100超卖 |
| cci_12 | CCI | 12日 | ±∞ | >100超买，<-100超卖 |
| cci_30 | CCI | 30日 | ±∞ | >100超买，<-100超卖 ⭐ |
| dx_6 | Directional Index | 6日 | 0-100 | >25趋势强 |
| dx_12 | DX | 12日 | 0-100 | >25趋势强 |
| dx_30 | DX | 30日 | 0-100 | >25趋势强 ⭐ |
| wr_6 | Williams %R | 6日 | -100-0 | >-20超买，<-80超卖 |
| wr_10 | Williams %R | 10日 | -100-0 | >-20超买，<-80超卖 |

### 3.3 波动率指标

| 指标 | 全称 | 参数 | 含义 | 用途 |
|------|------|------|------|------|
| boll | Bollinger Band Middle | (20,2) | 布林带中轨 | 支撑/阻力 |
| boll_ub | Bollinger Band Upper | (20,2) | 布林带上轨 | 超买区域 ⭐ |
| boll_lb | Bollinger Band Lower | (20,2) | 布林带下轨 | 超卖区域 ⭐ |
| atr | Average True Range | 14日 | - | 止损距离设置 |
| kdjk | KDJ K值 | (9,3,3) | 0-100 | >80超买，<20超卖 |
| kdjd | KDJ D值 | (9,3,3) | 0-100 | K>D金叉 |
| kdjj | KDJ J值 | (9,3,3) | 0-100 | 超前指标 |

### 3.4 成交量指标

| 指标 | 全称 | 含义 | 用途 |
|------|------|------|------|
| volume_delta | Volume Change | 成交量变化 | 资金流向 |
| volume_-1_s | Volume Shift | 前一日成交量 | 对比参考 |
| close_delta | Close Change | 收盘价变化 | 涨跌幅 |
| close_-1_s | Close Shift | 前一日收盘价 | 对比参考 |
| vr | Volume Ratio | 成交量比率 | 买卖力度对比 |
| vroc | Volume ROC | 量变动速率 | 量能变化 |

### 3.5 其他指标

| 指标 | 全称 | 含义 | 用途 |
|------|------|------|------|
| cr | Energy Index | 能量指标 | 多空力量对比 |
| tema | Triple EMA | 三重指数平滑 | 减少滞后 |
| trix | Triple EMA ROC | TEMA变动率 | 长期趋势 |
| vwap | Volume Weighted Average Price | 成交量加权均价 | 日内基准价 |

---

## 4. 市场风险指标

### 4.1 VIX 波动率指数

| 字段 | 来源 | 范围 | 含义 |
|------|------|------|------|
| VIXY | VIXY ETF | 通常10-80 | 市场恐慌指数 |

**解读：**
- VIXY < 15：市场极度平稳
- VIXY 15-20：正常波动
- VIXY 20-30：波动上升
- VIXY 30-40：市场恐慌
- VIXY > 40：极度恐慌（如2008金融危机）

**应用：**
```python
if data['VIXY'] > 30:
    # 市场恐慌，降低仓位
    position_size *= 0.5
```

---

### 4.2 Turbulence 动荡指数

| 字段 | 计算方法 | 阈值 | 含义 |
|------|---------|------|------|
| turbulence | 马氏距离 | 通常<100 | 市场异常程度 |

**计算公式：**
```
Turbulence = (r - μ)ᵀ Σ⁻¹ (r - μ)

其中：
r = 当前收益率向量
μ = 历史平均收益率
Σ = 协方差矩阵
```

**解读：**
- Turbulence < 50：市场正常
- Turbulence 50-100：波动加大
- Turbulence > 100：市场异常（危机信号）

**应用（风险控制）：**
```python
env = StockTradingEnv(
    df=data,
    turbulence_threshold=70,  # 超过70清仓
    risk_indicator_col='turbulence'
)
```

---

## 5. 衍生数据维度

### 5.1 日期时间维度

| 字段 | 类型 | 含义 | 示例 |
|------|------|------|------|
| date | string | 日期字符串 | 2023-01-03 |
| day | int | 星期几 | 0=周一, 4=周五 |
| timestamp | datetime | 完整时间戳 | 2023-01-03 09:30:00 |

### 5.2 价格变化维度

| 字段 | 计算方式 | 用途 |
|------|---------|------|
| returns | (close - close_prev) / close_prev | 收益率 |
| log_returns | log(close / close_prev) | 对数收益率 |
| price_change | close - open | 当日涨跌 |
| price_change_pct | (close - open) / open | 当日涨跌幅 |

---

## 6. 完整数据示例

下载完整数据后的DataFrame结构：

```python
processor = YahooFinanceProcessor()

# 下载数据
data = processor.download_data(
    ticker_list=["AAPL", "MSFT"],
    start_date="2020-01-01",
    end_date="2023-12-31",
    time_interval="1d"
)

# 清洗数据
data = processor.clean_data(data)

# 添加技术指标
data = processor.add_technical_indicator(
    data,
    ['macd', 'rsi_30', 'cci_30', 'dx_30', 'boll_ub', 'boll_lb']
)

# 添加VIX
data = processor.add_vix(data)

# 添加Turbulence
data = processor.add_turbulence(data)

# 最终数据列（每支股票每天一行）：
columns = [
    'timestamp',      # 时间戳
    'open',          # 开盘价
    'high',          # 最高价
    'low',           # 最低价
    'close',         # 收盘价
    'volume',        # 成交量
    'tic',           # 股票代码
    'macd',          # MACD
    'rsi_30',        # 30日RSI
    'cci_30',        # 30日CCI
    'dx_30',         # 30日DX
    'boll_ub',       # 布林带上轨
    'boll_lb',       # 布林带下轨
    'VIXY',          # VIX波动率
    'turbulence'     # 市场动荡指数
]

# 数据形状：
data.shape  # (天数 × 股票数, 列数)
# 例如：2支股票，1年数据 ≈ (504, 14)
```

---

## 7. 推荐配置

### 7.1 日线交易策略（中长线）

```python
INDICATORS = [
    'macd',         # 趋势判断
    'rsi_30',       # 超买超卖
    'cci_30',       # 价格偏离
    'dx_30',        # 趋势强度
    'boll_ub',      # 布林上轨
    'boll_lb',      # 布林下轨
    'close_30_sma', # 30日均线
    'close_60_sma', # 60日均线
]

time_interval = "1d"
```

### 7.2 日内交易策略（短线）

```python
INDICATORS = [
    'ema_5',        # 短期趋势
    'ema_10',       # 中期趋势
    'rsi_6',        # 快速超买超卖
    'cci_6',        # 快速价格偏离
    'atr',          # 止损设置
    'vwap',         # 日内基准价
]

time_interval = "5m"  # 或 "15m"
```

### 7.3 风险控制配置

```python
# 添加VIX和Turbulence
data_with_risk = processor.add_vix(data)
data_with_risk = processor.add_turbulence(data_with_risk)

# 在环境中使用
env = StockTradingEnv(
    df=data_with_risk,
    turbulence_threshold=70,      # 动荡指数阈值
    risk_indicator_col='turbulence'
)
```

---

## 8. 性能优化建议

### 8.1 数据量控制

| 时间间隔 | 推荐时间范围 | 数据量 |
|---------|-------------|--------|
| 1分钟 | 1天 | ~390行 |
| 5分钟 | 1周 | ~390行 |
| 1小时 | 1月 | ~150行 |
| 1天 | 3-5年 | ~750-1250行 |

### 8.2 指标选择

**避免冗余：**
- ❌ 不要同时使用 SMA_30 和 EMA_30
- ❌ 不要同时使用 RSI_6, RSI_12, RSI_30（选1-2个）
- ✅ 选择互补指标：趋势 + 动量 + 波动率

**推荐组合：**
```python
# 最小有效集（6个指标）
MINIMAL = ['macd', 'rsi_30', 'boll_ub', 'boll_lb', 'dx_30', 'close_30_sma']

# 标准配置（10个指标）
STANDARD = [
    'macd', 'rsi_30', 'cci_30', 'dx_30',
    'boll_ub', 'boll_lb',
    'close_30_sma', 'close_60_sma',
    'atr', 'volume_delta'
]

# 完整配置（15+指标）
FULL = STANDARD + ['ema_10', 'ema_20', 'kdjk', 'kdjd', 'wr_10', 'vr']
```

---

## 9. 数据质量检查

### 9.1 检查缺失值

```python
# 查看缺失数据
print(data.isnull().sum())

# 检查特定股票
aapl_data = data[data['tic'] == 'AAPL']
print(f"AAPL缺失率: {aapl_data.isnull().sum().sum() / aapl_data.size * 100:.2f}%")
```

### 9.2 检查数据范围

```python
# 检查技术指标范围
print(f"RSI范围: {data['rsi_30'].min():.2f} - {data['rsi_30'].max():.2f}")  # 应该在0-100
print(f"CCI范围: {data['cci_30'].min():.2f} - {data['cci_30'].max():.2f}")  # 可以超过±100
print(f"DX范围: {data['dx_30'].min():.2f} - {data['dx_30'].max():.2f}")    # 0-100
```

---

## 10. 常见问题

### Q1: 如何获取更早的历史数据？
**A:** Yahoo Finance免费数据通常可以追溯到IPO日期，但质量随时间递减。

### Q2: 1分钟数据有限制吗？
**A:** Yahoo Finance限制1分钟数据最多7天，使用`download_data`会自动分天下载。

### Q3: 技术指标如何自定义参数？
**A:** 使用stockstats库的语法，例如：
```python
'rsi_14'     # 14日RSI
'ema_50'     # 50日EMA
'boll_20'    # 20日布林带
```

### Q4: 如何处理股票拆分和分红？
**A:** `YahooDownloader`自动调整历史价格，使用`auto_adjust=True`（默认）。

---

## 总结

Yahoo Finance高级功能提供：
- ✅ **7种时间间隔**（1m到1mo）
- ✅ **30+技术指标**（趋势、动量、波动率、成交量）
- ✅ **2种风险指标**（VIX、Turbulence）
- ✅ **完整数据处理**（清洗、填充、标准化）
- ✅ **交易日历支持**
- ✅ **实时数据获取**

**最常用配置（推荐）：**
```python
from finrl.meta.data_processors.processor_yahoofinance import YahooFinanceProcessor

processor = YahooFinanceProcessor()

# 下载数据
data = processor.download_data(
    ticker_list=["AAPL", "MSFT", "GOOGL"],
    start_date="2020-01-01",
    end_date="2023-12-31",
    time_interval="1d"
)

# 清洗
data = processor.clean_data(data)

# 添加技术指标
data = processor.add_technical_indicator(
    data,
    ['macd', 'rsi_30', 'cci_30', 'dx_30', 'boll_ub', 'boll_lb']
)

# 添加风险指标
data = processor.add_vix(data)
data = processor.add_turbulence(data, time_period=252)
```

这样就得到了一个包含**价格+技术指标+风险指标**的完整数据集，可以直接用于AI策略训练！
