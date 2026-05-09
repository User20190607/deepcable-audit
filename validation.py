"""
validation.py — 电缆型号校验引擎

当前：
  - N/PE 截面校验（check_pe）

待扩展：
  - 电压等级校验
  - 导体材质兼容性校验
  - 铠装层标准校验
"""

import re
from typing import Optional
from spec import CableSpec


# 相线截面 → 最小 N/PE 截面（GB/T 标准）
PE_TABLE = {
    2.5: 1.5, 4: 2.5, 6: 4, 10: 6, 16: 10,
    25: 16, 35: 16, 50: 25, 70: 35, 95: 50,
    120: 70, 150: 70, 185: 95, 240: 120,
    300: 150, 400: 185,
}


def check_pe(model: str) -> dict:
    """
    检查 N/PE 线截面是否符合规范。

    参数：
        model: 标准型号字符串（如 'YJV-0.6/1kV-4×25+1×16'）

    返回：
        {'ok': True/False, 'warning': '描述'}
    """
    m = re.search(r'(\d+(?:\.\d+)?)×(\d+(?:\.\d+)?)\+\d+×(\d+(?:\.\d+)?)', model)
    if not m:
        return {'ok': True, 'warning': ''}

    phase_s = float(m.group(2))
    pe_s = float(m.group(3))
    min_pe = PE_TABLE.get(phase_s)

    if min_pe is None:
        return {'ok': True, 'warning': ''}
    if pe_s < min_pe:
        return {'ok': False, 'warning': 'N/PE 截面偏小，建议加大地线'}
    if pe_s > min_pe:
        return {'ok': True, 'warning': 'N/PE 截面偏大，可考虑缩小地线'}
    return {'ok': True, 'warning': ''}


def validate_cable(spec: CableSpec) -> list[dict]:
    """对 CableSpec 执行全部校验，返回校验结果列表"""
    warnings = []

    # N/PE 校验
    pe_result = check_pe(spec.to_string())
    if not pe_result['ok']:
        warnings.append({
            'field': 'pe_section',
            'severity': 'error',
            'message': pe_result['warning'],
        })
    elif pe_result['warning']:
        warnings.append({
            'field': 'pe_section',
            'severity': 'warn',
            'message': pe_result['warning'],
        })

    return warnings
