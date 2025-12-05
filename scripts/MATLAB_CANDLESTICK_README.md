# MATLAB 股票 K 线图绘制工具

这个工具可以生成专业的股票 K 线图，包含多个技术指标面板。

## 文件说明

### Python 脚本
- **generate_stock_data_with_indicators.py**: 从基础 OHLCV 数据生成包含完整技术指标的 CSV 文件

### MATLAB 脚本
- **plot_candlestick_chart.m**: K 线图绘制函数（主函数）
- **plot_stock.m**: 快速绘图函数（推荐使用）
- **example_plot_AAPL.m**: 苹果股票示例脚本

## 快速开始

### 直接绘制 K 线图

股票数据已经包含所有技术指标，存放在 `prices/` 目录中。

#### 方法一：使用快捷函数（推荐）

打开 MATLAB，切换到项目根目录，然后：

```matlab
% 添加脚本路径
addpath('scripts');

% 绘制完整历史数据
plot_stock('AAPL')        % 苹果
plot_stock('TSLA')        % 特斯拉
plot_stock('GOOGL')       % 谷歌

% 绘制指定日期范围
plot_stock('AAPL', [datetime(2024,1,1), datetime(2024,12,31)])  % 2024年全年
plot_stock('AAPL', [datetime(2025,1,1), datetime('today')])      % 2025年至今
```

#### 方法二：运行示例脚本

```matlab
run('scripts/example_plot_AAPL.m')
```

#### 方法三：直接调用底层函数

```matlab
% 添加脚本路径
addpath('scripts');

% 绘制 K 线图（使用 prices 目录下的数据）
plot_candlestick_chart('prices/AAPL.csv', 'AAPL');
```

### （可选）为其他数据源生成技术指标

如果你有其他来源的基础 OHLCV 数据，可以使用 Python 脚本生成技术指标：

```bash
python scripts/generate_stock_data_with_indicators.py
```

这个脚本会读取基础价格数据并计算所有 117 个技术指标。

## 图表说明

生成的图表包含 4 个子面板：

### 1. K 线图 + 移动平均线 + 布林带
- **绿色 K 线**：阳线（收盘价 >= 开盘价）
- **红色 K 线**：阴线（收盘价 < 开盘价）
- **蓝色线**：EMA 5 日均线
- **橙色线**：EMA 20 日均线
- **紫色线**：EMA 50 日均线
- **灰色虚线**：布林带上下轨
- **灰色区域**：布林带范围

### 2. MACD 指标面板
- **蓝色线**：MACD 线
- **橙色线**：信号线
- **绿色柱**：正向柱状图（MACD > 信号线）
- **红色柱**：负向柱状图（MACD < 信号线）

### 3. RSI 指标面板
- **紫色线**：14 日 RSI
- **红色虚线**：超买线（70）
- **绿色虚线**：超卖线（30）
- **红色区域**：超买区
- **绿色区域**：超卖区

### 4. 成交量面板
- **绿色柱**：上涨日成交量
- **红色柱**：下跌日成交量
- **蓝色线**：5 日成交量均线
- **橙色线**：20 日成交量均线

## 技术指标数据说明

生成的 CSV 文件包含以下技术指标（共 117 个字段）：

### 基础数据
- date, tic, open, high, low, close, volume

### 趋势指标
- **MACD**: macd, macds, macdh, macd_signal, macd_hist
- **移动平均线**:
  - EMA (3, 5, 8, 10, 12, 15, 20, 26, 30, 35, 40, 45, 50, 60, 100, 200 日)
  - SMA (5, 10, 15, 20, 30, 50, 60, 100, 200 日)
  - WMA (10, 20, 30 日)
  - DEMA (10, 20, 30 日)
  - TEMA (10, 20, 30 日)
- **TRIX**: trix, trix_signal

### 动量指标
- **RSI**: rsi_6, rsi_9, rsi_12, rsi_14, rsi_21, rsi_24
- **CCI**: cci_14, cci_20
- **ROC**: roc_12, roc_25
- **Momentum**: mom_10, mom_14, mom_20
- **Williams %R**: willr_14, willr_21
- **Stochastic**: stoch_k_9, stoch_d_9, stoch_j_9, stoch_k_14, stoch_d_14, stoch_j_14
- **Ultimate Oscillator**: uo

