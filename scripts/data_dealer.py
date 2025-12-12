import pandas as pd
from pathlib import Path

# 目录
news_dir = Path(r"D:\GitHub\LocalFinData\data\news-yh-stock")

# 获取所有csv文件
news_files = list(news_dir.glob("*.csv"))
print(f"news-yh-stock 目录: {len(news_files)} 个CSV文件\n")

total_chars = 0
total_rows = 0
error_files = []

for news_file in news_files:
    try:
        # 读取文件内容统计字符数
        with open(news_file, 'r', encoding='utf-8') as f:
            content = f.read()
            total_chars += len(content)

        # 统计行数
        df = pd.read_csv(news_file)
        total_rows += len(df)

    except Exception as e:
        error_files.append(f"{news_file.name}: {e}")

# Token估算（不同语言比例不同）
tokens_english = total_chars / 4  # 英文约4字符=1token
tokens_mixed = total_chars / 3  # 中英混合约3字符=1token
tokens_chinese = total_chars / 1.5  # 中文约1.5字符=1token

# gpt-5-nano 价格: $0.05 / 1M tokens
price_per_million = 0.05

cost_english = (tokens_english / 1_000_000) * price_per_million
cost_mixed = (tokens_mixed / 1_000_000) * price_per_million
cost_chinese = (tokens_chinese / 1_000_000) * price_per_million

# 打印结果
print(f"{'=' * 60}")
print(f"统计结果:")
print(f"{'=' * 60}")
print(f"  文件数量: {len(news_files)} 个")
print(f"  数据行数: {total_rows:,} 行")
print(f"  总字符数: {total_chars:,} 字符")
print(f"{'=' * 60}")
print(f"\nToken估算:")
print(f"  英文为主 (4字符/token):   {tokens_english:,.0f} tokens")
print(f"  中英混合 (3字符/token):   {tokens_mixed:,.0f} tokens")
print(f"  中文为主 (1.5字符/token): {tokens_chinese:,.0f} tokens")
print(f"{'=' * 60}")
print(f"\ngpt-5-nano 成本估算 ($0.05/1M tokens):")
print(f"  英文为主:   ${cost_english:.4f}")
print(f"  中英混合:   ${cost_mixed:.4f}")
print(f"  中文为主:   ${cost_chinese:.4f}")
print(f"{'=' * 60}")

if error_files:
    print(f"\n处理出错: {len(error_files)} 个")
    for e in error_files:
        print(f"  {e}")
