# Yahoo Finance Rate Limit 处理指南

## 问题背景

Yahoo Finance API 对请求频率有限制，当短时间内发送过多请求时会返回 `YFRateLimitError: Too Many Requests` 错误。限流主要基于：

1. **IP 地址**：同一 IP 的请求频率
2. **时间窗口**：通常为每分钟或每小时的请求数
3. **网络环境**：共享 IP（如公司网络、公共 WiFi）更容易触发限制

## 已实现的优化策略

### 1. 指数退避重试机制

当遇到 rate limit 错误时，系统会自动重试，等待时间呈指数增长：

- **最大重试次数**：5 次
- **基础延迟**：10 秒
- **等待时间序列**：
  - 第 1 次重试：等待 10 秒
  - 第 2 次重试：等待 20 秒
  - 第 3 次重试：等待 40 秒
  - 第 4 次重试：等待 80 秒
  - 第 5 次重试：等待 160 秒

**代码位置**：`localfindata/ticker_info.py:_retry_yf_call()`

### 2. API 调用间延迟

在处理单个股票时，每个 API 调用之间会自动等待 0.5 秒，避免连续请求触发限流：

```python
# 可通过 api_delay 参数调整（单位：秒）
data = fetch_daily_datasets("AAPL", api_delay=0.5)
```

### 3. 股票批量处理延迟

处理多个股票时，每个股票之间会等待 3 秒：

```python
# 可通过 delay_between_tickers 参数调整（单位：秒）
download_ticker_batch(["AAPL", "TSLA", "QQQ"], delay_between_tickers=3)
```

## 使用建议

### 基本使用（默认参数）

```bash
python scripts/download_ticker_info.py AAPL TSLA QQQ
```

### 遇到 Rate Limit 时的应对策略

#### 策略 1：减少批量数量

一次只处理 1-3 个股票，避免连续大量请求：

```bash
# 分批处理
python scripts/download_ticker_info.py AAPL
python scripts/download_ticker_info.py TSLA
python scripts/download_ticker_info.py QQQ
```

#### 策略 2：增加延迟时间

如果网络环境限制较严格，可以通过修改代码增加延迟：

```python
# 在 scripts/download_ticker_info.py 中修改
paths = download_ticker_batch(
    args.tickers,
    start=args.start,
    end=args.end,
    delay_between_tickers=10,  # 增加到 10 秒
    api_delay=1.0,              # 增加到 1 秒
)
```

#### 策略 3：等待后重试

如果连续多次失败，建议：

1. 等待 5-10 分钟后重试
2. 检查是否在短时间内运行了多次脚本
3. 确认同一网络下是否有其他人也在使用 Yahoo Finance API

#### 策略 4：更换网络环境

某些网络环境更容易触发限制：

- **问题环境**：公司网络、公共 WiFi、校园网（多人共享同一出口 IP）
- **推荐环境**：家庭网络、移动热点、VPN

## 不同环境的表现差异

### 为什么本地环境容易失败？

1. **IP 历史请求**：如果之前已经发送过大量请求，IP 可能已被临时限制
2. **共享 IP**：公司或公共网络多人共用同一 IP
3. **地理位置**：某些地区的 IP 可能被更严格地限制
4. **ISP 策略**：不同网络提供商的路由策略不同

### 为什么云端环境正常？

1. **全新 IP**：云端测试环境使用不同的 IP 地址
2. **数据中心网络**：云服务商的网络通常限制较少
3. **地理分布**：可能位于限制较少的地区

## 高级配置

### 自定义重试参数

如需更激进的重试策略，可以修改 `_retry_yf_call` 函数：

```python
# localfindata/ticker_info.py
def _retry_yf_call(func, *args, max_attempts: int = 7, backoff: int = 15, **kwargs):
    # 增加到 7 次重试，基础延迟 15 秒
    # 等待时间：15s, 30s, 60s, 120s, 240s, 480s, 960s
    ...
```

### 监控请求频率

建议在处理大量股票时添加日志记录：

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 常见问题

### Q: 为什么第一次请求就失败了？

A: 可能是您的 IP 之前已经发送过大量请求。建议等待 10-15 分钟后重试。

### Q: 所有重试都失败了怎么办？

A:
1. 确认网络连接正常
2. 等待更长时间（30 分钟到 1 小时）
3. 尝试更换网络环境或使用 VPN
4. 减少单次处理的股票数量

### Q: 如何知道当前 IP 是否被限制？

A: 如果连续多次请求都立即失败（不经过重试），说明 IP 可能被临时封禁。建议等待或更换 IP。

### Q: 付费 API 会更好吗？

A: Yahoo Finance 目前主要提供免费 API，如需更稳定的服务可考虑：
- Alpha Vantage
- Polygon.io
- IEX Cloud
- Quandl/Nasdaq Data Link

## 总结

通过合理配置重试机制和延迟参数，大多数 rate limit 问题都可以解决。如果仍然遇到问题，最有效的方法是：

1. **减少批量大小**：一次处理更少的股票
2. **增加延迟**：给 API 更多休息时间
3. **更换环境**：避免使用共享 IP 网络
4. **分时处理**：将大批量任务分散到不同时间段
