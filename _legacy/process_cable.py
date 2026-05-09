#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DeepCable-Grandmaster audit processor for 得力电缆.xlsx"""

import re
import math
from collections import defaultdict

# ============================================================
# RAW DATA
# ============================================================
raw_entries = [
    ("YJV-10KV 3x300", 32.48),
    ("YJV-4X240+1X120", 27.6),
    ("BBTRZ-5X6", 886.6),
    ("NHYJV-0.6/1KV- 5X6", 314.97),
    ("NHYJV-0.6/1KV- 5X4", 202.2),
    ("NHYJV-0.6/1KV-3x4", 726.9),
    ("YJV-0.6/1KV 5X10", 93.56),
    ("YJV-0.6/1KV 5X16", 1167.16),
    ("YJV-0.6/1KV 4X25+1X16", 48.8),
    ("BV2.5", 24086.04),
    ("BVR2.5", 11894.83),
    ("NH-BV2.5", 416.79),
    ("NH-BVR2.5", 163.11),
    ("NH-BV4", 5.44),
    ("NH-BVR4", 2.72),
    ("NH-RVS-2x2.5", 33.26),
    ("WDZN-RYSP-2X1.5", 24.84),
    ("WDZN-RYJS-2x2.5", 6804.2),
    ("BBTRZ-5X6", 865.3),
    ("NHYJV-0.6/1KV- 5X6", 865.3),
    ("NHYJV-0.6/1KV- 5X4", 271.2),
    ("NHYJV-0.6/1KV-3x4", 1068.4),
    ("YJV-0.6/1KV 5X4", 17.7),
    ("YJV-0.6/1KV 5X6", 32.74),
    ("YJV-0.6/1KV 5X16", 2950.58),
    ("YJV-0.6/1KV 4X25+1X16", 612.46),
    ("YJV-0.6/1KV 4X35+1X16", 1006.16),
    ("NH-YJV-0.6/1KV 3X25", 93.45),
    ("NH-YJV-0.6/1KV 3X25+1X16", 93.45),
    ("NH-YJV-0.6/1KV 3X95", 42.68),
    ("NH-YJV-0.6/1KV 3X95+1X50", 42.68),
    ("BV1.5", 18.62),
    ("BV2.5", 35123.68),
    ("BVR2.5", 17296.2),
    ("NH-BV2.5", 527.5),
    ("NH-BVR2.5", 221.36),
    ("WDZN-RYSP-2X1.5", 80.63),
    ("WDZN-RYJS-2x2.5", 9483.89),
    ("BBTRZ-5X6", 876.61),
    ("NHYJV-0.6/1KV- 5X6", 876.61),
    ("NHYJV-0.6/1KV- 5X4", 144.73),
    ("NHYJV-0.6/1KV-3x4", 1114.25),
    ("YJV-0.6/1KV 5X10", 221.04),
    ("YJV-0.6/1KV 5X16", 1840.61),
    ("YJV-0.6/1KV 4X25+1X16", 1215.22),
    ("YJV-0.6/1KV 4X35+1X16", 691.47),
    ("BV2.5", 43450.52),
    ("BVR2.5", 20844.83),
    ("NH-BV2.5", 215.32),
    ("NH-BVR2.5", 68.55),
    ("WDZN-RYSP-2X1.5", 138.13),
    ("WDZN-RYJS-2x2.5", 9028.81),
    ("BV2.5", 293.42),
    ("BVR2.5", 126.81),
    ("BV2.5", 152.8),
    ("BVR2.5", 76.4),
    ("NH-BV2.5", 757.51),
    ("NH-BVR2.5", 273.19),
    ("NH-RVS-2x2.5", 115.14),
    ("BBTRZ-3X4", 16.41),
    ("NHYJV-0.6/1KV- 3X6", 88.99),
    ("WDZBN-YJY-0.6/1KV 3X4", 0.73),
    ("YJV-0.6/1KV 3X6", 1162.01),
    ("YJV-0.6/1KV 5X4", 10.31),
    ("YJV-0.6/1KV 5X6", 261.33),
    ("YJV-0.6/1KV 5X10", 178.98),
    ("YJV-0.6/1KV 5X16", 59.2),
    ("YJV-0.6/1KV 4X25+1X16", 125.86),
    ("YJV-0.6/1KV 4X70+1X35", 114.66),
    ("BV1.5", 404.64),
    ("BV2.5", 519.6),
    ("BVR2.5", 221.21),
    ("NHBV2.5", 32.98),
    ("NHBVR2.5", 16.49),
    ("WDZN-RYJS-2x2.5", 848.09),
    ("BBTRZ-3X4", 42.83),
    ("NHYJV-0.6/1KV- 3X6", 187.31),
    ("WDZBN-YJY-0.6/1KV 3X4", 3.29),
    ("YJV-0.6/1KV 5X10", 298.24),
    ("YJV-0.6/1KV 4X25+1X16", 186.25),
    ("YJV-0.6/1KV 4X35+1X16", 175.99),
    ("BV2.5", 438.46),
    ("BVR2.5", 210.28),
    ("NH-BV2.5", 10.96),
    ("NH-BVR2.5", 5.48),
    ("WDZN-RYJS-2x2.5", 974.53),
    ("NH-RVS-2x2.5", 11.92),
    ("NHYJV-0.6/1KV 3X6", 26.16),
    ("WDZBN-YJY-0.6/1KV 3X4", 43.22),
    ("YJV-0.6/1KV 5X4", 32.03),
    ("BV2.5", 3622.3),
    ("BVR2.5", 1786.78),
    ("NH-BV2.5", 28.74),
    ("NH-BVR2.5", 12.24),
    ("WDZN-RYJS-2x2.5", 1320.2),
    ("YJV-0.6/1KV 3X4", 1276.25),
    ("YJV-0.6/1KV 3X6", 1237.94),
    ("NHYJV-0.6/1KV 5X16", 2678.33),
    ("NHYJV-0.6/1KV 4X95+1X50", 165.48),
    ("NHYJV-0.6/1KV 4X120+1X70", 775.81),
    ("YJV-0.6/1KV 5X16", 105.7),
    ("YJV-0.6/1KV 4X35+1X16", 119.68),
    ("YJV-0.6/1KV 4X70+1X35", 1637.37),
    ("YJV-0.6/1KV 4X120+1X70", 67.44),
    ("YJV-0.6/1KV 4X150+1X70", 194.54),
    ("YJV22-0.6/1KV 4X25+1X16", 633.89),
    ("YJV22-0.6/1KV 4X50+1X25", 633.89),
    ("YJV22-0.6/1KV 4X95+1X50", 304.51),
    ("YJV22-0.6/1KV 4X120+1X70", 609.01),
    ("YJV22-0.6/1KV 4X150+1X70", 473.16),
    ("YJV22-0.6/1KV 4X185+1X95", 304.51),
    ("YJV22-0.6/1KV 5X16", 329.13),
    ("WDZN-RYJSP 2*2.5", 384.23),
    ("WDZN-RYJSP 2*2.5", 711.3),
    ("WDZN-RYSP 2*1.5", 446.63),
    ("WDZN-RYSP 2*1.5", 452.04),
    ("WDZN-KYJYP2*1.5", 191.43),
    ("WDZN-KYJY2*2.5", 192.99),
    ("WDZN-KYJY10*1.5", 192.99),
    ("WDZN-RYJS 2*1.5", 7108.94),
    ("WDZN-RYS 2*1.5", 1702.33),
    ("WDZN-BYJ 2.5", 423.38),
    ("WDZN-YJY 2*6", 192.99),
    ("WDZN-RYJSP 2*2.5", 667.91),
    ("WDZN-RYJSP 2*2.5", 664.51),
    ("WDZN-RYSP 2*1.5", 281.07),
    ("WDZN-RYSP 2*1.5", 497.08),
    ("WDZN-RYJS 2*1.5", 11681.21),
    ("WDZN-RYS 2*1.5", 2974.98),
    ("WDZN-BYJ 2.5", 557.78),
    ("WDZN-KYJY8*1.5", 965.97),
    ("WDZN-KYJY7*1.5", 952.55),
    ("WDZN-KYJY2*2.5", 540.39),
    ("WDZN-RYJSP 2*2.5", 863.48),
    ("WDZN-RYJSP 2*2.5", 748.55),
    ("WDZN-RYSP 2*1.5", 535.03),
    ("WDZN-RYSP 2*1.5", 549.4),
    ("WDZN-RYS 2*1.5", 2906.56),
    ("WDZN-RYJS 2*1.5", 9245.13),
    ("WDZN-BYJ 2.5", 1010.69),
    ("WDZN-KYJY2*2.5", 30.36),
    ("WDZN-KYJY12*1.5", 139.58),
    ("WDZN-KYJY2*1.5", 139.58),
    ("WDZN-KYJY5*1.5", 135.62),
    ("WDZN-YJY 2*6", 135.62),
    ("WDZN-YJY 2*2.5", 168.38),
    ("WDZN-KYJY 3*1.5", 168.38),
    ("WDZN-BYJ 2.5", 48.84),
    ("WDZN-RYJS 2*1.5", 131.41),
    ("WDZN-RYJS 2*1.5", 160.57),
    ("WDZN-KYJY 3*1.5", 154.26),
    ("WDZN-RYSP-2x1.5", 19.95),
    ("WDZN-RYSP-2x1.5", 2.29),
    ("WDZN-RYSP-2x1.5", 2.72),
    ("WDZN-RYJS-2x1.5", 168.1),
    ("WDZN-RYSP 2*1.5", 25.36),
    ("WDZN-RYSP 2*1.5", 4.52),
    ("WDZN-RYJS 2*1.5", 117.35),
    ("WDZN-RYSP-2x1.5", 147.06),
    ("WDZN-RYSP-2x1.5", 145.78),
    ("WDZN-RYSP-2x1.5", 190.03),
    ("WDZN-RYJS 2*1.5", 338.88),
    ("WDZN-KYJYP2*1.5", 97.48),
    ("WDZN-KYJYP3*1.5", 434.1),
    ("WDZN-KYJY2*2.5", 625.71),
    ("WDZN-KYJY7*1.5", 293.65),
    ("WDZN-KYJY8*1.5", 293.93),
    ("WDZN-KYJY10*1.5", 96.23),
    ("WDZN-KYJY16*1.5", 194.24),
    ("WDZN-YJY 2*2.5", 217.02),
    ("WDZN-YJY 2*6", 290.27),
    ("WDZN-RYSP 2*1.5", 846.055),
    ("WDZN-RYSP 2*2.5", 95.115),
    ("WDZN-RYJSP 2*2.5", 258.9),
    ("BV2.5", 5020.47),
    ("BVR2.5", 2065.2),
    ("BV2.5", 5246.69),
    ("BVR2.5", 2169.34),
    ("BV2.5", 4629.51),
    ("BVR2.5", 1916.08),
    ("BV2.5", 2460.15),
    ("BVR2.5", 947.25),
    ("BV2.5", 5552.66),
    ("BVR2.5", 1673.14),
    ("BV4", 470.84),
    ("BVR4", 235.42),
    ("BV2.5", 9290.17),
    ("BVR2.5", 4068.22),
    ("YJV-0.6/1KV 4X25+1X16", 220.87),
    ("BV2.5", 248.75),
    ("BVR2.5", 103.19),
    ("BV4", 36.64),
    ("BVR4", 18.32),
    ("BV2.5", 320.01),
    ("BVR2.5", 134.59),
    ("BV2.5", 148.39),
    ("BVR2.5", 56.93),
]

