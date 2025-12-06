# Python K 线图生成器使用说明

`scripts/generate_candlestick_charts.py` 会读取 `data/prices/` 下的股票数据，自动生成专业的 K 线图，并保存到 `data/candles/<TICKER>/` 目录下（目录会自动创建）。

## ✨ 新功能

- ✅ **文件名纯数字格式**：`20221011_20241010.png`（易于排序和识别）
- ✅ **自动2年切分**：数据超过2年自动切分成多个图表
- ✅ **自定义均线周期**：支持最多10条均线，包括200日均线
- ✅ **智能颜色配置**：自动为不同均线分配颜色
- ✅ **批量处理**：支持多个股票同时处理

## 📊 均线类型详解

### 1. SMA (Simple Moving Average) - 简单移动平均线
- **计算方式**：所有价格的简单平均
- **特点**：对所有数据点权重相同
- **优点**：平滑，减少噪音
- **缺点**：滞后性强，反应慢
- **适用场景**：长期趋势判断

### 2. EMA (Exponential Moving Average) - 指数移动平均线 ⭐ 推荐
- **计算方式**：对近期价格赋予更大权重
- **特点**：更重视最新数据
- **优点**：反应快速，更及时
- **缺点**：可能产生更多假信号
- **适用场景**：短中期交易，股票分析
- **推荐指数**：⭐⭐⭐⭐⭐

### 3. WMA (Weighted Moving Average) - 加权移动平均线
- **计算方式**：线性递增权重（最新数据权重最大）
- **特点**：介于 SMA 和 EMA 之间
- **优点**：比 SMA 灵敏，比 EMA 平滑
- **缺点**：计算复杂，使用较少
- **适用场景**：特定策略

## 🔥 关于 ATR 指标 - 为什么它如此重要？

**ATR 是专业交易者必备的核心指标！** ⭐⭐⭐⭐⭐

### ATR 的四大核心用途

#### 1. 动态止损设置（最重要）
```
止损位 = 入场价 ± (2 × ATR)

示例：
- 入场价：$100
- ATR：$2
- 做多止损：$100 - $4 = $96
- 做空止损：$100 + $4 = $104
```

**为什么用 ATR？**
- 固定止损（如 -3%）可能被市场噪音扫出
- ATR 止损根据市场波动性自适应调整
- 高波动 = 宽止损，低波动 = 紧止损

#### 2. 仓位管理
```
仓位大小 = 风险资金 / (ATR × 倍数)

示例：
- 账户：$10,000
- 单笔风险：2% = $200
- ATR：$2
- 倍数：2
- 仓位 = $200 / ($2 × 2) = 50 股
```

#### 3. 突破真假判断
- **ATR 放大 + 突破** = 真突破（入场）
- **ATR 缩小 + 突破** = 假突破（观望）

#### 4. 市场状态识别
- **高 ATR** = 趋势行情（适合趋势跟踪策略）
- **低 ATR** = 震荡行情（适合区间交易策略）

### ATR 实战技巧

**交易系统示例：ATR + EMA**
```
入场条件：
1. 价格突破 EMA 20
2. ATR 在上升（确认趋势强度）
3. 止损：入场价 - 2 × ATR
4. 止盈：入场价 + 6 × ATR（风险回报比 1:3）
```

### 📈 推荐的 EMA 均线组合

| 周期 | 用途 | 时间跨度 |
|------|------|----------|
| **EMA 5/10** | 短期趋势 | 1-2 周 |
| **EMA 20/30** | 中期趋势 | 1 个月 |
| **EMA 50** | 中长期趋势 | 2-3 个月 |
| **EMA 100** | 长期趋势 | 半年 |
| **EMA 200** | 超长期趋势 | 1 年 |

**本脚本默认使用：EMA 5, 20, 50, 100, 200**

## 🚀 快速开始

### 基本用法（推荐）

```bash
# 自动切分并生成所有时间段的 K 线图（推荐！）
python scripts/generate_candlestick_charts.py AAPL --auto-split --data-dir data/prices --output-dir data/candles

# 自定义均线周期（最多10条）
python scripts/generate_candlestick_charts.py AAPL --auto-split --data-dir data/prices \
  --output-dir data/candles --ma-periods 5,10,20,30,50,100,150,200
```

