#!/usr/bin/env python3
"""
deepcable_run.py — 一键运行入口（6-Sheet 审计输出）

用法：
    python deepcable_run.py 原始清单.xlsx
    python deepcable_run.py 原始清单.xlsx --project 项目名
    python deepcable_run.py 原始清单.xlsx --out 输出目录/
    python deepcable_run.py 原始清单.xlsx --prefix WDZB-YJY

流程：
    1. 读取原始 Excel（保留非电缆行）
    2. 规格预处理（并联2*翻倍、裸芯加前缀）
    3. 标准化型号
    4. 聚合数量
    5. N/PE 截面校验
    6. 输出 6-Sheet Excel

输出文件：
    <项目名>_电缆审计_<日期>.xlsx
"""

import sys
import os
import re
import math
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from deepcable_read_excel import read_cable_list
from deepcable_normalize import normalize, normalize_with_log
from validation import check_pe
from model_interpreter import interpret_model_short
from excel_output import build_output


def _classify_change(patch_log: list[str], raw: str, model: str) -> tuple[str, str]:
    """根据 patch_log 分类修正类型"""
    if not patch_log:
        return '无修正', ''

    log_str = '; '.join(patch_log)
    types = []

    if any('互斥' in s or 'YJV→YJY' in s for s in patch_log):
        types.append('材质互斥')
    if any('前缀' in s or 'NH→N' in s or 'ZR' in s.replace('ZR', '') != s for s in patch_log):
        types.append('前缀标准化')
    if any('电压' in s or '补全' in s for s in patch_log):
        types.append('电压补全')
    if any('阻燃' in s or 'WD' in s for s in patch_log):
        types.append('阻燃等级修正')

    if not types:
        types.append('多项修正')

    return ' + '.join(types), log_str


def _make_verification(source_qties: list[float]) -> str:
    """生成验算式 860+1200+540=2600"""
    ints = [int(q) for q in source_qties]
    expr = '+'.join(str(i) for i in ints)
    total = sum(ints)
    return f'{expr}={total}'


