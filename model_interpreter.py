"""
model_interpreter.py — 电缆型号中文解释器

将标准化型号转译为逗号分隔的属性链，便于非专业人员快速理解电缆构成。

用法：
    from model_interpreter import interpret_model

    interpret_model('N-YJV22-0.6/1kV-4×25')
    # → '铜芯，云母带，XLPE绝缘，聚氯乙烯护套，镀锌钢带铠装，电力电缆'

    interpret_model('ZC-RVS-300/300V-2×1.5')
    # → '阻燃C级，导体5类，聚氯乙烯绝缘，双绞线'
"""

import re


# ── 基础型号属性表 ─────────────────────────────────────────────────────
# conductor: None = 需动态确定（BV 按截面），str = 固定导体描述
# attrs: 构造属性（绝缘/屏蔽/护套/铠装）
# cat: 品类

MODEL_INFO = {
    # ── 电力电缆 ──
    'YJV':   {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '聚氯乙烯护套'], 'cat': '电力电缆'},
    'YJY':   {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '聚乙烯护套'], 'cat': '电力电缆'},
    'YJV22': {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '聚氯乙烯护套', '镀锌钢带铠装'], 'cat': '电力电缆'},
    'YJV23': {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '聚乙烯护套', '镀锌钢带铠装'], 'cat': '电力电缆'},
    'YJV32': {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '聚氯乙烯护套', '钢丝铠装'], 'cat': '电力电缆'},
    'YJV33': {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '聚乙烯护套', '钢丝铠装'], 'cat': '电力电缆'},
    'YJV42': {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '聚氯乙烯护套', '粗钢丝铠装'], 'cat': '电力电缆'},
    'YJV43': {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '聚乙烯护套', '粗钢丝铠装'], 'cat': '电力电缆'},
    'VV':    {'conductor': '铜芯', 'attrs': ['聚氯乙烯绝缘', '聚氯乙烯护套'], 'cat': '电力电缆'},
    'VY':    {'conductor': '铜芯', 'attrs': ['聚氯乙烯绝缘', '聚乙烯护套'], 'cat': '电力电缆'},

    # ── 控制电缆 ──
    'KVV':   {'conductor': '铜芯', 'attrs': ['聚氯乙烯绝缘', '聚氯乙烯护套'], 'cat': '控制电缆'},
    'KVVP':  {'conductor': '铜芯', 'attrs': ['聚氯乙烯绝缘', '屏蔽', '聚氯乙烯护套'], 'cat': '控制电缆'},
    'KYJY':  {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '聚乙烯护套'], 'cat': '控制电缆'},
    'KYJYP': {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '屏蔽', '聚乙烯护套'], 'cat': '控制电缆'},

    # ── 布电线 ──
    'BV':    {'conductor': None,   'attrs': ['聚氯乙烯绝缘'], 'cat': '布电线'},
    'BVR':   {'conductor': '导体2类，多股软导体', 'attrs': ['聚氯乙烯绝缘'], 'cat': '布电线'},
    'BYJ':   {'conductor': None,   'attrs': ['XLPE绝缘'], 'cat': '布电线'},
    'BYJR':  {'conductor': '导体2类，多股软导体', 'attrs': ['XLPE绝缘'], 'cat': '布电线'},
    'BVV':   {'conductor': '铜芯', 'attrs': ['聚氯乙烯绝缘', '聚氯乙烯护套'], 'cat': '布电线'},

    # ── 软线 / 护套线 ──
    'RVS':   {'conductor': '导体5类', 'attrs': ['聚氯乙烯绝缘'], 'cat': '双绞线'},
    'RYJS':  {'conductor': '导体5类', 'attrs': ['XLPE绝缘'], 'cat': '双绞线'},
    'RVSP':  {'conductor': '导体5类', 'attrs': ['聚氯乙烯绝缘', '屏蔽'], 'cat': '双绞线'},
    'RYJSP': {'conductor': '导体5类', 'attrs': ['XLPE绝缘', '屏蔽'], 'cat': '双绞线'},
    'RVV':   {'conductor': '导体5类', 'attrs': ['聚氯乙烯绝缘', '聚氯乙烯护套'], 'cat': '护套线'},
    'RVVP':  {'conductor': '导体5类', 'attrs': ['聚氯乙烯绝缘', '屏蔽', '聚氯乙烯护套'], 'cat': '护套线'},
    'RYJY':  {'conductor': '导体5类', 'attrs': ['XLPE绝缘', '聚乙烯护套'], 'cat': '软电缆'},
    'RYJYP': {'conductor': '导体5类', 'attrs': ['XLPE绝缘', '屏蔽', '聚乙烯护套'], 'cat': '软电缆'},
    'RYY':   {'conductor': '导体5类', 'attrs': ['聚氯乙烯绝缘', '聚氯乙烯护套'], 'cat': '软电缆'},

    # ── 矿物绝缘 ──
    'BBTRZ': {'conductor': '铜芯', 'attrs': ['矿物绝缘'], 'cat': '防火电缆'},
    'RTTZ':  {'conductor': '铜芯', 'attrs': ['矿物绝缘'], 'cat': '防火电缆'},
    'RTTYZ': {'conductor': '铜芯', 'attrs': ['矿物绝缘'], 'cat': '防火电缆'},
    'RTTVZ': {'conductor': '铜芯', 'attrs': ['矿物绝缘'], 'cat': '防火电缆'},

    # ── 仪表/计算机 ──
    'DJYPVRP': {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '屏蔽', '聚氯乙烯护套'], 'cat': '计算机电缆'},
    'DJYVP':   {'conductor': '铜芯', 'attrs': ['XLPE绝缘', '屏蔽'], 'cat': '计算机电缆'},

    # ── 光伏 ──
    'PV1-F': {'conductor': '铜芯', 'attrs': [], 'cat': '光伏电缆'},

    # ── 电机引接线 ──
    'RZDJ':  {'conductor': '铜芯', 'attrs': ['热塑性弹性体绝缘'], 'cat': '电机引接线'},
    'RZDF':  {'conductor': '铜芯', 'attrs': ['热塑性弹性体绝缘', '热塑性弹性体护套'], 'cat': '电机引接线'},
}