### 波动性指标
- **Bollinger Bands**: bb_upper_20, bb_lower_20, bb_width_20, bb_pct_20, bb_upper_50, bb_lower_50, bb_width_50, bb_pct_50
- **ATR**: atr_7, atr_14, atr_21
- **Standard Deviation**: std_10, std_20, std_30
- **Keltner Channels**: kc_upper, kc_lower
- **Donchian Channels**: dc_upper, dc_lower, dc_middle

### 成交量指标
- **OBV**: obv (能量潮)
- **Volume MA**: vol_ma_5, vol_ma_10, vol_ma_20
- **Volume Ratio**: vol_ratio
- **MFI**: mfi (资金流量指标)
- **A/D Line**: ad_line (累积/派发线)
- **VWAP**: vwap (成交量加权平均价)

### 其他指标
- **ADX**: adx, pos_di, neg_di (平均趋向指标)
- **Aroon**: aroon_up, aroon_down, aroon_osc
- **Pivot Points**: pivot, r1, r2, s1, s2
- **SAR**: sar (抛物线转向)
- **Price Statistics**: price_change, price_change_pct, true_range, typical_price, median_price, weighted_close
- **Intraday Intensity**: intraday_intensity

## 自定义配置

### 使用其他股票数据

如果你想绘制其他股票的 K 线图（假设数据格式相同）：

```matlab
% 直接调用绘图函数
plot_candlestick_chart('prices/TSLA.csv', 'TSLA');  % 特斯拉
plot_candlestick_chart('prices/GOOGL.csv', 'GOOGL');  % 谷歌
plot_candlestick_chart('prices/MSFT.csv', 'MSFT');  % 微软
```

### 处理新的数据源

如果要从其他来源导入数据并生成技术指标，可以修改 `generate_stock_data_with_indicators.py`：

```python
# 在脚本末尾修改这些参数
input_file = 'your_data_file.csv'  # 你的基础数据文件
output_file = 'prices/YOUR_STOCK.csv'  # 输出文件
ticker = 'YOUR_STOCK'  # 股票代码
```

### 修改图表样式

在 `plot_candlestick_chart.m` 中，你可以自定义：
- 颜色方案
- 线条宽度
- 子图布局
- 显示的技术指标

例如，修改 K 线颜色：

```matlab
% 在 plot_candles 函数中
% 阳线颜色
body_color = [0.2, 0.8, 0.2];  % RGB 格式

% 阴线颜色
body_color = [0.8, 0.2, 0.2];  % RGB 格式
```

## 系统要求

### Python 要求
- Python 3.7+
- pandas
- numpy

安装依赖：
```bash
pip install pandas numpy
```

### MATLAB 要求
- MATLAB R2016b 或更高版本
- 不需要额外的 toolbox

## 数据说明

### 苹果股票数据 (prices/AAPL.csv)
- **日期范围**: 2020-11-23 至 2025-11-19
- **数据点**: 超过 1000 个交易日
- **字段数**: 117 个（包含基础 OHLCV 和所有技术指标）
- **更新**: 数据包含最新的市场信息

### 数据格式
每行包含一个交易日的完整数据：
- 基础数据：date, tic, open, high, low, close, volume
- 技术指标：MACD, RSI, 各种均线, 布林带, ATR, ADX, 成交量指标等

## 示例输出

运行示例脚本后，你将看到一个包含 4 个子面板的图表：
1. 顶部：K 线图 + 均线 + 布林带
2. 中上：MACD 指标
3. 中下：RSI 指标
4. 底部：成交量

所有子面板的 X 轴（时间）都是同步的，可以一起缩放和平移。

## 交互功能

MATLAB 图表支持以下交互操作：

- **缩放**：使用鼠标滚轮或工具栏的放大镜工具
- **平移**：点击工具栏的手型工具，然后拖动图表
- **数据提示**：点击工具栏的数据提示工具，然后点击任意数据点查看数值
- **保存**：文件 > 另存为... 可以保存为图片（PNG, JPG, PDF 等）

## 故障排除

### 问题 1: "数据文件不存在"
**解决方案**：确保 `prices/AAPL.csv` 文件存在。如果你的数据在其他位置，可以修改 `example_plot_AAPL.m` 中的路径：
```matlab
data_file = 'your/path/to/stock_data.csv';
```

### 问题 2: MATLAB 找不到函数
**解决方案**：添加脚本路径
```matlab
addpath('scripts');
```

### 问题 3: 图表显示不全
**解决方案**：调整图形窗口大小，或在 plot_candlestick_chart.m 中修改 figure 的 Position 参数

## 联系与反馈

如有问题或建议，欢迎提交 Issue 或 Pull Request。

## 许可证

本项目遵循 MIT 许可证。
