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
from cable_rules import PREFIXES, MODEL_START_RE

# 主型号提取正则（预编译）：prefix[-]base + 后续规格字符
# MODEL_START_RE 的 base 带 (?![A-Z]) 前瞻，本身可以吃掉 KYJVP7X1.5 这类
# "型号后直接粘数字"的写法；但原实现要求尾随 [\w...]+ 至少一个字符且不含
# 前瞻协调，导致 'KYJVP7X1.5' 整体匹配失败。这里把尾部改为可重复的
# 规格字符集（允许为空），确保只要前缀+基础型号成立就能提取整段。
_MODEL_RE = re.compile(rf'({MODEL_START_RE}[0-9]*(?:[0-9]*[\w\s\*\.\+/×-]*)*)')


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
# BASE_MODELS / PREFIXES 定义见 cable_rules.py（单一数据源）


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

    # 提取主型号（正则已预编译，见 _MODEL_RE / cable_rules.MODEL_START_RE）
    # 注意：'-' 在 prefix alternation 外层，不能绑在 'N-' 上，
    # 否则 WDZN-YJV 会被错误匹配为 N-YJV（跳过 WDZ 后在位置 3 重匹配）
    start = re.search(r'[A-Z]', r)  # 第一个大写字母 = 型号起点（跳过"电缆"等中文前缀）
    if start:
        body = r[start.start():]
        m = _MODEL_RE.match(body)
        # 匹配失败时保留从型号起点开始的完整字符串（交由 parser 兜底解析），
        # 不能退回整串——否则中文前缀会混入 cleaned，导致 parser 前缀匹配失败、
        # 进而丢失 NH/ZC 等燃烧特性前缀。
        source = m.group(1).strip() if m else body
        cleaned = re.sub(r'\s+', '', source)
    else:
        cleaned = re.sub(r'\s+', '', r)

    return TokenResult(cleaned, color, 'cable')
