"""
CableSpec — 电缆型号结构化 AST（Abstract Syntax Tree）

所有模块通过这个数据结构交换信息，避免字符串解析链。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CoreSpec:
    """单根芯线规格"""
    count: int          # 芯数，如 4×25 → 4
    section: float      # 截面 mm²，如 4×25 → 25.0
    role: str = ''      # 'phase' | 'neutral' | 'pe' | 'earth' | ''


def fmt_section(s: float) -> str:
    """格式化截面：整数去 .0，小数保留"""
    return str(int(s)) if s == int(s) else str(s)


@dataclass
class CableSpec:
    """完整的电缆型号结构化表示"""
    raw: str                        # 原始输入字符串
    prefix: str = ''                # GB/T 19666 燃烧特性前缀，如 ZCN, WDZC, N
    base: str = ''                  # 基础型号，如 YJV, YJY, KVV, RVS
    voltage: str = ''               # 额定电压，如 0.6/1kV, 450/750V
    cores: list[CoreSpec] = field(default_factory=list)  # 芯线列表
    color: str = ''                 # 颜色后缀，如 红, 蓝
    b1: bool = False                # B1 级阻燃标志
    is_pv: bool = False             # 光伏电缆 PV1-F
    is_guess: bool = False          # True = 有字段是推断补全的，非原始数据
    patch_log: list[str] = field(default_factory=list)  # 变更日志，如 ['[P1] NH→N', '[P3] YJV→YJY']

    def to_string(self) -> str:
        """序列化为标准型号字符串"""
        parts = []
        if self.prefix:
            parts.append(self.prefix)
        core_model = self.base
        if self.b1:
            core_model += '-B1'
        parts.append(core_model)
        if self.voltage:
            parts.append(self.voltage)
        core_str = '+'.join(f'{c.count}×{fmt_section(c.section)}' for c in self.cores)
        if core_str:
            parts.append(core_str)
        result = '-'.join(parts)
        if self.color:
            result += f'({self.color})'
        return result

    def to_fingerprint(self) -> str:
        """型号指纹（用于聚合）：忽略颜色，仅取结构特征"""
        parts = []
        if self.prefix:
            parts.append(self.prefix)
        core_model = self.base
        if self.b1:
            core_model += '-B1'
        parts.append(core_model)
        if self.voltage:
            parts.append(self.voltage)
        core_str = '+'.join(f'{c.count}×{fmt_section(c.section)}' for c in self.cores)
        if core_str:
            parts.append(core_str)
        return '-'.join(parts)