# ============================================================
# PE TABLE
# ============================================================
PE_TABLE = {
    2.5: 1.5, 4: 2.5, 6: 4, 10: 6, 16: 10, 25: 16, 35: 16,
    50: 25, 70: 35, 95: 50, 120: 70, 150: 70, 185: 95, 240: 120,
    300: 150, 400: 185
}

# Core model type categories (longest first for matching)
ALL_CORES = ['YJV22', 'YJV', 'YJY', 'VV', 'KYJYP', 'KYJY', 'KVV', 'KVVP',
             'RYJSP', 'RYJS', 'RVS', 'RVSP', 'BYJR', 'BYJ', 'BVR', 'BV', 'BBTRZ']

POWER_CORES = {'YJV22', 'YJV', 'YJY', 'VV', 'BBTRZ'}
CONTROL_CORES = {'KYJYP', 'KYJY', 'KVV', 'KVVP'}
TWISTED_CORES = {'RYJSP', 'RYJS', 'RVS', 'RVSP'}
WIRE_CORES = {'BYJR', 'BYJ', 'BVR', 'BV'}

# Voltage table
VOLTAGE_MAP = {
    'POWER': '0.6/1kV',
    'CONTROL': '450/750V',
    'TWISTED': '300/300V',
    'BYJ': '450/750V',
    'BVR': '450/750V',
    'BV_GE_1.5': '450/750V',
    'BV_LE_1.0': '300/500V',
}


