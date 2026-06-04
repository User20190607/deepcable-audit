"""
tokenizer.py — 原始字符串 → 初步 token

职责：
  1. 清理原始字符串（大写、去换行、去空格）
  2. 提取颜色后缀
  3. 检测 PV1-F 光伏电缆（独立走）
  4. 提取主型号字符串（去除中文前缀、杂物）
  5. 返回 TokenResult 供 parser 使用

不负责：
  - 解析语义（那是 parser 的事）
  - 标准化（那是 normalizer 的事）
"""

import re
from typing import Optional, NamedTuple


class TokenResult(NamedTuple):
    """Tokenizer 的输出"""
    cleaned: str            # 清理后的纯型号字符串（无中文前缀、无颜色）
    color: str              # 提取的颜色后缀
    base_type: str          # 'cable' | 'pv' | 'unknown'


# ── 颜色后缀 ────────────────────────────────────────────────────────

COLORS = {'红', '蓝', '黄', '绿', '双色', '白', '黑', '棕', '灰', '紫'}


def extract_color(raw: str) -> tuple[str, str]:
    """提取末尾颜色后缀，返回 (去掉颜色的字符串, 颜色)"""
    m = re.search(r'[（(]([^）)]*)[）)]$', raw)
    if m and m.group(1) in COLORS:
        return raw[:m.start()].strip(), m.group(1)
    return raw, ''


# ── PV1-F 光伏电缆 ──────────────────────────────────────────────────

def detect_pv(raw: str) -> Optional[dict]:
    """
    如果是 PV1-F 光伏电缆，直接解析完成，返回 dict。
    否则返回 None。
    """
    r = raw.replace('-', '')
    if 'PV1F' not in r:
        return None

    # 颜色提取
    pv_color = ''
    ccm = re.search(r'[,，](红|黑|红色|黑色)', raw)
    if ccm:
        pv_color = ccm.group(1).replace('色', '')
        raw = raw[:ccm.start()]

    # 电压锁定 DC1500V
    pv_voltage = 'DC1500V'

    # 提取截面
    for pat in [r'1\*(\d+(?:\.\d+)?)', r'PV1-F-1\*(\d+(?:\.\d+)?)',
                r'1×(\d+(?:\.\d+)?)', r'PV1-F-1×(\d+(?:\.\d+)?)']:
        m = re.search(pat, raw)
        if m:
            return {
                'base': 'PV1-F',
                'voltage': pv_voltage,
                'cores': [{'count': 1, 'section': float(m.group(1))}],
                'color': pv_color,
            }
    return None


# ── 主型号提取 ───────────────────────────────────────────────────────

# 所有支持的基础型号（按长度降序排列，避免短型号提前匹配）
BASE_MODELS = sorted([
    'YJV22', 'YJV', 'YJY', 'KYJYP', 'KYJY', 'KVV', 'KVVP',
    'RYJSP', 'RYSP', 'RYJS', 'RYS', 'RVS', 'RVSP', 'RVVSP',
    'DJYPVRP', 'DJYVP',
    'BYJR', 'BYJ', 'BVR', 'BV',
    'RYJY', 'RYY', 'RVV', 'RVVP',
    'BBTRZ', 'RTTYZ', 'RTTVZ', 'RTTZ', 'RZDJ', 'RZDF',
    'BVV', 'KYJP', 'RYJ',
], key=len, reverse=True)

# 前缀（可选，按长度降序）
PREFIXES = sorted([
    # ── 无卤低烟低毒阻燃耐火 (WDUZ + grade + N/NJ/NS) ──
    'WDUZDNJ', 'WDUZDNS', 'WDUZDN',
    'WDUZCNJ', 'WDUZCNS', 'WDUZCN',
    'WDUZBNJ', 'WDUZBNS', 'WDUZBN',
    'WDUZANJ', 'WDUZANS', 'WDUZAN',
    'WDUZNJ', 'WDUZNS', 'WDUZN',
    # ── 无卤低烟低毒阻燃 (WDUZ + grade) ──
    'WDUZD', 'WDUZC', 'WDUZB', 'WDUZA', 'WDUZ',
    # ── 无卤低烟阻燃耐火 (WDZ + grade + N/NJ/NS) ──
    'WDZDNJ', 'WDZDNS', 'WDZDN',
    'WDZCNJ', 'WDZCNS', 'WDZCN',
    'WDZBNJ', 'WDZBNS', 'WDZBN',
    'WDZANJ', 'WDZANS', 'WDZAN',
    'WDZNJ', 'WDZNS', 'WDZN',
    # ── 无卤低烟阻燃 (WDZ + grade) ──
    'WDZD', 'WDZC', 'WDZB', 'WDZA', 'WDZ',
    # ── 含卤阻燃耐火 (Z[A~D] + N/NJ/NS) ──
    'ZDNJ', 'ZDNS', 'ZDN',
    'ZCNJ', 'ZCNS', 'ZCN',
    'ZBNJ', 'ZBNS', 'ZBN',
    'ZANJ', 'ZANS', 'ZAN',
    # ── 含卤阻燃 (Z[A~D]，单根 Z) ──
    'ZD', 'ZC', 'ZB', 'ZA', 'ZR', 'Z',
    # ── 纯耐火 (含卤) ──
    'NJ', 'NS', 'N',
    # ── 废弃代号 ──
    'NH',
], key=len, reverse=True)


def tokenize(raw: str) -> TokenResult:
    """
    原始字符串 → TokenResult

    示例：
        tokenize('电缆NHYJV-0.6/1KV- 5X16')  → TokenResult('NHYJV-0.6/1KV-5X16', '', 'cable')
        tokenize('电缆ZC-YJV-0.6/1KV-4×25+1×16(红)') → TokenResult('ZC-YJV-0.6/1KV-4×25+1×16', '红', 'cable')
    """
    # 大写、去换行、去首尾空格
    r = raw.upper().replace('\n', ' ').strip()

    # 提取颜色
    r, color = extract_color(r)

    # PV1-F 检测
    pv_result = detect_pv(r)
    if pv_result:
        return TokenResult(r, pv_result['color'], 'pv')

    # 构建主型号提取正则
    # 注意：- 必须在 prefix alternation 外层，不能绑在 N- 上
    # 否则 WDZN-YJV 会被错误匹配为 N-YJV (跳过 WDZ 在位置3重匹配)
    prefix_pattern = '|'.join(PREFIXES)
    base_pattern = '|'.join(f'{b}(?![A-Z])' for b in BASE_MODELS)

    # 找到第一个大写字母作为型号起点（跳过中文前缀如"电缆"）
    start = re.search(r'[A-Z]', r)
    if start:
        r_from_letter = r[start.start():]
        m = re.match(
            rf'((?:(?:{prefix_pattern})-)?'   # - 在外层，所有前缀统一要求
            rf'(?:{base_pattern})'
            r'[\w\s\*\.\+/×-]+)',
            r_from_letter
        )
        if m:
            cleaned = re.sub(r'\s+', '', m.group(1).strip())
        else:
            cleaned = re.sub(r'\s+', '', r)
    else:
        cleaned = re.sub(r'\s+', '', r)

    return TokenResult(cleaned, color, 'cable')
