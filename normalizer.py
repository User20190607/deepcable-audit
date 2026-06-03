"""
normalizer.py — CableSpec AST → 标准化 CableSpec

应用 GB/T 19666 规则：
  1. 前缀标准化：NH → N, ZR → ZC, NH-ZC → ZCN
  2. 型号映射修正：RVS → RYJS, VV → YJV
  3. WD+V 材质互斥：YJV → YJY, KVV → KYJY
  4. KYJY 清理
  5. 电压格式统一和死锁补全
  6. 单芯补全
  7. 最终清理
"""

import re
from typing import Optional
from spec import CableSpec, CoreSpec


# ── 辅助函数 ─────────────────────────────────────────────────────────

SINGLE_CORE_WIRES = {'BYJ', 'BYJR', 'BVR', 'BV'}

VOLTAGE_MAP = [
    (['RYJSP', 'RYSP', 'RYJS', 'RVS'],    '300/300V'),
    (['KYJYP'],                            '450/750V'),
    (['KVVP', 'KYJV'],                     '450/750V'),
    (['KYJY'],                             '450/750V'),
    (['BYJR', 'BVR'],                      '450/750V'),
    (['WDZ-BYJ', 'BYJ', 'BV'],             '450/750V'),
    (['RYJY', 'RYY', 'RVV'],               '300/500V'),
    (['RYJYP', 'RVVP'],                    '300/300V'),
    (['BVV'],                              '300/500V'),
    (['DJYPVRP', 'DJYVP'],                 '300/500V'),
    (['RTTZ', 'RTTYZ', 'RTTVZ'],           '0.6/1kV'),
    (['RZDJ', 'RZDF'],                     '450/750V'),
]

RVSP_VOLTAGE = '300/300V'  # 须在RVS前匹配


# ── AST 级标准化 ─────────────────────────────────────────────────────

def normalize_ast(spec: CableSpec) -> CableSpec:
    """在 AST 层面直接修改字段"""
    _fix_prefix(spec)
    _fix_base_model(spec)
    _fix_wd_material(spec)
    return spec


def _fix_prefix(spec: CableSpec) -> None:
    """前缀标准化 per GB/T 19666-2019"""
    p = spec.prefix
    old = p

    # ── 1. 废弃代号替换 ──
    if p == 'NH':
        spec.prefix = 'N'
        p = 'N'
    elif p == 'ZR':
        spec.prefix = 'ZC'
        p = 'ZC'
    elif p == 'ZRC':
        spec.prefix = 'ZC'
        p = 'ZC'

    # ── 2. 顺序修正 (N-ZC → ZCN 等) ──
    order_map = {
        'N-ZC': 'ZCN', 'N-ZB': 'ZBN', 'N-ZA': 'ZAN', 'N-ZD': 'ZDN',
        'N-Z': 'ZCN', 'N-WDZC': 'WDZCN', 'N-WDZB': 'WDZBN', 'N-WDZA': 'WDZAN',
        'NH-ZC': 'ZCN', 'NH-ZB': 'ZBN', 'NH-ZA': 'ZAN',
        'ZN': 'ZCN', 'ZRNH': 'ZCN', 'NHZR': 'ZCN',
    }
    for wrong, right in order_map.items():
        if p.startswith(wrong):
            p = right + p[len(wrong):]
            break
    for wrong, right in order_map.items():
        if p.startswith(wrong):
            p = right + p[len(wrong):]
            break

    # ── 3. 逆序修正 (DW → WD, DUW → WDU 等) ──
    if p.startswith('DW'):
        p = 'WD' + p[2:]
    if p.startswith('DUW'):
        p = 'WDU' + p[3:]
    if p.startswith('UW'):
        p = 'WU' + p[2:]

    # ── 4. WDZ (单根阻燃) 是合法型号，保留 ──
    # 之前 WRONG: if p == 'WDZ': spec.prefix = 'WDZC'
    # GB/T 19666 表2: WDZ=无卤低烟单根阻燃, WDZC=无卤低烟阻燃C类 — 两者不同

    spec.prefix = p

    if spec.prefix != old:
        spec.patch_log.append(f'[P1] {old}→{spec.prefix}')