def check_n_pe(std_model):
    """N/PE截面校验"""
    warnings = []
    m = re.search(r'(?:kV|V)-(.+)$', std_model)
    if not m:
        return warnings
    sec = m.group(1)
    p = re.search(r'(\d+)×(\d+\.?\d*)\+(\d+)×(\d+\.?\d*)', sec)
    if p:
        ps = float(p.group(2))
        ns = float(p.group(4))
        for k in sorted(PE_TABLE.keys()):
            if ps <= k:
                if ns < PE_TABLE[k]:
                    warnings.append(
                        f'[PE报警] 相线{ps}mm²→PE需≥{PE_TABLE[k]}mm²，实配{ns}mm²'
                    )
                break
    return warnings


def extract_components(m):
    """Parse model into structured components.
    Returns dict with: prefix, core, core_count, section, pe_section, voltage, b1
    """
    # ---- Global format fixes first ----
    # RYS→RYJS, RYSP→RYJSP (user confirmed)
    m = re.sub(r'\bRYS\b', 'RYJS', m)
    m = m.replace('RYSP', 'RYJSP')
    # NH→N
    m = re.sub(r'\bNH-', 'N-', m)
    m = re.sub(r'\bNH(?=[A-Z])', 'N', m)
    m = re.sub(r'\bNHBV', 'N-BV', m)
    m = re.sub(r'\bNHBVR', 'N-BVR', m)
    m = re.sub(r'\bNHRVS', 'N-RVS', m)
    # NYJV → N-YJV
    m = re.sub(r'\bNYJV22\b', 'N-YJV22', m)
    m = re.sub(r'\bNYJV\b', 'N-YJV', m)
    # * and x to ×
    m = re.sub(r'\*', '×', m)
    m = re.sub(r'(?<=\d)[xX](?=\d)', '×', m)
    # Voltage case
    m = re.sub(r'(\d)[Kk][Vv]', lambda x: x.group(1).lower() + 'kV', m)
    # Clean spaces
    m = re.sub(r'-\s+', '-', m)
    m = re.sub(r'\s+', '', m)  # remove all spaces
    # Collapse hyphens
    m = re.sub(r'-+', '-', m)
    m = m.strip('-')

    comps = {'prefix': '', 'core': '', 'voltage': '', 'section': '',
             'core_count': 0, 'pe_section': '', 'b1': '', 'is_mv': False}

    # B1
    if '-B1-' in m:
        comps['b1'] = 'B1'
        m = m.replace('-B1-', '')

    # Detect MV
    if re.search(r'\b(\d+)kV\b', m):
        kv = int(re.search(r'\b(\d+)kV\b', m).group(1))
        if kv >= 6:
            comps['is_mv'] = True

    # Extract prefix
    prefixes = sorted(['WDZBN', 'WDZCN', 'WDZN', 'WDZB', 'WDZC', 'WDZ', 'WDUZC', 'WDUZ', 'N'],
                      key=len, reverse=True)
    for p in prefixes:
        if m.startswith(p):
            comps['prefix'] = p
            m = m[len(p):]
            if m.startswith('-'):
                m = m[1:]
            break

    # Extract voltage
    vm = re.search(r'(DC\d+V|\d+\.?\d*/\d+\.?\d*kV|\d+kV|\d+/\d+V)', m)
    if vm:
        comps['voltage'] = vm.group(1)
        m = m[:vm.start()] + m[vm.end():]
        if m.startswith('-'):
            m = m[1:]

    # m now contains core + section info
    # Try to extract core type
    core_found = ''
    for c in sorted(ALL_CORES, key=len, reverse=True):
        if m.startswith(c):
            core_found = c
            m = m[len(c):]
            break
    # Also try to find core in the middle (for patterns like YJV22 mixed with core count)
    if not core_found:
        for c in sorted(ALL_CORES, key=len, reverse=True):
            if c in m:
                core_found = c
                m = m.replace(c, '', 1)
                break

    comps['core'] = core_found
    if m.startswith('-'):
        m = m[1:]

    # Rest is section info
    # Patterns: 5×16, 4×25+1×16, 1×2.5, etc.
    # Also handle bare section: 2.5, 4, 1.5 (no × separator)
    sec_match = re.search(r'(\d+)×(\d+\.?\d*)(?:\+(\d+)×(\d+\.?\d*))?', m)
    if sec_match:
        comps['core_count'] = int(sec_match.group(1))
        comps['section'] = sec_match.group(2)
        if sec_match.group(3) and sec_match.group(4):
            comps['pe_section'] = f'+{sec_match.group(3)}×{sec_match.group(4)}'
    else:
        # Bare section number (e.g., "2.5" or "4")
        bare = re.search(r'^(\d+\.?\d*)$', m)
        if bare:
            comps['section'] = bare.group(1)

    return comps


