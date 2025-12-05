#!/usr/bin/env python3
"""
清理 CSV 文件中的重复列

功能：
1. 遍历 data/prices/ 下所有 CSV 文件
2. 统计列数分布（100+列、200+列等）
3. 检测并删除重复的列名
4. 检测并删除内容重复的列（即使列名不同）
5. 报告清理的文件和列名

使用方法：
    python scripts/remove_duplicate_columns.py
"""

import os
import pandas as pd
import numpy as np
import glob
from collections import Counter, defaultdict


def check_duplicate_columns(filepath):
    """
    检查 CSV 文件中的重复列（包括列名重复和内容重复）

    返回: (column_count, name_duplicates, content_duplicates)
        column_count: int - 列数
        name_duplicates: list - 重复的列名列表
        content_duplicates: dict - 内容重复的列组 {kept_col: [dup_col1, dup_col2, ...]}
    """
    try:
        # 读取文件
        df = pd.read_csv(filepath)
        column_count = len(df.columns)

        # 1. 检查重复的列名
        column_counts = Counter(df.columns)
        name_duplicates = [col for col, count in column_counts.items() if count > 1]

        # 2. 检查内容重复的列
        content_duplicates = {}
        checked = set()

        for i, col1 in enumerate(df.columns):
            if col1 in checked:
                continue

            duplicates_of_col1 = []

            for j, col2 in enumerate(df.columns):
                if i >= j:  # 跳过自己和已检查的
                    continue
                if col2 in checked:
                    continue

                # 比较两列内容是否完全相同
                # 使用 equals() 方法，处理 NaN 的情况
                if df[col1].equals(df[col2]):
                    duplicates_of_col1.append(col2)
                    checked.add(col2)

            if duplicates_of_col1:
                content_duplicates[col1] = duplicates_of_col1
                checked.add(col1)

        return column_count, name_duplicates, content_duplicates

    except Exception as e:
        print(f"    ❌ 错误: {e}")
        return 0, [], {}


def remove_duplicate_columns(filepath, name_duplicates, content_duplicates):
    """
    删除 CSV 文件中的重复列

    返回: (removed_count, removed_columns)
    """
    try:
        # 读取文件
        df = pd.read_csv(filepath)

        removed_columns = []

        # 1. 删除列名重复的列（保留第一个）
        if name_duplicates:
            df = df.loc[:, ~df.columns.duplicated()]
            removed_columns.extend(name_duplicates)

        # 2. 删除内容重复的列
        if content_duplicates:
            columns_to_drop = []
            for kept_col, dup_cols in content_duplicates.items():
                columns_to_drop.extend(dup_cols)
                removed_columns.extend(dup_cols)

            df = df.drop(columns=columns_to_drop)

        # 保存文件
        if removed_columns:
            df.to_csv(filepath, index=False)
            return len(removed_columns), removed_columns
        else:
            return 0, []

    except Exception as e:
        print(f"    ❌ 错误: {e}")
        return 0, []