### 高级用法

```bash
# 指定每段的年限（1年一段）
python scripts/generate_candlestick_charts.py AAPL --auto-split --max-years 1 --data-dir data/prices --output-dir data/candles

# 批量生成多个股票（自动切分）
python scripts/generate_candlestick_charts.py AAPL TSLA GOOGL MSFT --auto-split --data-dir data/prices --output-dir data/candles

# 高分辨率输出（300 DPI）
python scripts/generate_candlestick_charts.py AAPL --auto-split --dpi 300 --data-dir data/prices --output-dir data/candles

# 手动指定日期范围（不自动切分）
python scripts/generate_candlestick_charts.py AAPL --data-dir data/prices --output-dir data/candles \
  --start 2024-01-01 --end 2024-12-31
```

## 📋 命令参数完整列表

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `tickers` | 股票代码（可多个） | `AAPL` 或 `AAPL TSLA GOOGL` |

### 可选参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--data-dir` | 数据目录路径 | `../prices` | `--data-dir prices` |
| `--auto-split` | 自动按年限切分 | 关闭 | `--auto-split` |
| `--max-years` | 每段最大年限 | `2` | `--max-years 1` |
| `--ma-periods` | 均线周期（逗号分隔） | `5,20,50,100,200` | `--ma-periods 5,10,20,50,100,200` |
| `--start` / `-s` | 开始日期 | 无 | `--start 2024-01-01` |
| `--end` / `-e` | 结束日期 | 无 | `--end 2024-12-31` |
| `--output-dir` / `-o` | 输出目录 | `candles` | `--output-dir my_charts` |
| `--dpi` | 图像分辨率 | `150` | `--dpi 300` |

## 💡 使用示例详解

### 示例 1：自动切分（推荐使用）

如果你的数据跨度超过2年，使用自动切分功能：

```bash
python generate_candlestick_charts.py AAPL --auto-split --data-dir prices
```

**效果**：
- 假设数据从 2020-11-23 到 2025-11-19（约5年）
- 自动切分为 3 个时间段：
  - `20201123_20221123.png`（2020-2022）
  - `20221124_20241124.png`（2022-2024）
  - `20241125_20251119.png`（2024-2025）

### 示例 2：自定义均线（最多10条）

```bash
python generate_candlestick_charts.py AAPL --auto-split --data-dir prices \
  --ma-periods 5,10,20,30,50,100,150,200
```

**效果**：
- 图表将显示 8 条 EMA 均线
- 不同颜色自动分配
- 短期均线（≤20）细线，长期均线（>100）粗线

### 示例 3：1年一段（更细致的切分）

```bash
python generate_candlestick_charts.py AAPL --auto-split --max-years 1 --data-dir prices
```

**效果**：
- 每个图表最多包含1年的数据
- 适合详细分析每年的走势

### 示例 4：批量生成高质量图表

```bash
python generate_candlestick_charts.py AAPL TSLA GOOGL MSFT \
  --auto-split --dpi 300 --data-dir prices \
  --ma-periods 5,20,50,100,200
```

**效果**：
- 同时处理 4 个股票
- 每个股票自动切分（如果超过2年）
- 300 DPI 高分辨率（适合演示）
- 使用 5 条主流 EMA 均线

### 示例 5：仅生成特定时间段

```bash
python generate_candlestick_charts.py AAPL --data-dir prices \
  --start 2024-01-01 --end 2024-12-31
```

**输出文件名**：`20240101_20241231.png`

## 📂 输出文件结构

```
data/
├── candles/                    # 图表输出目录
│   ├── AAPL/                  # 苹果股票
│   │   ├── 20201123_20221123.png   # 2020-2022
│   │   ├── 20221124_20241124.png   # 2022-2024
│   │   └── 20241125_20251119.png   # 2024-2025
│   ├── TSLA/                  # 特斯拉
│   │   ├── 20201123_20221123.png
│   │   └── ...
│   └── GOOGL/                 # 谷歌
│       └── ...
├── generate_candlestick_charts.py
└── README_CANDLES.md
```

