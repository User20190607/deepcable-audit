"""
deepcable_read_excel.py
从原始 Excel 清单中提取型号和数量
Claude Code 可直接调用

支持格式：
  - 列名模糊匹配（项目名称/规格型号/型号/名称）
  - 单位列过滤（只取 m/米）
  - 多 Sheet 自动合并
  - 描述性文字提取型号（如"1.名称:电缆 2.规格:WDZN-..."）

用法：
    from deepcable_read_excel import read_cable_list
    records = read_cable_list('原始清单.xlsx')
    # → [{'raw': '型号字符串', 'qty': 数量, 'sheet': 'Sheet1', 'row': 5}, ...]
"""

import pandas as pd
import re


# 列名关键词匹配
NAME_KEYWORDS = ['规格型号', '物料名称', '型号', '名称', '规格', 'spec', 'description', '项目名称', '材料名称']
UNIT_KEYWORDS = ['单位', '计量单位', 'unit']
QTY_KEYWORDS  = ['数量', '工程量', '申购量', '可申请量', 'qty', 'quantity']
SKIP_UNITS    = ['-', 'nan', '']
VALID_UNITS   = ['m', '米', 'M']


def _find_col(df_cols, keywords):
    """模糊匹配列名，返回第一个匹配的列索引"""
    cols = [str(c).strip() for c in df_cols]
    for kw in keywords:
        for i, col in enumerate(cols):
            if kw.lower() in col.lower():
                return i
    return None


def _extract_spec_from_desc(text: str) -> str:
    """从描述性文字中提取型号（如：1.名称:xx 2.规格:WDZN-...）"""
    # 优先找"规格"或"型号"字段
    m = re.search(r'(?:规格|型号|spec)[：:]\s*([A-Z][\w\-\./×\*\+\s]+)', text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text


def read_cable_list(filepath: str, sheet_name=None) -> list[dict]:
    """
    读取原始清单 Excel，返回标准记录列表

    参数：
        filepath:   Excel 文件路径
        sheet_name: 指定 Sheet 名，None 表示读取所有 Sheet

    返回：
        [{'raw': str, 'qty': float, 'sheet': str, 'row': int}, ...]
    """
    xl = pd.ExcelFile(filepath)
    sheets = [sheet_name] if sheet_name else xl.sheet_names

    records = []

    for sheet in sheets:
        df = pd.read_excel(filepath, sheet_name=sheet, header=None, dtype=str)
        if df.empty or df.shape[1] == 0:
            continue

        # 自动检测表头行（找包含关键词最多的行，型号/数量列权重×2）
        header_row = 0
        best_score = 0
        for i in range(min(10, len(df))):
            row_str = ' '.join([str(v) for v in df.iloc[i].tolist()])
            score = (
                sum(2 for kw in NAME_KEYWORDS if kw.lower() in row_str.lower()) +
                sum(2 for kw in QTY_KEYWORDS  if kw.lower() in row_str.lower()) +
                sum(1 for kw in UNIT_KEYWORDS if kw.lower() in row_str.lower())
            )
            if score > best_score:
                best_score = score
                header_row = i

        df.columns = df.iloc[header_row].tolist()
        df = df.iloc[header_row + 1:].reset_index(drop=True)

        # 找各列
        name_col = _find_col(df.columns, NAME_KEYWORDS)
        unit_col = _find_col(df.columns, UNIT_KEYWORDS)
        qty_col  = _find_col(df.columns, QTY_KEYWORDS)

        if name_col is None or qty_col is None:
            continue  # 这个 Sheet 没有可识别的列

        for i, row in df.iterrows():
            raw_name = str(row.iloc[name_col]).strip() if pd.notna(row.iloc[name_col]) else ''
            raw_unit = str(row.iloc[unit_col]).strip() if unit_col is not None and pd.notna(row.iloc[unit_col]) else 'm'
            raw_qty  = row.iloc[qty_col]

            # 过滤空行
            if not raw_name or raw_name in ['nan', 'None', '项目名称', '合计', '小计']:
                continue

            # 单位过滤
            if raw_unit not in VALID_UNITS and raw_unit not in ['nan', '', '-']:
                # 非米单位：跳过（如个、套、台）
                # 但"棒""捆"等疑似米的非标单位保留并标注
                if any(kw in raw_unit for kw in ['棒', '捆', '盘', '卷', '扎']):
                    pass  # 保留，后续单位换算处理
                else:
                    continue

            # 数量解析
            try:
                qty = float(str(raw_qty).replace(',', '').strip())
            except (ValueError, TypeError):
                continue
            if qty <= 0:
                continue

            # 描述性文字提取型号
            raw_model = _extract_spec_from_desc(raw_name.replace('\n', ' '))

            records.append({
                'raw':   raw_model,
                'qty':   qty,
                'sheet': sheet,
                'row':   header_row + i + 2,  # Excel 行号（1-indexed）
            })

    return records


def read_tsv(text: str) -> list[dict]:
    """
    从粘贴的 TSV 文本中读取型号和数量
    支持格式：型号\\t单位\\t数量
    """
    records = []
    for line in text.strip().splitlines():
        parts = line.split('\t')
        if len(parts) >= 3:
            try:
                qty = float(parts[2].strip().replace(',', ''))
                records.append({'raw': parts[0].strip(), 'qty': qty})
            except ValueError:
                continue
    return records