def _fmt_ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='DeepCable 6-Sheet 审计工具')
    parser.add_argument('input', help='原始清单 Excel 路径')
    parser.add_argument('--out', default=None, help='输出目录（默认桌面）')
    parser.add_argument('--project', default='', help='项目名（用于输出文件名）')
    parser.add_argument('--prefix', default='', help='裸芯规格前缀（如 YJV/WDZB-YJY）')
    parser.add_argument('--sheet', default=None, help='指定 Sheet 名')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f'错误：文件不存在 {input_path}')
        sys.exit(1)

    # 输出路径
    project = args.project or input_path.stem
    date_str = datetime.now().strftime('%Y%m%d')
    out_dir = Path(args.out) if args.out else Path.home() / 'Desktop'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'{project}_电缆审计_{date_str}.xlsx'

    print(f'\n{"=" * 60}')
    print(f'DeepCable 6-Sheet 审计工具')
    print(f'输入：{input_path.name}')
    print(f'输出：{out_path.name}')
    print(f'{"=" * 60}')

    # ── Step1: 读取 ──
    records = read_cable_list(str(input_path), sheet_name=args.sheet)
    print(f'\n[Step1] 读取原始数据：{len(records)} 条')
    cable_recs = [r for r in records if r['is_cable']]
    non_cable = [r for r in records if not r['is_cable']]
    print(f'  其中电缆 {len(cable_recs)} 条，非电缆 {len(non_cable)} 条')
    if non_cable:
        for n in non_cable:
            print(f'  ⚠ 行{n["row"]}: {n["raw"]}（非电缆，已标记排除）')

    if len(records) > 30:
        print(f'  ⚠ 数据量较大（{len(records)}条），自动批量处理，请知会后人工复核关键项')

    # ── Step1.5: 预处理 ──
    log_entries = []
    issues = []
    bare_specs = []
    parallel_specs = []

    for r in records:
        raw = r['raw']
        if not r['is_cable'] or not raw:
            continue

        # 2*(...) 并联
        m = re.match(r'2\*[（(]\s*(.+?)\s*[）)]', raw)
        if m:
            r['raw'] = m.group(1).strip()
            r['qty'] *= 2
            parallel_specs.append(r)
            log_entries.append({
                'timestamp': _fmt_ts(), 'phase': 'P2',
                'item_ref': f'行{r["row"]}',
                'operation': f'并联翻倍: {raw} → {r["raw"]}, qty×2={r["qty"]}',
                'rule': 'P2.1 并联格式',
            })
            continue

        # 裸芯规格（无型号前缀）
        if re.match(r'^[\d\*\×\+]+$', raw):
            bare_specs.append(r)

    if bare_specs:
        prefix = args.prefix
        print(f'\n[Step1.5] {len(bare_specs)} 条裸芯规格，需加前缀')
        if prefix:
            for b in bare_specs:
                old_raw = b['raw']
                b['raw'] = prefix + old_raw
                log_entries.append({
                    'timestamp': _fmt_ts(), 'phase': 'P2',
                    'item_ref': f'行{b["row"]}',
                    'operation': f'裸芯加前缀: {old_raw} → {b["raw"]}',
                    'rule': '用户指定前缀',
                })
            print(f'  已自动添加前缀 "{prefix}"')
        else:
            print(f'  ⚠ 请用 --prefix 参数指定电缆前缀（如 --prefix WDZB-YJY）')
            for b in bare_specs[:5]:
                print(f'    行{b["row"]}: {b["raw"]}')
            # 临时加默认前缀
            for b in bare_specs:
                b['raw'] = 'YJY' + b['raw']

    if parallel_specs:
        print(f'  ℹ {len(parallel_specs)} 条 2*(...) 并联记录已翻倍')

    # ── Step2: 标准化 ──
    print(f'\n[Step2] 标准化型号...')

    model_results = []
    agg_map = {}  # model -> {qty, source_rows, source_qties, record_indices}

    # 先处理非电缆行
    for r in records:
        if not r['is_cable']:
            model_results.append({
                'raw': r['raw'], 'qty': r['qty'], 'raw_qty': r['qty'],
                'raw_unit': r.get('unit', 'm'), 'row': r['row'],
                'sheet': r.get('sheet', ''), 'is_cable': False,
                'model': None, 'change_type': '', 'change_desc': '非电线电缆',
                'pe_status': '—', 'status': '❌失败',
            })
            continue

    # 处理电缆行
    for r in records:
        if not r['is_cable']:
            continue

        raw = r['raw']
        model, patch_log = normalize_with_log(raw)
        pe_result = check_pe(model) if model else {'ok': True, 'warning': ''}

        if model:
            ctype, cdesc = _classify_change(patch_log, raw, model)
            pe_status = '✓ OK' if pe_result['ok'] else '⚠ ' + pe_result.get('warning', '')
            status = '⚠️警告' if not pe_result['ok'] else ('✅正常')

            # Aggregate
            if model not in agg_map:
                agg_map[model] = {'qty': 0, 'source_rows': [], 'source_qties': [], 'indices': []}
            agg_map[model]['qty'] += r['qty']
            agg_map[model]['source_rows'].append(r['row'])
            agg_map[model]['source_qties'].append(r['qty'])

            log_entries.append({
                'timestamp': _fmt_ts(), 'phase': 'P3',
                'item_ref': f'行{r["row"]}',
                'operation': f'标准化: {raw} → {model}',
                'rule': ctype or '无修正',
            })

            if not pe_result['ok']:
                issues.append({
                    'type': '⚠️ 警告',
                    'raw_spec': model,
                    'description': f'PE 截面校验：{pe_result.get("warning", "")}',
                    'suggestion': '确认是否接受当前截面或更换更大规格',
                })
        else:
            ctype, cdesc = '', '解析失败'
            pe_status = '—'
            status = '❌失败'
            issues.append({
                'type': '❌ 失败',
                'raw_spec': raw,
                'description': '无法识别型号',
                'suggestion': '请补充标准型号或修正写法',
            })

        model_results.append({
            'raw': raw, 'qty': r['qty'], 'raw_qty': r['qty'],
            'raw_unit': r.get('unit', 'm'), 'row': r['row'],
            'sheet': r.get('sheet', ''), 'is_cable': True,
            'model': model, 'change_type': ctype, 'change_desc': cdesc,
            'pe_status': pe_status, 'status': status,
        })

    # ── Step3: 聚合并构建验证 ──
    print(f'\n[Step3] 聚合数量...')
    aggregated = []
    for model, info in sorted(agg_map.items(), key=lambda x: sort_key(x[0])):
        aggregated.append({
            'model': model,
            'qty': info['qty'],
            'source_rows': info['source_rows'],
            'source_qties': info['source_qties'],
            'verification_expr': _make_verification(info['source_qties']),
            'note': '',
        })
        log_entries.append({
            'timestamp': _fmt_ts(), 'phase': 'P4',
            'item_ref': f"{','.join(str(s) for s in info['source_rows'])}",
            'operation': f'聚合: {model} 合计 {info["qty"]}m',
            'rule': '§8 型号指纹',
        })

    print(f'  {len(model_results)}条 → {len(aggregated)}个唯一型号')

    # ── Step4: 校验 ──
    print(f'\n[Step4] N/PE 截面校验...')
    warn_count = sum(1 for iss in issues if '⚠' in iss['type'])
    fail_count = sum(1 for iss in issues if '❌' in iss['type'])
    print(f'  警告 {warn_count} 条，失败 {fail_count} 条' if warn_count or fail_count else '  全部通过 ✓')

    # ── Step5: 输出 ──
    print(f'\n[Step5] 生成 6-Sheet 输出...')
    build_output(
        records=records,
        model_results=model_results,
        aggregated=aggregated,
        issues=issues,
        log_entries=log_entries,
        original_path=str(input_path),
        output_path=str(out_path),
        project_name=project,
    )

    # ── 汇总 ──
    print(f'\n{"─" * 110}')
    print(f'{"规格型号":<48} {"数量(m)":>10}')
    print(f'{"─" * 110}')
    total_qty = 0
    for a in aggregated:
        print(f'{a["model"]:<48} {int(a["qty"]):>10}')
        total_qty += a['qty']
    print(f'{"─" * 110}')
    print(f'{"合计":>58} {int(total_qty):>10}')

    print(f'\n{"=" * 60}')
    print(f'原始 {len(records)} 条 → 聚合 {len(aggregated)} 行')
    print(f'非电缆排除: {len(non_cable)} 条')
    print(f'解析失败: {fail_count} 条')
    print(f'N/PE 警告: {warn_count} 条')
    print(f'输出文件: {out_path}')
    print(f'{"=" * 60}\n')


def sort_key(model):
    """标准排序（与 aggregator.sort_key 一致）"""
    if '10kV' in model or '35kV' in model: return (0, model)
    if 'BBTRZ' in model: return (1, model)
    if 'YJV22' in model: return (2, model)
    if re.search(r'N-YJV|WDZBN|WDZN-YJY|WDZA.*YJY|WDZB.*YJY', model): return (3, model)
    if re.search(r'YJV-0\.|YJY-0\.', model): return (4, model)
    if 'KYJYP' in model: return (5, model)
    if 'KYJY' in model: return (6, model)
    if re.search(r'^(?:N-)?BV(?!R)', model): return (7, model)
    if re.search(r'^(?:N-)?BVR', model): return (8, model)
    if re.search(r'BYJ|BYJR', model): return (9, model)
    if re.search(r'RYJSP|RYSP|RYJS|RVS', model): return (10, model)
    return (11, model)


if __name__ == '__main__':
    main()