def _fix_base_model(spec: CableSpec) -> None:
    """型号映射修正"""
    b = spec.base
    old = b

    # RVS 系列映射
    if b == 'RYS':
        spec.base = 'RYJS'
    elif b == 'KYJP':
        spec.base = 'KYJYP'
    elif b == 'RVS':
        # RVS 一般不映射，但如果带 WD 前缀会在 _fix_wd_material 里处理
        pass

    # VV → YJV（XLPE 升级，排除 RVV/RVVP）
    if b == 'VV' and not spec.prefix:  # 纯 VV，不带 WD
        pass  # 保留 VV，后续 string 层处理

    if spec.base != old:
        spec.patch_log.append(f'[P2] {old}→{spec.base}')


def _fix_wd_material(spec: CableSpec) -> None:
    """WD+V 材质互斥修正 PVC → 聚烯烃"""
    if not spec.prefix or not spec.prefix.startswith('WD'):
        return

    b = spec.base
    old = b
    wd_map = {
        'YJV': 'YJY', 'YJV22': 'YJV22',  # 铠装 YJV22 保留
        'KVV': 'KYJY', 'KVVP': 'KYJYP',
        'RVV': 'RYJY', 'RYY': 'RYJY', 'RVVP': 'RYJYP',
        'RVSP': 'RYJSP', 'RVS': 'RYJS',
        'BVR': 'BYJR', 'BV': 'BYJ',
    }
    if b in wd_map:
        spec.base = wd_map[b]
        if spec.base != old:
            spec.patch_log.append(f'[P3] {old}→{spec.base}')


def _validate_prefix(spec: CableSpec) -> list[str]:
    """校验前缀合法性 per GB/T 19666-2019，返回警告列表"""
    p = spec.prefix
    if not p:
        return []
    warnings = []

    # U 前必须有 WD
    if 'U' in p:
        if not p.startswith('WD'):
            warnings.append(f'低毒(U)前缀必须有无卤低烟(WD)，当前: {p}')

    # D 前必须有 W
    if 'D' in p and p[0] == 'D':
        warnings.append(f'低烟(D)前必须有无卤(W)，当前: {p}')

    # NJ/NS 提示
    if 'NJ' in p:
        warnings.append(f'[INFO] NJ=供火+机械冲击耐火，用于有机械冲击风险的场景')
    if 'NS' in p:
        warnings.append(f'[INFO] NS=供火+冲击+喷水耐火，最严苛耐火等级')

    return warnings


# ── 字符串级标准化 ────────────────────────────────────────────────────
# 以下规则在序列化后的字符串上操作（逐步迁移到 AST 层）