def main():
    """主函数"""
    print("\n" + "="*80)
    print("CSV 文件重复列检测与清理")
    print("="*80)

    # 设置路径
    prices_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'prices')

    if not os.path.exists(prices_dir):
        print(f"❌ 目录不存在: {prices_dir}")
        return

    # 获取所有 CSV 文件
    csv_files = glob.glob(os.path.join(prices_dir, '*.csv'))
    # 排除 .gitkeep 和示例文件
    csv_files = [f for f in csv_files if not os.path.basename(f).startswith('.')
                 and 'EXAMPLE' not in os.path.basename(f).upper()]
    total_files = len(csv_files)

    if total_files == 0:
        print(f"❌ 在 {prices_dir} 中未找到 CSV 文件")
        return

    print(f"找到 {total_files} 个 CSV 文件")
    print(f"开始扫描...\n")

    # 统计信息
    column_distribution = defaultdict(int)  # {列数: 文件数}
    files_with_name_dup = []  # 列名重复的文件
    files_with_content_dup = []  # 内容重复的文件
    files_200plus = []  # 200+ 列的文件详情

    # 第一轮：扫描所有文件
    print("="*80)
    print("第一步：扫描所有文件的列数和重复情况")
    print("="*80)

    for i, filepath in enumerate(csv_files, 1):
        filename = os.path.basename(filepath)

        # 检查重复列
        column_count, name_duplicates, content_duplicates = check_duplicate_columns(filepath)

        # 统计列数分布
        if column_count > 0:
            # 按 50 列为一组统计
            group = (column_count // 50) * 50
            column_distribution[group] += 1

        # 记录有重复的文件
        if name_duplicates:
            files_with_name_dup.append((filename, column_count, name_duplicates))

        if content_duplicates:
            files_with_content_dup.append((filename, column_count, content_duplicates))

        # 记录 200+ 列的文件
        if column_count >= 200:
            files_200plus.append({
                'filename': filename,
                'column_count': column_count,
                'name_duplicates': name_duplicates,
                'content_duplicates': content_duplicates
            })

        # 每 100 个文件显示一次进度
        if i % 100 == 0:
            print(f"进度: {i}/{total_files} ({i/total_files*100:.1f}%)")

    # 显示列数分布
    print("\n" + "="*80)
    print("列数分布统计")
    print("="*80)
    sorted_groups = sorted(column_distribution.items())
    for group, count in sorted_groups:
        print(f"  {group:3d}-{group+49:3d} 列: {count:4d} 个文件")

    # 显示 200+ 列文件的详细信息
    print("\n" + "="*80)
    print(f"200+ 列的文件详情 (共 {len(files_200plus)} 个)")
    print("="*80)
    if files_200plus:
        for i, info in enumerate(files_200plus[:20], 1):  # 只显示前 20 个
            print(f"\n{i}. {info['filename']}")
            print(f"   总列数: {info['column_count']}")

            if info['name_duplicates']:
                print(f"   ⚠️  列名重复: {len(info['name_duplicates'])} 个")
                print(f"       {', '.join(info['name_duplicates'][:10])}" +
                      (f" ... (还有 {len(info['name_duplicates'])-10} 个)" if len(info['name_duplicates']) > 10 else ""))

            if info['content_duplicates']:
                total_dup = sum(len(v) for v in info['content_duplicates'].values())
                print(f"   ⚠️  内容重复: {total_dup} 个列的内容与其他列相同")
                for kept_col, dup_cols in list(info['content_duplicates'].items())[:5]:
                    print(f"       '{kept_col}' 与以下列内容相同: {', '.join(dup_cols)}")
                if len(info['content_duplicates']) > 5:
                    print(f"       ... 还有 {len(info['content_duplicates'])-5} 组重复")

            if not info['name_duplicates'] and not info['content_duplicates']:
                print(f"   ✅ 无重复列")

        if len(files_200plus) > 20:
            print(f"\n... 还有 {len(files_200plus)-20} 个 200+ 列的文件未显示")
    else:
        print("  ✅ 无 200+ 列的文件")

    # 显示列名重复统计
    print("\n" + "="*80)
    print(f"列名重复文件统计 (共 {len(files_with_name_dup)} 个)")
    print("="*80)
    if files_with_name_dup:
        for filename, col_count, name_dups in files_with_name_dup[:10]:
            print(f"  📄 {filename} ({col_count} 列)")
            print(f"      重复列名: {', '.join(name_dups)}")
        if len(files_with_name_dup) > 10:
            print(f"\n  ... 还有 {len(files_with_name_dup)-10} 个文件")
    else:
        print("  ✅ 无列名重复的文件")

    # 显示内容重复统计
    print("\n" + "="*80)
    print(f"内容重复文件统计 (共 {len(files_with_content_dup)} 个)")
    print("="*80)
    if files_with_content_dup:
        for filename, col_count, content_dups in files_with_content_dup[:10]:
            total_dup = sum(len(v) for v in content_dups.values())
            print(f"  📄 {filename} ({col_count} 列)")
            print(f"      {total_dup} 个重复列，{len(content_dups)} 组重复")
            for kept_col, dup_cols in list(content_dups.items())[:3]:
                print(f"      '{kept_col}' = {', '.join(dup_cols)}")
            if len(content_dups) > 3:
                print(f"      ... 还有 {len(content_dups)-3} 组")
        if len(files_with_content_dup) > 10:
            print(f"\n  ... 还有 {len(files_with_content_dup)-10} 个文件")
    else:
        print("  ✅ 无内容重复的文件")

    # 第二轮：清理重复列
    if files_with_name_dup or files_with_content_dup:
        print("\n" + "="*80)
        print("第二步：清理重复列")
        print("="*80)

        cleaned_files = []
        total_removed = 0

        # 合并需要清理的文件列表
        files_to_clean = {}
        for filename, col_count, name_dups in files_with_name_dup:
            files_to_clean[filename] = (name_dups, {})

        for filename, col_count, content_dups in files_with_content_dup:
            if filename in files_to_clean:
                files_to_clean[filename] = (files_to_clean[filename][0], content_dups)
            else:
                files_to_clean[filename] = ([], content_dups)

        for i, (filename, (name_dups, content_dups)) in enumerate(files_to_clean.items(), 1):
            filepath = os.path.join(prices_dir, filename)
            removed_count, removed_columns = remove_duplicate_columns(filepath, name_dups, content_dups)

            if removed_count > 0:
                print(f"[{i}/{len(files_to_clean)}] 🧹 {filename}: 删除 {removed_count} 个重复列")
                cleaned_files.append((filename, removed_columns))
                total_removed += removed_count

        print("\n" + "="*80)
        print("清理完成！")
        print("="*80)
        print(f"总文件数: {total_files}")
        print(f"🧹 清理的文件数: {len(cleaned_files)}")
        print(f"🗑️  删除的列总数: {total_removed}")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("✅ 所有文件都没有重复列，无需清理！")
        print("="*80)

    print("\n✅ 全部完成！\n")


if __name__ == '__main__':
    main()
