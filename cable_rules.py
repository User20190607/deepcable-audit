"""
cable_rules.py — GB/T 19666 型号规则常量表（单一数据源）

tokenizer / parser / normalizer / aggregator 共用这里的定义，
避免同一份前缀/型号清单在多个模块中重复维护。
"""

# ── 燃烧特性前缀（GB/T 19666-2019）───────────────────────────────
PREFIXES_LIST = [
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

# 按长度降序，避免短前缀提前匹配
PREFIXES = sorted(PREFIXES_LIST, key=len, reverse=True)
PREFIXES_SET = frozenset(PREFIXES)


# ── 基础型号 ──────────────────────────────────────────────────────
BASE_MODELS_LIST = [
    'YJV22', 'YJV', 'YJY', 'KYJYP', 'KYJY', 'KVV', 'KVVP',
    'RYJSP', 'RYSP', 'RYJS', 'RYS', 'RVS', 'RVSP', 'RVVSP',
    'DJYPVRP', 'DJYVP',
    'BYJR', 'BYJ', 'BVR', 'BV',
    'RYJY', 'RYY', 'RVV', 'RVVP',
    'BBTRZ', 'RTTYZ', 'RTTVZ', 'RTTZ', 'RZDJ', 'RZDF',
    'BVV', 'KYJP', 'RYJ',
]

BASE_MODELS = sorted(BASE_MODELS_LIST, key=len, reverse=True)
BASE_MODELS_SET = frozenset(BASE_MODELS_LIST)


# ── 布电线（单芯线，聚合时按芯数拆分）────────────────────────────
SINGLE_CORE_WIRES = {'BYJ', 'BYJR', 'BVR', 'BV'}


def _build_regex() -> str:
    """构建 prefix[-]base 匹配正则片段（不捕获，仅用于 finditer/match）

    注意：
      1. '-' 必须在 prefix alternation 外层，不能绑在 'N-' 上，
         否则 WDZN-YJV 会被错误匹配为 N-YJV（跳过 WDZ 后从位置 3 重匹配）。
      2. prefix 与 base 之间除 '-' 外还允许"直接粘连"（lookahead 确认后面
         紧跟已知 base），否则 NHYJV/ZCYJV/WDZBNYJY 这类无横杠写法整体
         匹配失败，tokenizer 回退正则会从中间截取 'YJV…' 导致前缀丢失。
    """
    prefix_pat = '|'.join(PREFIXES)
    base_pat = '|'.join(f'{b}(?![A-Z])' for b in BASE_MODELS)
    # 末尾 '[A-Z]+(?=\d)' 分支：兼容不在表内但"字母+数字"粘连的写法（如 KYJVP7×1.5）
    return (rf'(?:(?:{prefix_pat})(?:-|(?=(?:{base_pat}))))?'
            rf'(?:{base_pat}|[A-Z]+(?=\d))')


MODEL_START_RE = _build_regex()
