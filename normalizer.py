"""
normalizer.py — CableSpec AST → 标准化 CableSpec

应用 GB/T 19666 规则：
  1. 前缀标准化：NH → N, ZR → ZC, NH-ZC → ZCN
  2. 型号映射修正：RVS → RYJS, VV → YJV
  3. WD+V 材质互斥：YJV → YJY, KVV → KYJY
  4. 电压格式统一和缺失值补全
"""

import re
from typing import Optional
from spec import CableSpec
from cable_rules import DEFAULT_VOLTAGE


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
        'N-Z': 'ZN', 'N-WDZC': 'WDZCN', 'N-WDZB': 'WDZBN', 'N-WDZA': 'WDZAN',
        'NH-ZC': 'ZCN', 'NH-ZB': 'ZBN', 'NH-ZA': 'ZAN',
    }
    for wrong, right in order_map.items():
        if p.startswith(wrong):
            p = right + p[len(wrong):]
            break

    # ── 3. 逆序修正 (DW → WD, DUW → WDU 等) ──
    for wrong, right in (('DUW', 'WDU'), ('DW', 'WD'), ('UW', 'WU')):
        if p.startswith(wrong):
            p = right + p[len(wrong):]
            break

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


def _canonical_voltage(voltage: str) -> str:
    """Canonicalize an already parsed voltage without inferring a new one."""
    v = voltage.strip()
    if not v:
        return ''
    if re.fullmatch(r'10[kK]V', v):
        return '8.7/15kV'
    if re.fullmatch(r'6[kK]V', v):
        return '3.6/6kV'
    if re.fullmatch(r'35[kK]V', v):
        return '26/35kV'
    v = re.sub(r'0\.6/1\.0[kK]V', '0.6/1kV', v)
    v = re.sub(r'0\.3/0\.5[kK]?V', '300/500V', v)
    v = re.sub(r'0\.45/0\.75[kK]?V', '450/750V', v)
    if re.fullmatch(r'1[kK]V', v):
        return '0.6/1kV'
    if re.fullmatch(r'0\.6[kK]V', v):
        return '0.6/1kV'
    return re.sub(
        r'(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)[kK]V',
        r'\1kV',
        v,
    )


def _normalize_voltage_ast(spec: CableSpec) -> None:
    """Normalize or infer voltage directly on the AST."""
    if spec.voltage:
        old = spec.voltage
        spec.voltage = _canonical_voltage(spec.voltage)
        if spec.voltage.lower() != old.lower():
            spec.patch_log.append(f'[P4] 电压格式 {old}→{spec.voltage}')

    # A control cable carrying the common power-cable default is a known input
    # error. Clear it before applying the model-specific default.
    if spec.base == 'KYJY' and spec.voltage == '0.6/1kV':
        spec.voltage = ''

    if not spec.voltage and spec.cores and spec.base in DEFAULT_VOLTAGE:
        spec.voltage = DEFAULT_VOLTAGE[spec.base]
        spec.is_guess = True
        spec.inferred_fields.append('voltage')
        spec.patch_log.append(f'[P4] 补全电压 {spec.voltage}')


# ── 入口 ─────────────────────────────────────────────────────────────

def normalize(spec: CableSpec) -> Optional[CableSpec]:
    """
    CableSpec AST → 标准化后的 CableSpec

    All transformations happen on the AST. Serialization is intentionally
    deferred to the caller so parsed fields cannot be lost by a second parse.
    """
    spec = normalize_ast(spec)
    _normalize_voltage_ast(spec)
    return spec if spec.base else None