def normalize_string(s: str, base: str, prefix: str) -> str:
    """
    在字符串上应用剩余的标准化规则

    参数：
        s: CableSpec.to_string() 的结果
        base: 基础型号（用于电压判断）
        prefix: 燃烧特性前缀（用于 WD 判断）

    返回：标准化后的字符串
    """
    # 前缀标准化（补齐 AST 层漏掉的）
    s = re.sub(r'^NHYJV', 'N-YJV', s)
    s = re.sub(r'^NHBV', 'N-BV', s)
    s = re.sub(r'^NHBVR', 'N-BVR', s)
    s = re.sub(r'^NH-', 'N-', s)
    # N-ZC → ZCN 等（顺序修正）
    s = re.sub(r'^N-ZC-', 'ZCN-', s)
    s = re.sub(r'^N-ZB-', 'ZBN-', s)
    s = re.sub(r'^N-ZA-', 'ZAN-', s)
    s = re.sub(r'^N-ZD-', 'ZDN-', s)
    s = re.sub(r'^N-WDZC-', 'WDZCN-', s)
    s = re.sub(r'^N-WDZB-', 'WDZBN-', s)
    s = re.sub(r'^N-WDZA-', 'WDZAN-', s)
    # WDZ 单根阻燃是合法型号 (GB/T 19666 表2)
    # 不再强制转 WDZC
    # NH+WD → WDZN 合并
    s = re.sub(r'^WDNH-(?=RYY|RYJY|KYJY)', 'WDZN-', s)
    s = re.sub(r'^ZRC-', 'ZC-', s)
    s = re.sub(r'^DWZ', 'WDZ', s)
    s = re.sub(r'^DWU', 'WDU', s)

    # 型号映射（补充 AST 层漏掉的）
    s = re.sub(r'(?<![A-Z])RYS(?![JP])', 'RYJS', s)
    s = re.sub(r'KYJY-?P', 'KYJYP', s)
    s = re.sub(r'(?<![A-Z])KYJP(?!\w)', 'KYJYP', s)
    s = re.sub(r'RYJS-?P', 'RYJSP', s)
    s = re.sub(r'(?<![A-ZR])VV(?![A-Z])', 'YJV', s)

    # WD+V 材质互斥（补充）
    if prefix and prefix.startswith('WD'):
        s = re.sub(r'(?<![A-Z])YJV(?!2|Y)', 'YJY', s)
        s = re.sub(r'(?<![A-Z])KVV', 'KYJY', s)
        s = re.sub(r'(?<![A-Z])KVVP', 'KYJYP', s)
        s = re.sub(r'(?<![A-Z])RVV(?!P)', 'RYJY', s)
        s = re.sub(r'(?<![A-Z])RYY', 'RYJY', s)
        s = re.sub(r'(?<![A-Z])RVVP', 'RYJYP', s)
        s = re.sub(r'(?<![A-Z])RVSP', 'RYJSP', s)
        s = re.sub(r'(?<![A-Z])RVS(?![P])', 'RYJS', s)
        s = re.sub(r'(?<![A-Z])BVR', 'BYJR', s)
        s = re.sub(r'(?<![A-Z])BV(?!R|Y)', 'BYJ', s)

    # KYJY 清理（控制电缆电压修正）
    if 'KYJY' in s:
        s = re.sub(r'[-]?0\.6/1[kK]V-?', '', s)

    return s


# ── 电压处理 ─────────────────────────────────────────────────────────

def fix_voltage(s: str, base: str) -> str:
    """电压格式统一和死锁补全"""
    # 补充分隔符
    s = re.sub(r'(\d+[kK]V)(\d)', r'\1-\2', s)

    # 系统电压转换为额定电压 (U0/U)
    # 10kV 系统 → 8.7/15kV 电缆
    s = re.sub(r'(?<![0-9./])10[kK][vV]', '8.7/15kV', s)
    # 6kV 系统 → 3.6/6kV 电缆  
    s = re.sub(r'(?<![0-9./])6[kK][vV](?!/)', '3.6/6kV', s)
    # 35kV 系统 → 26/35kV 电缆
    s = re.sub(r'(?<![0-9./])35[kK][vV]', '26/35kV', s)
    
    # 电压格式统一
    s = re.sub(r'0\.6/1\.0[kK]V', '0.6/1kV', s)
    s = re.sub(r'0\.3/0\.5[kK]?V', '300/500V', s)
    s = re.sub(r'0\.45/0\.75[kK]?V', '450/750V', s)
    s = re.sub(r'(?<!/)1[kK]V(?!V)', '0.6/1kV', s)
    s = re.sub(r'0\.6[kK]V(?!\/1)', '0.6/1kV', s)

    # kV 统一小写
    s = re.sub(r'(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)[kK][vV]', r'\1kV', s)

    # 电压死锁补全（对已知型号）
    has_voltage = bool(re.search(r'\d+\.?\d*/\d+\.?\d*[kK]?V|\d+[kK]?V', s))

    if not has_voltage:
        # RVSP 优先匹配
        if 'RVSP' in s and RVSP_VOLTAGE not in s:
            s = re.sub(r'(RVSP)(-B1)?-?(\d)', rf'\1\2-{RVSP_VOLTAGE}-\3', s)

        for pats, volt in VOLTAGE_MAP:
            for pat in pats:
                if pat in s and volt not in s:
                    s = re.sub(rf'({pat})(-B1)?-?(\d)', rf'\1\2-{volt}-\3', s)
                    break

        # YJV22/YJV/YJY 电压
        for pat in ['YJV22', 'YJV', 'YJY']:
            if pat in s and not re.search(r'\d+\.?\d*/\d+\.?\d*[kK]?V|\d+[kK]?V', s):
                s = re.sub(rf'({pat})(-B1)?-?(\d)', rf'\1\2-0.6/1kV-\3', s)
                break

        # VV 单独处理
        if re.search(r'(?<![A-Z])VV(?![A-Z])', s) and 'YJV' not in s \
           and not re.search(r'\d+\.?\d*/\d+\.?\d*[kK]?V|\d+[kK]?V', s):
            s = re.sub(r'(\bVV|-VV)(-B1)?-?(\d)', r'\1\2-0.6/1kV-\3', s)

    return s