# 型号匹配顺序（长优先）
_BASE_LIST = sorted(MODEL_INFO.keys(), key=len, reverse=True)

# 前缀匹配顺序（长优先）
_PREFIX_LIST = [
    'WDZBN', 'WDZAN', 'WDZCN', 'WDZN', 'WDZC', 'WDZA', 'WDZB',
    'WDUZ', 'ZCN', 'ZBN', 'ZAN', 'ZC', 'ZA', 'ZB', 'ZR', 'N',
]


# ── 前缀解析 ──────────────────────────────────────────────────────────

def _parse_prefix_attrs(prefix: str) -> tuple[list[str], str]:
    """
    解析燃烧特性前缀，返回 (prefix_attrs, n_attr)。
    prefix_attrs 放在型号属性链最前面（如 无卤低烟，阻燃C级）
    n_attr（云母带/耐火层）放在导体之后、绝缘之前
    """
    if not prefix:
        return [], ''

    p = prefix.upper()
    prefix_attrs = []
    has_n = False

    # 无卤低烟
    if 'WD' in p or 'WDU' in p:
        prefix_attrs.append('无卤低烟')

    # 阻燃等级
    if 'ZA' in p:
        prefix_attrs.append('阻燃A级')
    elif 'ZB' in p:
        prefix_attrs.append('阻燃B级')
    elif 'ZC' in p or 'ZR' in p:
        prefix_attrs.append('阻燃C级')
    elif 'Z' in p and p != 'N':
        # 单独 Z（如 WDZN 中的 Z）→ 默认 C 类
        prefix_attrs.append('阻燃C级')

    # 耐火：末尾 N 表示耐火构造（云母带）
    if p.endswith('N'):
        has_n = True

    return prefix_attrs, ('云母带' if has_n else '')


# ── 型号分解 ──────────────────────────────────────────────────────────

