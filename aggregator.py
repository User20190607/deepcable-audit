"""
aggregator.py — 型号指纹聚合和排序

职责：
  1. 按型号指纹聚合数量
  2. 单芯线拆分（BV-2×2.5 → BV-1×2.5, qty×2）
  3. 标准排序
"""

import re
import math
from collections import defaultdict
from typing import Optional

from spec import CableSpec, CoreSpec


SINGLE_CORE_WIRES = {'BYJ', 'BYJR', 'BVR', 'BV'}


def aggregate(records: list[dict]) -> tuple[dict, list, list]:
    """
    输入：[{'raw': '原始型号', 'qty': 数量}, ...]
    输出：(aggregated, failed, index_log)
        aggregated: {标准型号: 合计数量}
        failed:     [{'raw': ..., 'qty': ...}]
        index_log:  [{'seq': ..., 'raw': ..., 'model': ..., 'qty': ...}]
    """
    from deepcable_normalize import normalize

    aggregated = defaultdict(float)
    failed = []
    index_log = []

    for i, r in enumerate(records, 1):
        model = normalize(r['raw'])
        qty = float(r['qty'])

        if model:
            # 单芯线拆分
            split_factor = _calc_split_factor(model)
            if split_factor > 1:
                model = re.sub(r'(\d+)×(\d+(?:\.\d+)?)$', r'1×\2', model)
            aggregated[model] += qty * split_factor
            index_log.append({
                'seq': i, 'raw': r['raw'],
                'model': model, 'qty': qty * split_factor,
            })
        else:
            failed.append(r)
            index_log.append({
                'seq': i, 'raw': r['raw'],
                'model': None, 'qty': qty,
            })

    return dict(aggregated), failed, index_log


def _calc_split_factor(model: str) -> int:
    """计算单芯线拆分因子：BV-2×2.5 → 拆 2 倍"""
    for core in sorted(SINGLE_CORE_WIRES, key=len, reverse=True):
        if f'-{core}-' in model or f'-{core}-B1' in model or model.startswith(f'{core}-'):
            m = re.search(r'(\d+)×(\d+(?:\.\d+)?)$', model)
            if m and int(m.group(1)) > 1:
                return int(m.group(1))
            break
    return 1


def sort_key(model: str) -> tuple:
    """标准排序键：中压 > 低压电力 > 控制 > 布电线 > 软线 > 弱电"""
    if '10kV' in model or '35kV' in model:
        return (0, model)
    if 'BBTRZ' in model:
        return (1, model)
    if 'YJV22' in model:
        return (2, model)
    if re.search(r'N-YJV|WDZBN|WDZN-YJY|WDZA.*YJY|WDZB.*YJY', model):
        return (3, model)
    if re.search(r'YJV-0\.|YJY-0\.', model):
        return (4, model)
    if 'KYJYP' in model:
        return (5, model)
    if 'KYJY' in model:
        return (6, model)
    if re.search(r'^(?:N-)?BV(?!R)', model):
        return (7, model)
    if re.search(r'^(?:N-)?BVR', model):
        return (8, model)
    if re.search(r'BYJ|BYJR', model):
        return (9, model)
    if re.search(r'RYJSP|RYSP|RYJS|RVS', model):
        return (10, model)
    return (11, model)


def sort_aggregated(aggregated: dict) -> list[tuple]:
    """对聚合结果按标准排序"""
    return sorted(aggregated.items(), key=lambda x: sort_key(x[0]))