# ── 单芯补全 ─────────────────────────────────────────────────────────

def fix_single_core(s: str) -> str:
    """BV/BYJ/BVR/BYJR 单芯补全 1×"""
    for pat in ['BYJR', 'BVR', 'BYJ', 'BV']:
        if re.search(rf'(?:^|-){pat}(?:-B1)?-\d+(?:\.\d+)?/\d+(?:\.\d+)?[kK]?V-\d+(?:\.\d+)?$', s):
            s = re.sub(
                rf'({pat}(?:-B1)?-\d+(?:\.\d+)?/\d+(?:\.\d+)?[kK]?V-)(\d+(?:\.\d+)?)$',
                rf'\g<1>1×\2', s
            )
            break
    return s


# ── 最终清理 ─────────────────────────────────────────────────────────

def final_clean(s: str) -> str:
    """连字符清理、空结果处理"""
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s


# ── 入口 ─────────────────────────────────────────────────────────────

def normalize(spec: CableSpec) -> Optional[CableSpec]:
    """
    CableSpec AST → 标准化后的 CableSpec

    流程：
      1. AST 级标准化（前缀、型号映射、材质互斥）
      2. 序列化为字符串
      3. 字符串级标准化
      4. 电压处理
      5. 单芯补全
      6. 最终清理
      7. 重新解析回 CableSpec（为下游提供 AST）
    """
    # Step 1: AST 级标准化（已在各 _fix_* 函数中写入 patch_log）
    spec = normalize_ast(spec)

    # Step 2: 序列化
    s = spec.to_string()

    if not s:
        return None

    # Step 3: 字符串级标准化
    before = s
    s = normalize_string(s, spec.base, spec.prefix)
    if s != before:
        spec.patch_log.append(f'[P2+P3] 字符串级修正')

    # Step 4: 电压处理
    before = s
    s = fix_voltage(s, spec.base)
    if s != before:
        spec.patch_log.append('[P4] 电压补全/修正')

    # Step 5: 单芯补全
    before = s
    s = fix_single_core(s)
    if s != before:
        spec.patch_log.append('[P5] 单芯补全')

    # Step 6: 最终清理
    before = s
    s = final_clean(s)
    if s != before:
        spec.patch_log.append('[P6] 连字符清理')

    if not s:
        return None

    # Step 7: 重新解析
    from parser import parse
    result = parse(s, color=spec.color, is_pv=spec.is_pv)
    if result:
        # 保留原始 raw 和 patch_log
        result.raw = spec.raw
        result.patch_log = spec.patch_log
        return result
    return None
