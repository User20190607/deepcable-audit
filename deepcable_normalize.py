"""
deepcable_normalize.py — 向后兼容包装器（v24.2）

原有 import 方式不变：
    from deepcable_normalize import normalize, aggregate, to_excel

内部已拆分为独立模块：
    tokenizer → parser → normalizer → validation → aggregator → excel_output
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# 保证同目录模块可导入
_parent = Path(__file__).parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from tokenizer import tokenize, detect_pv
from parser import parse
from normalizer import normalize as normalize_ast
from spec import CableSpec, CoreSpec
from aggregator import aggregate, sort_key
from validation import check_pe, validate_cable
from model_interpreter import interpret_model
from english_parser import parse_english_model


ProcessingStatus = Literal[
    'accepted', 'corrected', 'inferred', 'needs_review', 'rejected'
]


@dataclass(frozen=True)
class ProcessingIssue:
    code: str
    message: str
    severity: Literal['info', 'warning', 'error'] = 'warning'
    field: str = ''


@dataclass
class NormalizeResult:
    raw: str
    status: ProcessingStatus
    model: str | None = None
    spec: CableSpec | None = None
    changes: list[str] = field(default_factory=list)
    issues: list[ProcessingIssue] = field(default_factory=list)
    unparsed: str = ''
    error: str = ''

    @property
    def ok(self) -> bool:
        return self.status in {'accepted', 'corrected', 'inferred'}


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
    return normalize_detailed(raw).model


def normalize_with_log(raw: str) -> tuple[str | None, list[str]]:
    """
    标准化并返回变更日志。

    返回 (标准化型号, patch_log)，便于审计每个字段的修改过程。
    """
    result = normalize_detailed(raw)
    return result.model, result.changes


def normalize_detailed(raw: str) -> NormalizeResult:
    """Run the full pipeline and retain status, diagnostics and structured data."""
    try:
        return _normalize_pipeline_detailed(raw)
    except Exception as exc:
        return NormalizeResult(
            raw=raw,
            status='rejected',
            issues=[ProcessingIssue(
                code='pipeline_error',
                message='处理过程中发生内部错误',
                severity='error',
            )],
            error=f'{type(exc).__name__}: {exc}',
        )


def _normalize_pipeline(raw: str, with_log: bool = False) -> str | None | tuple[str | None, list[str]]:
    """Compatibility adapter for older internal callers."""
    result = normalize_detailed(raw)
    if with_log:
        return result.model, result.changes
    return result.model


def _normalize_pipeline_detailed(raw: str) -> NormalizeResult:
    """tokenizer → parser → AST normalizer → decision"""
    working_raw = raw
    pre_changes = []
    upper_raw = raw.strip().upper()
    if (upper_raw.startswith(('CU/', 'AL/'))
            or '接地线' in raw or '接地裸铜线' in raw):
        english_result = parse_english_model(raw)
        if english_result:
            working_raw = english_result
            pre_changes.append(f'[P0] 英文型号映射 {english_result}')

    # Step 1: Tokenize
    result = tokenize(working_raw)

    # PV1-F 特殊处理
    if result.base_type == 'pv':
        pv = detect_pv(working_raw)
        if pv:
            spec = CableSpec(
                raw=raw,
                base=pv['base'],
                voltage=pv['voltage'],
                cores=[CoreSpec(**c) for c in pv['cores']],
                color=pv['color'],
                is_pv=True,
                recognized_base=True,
            )
            out = spec.to_string()
            return NormalizeResult(raw=raw, status='accepted', model=out, spec=spec)
        return NormalizeResult(
            raw=raw,
            status='rejected',
            issues=[ProcessingIssue('invalid_pv', '无法提取光伏电缆截面', 'error', 'cores')],
        )

    # Step 2: Parse → CableSpec AST
    spec = parse(result.cleaned, color=result.color)

    if spec is None or not spec.base:
        return NormalizeResult(
            raw=raw,
            status='rejected',
            issues=[ProcessingIssue('missing_base', '无法识别基础型号', 'error', 'base')],
        )

    # Step 3: Normalize
    normalized = normalize_ast(spec)
    if normalized is None:
        return NormalizeResult(raw=raw, status='rejected')

    normalized.raw = raw
    if pre_changes:
        normalized.patch_log[:0] = pre_changes
    out = normalized.to_string()
    issues = []
    if not normalized.recognized_base:
        issues.append(ProcessingIssue(
            'unknown_base', f'基础型号 {normalized.base} 尚未进入规则表',
            'warning', 'base',
        ))
    if normalized.unparsed:
        issues.append(ProcessingIssue(
            'unparsed_content', f'存在未解析内容：{normalized.unparsed}',
            'warning', 'raw',
        ))

    for item in validate_cable(normalized):
        issues.append(ProcessingIssue(
            code=f'validation_{item["field"]}',
            message=item['message'],
            severity=item['severity'],
            field=item['field'],
        ))

    if issues:
        status: ProcessingStatus = 'needs_review'
    elif normalized.is_guess:
        status = 'inferred'
    elif normalized.patch_log:
        status = 'corrected'
    else:
        status = 'accepted'

    return NormalizeResult(
        raw=raw,
        status=status,
        model=out,
        spec=normalized,
        changes=list(normalized.patch_log),
        issues=issues,
        unparsed=normalized.unparsed,
    )


def to_excel(*args, **kwargs):
    """Lazy import so normalization does not require spreadsheet dependencies."""
    from excel_output import to_excel as _to_excel
    return _to_excel(*args, **kwargs)


# 重新导出
__all__ = [
    'normalize', 'normalize_with_log', 'normalize_detailed',
    'NormalizeResult', 'ProcessingIssue',
    'aggregate', 'to_excel', 'check_pe', 'sort_key', 'interpret_model',
]
