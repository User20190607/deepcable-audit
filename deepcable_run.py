#!/usr/bin/env python3
"""
deepcable_run.py
一键运行入口 — Claude Code 直接调用

用法：
    python deepcable_run.py 原始清单.xlsx
    python deepcable_run.py 原始清单.xlsx --sheet 得力电缆
    python deepcable_run.py 原始清单.xlsx --out 输出目录/

流程：
    1. 读取原始 Excel
    2. 标准化型号
    3. 聚合数量
    4. N/PE 截面校验
    5. 输出标准化 Excel（含原始索引 Sheet）
    6. 打印问题清单

输出文件：
    <原文件名>_标准化.xlsx
"""

import sys
import os
import math
import argparse
from pathlib import Path

# 同目录下的模块
sys.path.insert(0, str(Path(__file__).parent))
from deepcable_read_excel import read_cable_list
from deepcable_normalize import normalize, aggregate, to_excel, check_pe, sort_key


def main():
    parser = argparse.ArgumentParser(description='电线电缆清单标准化工具 v24.2')
    parser.add_argument('input', help='原始清单 Excel 路径')
    parser.add_argument('--sheet', default=None, help='指定 Sheet 名（默认读取所有）')
    parser.add_argument('--out', default=None, help='输出目录（默认同输入文件目录）')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f'错误：文件不存在 {input_path}')
        sys.exit(1)

    out_dir = Path(args.out) if args.out else input_path.parent
    out_path = out_dir / f'{input_path.stem}_标准化.xlsx'

    print(f'\n{'='*60}')
    print(f'DeepCable 标准化工具 v24.2')
    print(f'输入：{input_path.name}')
    print(f'{'='*60}')

    # Step1: 读取
    records = read_cable_list(str(input_path), sheet_name=args.sheet)
    print(f'\n[Step1] 读取原始数据：{len(records)} 条')
    if len(records) > 30:
        print(f'  ⚠ 数据量较大（{len(records)}条），建议分批处理以确保准确性')

    # Step2: 聚合
    aggregated, failed, index_log = aggregate(records)
    print(f'\n[Step2] 型号聚合：{len(records)}条 → {len(aggregated)}行')
    if failed:
        print(f'  ⚠ 解析失败 {len(failed)} 条：')
        for f in failed:
            print(f"    - {f['raw']}")

    # Step3: 截面校验
    warnings = []
    for model in aggregated:
        pe = check_pe(model)
        if not pe['ok']:
            warnings.append((model, pe['warning']))
    if warnings:
        print(f'\n[Step3] N/PE截面校验警告 {len(warnings)} 条：')
        for model, warn in warnings:
            print(f'  ⚠ {model}')
            print(f'    {warn}')
    else:
        print(f'\n[Step3] N/PE截面校验：全部通过 ✓')

    # Step4: 输出
    n = to_excel(aggregated, str(out_path), index_log=index_log)
    print(f'\n[Step4] 输出：{out_path.name}（{n}行数据）')

    # Step5: 打印汇总
    results = sorted(aggregated.items(), key=lambda x: sort_key(x[0]))
    print(f'\n{"─"*60}')
    print(f'{"规格型号":<50} {"单位":^6} {"数量(m)":>10}')
    print(f'{"─"*60}')
    for model, qty in results:
        print(f'{model:<50} {"m":^6} {math.ceil(qty):>10}')
    total = sum(math.ceil(q) for q in aggregated.values())
    print(f'{"─"*60}')
    print(f'{"合计":>56} {total:>10}')
    print(f'\n原始{len(records)}条 → 聚合{len(results)}行'
          f'  |  失败{len(failed)}条  |  警告{len(warnings)}条')
    print(f'输出文件：{out_path}\n')


if __name__ == '__main__':
    main()