## 📊 图表内容说明 - **专业 6 面板完整布局**

每个图表包含 **6 个技术分析面板**，提供全方位的市场分析：

### 1️⃣ K 线图 + 均线 + 布林带 + SAR（顶部 40%）
- **绿色 K 线**：阳线（收盘 ≥ 开盘）
- **红色 K 线**：阴线（收盘 < 开盘）
- **彩色线条**：EMA 均线（根据配置动态显示）
  - 蓝色：EMA 5
  - 橙色：EMA 20
  - 紫色：EMA 50
  - 绿色：EMA 100
  - 红色：EMA 200
  - 更多均线自动分配颜色
- **灰色区域**：布林带（20日）
- **彩色点**：SAR 抛物线转向点
  - 绿点：看涨（SAR 在价格下方）
  - 红点：看跌（SAR 在价格上方）

### 2️⃣ MACD 指标面板（12%）
- **蓝色线**：MACD 快线
- **橙色线**：MACD 信号线
- **绿色柱**：正向柱状图（MACD > 信号线，看涨）
- **红色柱**：负向柱状图（MACD < 信号线，看跌）
- **黑色虚线**：零轴

### 3️⃣ Stochastic (KDJ) 指标面板（12%）⭐ 新增
- **蓝色线**：%K 快线
- **橙色线**：%D 慢线
- **紫色虚线**：%J 超快线
- **红色虚线**：超买线（80）
- **绿色虚线**：超卖线（20）
- **红色/绿色区域**：超买/超卖区
- **交易信号**：金叉做多，死叉做空

### 4️⃣ RSI 指标面板（12%）
- **紫色线**：14 日 RSI
- **红色虚线**：超买线（70）
- **绿色虚线**：超卖线（30）
- **红色/绿色区域**：超买/超卖区

### 5️⃣ ADX + ATR 双指标面板（12%）⭐ 新增
**左Y轴 - ADX/DMI（紫色系）**：
- **紫色粗线**：ADX 趋势强度（>25 = 强趋势）
- **绿色线**：+DI 上升趋势强度
- **红色线**：-DI 下降趋势强度
- **红色虚线**：强趋势参考线（25）

**右Y轴 - ATR（橙色）**：
- **橙色虚线**：ATR 14 日平均真实波动幅度
- **橙色填充**：波动率区域
- **用途**：设置止损、判断市场活跃度

### 6️⃣ 成交量 + OBV 面板（12%）⭐ 升级
**左Y轴 - 成交量（绿色系）**：
- **绿色柱**：上涨日成交量
- **红色柱**：下跌日成交量
- **蓝色线**：5 日成交量均线
- **橙色线**：20 日成交量均线

**右Y轴 - OBV（紫色）**：
- **紫色线**：OBV 能量潮（累积成交量）
- **用途**：确认价格趋势，发现价量背离

## 🎯 最佳实践

### 1. 日常使用（推荐配置）

```bash
python generate_candlestick_charts.py AAPL --auto-split --data-dir prices \
  --ma-periods 5,20,50,100,200
```

这个配置：
- ✅ 自动切分（不超过2年一张图）
- ✅ 使用5条主流EMA均线
- ✅ 标准分辨率（150 DPI）
- ✅ 文件名纯数字格式

### 2. 演示报告（高质量）

```bash
python generate_candlestick_charts.py AAPL --auto-split --data-dir prices \
  --ma-periods 5,20,50,100,200 --dpi 300
```

### 3. 详细分析（1年一图）

```bash
python generate_candlestick_charts.py AAPL --auto-split --max-years 1 \
  --data-dir prices --ma-periods 5,10,20,30,50,100,200
```

### 4. 快速预览（低分辨率）

```bash
python generate_candlestick_charts.py AAPL --auto-split --data-dir prices \
  --dpi 100
```

## ❓ 常见问题

### Q1: 如何查看帮助信息？

```bash
python generate_candlestick_charts.py --help
```

### Q2: 为什么建议使用 EMA 而不是 SMA？

EMA 对最新价格更敏感，能更快地反映市场变化，更适合股票交易分析。SMA 对所有数据平等对待，反应较慢，适合长期趋势判断。

