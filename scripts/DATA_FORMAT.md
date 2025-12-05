# 数据格式说明

## 日期格式与时区

### 原始数据
Yahoo Finance 返回的数据包含时区信息：
```
2022-11-21 00:00:00-05:00  # EST (东部标准时间)
2022-06-15 00:00:00-04:00  # EDT (东部夏令时)
```

**时区说明：**
- **EST (Eastern Standard Time)**: UTC-5，美国东部标准时间（11月-3月）
- **EDT (Eastern Daylight Time)**: UTC-4，美国东部夏令时（3月-11月）
- 美股交易使用纽约时间（EST/EDT）

### 处理后的数据
脚本会自动处理日期格式：
1. **移除时区信息** - 转换为本地时间
2. **只保留日期** - 去掉时间部分（00:00:00）
3. **最终格式**: `2022-11-21` (纯日期格式)

这样做的好处：
- ✅ 数据更简洁易读
- ✅ CSV 文件更小
- ✅ 在不同时区环境中一致
- ✅ 便于日期比较和排序

## 价格数据精度

### 原始精度
Yahoo Finance 返回的价格数据有很多小数位：
```
150.16000366211  # 开盘价
148.00999450684  # 收盘价
```

### 处理后的精度
所有价格数据四舍五入到 **2位小数**：
```
150.16  # 开盘价
148.01  # 收盘价
```

**处理的列：**
- `open` - 开盘价
- `high` - 最高价
- `low` - 最低价
- `close` - 收盘价
- `adj close` - 复权收盘价
- 所有技术指标

**不处理的列：**
- `volume` - 成交量（保持整数）
- `date` - 日期
- `tic` - 股票代码

## 数据示例

### 下载前（Yahoo Finance 原始数据）
```csv
Date,Open,High,Low,Close,Adj Close,Volume
2022-11-21 00:00:00-05:00,150.16000366211,150.36999511719,147.72000122070,148.00999450684,147.55497741699,58724100
```

### 下载后（处理后的数据）
```csv
date,tic,open,high,low,close,adj close,volume,macd,rsi_12,cci_14
2022-11-21,AAPL,150.16,150.37,147.72,148.01,147.55,58724100,0.00,45.23,-25.34
```

## 列说明

### 基础价格列（8列）
| 列名 | 说明 | 数据类型 | 精度 |
|------|------|----------|------|
| `date` | 交易日期 | date | YYYY-MM-DD |
| `tic` | 股票代码 | string | - |
| `open` | 开盘价 | float | 2位小数 |
| `high` | 最高价 | float | 2位小数 |
| `low` | 最低价 | float | 2位小数 |
| `close` | 收盘价 | float | 2位小数 |
| `adj close` | 复权收盘价 | float | 2位小数 |
| `volume` | 成交量 | int | 整数 |

### 技术指标列（60+列）

所有技术指标都四舍五入到 **2位小数**，便于阅读和分析。

**趋势指标：**
- `macd`, `macds`, `macdh` - MACD 指标
- `ema_3`, `ema_5`, ..., `ema_60` - 指数移动平均
- `sma_5`, `sma_10`, ..., `sma_60` - 简单移动平均
- `dma` - 双移动平均

**动量指标：**
- `rsi_6`, `rsi_12`, `rsi_24` - 相对强弱指标
- `cci_14`, `cci_20` - 商品通道指数
- `dx` - 动向指数
- `wr` - 威廉指标
- `kdjk`, `kdjd`, `kdjj` - KDJ 指标

**波动率指标：**
- `boll`, `boll_ub`, `boll_lb` - 布林带
- `atr_14`, `atr_21` - 真实波动幅度

**成交量指标：**
- `volume_delta` - 成交量变化
- `vr` - 成交量比率
- `vroc` - 成交量变化率
- `cr` - 能量指标

**其他指标：**
- `trix`, `trixs` - TRIX 指标
- `obv` - 能量潮
- `mfi` - 资金流量指标

## 数据质量保证

### 自动处理
1. **时区标准化** - 统一转换为本地日期
2. **精度控制** - 价格保留2位小数
3. **数据清理** - 移除缺失值和异常值
4. **类型转换** - 确保数据类型正确

### 数据验证
```python
import pandas as pd

# 读取数据
df = pd.read_csv('data/prices/AAPL_2022-11-20_2025-11-19.csv')

# 验证日期格式
print(df['date'].dtype)  # 应该是 object 或 datetime64

# 验证价格精度
print(df['close'].apply(lambda x: len(str(x).split('.')[-1])).max())  # 应该 <= 2

# 验证数据完整性
print(df.isnull().sum())  # 检查缺失值

# 验证数据范围
print(df[['open', 'high', 'low', 'close']].describe())
```

## 常见问题

### Q1: 为什么日期格式是 YYYY-MM-DD 而不是 MM/DD/YYYY？
**A:** ISO 8601 标准格式（YYYY-MM-DD）有以下优点：
- 国际通用标准
- 便于排序（字符串排序等同于日期排序）
- 避免不同地区的格式混淆（美式 vs 欧式）
- Python/Pandas 默认支持

### Q2: 为什么要移除时区信息？
**A:**
- 日线数据不需要精确到小时
- 简化数据存储
- 避免不同时区转换的复杂性
- 所有美股都使用相同的交易日历

### Q3: 复权价格（Adj Close）是什么？
**A:**
- 调整了股票分红、拆股等事件的价格
- 用于计算真实的投资回报
- 技术分析通常使用 `close`，回报计算使用 `adj close`

### Q4: 为什么有些技术指标是 NaN？
**A:**
- 技术指标需要足够的历史数据
- 例如：60日 EMA 需要至少 60 个数据点
- 前 N 行数据的 N 日指标会是 NaN
- 可以使用 `df.dropna()` 移除这些行

### Q5: 如何修改价格精度？
**A:**
编辑 `scripts/download_stock_data_simple.py`，修改四舍五入精度：
```python
# 修改为 4 位小数
df[col] = df[col].round(4)

# 或者不四舍五入（保留原始精度）
# 注释掉 round() 那行代码
```

## 最佳实践

### 数据存储
```python
# 保存时保持日期格式
df.to_csv('data.csv', index=False, date_format='%Y-%m-%d')

# 读取时解析日期
df = pd.read_csv('data.csv', parse_dates=['date'])
```

### 数据分析
```python
# 按日期排序
df = df.sort_values('date')

# 按日期筛选
df_2023 = df[df['date'] >= '2023-01-01']

# 计算日收益率
df['return'] = df['close'].pct_change()
```

### 可视化
```python
import matplotlib.pyplot as plt

# 绘制价格走势
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['close'], label='Close Price')
plt.plot(df['date'], df['sma_20'], label='SMA 20')
plt.xlabel('Date')
plt.ylabel('Price ($)')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```