def rebuild(comps):
    """Rebuild standard model from components with voltage and format."""
    prefix = comps['prefix']
    core = comps['core']
    cc = comps['core_count']
    sec = comps['section']
    pe = comps['pe_section']
    voltage = comps['voltage']
    b1 = comps['b1']
    is_mv = comps['is_mv']

    # Determine voltage if not present
    if not voltage and not is_mv:
        if core in POWER_CORES:
            voltage = '0.6/1kV'
        elif core in CONTROL_CORES:
            voltage = '450/750V'
        elif core in TWISTED_CORES:
            voltage = '300/300V'
        elif core == 'BYJ' or core == 'BYJR':
            voltage = '450/750V'
        elif core == 'BVR':
            voltage = '450/750V'
        elif core == 'BV':
            if sec:
                s = float(sec)
                voltage = '300/500V' if s <= 1.0 else '450/750V'
            else:
                voltage = '450/750V'
    elif is_mv:
        pass  # keep original voltage

    # For non-power non-control non-twisted (bare wires with section but no core count)
    # e.g., BV-2.5 → BV-1×2.5
    sec_str = sec
    if cc > 0:
        sec_str = f'{cc}×{sec}'
        if pe:
            sec_str += pe
    elif sec:
        # Single core, add 1×
        sec_str = f'1×{sec}'
    else:
        sec_str = '?'

    # Build result
    parts = []
    if prefix:
        parts.append(prefix)
    parts.append(core)
    if b1:
        parts.append(f'B1({b1})')
    if voltage:
        parts.append(voltage)
    parts.append(sec_str)

    return '-'.join(parts)


