"""
deepcable_normalize.py — 向后兼容包装器（v24.2）

原有 import 方式不变：
    from deepcable_normalize import normalize, aggregate, to_excel

内部已拆分为独立模块：
    tokenizer → parser → normalizer → validation → aggregator → excel_output
"""

import sys
from pathlib import Path

# 保证同目录模块可导入
_parent = Path(__file__).parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from tokenizer import tokenize, detect_pv
from parser import parse
from normalizer import normalize as normalize_ast
from aggregator import aggregate, sort_key
from validation import check_pe
from excel_output import to_excel
from model_interpreter import interpret_model
from english_parser import parse_english_model


def normalize(raw: str) -> str | None:
    """
    原始型号字符串 → 标准化型号字符串。

    输入：原始型号（含中文前缀、空格、旧写法均可）
    输出：标准化型号字符串，无法识别返回 None

    示例：
        normalize('电缆NHYJV-0.6/1KV- 5X16')  → 'N-YJV-0.6/1KV-5×16'
        normalize('WDZN-RVS-2*1.5')            → 'WDZN-RYJS-300/300V-2×1.5'
        normalize('电线BVR2.5')                → 'BVR-450/750V-1×2.5'
    """
    try:
        return _normalize_pipeline(raw)
    except Exception:
        return None


def normalize_with_log(raw: str) -> tuple[str | None, list[str]]:
    """
    标准化并返回变更日志。

    返回 (标准化型号, patch_log)，便于审计每个字段的修改过程。
    """
    try:
        return _normalize_pipeline(raw, with_log=True)
    except Exception:
        return None, []


def _normalize_pipeline(raw: str, with_log: bool = False) -> str | None | tuple[str | None, list[str]]:
    """新 pipeline：tokenizer → parser → normalizer，支持英文型号自动 fallback"""
    # Step 0: Try English model parser first for CU/... format or Chinese prefixes
    if (raw.strip().upper().startswith('CU/') or 
        raw.strip().upper().startswith('AL/') or
        '接地线' in raw or 
        '接地裸铜线' in raw):
        english_result = parse_english_model(raw)
        if english_result:
            raw = english_result
    
    # Step 1: Tokenize
    result = tokenize(raw)

    # PV1-F 特殊处理
    if result.base_type == 'pv':
        pv = detect_pv(raw)
        if pv:
            from spec import CableSpec, CoreSpec
            spec = CableSpec(
                raw=raw,
                base=pv['base'],
                voltage=pv['voltage'],
                cores=[CoreSpec(**c) for c in pv['cores']],
                color=pv['color'],
                is_pv=True,
            )
            out = spec.to_string()
            return (out, []) if with_log else out
        return (None, []) if with_log else None

    # Step 2: Parse → CableSpec AST
    spec = parse(result.cleaned, color=result.color)

    if spec is None or not spec.base:
        return (None, []) if with_log else None

    # Step 3: Normalize
    normalized = normalize_ast(spec)
    if normalized is None:
        return (None, []) if with_log else None

    out = normalized.to_string()
    if with_log:
        return out, normalized.patch_log
    return out


# 重新导出
__all__ = ['normalize', 'aggregate', 'to_excel', 'check_pe', 'sort_key', 'interpret_model']