### Q3: 可以添加超过 200 日的均线吗？

可以！只要数据中包含对应的 `ema_XXX` 字段，就可以使用。例如：

```bash
--ma-periods 5,20,50,100,200,250,300
```

但建议最多使用 10 条均线，太多会导致图表混乱。

### Q4: 文件名为什么要用纯数字？

纯数字格式 `20221011_20241010.png` 的优点：
- 易于排序（按文件名自然排序就是时间顺序）
- 文件名简洁
- 跨平台兼容性好
- 便于程序处理

### Q5: 如何处理超过 5 年的数据？

使用 `--auto-split` 参数，脚本会自动切分：

```bash
python generate_candlestick_charts.py AAPL --auto-split --max-years 2 --data-dir prices
```

例如 5 年数据会切分为 3 个图表（2年 + 2年 + 1年）

### Q6: 中文显示有警告怎么办？

这是正常的，matplotlib 在 Linux 环境下可能缺少中文字体。图表会正常生成，只是中文可能显示为方框。如果需要完美的中文显示，可以安装中文字体：

```bash
# Ubuntu/Debian
sudo apt-get install fonts-wqy-microhei fonts-wqy-zenhei
```

### Q7: 如何只生成最近一年的数据？

```bash
python generate_candlestick_charts.py AAPL --data-dir prices \
  --start 2024-01-01 --end 2024-12-31
```

或者使用自动切分，每年一张图：

```bash
python generate_candlestick_charts.py AAPL --auto-split --max-years 1 --data-dir prices
```

### Q8: 均线太多图表看不清怎么办？

减少均线数量，只保留关键周期：

```bash
# 精简版（3条均线）
--ma-periods 20,50,200

# 标准版（5条均线，推荐）
--ma-periods 5,20,50,100,200
```

## 🔧 技术细节

### 文件命名规则
- **格式**：`YYYYMMDD_YYYYMMDD.png`
- **示例**：`20221011_20241010.png`
- **说明**：开始日期_结束日期

### 自动切分逻辑
1. 如果数据 ≤ 2年（或指定年限），不切分
2. 如果数据 > 2年，按年限切分
3. 最后一段如果 < 6个月，合并到前一段
4. 确保每段数据充足，避免太短的图表

### 均线显示规则
- 短期均线（≤20日）：细线（1.2px）
- 中期均线（21-100日）：中线（1.5px）
- 长期均线（>100日）：粗线（1.8px）
- 图例自动分2列显示

### 图像规格
- **默认尺寸**：16 × 10 英寸
- **默认分辨率**：150 DPI
- **文件格式**：PNG
- **典型大小**：150-300 KB（取决于数据点数和 DPI）

## 📝 更新日志

### v3.0 (最新) - 专业完整版 🎉
- ✅ **6 面板完整布局**：从 3 面板升级到 6 面板
- ✅ **新增 Stochastic (KDJ)**：精准的超买超卖指标
- ✅ **新增 ADX + DMI**：趋势强度和方向判断
- ✅ **新增 ATR**：波动率和止损设置（附详细使用说明）
- ✅ **新增 OBV**：能量潮，确认价格趋势
- ✅ **新增 SAR**：抛物线转向点，标记趋势反转
- ✅ **双 Y 轴显示**：ADX+ATR、成交量+OBV 智能组合
- ✅ **优化图表尺寸**：16×14 英寸，容纳更多信息
- ✅ **专业配色方案**：每个指标独立配色，易于识别
- ✅ **完整技术分析体系**：覆盖趋势、动量、波动率、成交量

### v2.0
- ✅ 文件名改为纯数字格式
- ✅ 添加自动2年切分功能
- ✅ 支持自定义均线周期（最多10条）
- ✅ 添加均线类型说明文档
- ✅ 智能颜色分配
- ✅ 优化图例显示（2列布局）

### v1.0
- ✅ 基础 K 线图生成
- ✅ 3 面板布局：K线、MACD、RSI
- ✅ 固定 3 条 EMA 均线
- ✅ 布林带显示

## 📞 联系与反馈

如有问题或建议，欢迎提交 Issue 或 Pull Request。

## 📄 许可证

本脚本遵循 MIT 许可证。