def build_fingerprint(std):
    """Build 5-part fingerprint: prefix|core|B1|voltage|section"""
    parts = std.split('-')
    prefix = ''
    core = ''
    b1 = ''
    voltage = ''
    section = ''

    # Find known prefix at start
    prefixes = sorted(['WDZBN', 'WDZCN', 'WDZN', 'WDZB', 'WDZC', 'WDZ', 'WDUZC', 'WDUZ', 'N'],
                      key=len, reverse=True)
    for p in prefixes:
        if std.startswith(p):
            prefix = p
            std = std[len(p):]
            if std.startswith('-'):
                std = std[1:]
            break

    # B1
    if '-B1-' in std:
        b1 = 'B1'
        std = std.replace('-B1-', '')

    # Voltage
    vm = re.search(r'(DC\d+V|\d+\.?\d*/\d+\.?\d*kV|\d+kV)', std)
    if vm:
        voltage = vm.group(1)
        std = std[:vm.start()] + std[vm.end():]

    # Core: first part of remaining
    std = std.lstrip('-')
    for c in sorted(ALL_CORES, key=len, reverse=True):
        if std.startswith(c):
            core = c
            std = std[len(c):]
            break

    std = std.lstrip('-')
    section = std if std else '?'

    return f'{prefix}|{core}|{b1}|{voltage}|{section}'


