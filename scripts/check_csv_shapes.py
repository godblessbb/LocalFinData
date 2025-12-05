#!/usr/bin/env python3
"""
检查所有 CSV 文件的形状（列数和列名）是否一致

功能：
1. 遍历 data/prices/ 下所有 CSV 文件
2. 统计每个文件的列数和列名
3. 检查是否所有文件具有相同的形状
4. 报告不同形状的分布情况

使用方法：
    python scripts/check_csv_shapes.py
"""

import os
import pandas as pd
import glob
from collections import defaultdict


def get_csv_shape(filepath):
    """
    获取 CSV 文件的形状（列数和列名）

    返回: (column_count, column_names_tuple)
    """
    try:
        df = pd.read_csv(filepath, nrows=0)  # 只读取列名，不读取数据
        column_count = len(df.columns)
        column_names = tuple(df.columns)
        return column_count, column_names
    except Exception as e:
        print(f"❌ 读取失败 {os.path.basename(filepath)}: {e}")
        return None, None


def main():
    """主函数"""
    print("\n" + "="*80)
    print("CSV 文件形状一致性检查")
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

    print(f"找到 {total_files} 个 CSV 文件\n")
    print("开始扫描...")

    # 统计信息
    # key: (column_count, column_names_tuple), value: [file1, file2, ...]
    shapes = defaultdict(list)
    column_count_dist = defaultdict(int)  # 列数分布

    # 扫描所有文件
    for i, filepath in enumerate(csv_files, 1):
        filename = os.path.basename(filepath)

        column_count, column_names = get_csv_shape(filepath)

        if column_count is not None:
            # 记录完整形状
            shapes[(column_count, column_names)].append(filename)
            # 记录列数分布
            column_count_dist[column_count] += 1

        # 显示进度
        if i % 100 == 0:
            print(f"进度: {i}/{total_files} ({i/total_files*100:.1f}%)")

    print(f"扫描完成！\n")

    # 显示结果
    print("="*80)
    print("扫描结果")
    print("="*80)

    # 1. 显示列数分布
    print(f"\n📊 列数分布:")
    print("-"*80)
    sorted_counts = sorted(column_count_dist.items())
    for col_count, file_count in sorted_counts:
        print(f"  {col_count:3d} 列: {file_count:4d} 个文件")

    # 2. 显示唯一形状数量
    unique_shapes = len(shapes)
    print(f"\n📐 唯一形状数量: {unique_shapes}")
    print("-"*80)

    if unique_shapes == 1:
        # 所有文件形状相同
        print("✅ 所有 CSV 文件具有相同的形状！")
        shape_key = list(shapes.keys())[0]
        col_count, col_names = shape_key
        print(f"\n列数: {col_count}")
        print(f"列名: {', '.join(col_names[:10])}" +
              (f" ... (还有 {len(col_names)-10} 列)" if len(col_names) > 10 else ""))
    else:
        # 存在不同形状
        print(f"⚠️  发现 {unique_shapes} 种不同的形状！")

        # 显示每种形状的详情
        print("\n" + "="*80)
        print("形状详情")
        print("="*80)

        # 按文件数量排序
        sorted_shapes = sorted(shapes.items(), key=lambda x: len(x[1]), reverse=True)

        for i, ((col_count, col_names), files) in enumerate(sorted_shapes, 1):
            print(f"\n形状 {i}: {col_count} 列，{len(files)} 个文件")
            print(f"列名: {', '.join(col_names[:15])}" +
                  (f" ... (还有 {len(col_names)-15} 列)" if len(col_names) > 15 else ""))

            # 显示示例文件
            if len(files) <= 10:
                print(f"文件: {', '.join(files)}")
            else:
                print(f"示例文件: {', '.join(files[:5])} ... (还有 {len(files)-5} 个)")

        # 如果有多种形状，比较它们的差异
        if unique_shapes == 2:
            print("\n" + "="*80)
            print("形状差异分析")
            print("="*80)

            shapes_list = list(sorted_shapes)
            shape1_cols = set(shapes_list[0][0][1])
            shape2_cols = set(shapes_list[1][0][1])

            only_in_shape1 = shape1_cols - shape2_cols
            only_in_shape2 = shape2_cols - shape1_cols
            common_cols = shape1_cols & shape2_cols

            print(f"\n共同列: {len(common_cols)} 个")
            print(f"仅在形状1中: {len(only_in_shape1)} 个")
            if only_in_shape1:
                print(f"  {', '.join(list(only_in_shape1)[:10])}" +
                      (f" ... (还有 {len(only_in_shape1)-10} 个)" if len(only_in_shape1) > 10 else ""))

            print(f"仅在形状2中: {len(only_in_shape2)} 个")
            if only_in_shape2:
                print(f"  {', '.join(list(only_in_shape2)[:10])}" +
                      (f" ... (还有 {len(only_in_shape2)-10} 个)" if len(only_in_shape2) > 10 else ""))

    print("\n" + "="*80)
    print("✅ 检查完成！")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