def _split_model(model: str) -> dict:
    """将标准化型号分解为 {prefix, b1, base, voltage, cores, color}"""
    result = {'prefix': '', 'b1': False, 'base': '', 'voltage': '', 'cores': '', 'color': ''}
    work = model

    # 颜色后缀
    m = re.search(r'[（(]([^）)]*)[）)]$', work)
    if m:
        result['color'] = m.group(1)
        work = work[:m.start()]

    # 前缀
    for p in _PREFIX_LIST:
        if work.startswith(p):
            result['prefix'] = p
            work = work[len(p):].lstrip('-')
            break

    # B1
    if '-B1-' in work or work.endswith('-B1'):
        result['b1'] = True
        work = work.replace('-B1-', '-')
        if work.endswith('-B1'):
            work = work[:-3]
        work = work.lstrip('-')

    # 基础型号
    for b in _BASE_LIST:
        if work.startswith(b):
            result['base'] = b
            work = work[len(b):].lstrip('-')
            break

    # 电压（DC / AC）
    m = re.search(r'^(DC\d+(?:\.\d+)?[kK]?V)-?', work)
    if not m:
        m = re.search(r'^(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?[kK]?V)-?', work)
    if m:
        result['voltage'] = m.group(1)
        work = work[m.end():]

    # 剩余 = 芯线规格
    result['cores'] = work.rstrip('-')
    return result


# ── 导体描述（BV 按截面动态判断） ─────────────────────────────────────

def _get_first_section(core_str: str) -> float | None:
    """从芯线串提取第一根截面，如 4×25+1×16 → 25.0"""
    m = re.search(r'×(\d+(?:\.\d+)?)', core_str)
    if m:
        return float(m.group(1))
    return None


def _get_conductor(base: str, core_str: str, info: dict) -> str:
    """获取导体描述"""
    if info['conductor'] is not None:
        return info['conductor']
    # BV/BYJ 动态判断
    section = _get_first_section(core_str)
    if section is not None and section <= 10:
        return '单根硬导体'
    return '导体1类'


# ── 主入口 ─────────────────────────────────────────────────────────────

def interpret_model(model: str) -> str:
    """
    解释标准化电缆型号，返回逗号分隔的属性链。

    参数：
        model: 标准化型号（如 'N-YJV-0.6/1kV-5×16'）

    返回：
        str: 属性链（如 '铜芯，云母带，XLPE绝缘，聚氯乙烯护套，电力电缆'）
    """
    if not model:
        return ''

    parts = _split_model(model)
    info = MODEL_INFO.get(parts['base'])

    if not info:
        # 无法识别的型号，返回原始型号
        return model

    # 前缀属性（放在最前面）
    prefix_attrs, n_attr = _parse_prefix_attrs(parts['prefix'])

    # 导体
    conductor = _get_conductor(parts['base'], parts['cores'], info)

    # 装配输出
    out = []

    # 1. 前缀特性（无卤低烟，阻燃X级）
    out.extend(prefix_attrs)

    # 2. B1 级阻燃
    if parts['b1']:
        out.append('B1级阻燃')

    # 3. 导体
    out.append(conductor)

    # 4. 云母带（耐火构造，导体之后）
    if n_attr:
        out.append(n_attr)

    # 5. 绝缘 / 屏蔽 / 护套 / 铠装
    out.extend(info['attrs'])

    # 6. 品类
    out.append(info['cat'])

    return '，'.join(out)


# ── 简版解释（Sheet3 采购清单用） ──────────────────────────────────────

def interpret_model_short(model: str) -> str:
    """
    一句话解释，面向采购人员。如：
    '无卤阻燃B类铜芯电力电缆 0.6/1kV'
    """
    if not model:
        return ''

    parts = _split_model(model)
    info = MODEL_INFO.get(parts['base'])
    if not info:
        return model

    fragments = []

    p = parts['prefix'].upper()
    if 'WD' in p:
        fragments.append('无卤')
    if 'ZA' in p:
        fragments.append('阻燃A类')
    elif 'ZB' in p:
        fragments.append('阻燃B类')
    elif 'ZC' in p or 'ZR' in p:
        fragments.append('阻燃C类')
    if 'N' in p:
        fragments.append('耐火')

    conductor = _get_conductor(parts['base'], parts['cores'], info)
    if conductor not in ('单根硬导体', '导体1类'):
        fragments.append(conductor)

    fragments.append(info['cat'])

    if parts['voltage']:
        fragments.append(parts['voltage'])

    return ' '.join(fragments)


