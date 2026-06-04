"""
parser.py — token → CableSpec AST

职责：
  1. 格式统一（乘号、单位清理）
  2. 解析前缀、基础型号、电压、芯线
  3. 返回 CableSpec 结构

不负责：
  - 标准化/修正（那是 normalizer 的事）
  - 校验（那是 validation 的事）
"""

import re
from typing import Optional
from spec import CableSpec, CoreSpec


# ── 已知型号列表 ────────────────────────────────────────────────────
# 预编译：按长度降序排列，避免短型号提前匹配

_PREFIXES_LIST = [
    # ── 含连字符的复合前缀（先匹配，更长）──
    'NH-ZC', 'NH-ZB', 'NH-ZA',
    'N-ZC', 'N-ZB', 'N-ZA', 'N-ZD', 'N-Z',
    'N-WDZC', 'N-WDZB', 'N-WDZA',
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
]
PREFIXES = sorted(_PREFIXES_LIST, key=len, reverse=True)
_PREFIXES_SET = frozenset(PREFIXES)

_BASE_MODELS_LIST = [
    'YJV22', 'YJV', 'YJY', 'KYJYP', 'KYJY', 'KVV', 'KVVP',
    'RYJSP', 'RYSP', 'RYJS', 'RYS', 'RVS', 'RVSP',
    'DJYPVRP', 'DJYVP',
    'BYJR', 'BYJ', 'BVR', 'BV',
    'RYJY', 'RYY', 'RVV', 'RVVP',
    'BBTRZ', 'RTTYZ', 'RTTVZ', 'RTTZ', 'RZDJ', 'RZDF',
    'BVV', 'KYJP', 'RYJ',
]
BASE_MODELS = sorted(_BASE_MODELS_LIST, key=len, reverse=True)

# 用于检查 rest 是否以已知 base 开头（支持无短横前缀）
_BASE_SET = frozenset(_BASE_MODELS_LIST)

# 预编译正则
_V_VOLTAGE_PATTERN = r'(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?[kK][vV])'
_CORE_PATTERN = r'(\d+)[xX×*](\d+(?:\.\d+)?)'
_VOLTAGE_RE = re.compile(_V_VOLTAGE_PATTERN)
_CORE_RE = re.compile(_CORE_PATTERN)


# ── 格式统一 ─────────────────────────────────────────────────────────

def unify_format(s: str) -> str:
    """预处理：统一乘号、清理单位等"""
    s = re.sub(r'[xX×*]', '×', s)
    s = re.sub(r'MM2$', '', s, flags=re.IGNORECASE)
    s = re.sub(r'MM²$', '', s)
    s = re.sub(r'平方', '', s)
    return s


# ── 主解析逻辑 ───────────────────────────────────────────────────────

def parse(model_str: str, color: str = '', is_pv: bool = False) -> Optional[CableSpec]:
    """
    解析纯型号字符串 → CableSpec AST

    参数：
        model_str: tokenizer 输出的 cleaned 字符串
        color: tokenizer 提取的颜色后缀
        is_pv: 是否为光伏电缆

    返回：
        CableSpec 或 None（解析失败）

    示例：
        parse('NHYJV-0.6/1KV-5X16') → CableSpec(prefix='NH', base='YJV', voltage='0.6/1kV', cores=[CoreSpec(5, 16)])
    """
    r = unify_format(model_str)

    spec = CableSpec(
        raw=model_str,
        color=color,
        is_pv=is_pv,
    )

    # PV1-F 用特殊路径
    if is_pv:
        spec.base = 'PV1-F'
        spec.voltage = 'DC1500V'
        m = re.search(r'1×(\d+(?:\.\d+)?)', r)
        if m:
            spec.cores = [CoreSpec(1, float(m.group(1)))]
        return spec

    # Step 1: 提取前缀
    for prefix in sorted(PREFIXES, key=len, reverse=True):
        if r.startswith(prefix):
            rest = r[len(prefix):]
            # 接受三种情况：
            #   1. 前缀后带短横: NH-YJV
            #   2. 前缀到结尾: just "NH"
            #   3. 无短横直接跟已知 base: NHYJV, NHBV
            if (not rest or rest[0] == '-'
                or any(rest.startswith(b) for b in BASE_MODELS)):
                spec.prefix = prefix
                r = rest.lstrip('-')
                break

    # Step 2: 提取 B1/B2 标志
    if 'B1-' in r or '-B1-' in r or r.startswith('B1'):
        spec.b1 = True
        r = re.sub(r'B1-?', '', r)
    elif 'B2-' in r or '-B2-' in r or r.startswith('B2'):
        spec.b2 = True
        r = re.sub(r'B2-?', '', r)

    # Step 3: 提取基础型号
    found_base = False
    for base in sorted(BASE_MODELS, key=len, reverse=True):
        if r.startswith(base):
            spec.base = base
            r = r[len(base):].lstrip('-')
            found_base = True
            break

    if not found_base:
        # 尝试用正则查找
        base_pat = '|'.join(sorted(BASE_MODELS, key=len, reverse=True))
        m = re.search(rf'({base_pat})', r)
        if m:
            spec.base = m.group(1)
            r = r[m.end():].lstrip('-')
        else:
            # 实在找不到，整个当 base 吧
            spec.base = r
            return spec

    # Step 4: 提取电压
    vm = _VOLTAGE_RE.search(r)
    if vm:
        spec.voltage = vm.group(1)
        r = r[:vm.start()] + r[vm.end():]
        r = r.strip('-')

    # Step 5: 提取芯线
    cores = _parse_cores(r)
    if cores:
        spec.cores = cores

    return spec


def _parse_cores(s: str) -> list[CoreSpec]:
    """解析芯线规格字符串 → CoreSpec 列表"""
    s = s.strip().strip('-')
    if not s:
        return []

    # + 分隔的多芯组合：4×25+1×16
    parts = re.split(r'\s*\+\s*', s)
    result = []
    for part in parts:
        m = _CORE_RE.search(part)
        if m:
            result.append(CoreSpec(int(m.group(1)), float(m.group(2))))
        # 裸数字 → 单芯线：BV2.5 → 1×2.5
        elif re.fullmatch(r'\d+(?:\.\d+)?', part):
            result.append(CoreSpec(1, float(part)))
    return result
