"""
excel_output.py — 标准化采购清单 Excel 输出

职责：
  1. 生成格式化的采购清单 Excel
  2. 颜色合并（同型号不同颜色合并为一行）
  3. 校验警告标记（红色底色）
  4. 原始数据索引 Sheet（用于追溯）
"""

import re
import math
from collections import defaultdict
from typing import Optional

from validation import check_pe
from aggregator import sort_key


# 样式常量
HEADER_FILL = '1A3A6B'
ALT_ROW_FILL = 'EEF4FB'
TOTAL_FILL = 'D6E4F0'
WARN_FILL = 'FDECEA'

COLOR_ORDER = {
    '黄': 0, '绿': 1, '红': 2, '蓝': 3,
    '黑': 4, '白': 5, '双色': 6, '双': 6,
}


def to_excel(aggregated: dict, output_path: str, index_log: list = None,
             records: list = None) -> int:
    """
    生成标准化采购清单 Excel。

    参数：
        aggregated:   {标准型号: 数量}
        output_path:  输出路径
        index_log:    原始数据索引（可选）
        records:      原始记录列表（含 patch_log，可选，用于验算报告）

    返回：输出行数
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = '标准化采购清单'

    # 边框
    thin = Side(style='thin', color='CCCCCC')
    bd = Border(left=thin, right=thin, top=thin, bottom=thin)

    # 颜色合并
    merged = _merge_colors(aggregated)
    merged.sort(key=lambda x: sort_key(x[0]))

    # 写数据
    _write_header(ws, bd)
    for idx, (model, qty, remark) in enumerate(merged, start=2):
        _write_row(ws, idx, model, qty, remark, bd)

    # 合计
    _write_total(ws, len(merged), bd)

    # 原始数据索引
    if index_log:
        _write_index_sheet(wb, index_log)

    # 合并验算报告
    _write_audit_sheet(wb, merged)

    ws.freeze_panes = 'A2'
    wb.save(output_path)
    return len(merged)


def _merge_colors(aggregated: dict) -> list[tuple]:
    """同型号不同颜色合并"""
    color_pat = re.compile(r'\(([^)]+)\)$')

    color_groups = defaultdict(list)
    plain_items = {}

    for model, qty in aggregated.items():
        m = color_pat.search(model)
        if m and m.group(1) in COLOR_ORDER:
            base = model[:m.start()]
            color_groups[base].append((m.group(1), qty))
        else:
            plain_items[model] = qty

    result = []
    for base, items in color_groups.items():
        total = sum(q for _, q in items)
        items.sort(key=lambda x: COLOR_ORDER.get(x[0], 99))
        remark = ' '.join(f'{c}{int(q)}' for c, q in items)
        result.append((base, total, remark))

    for model, qty in plain_items.items():
        result.append((model, qty, ''))

    return result


def _write_header(ws, border):
    """写表头行"""
    from openpyxl.styles import Font, PatternFill, Alignment

    headers = ['序号', '规格型号', '单位', '数量', '备注']
    col_widths = [8, 54, 8, 12, 30]
    hdr_fill = PatternFill('solid', fgColor=HEADER_FILL)
    hdr_font = Font(name='Arial', bold=True, color='FFFFFF', size=11)
    center = Alignment(horizontal='center', vertical='center')

    from openpyxl.utils import get_column_letter
    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        c = ws.cell(row=1, column=col, value=h)
        c.font = hdr_font
        c.fill = hdr_fill
        c.alignment = center
        c.border = border
        ws.column_dimensions[get_column_letter(col)].width = w
    ws.row_dimensions[1].height = 28


def _write_row(ws, row, model, qty, remark, border):
    """写一行数据"""
    from openpyxl.styles import Font, PatternFill, Alignment

    alt_fill = PatternFill('solid', fgColor=ALT_ROW_FILL)
    warn_fill = PatternFill('solid', fgColor=WARN_FILL)
    white_fill = PatternFill('solid', fgColor='FFFFFF')
    center = Alignment(horizontal='center', vertical='center')
    left = Alignment(horizontal='left', vertical='center')

    fill = alt_fill if row % 2 == 0 else white_fill
    pe = check_pe(model)
    note = '; '.join(filter(None, [remark, pe['warning']]))
    row_fill = warn_fill if not pe['ok'] else fill

    vals = [row - 1, model, 'm', math.ceil(qty), note]
    for col, val in enumerate(vals, 1):
        c = ws.cell(row=row, column=col, value=val)
        c.fill = row_fill
        c.border = border
        c.alignment = center if col in (1, 3, 4) else left
        if col == 5 and not pe['ok']:
            c.font = Font(name='Arial', size=10, color='C0392B')
        else:
            c.font = Font(name='Arial', size=10)
    ws.row_dimensions[row].height = 20


def _write_total(ws, data_rows, border):
    """写合计行"""
    from openpyxl.styles import Font, PatternFill, Alignment

    total_fill = PatternFill('solid', fgColor=TOTAL_FILL)
    bold_font = Font(name='Arial', bold=True, size=10)
    center = Alignment(horizontal='center', vertical='center')

    total_row = data_rows + 2
    ws.cell(row=total_row, column=1, value='合　计').font = bold_font
    ws.cell(row=total_row, column=4, value=f'=SUM(D2:D{total_row - 1})').font = bold_font
    for col in range(1, 6):
        c = ws.cell(row=total_row, column=col)
        c.border = border
        c.alignment = center
        c.fill = total_fill
    ws.row_dimensions[total_row].height = 24


def _write_index_sheet(wb, index_log):
    """写原始数据索引 Sheet"""
    ws2 = wb.create_sheet('原始数据索引')
    ws2.append(['序号', '原始型号', '解析结果', '数量(m)', '状态'])
    for row in index_log:
        status = '✓' if row['model'] else '✗ 解析失败'
        ws2.append([row['seq'], row['raw'], row['model'] or '', row['qty'], status])

    ws2.column_dimensions['A'].width = 6
    ws2.column_dimensions['B'].width = 48
    ws2.column_dimensions['C'].width = 48
    ws2.column_dimensions['D'].width = 12
    ws2.column_dimensions['E'].width = 14


def _write_audit_sheet(wb, merged):
    """写合并验算报告 Sheet（N/PE 校验汇总）"""
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    ws = wb.create_sheet('合并验算报告')

    thin = Side(style='thin', color='CCCCCC')
    bd = Border(left=thin, right=thin, top=thin, bottom=thin)
    warn_fill = PatternFill('solid', fgColor=WARN_FILL)
    hdr_fill = PatternFill('solid', fgColor=HEADER_FILL)
    hdr_font = Font(name='Arial', bold=True, color='FFFFFF', size=11)
    center = Alignment(horizontal='center', vertical='center')
    left = Alignment(horizontal='left', vertical='center')

    headers = ['序号', '规格型号', '数量(m)', 'N/PE 校验', '说明']
    col_widths = [8, 54, 12, 12, 50]
    from openpyxl.utils import get_column_letter
    for col, (h, w) in enumerate(zip(headers, col_widths), 1):
        c = ws.cell(row=1, column=col, value=h)
        c.font = hdr_font
        c.fill = hdr_fill
        c.alignment = center
        c.border = bd
        ws.column_dimensions[get_column_letter(col)].width = w

    for idx, (model, qty, _) in enumerate(merged, start=2):
        pe = check_pe(model)
        result = '✓ 合格' if pe['ok'] else '⚠ 需复核'
        desc = pe.get('warning', '')
        row_fill = warn_fill if not pe['ok'] else None

        for col, val in enumerate([idx - 1, model, qty, result, desc], 1):
            c = ws.cell(row=idx, column=col, value=val)
            c.border = bd
            c.alignment = center if col in (1, 3, 4) else left
            c.font = Font(name='Arial', size=10,
                          color='C0392B' if col == 4 and not pe['ok'] else '000000')
            if row_fill:
                c.fill = row_fill

    ws.freeze_panes = 'A2'