# ── 通俗解释（Sheet4 非专业人员用） ─────────────────────────────────────

def interpret_model_simple(model: str) -> dict:
    """
    详细通俗解释，返回字典包含字段：
        plain, insulation, fire_rating, halogen_free, scenario, caution
    """
    if not model:
        return {k: '' for k in ('plain', 'insulation', 'fire_rating',
                                 'halogen_free', 'scenario', 'caution')}

    parts = _split_model(model)
    info = MODEL_INFO.get(parts['base'])
    if not info:
        return {'plain': model, 'insulation': '', 'fire_rating': '',
                'halogen_free': '—', 'scenario': '', 'caution': ''}

    p = parts['prefix'].upper()

    # 一句话解释
    short = interpret_model_short(model)

    # 绝缘/护套材质
    ins_parts = []
    if info['attrs']:
        for a in info['attrs']:
            if '绝缘' in a:
                ins_parts.append(a)
            if '护套' in a:
                ins_parts.append(a)
    insulation = ' / '.join(ins_parts)

    # 阻燃耐火等级
    fire = ''
    if 'ZA' in p: fire = '阻燃A级'
    elif 'ZB' in p: fire = '阻燃B级'
    elif 'ZC' in p or 'ZR' in p: fire = '阻燃C级'
    if 'N' in p:
        fire = fire + ' 耐火' if fire else '耐火'
    if parts['b1']:
        fire = 'B1级阻燃' + (f' {fire}' if fire else '')

    # 是否无卤
    halogen_free = '是' if 'WD' in p else '否'
    # LSOH / PE 外护套的特殊处理
    if 'YJY' in parts['base'] or 'YJLY' in parts['base']:
        if 'WD' in p:
            halogen_free = '是（低烟无卤聚烯烃）'
        else:
            halogen_free = '否（聚乙烯护套，燃烧产生黑烟）'

    # 适用场景
    scenario = _infer_scenario(parts, info)

    # 注意事项
    caution = _infer_caution(parts, info)

    return {
        'plain': short,
        'insulation': insulation,
        'fire_rating': fire,
        'halogen_free': halogen_free,
        'scenario': scenario,
        'caution': caution,
    }


def _infer_scenario(parts: dict, info: dict) -> str:
    """根据型号推断适用场景"""
    base = parts['base']
    p = parts['prefix'].upper()
    cat = info['cat']
    scenarios = []

    if '防火' in cat or 'BBTRZ' in base or 'RTTZ' in base:
        scenarios.append('消防干线/应急照明')
    if 'N' in p:
        scenarios.append('消防回路')
    if 'WD' in p:
        scenarios.append('人员密集场所/医院/学校/地铁')
    if 'K' in base:
        scenarios.append('控制信号传输')
    if 'DJ' in base:
        scenarios.append('计算机/仪表信号')
    if 'BV' in base or 'BYJ' in base:
        scenarios.append('室内明敷/穿管敷设')
    if 'R' in base and 'K' not in base and 'DJ' not in base:
        scenarios.append('设备连接/盘柜配线')
    if '22' in base or '23' in base:
        scenarios.append('直埋/电缆沟敷设')
    if '32' in base or '33' in base:
        scenarios.append('竖井/垂直敷设')
    if 'PV' in base:
        scenarios.append('光伏系统')

    return '；'.join(scenarios) if scenarios else '通用敷设'


def _infer_caution(parts: dict, info: dict) -> str:
    """注意事项"""
    base = parts['base']
    p = parts['prefix'].upper()
    notes = []

    if '22' in base or '23' in base:
        notes.append('铠装层需可靠接地')
    if 'WD' in p:
        notes.append('需与同等阻燃等级桥架配套')
    if 'N' in p:
        notes.append('耐火接头配套使用')
    if info['cat'] == '控制电缆' and 'P' in base:
        notes.append('屏蔽层单端接地')

    return '；'.join(notes) if notes else ''