def fmt_name(fp):
    p, c, b1, v, s = fp.split('|')
    parts = []
    if p: parts.append(p)
    parts.append(c)
    if b1: parts.append(b1)
    if v: parts.append(v)
    parts.append(s)
    return '-'.join(parts)


# ============================================================
# MAIN
# ============================================================
print('=' * 120)
print('《原始数据索引》（共{}条）'.format(len(raw_entries)))
print('=' * 120)
print(f'{"序号":>4s}  {"原始型号":<55s}  {"数量":>12s}')
print('-' * 75)
for i, (m, q) in enumerate(raw_entries):
    print(f'{i+1:>4d}  {m:<55s}  {q:>12.2f}')

groups = defaultdict(list)
results = []

for i, (model, qty) in enumerate(raw_entries):
    comps = extract_components(model)
    std = rebuild(comps)
    fp = build_fingerprint(std)
    warns = check_n_pe(std)
    groups[fp].append((i, qty))
    results.append((i, model, std, fp, warns))

print()
print()
print('=' * 120)
print('逐条规则校验结果')
print('=' * 120)
for i, orig, std, fp, warns in results:
    ws = '; '.join(warns) if warns else ''
    print(f'{i+1:>4d}  {orig:<45s} → {std:<60s}  {ws}')

print()
print()
print('=' * 120)
print('按型号指纹分组合并')
print('=' * 120)


def sort_key(item):
    fp, entries = item
    parts = fp.split('|')
    core = parts[1]
    voltage = parts[3]

    if core in POWER_CORES:
        cat = 1
        if voltage and not voltage.startswith('0.6/'):
            cat = 0  # MV
    elif core in CONTROL_CORES:
        cat = 2
    elif core == 'BBTRZ':
        cat = 3
    elif core in {'BYJ', 'BYJR'}:
        cat = 4
    elif core in {'BV', 'BVR'}:
        cat = 5
    elif core in TWISTED_CORES:
        cat = 6
    else:
        cat = 7

    sec = parts[4]
    sm = re.search(r'(\d+\.?\d*)', sec)
    sv = float(sm.group(1)) if sm else 0

    return (cat, -sv)


sorted_groups = sorted(groups.items(), key=sort_key)

for fp, entries in sorted_groups:
    dn = fmt_name(fp)
    total = sum(e[1] for e in entries)
    qty_strs = [f'条目{i+1}: {qty}' for i, qty in entries]
    print(f'\n{dn}')
    print(f'  {"  +  ".join(qty_strs)}')
    print(f'  合计：{" + ".join(f"{qty}" for _, qty in entries)} = {total:,.2f}m')

print()
print()
print('=' * 120)
print('标准化输出（TSV格式，可直接复制到Excel）')
print('=' * 120)
print('规格型号\t单位\t数量')

for fp, entries in sorted_groups:
    dn = fmt_name(fp)
    total = sum(e[1] for e in entries)
    total_rounded = math.ceil(total * 100) / 100
    print(f'{dn}\tm\t{total_rounded}')

total_orig = len(raw_entries)
total_merged = len(groups)
print(f'\n原始条目：{total_orig}条 → 合并后：{total_merged}行（已合并{total_orig - total_merged}条）')

print()
print()
print('=' * 120)
print('《合并验算报告》')
print('=' * 120)
print(f'{"规格型号":<70s} {"数量":>12s}')
print('-' * 85)
grand_total = 0
for fp, entries in sorted_groups:
    dn = fmt_name(fp)
    total = sum(e[1] for e in entries)
    total_rounded = math.ceil(total * 100) / 100
    print(f'{dn:<70s} {total_rounded:>12.2f}')
    grand_total += total_rounded
print('-' * 85)
print(f'{"合计":<70s} {grand_total:>12.2f}')
print(f'原始条目：{total_orig}条 → 合并后：{total_merged}行（已合并{total_orig - total_merged}条）')

# PE warnings
pe_all = [(i+1, orig, std, w) for i, orig, std, fp, warns in results for w in warns if 'PE' in w]
if pe_all:
    print()
    print('⚠ PE截面报警汇总：')
    for idx, orig, std, w in pe_all:
        print(f'  条目{idx:>3d}: {orig:<45s} → {w}')
