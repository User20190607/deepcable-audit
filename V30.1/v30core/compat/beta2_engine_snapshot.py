#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V30.0 Code-First Hybrid Runtime: deterministic-core MVP.

Standard-library only. This script does not call an LLM or launch agents.
It parses common cable models, applies exact authorized project mappings,
performs Decimal quantity conversion, detects selected risks, aggregates,
sorts, exports TSV-5 and runs a release gate.

The embedded rules are starter rules, not a certified national-standards
knowledge base. Review/freeze them before production use.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

VERSION = "30.0.0-alpha1"
PREFIXES = {"WDZBN","WDZCN","WDZAN","WDZB","WDZN","WDZC","WDZ","WDU","ZRA","ZRB","ZRC","ZCN","ZB","ZC","ZA","ZR"}
PRODUCTS = {
    "RYJSP","RYJYP","RYJY","RYJS","RYJP","RYSP","RVVSP","RVVPS","RVVP","RVV","RVSP","RVS","RV",
    "RYYSP","RYYP","RYY","RYS","RYJ","RY","YJLV","YJLY","YJV","YJY","BYJR","BYJS","BYJ","BYR","BVR","BVV","BV",
    "KVVRP","KVVR","KVVP","KVV","KYYP","KYJY","KYY","JHS","BTTRZ","BBTRZ","BTTZ","YTTWY"
}
PRODUCTS_BY_LENGTH = sorted(PRODUCTS, key=len, reverse=True)
WIRE_PRODUCTS = {"BV","BVR","BYJ","BYR","BYJR","BYJS"}
PVC_PRODUCTS = {"YJV","YJLV","BV","BVR","BVV","RV","RVV","RVS","RVVP","RVSP","RVVSP","RVVPS","KVV","KVVP","KVVR","KVVRP"}
POWER_PRODUCTS = {"YJV","YJY","YJLV","YJLY","JHS"}
CONTROL_PRODUCTS = {"KVV","KVVP","KVVR","KVVRP","KYY","KYYP","KYJY"}
WIRE_300_500 = {"BVV","RVV","RYJY","RYY"}
PAIR_300_300 = {"RVS","RYJS","RYS","RVVP","RVSP","RYSP","RYJSP","RVVSP","RYYSP","RYYP"}
AUX_SECTION_REFERENCE = {"4":"2.5","6":"4","10":"6","16":"10","25":"16","35":"16","50":"25","70":"35","95":"50","120":"70","150":"70","185":"95","240":"120","300":"150"}
COLOR_ORDER = ["黄","绿","红","蓝","双","黑","白","棕"]
COLOR_ALIASES = {"地线":"双","黄绿":"双","黄绿双色":"双","双色":"双"}
CORE_RE = re.compile(r"(?P<expr>(?:\d+\s*[×xX*]\s*)?\d+(?:\.\d+)?(?:\s*\+\s*\d+\s*[×xX*]\s*\d+(?:\.\d+)?)*?)\s*(?:mm(?:²|2)?|平方)?\s*$", re.I)
VOLTAGE_RE = re.compile(r"(?<![\w.])(?P<v>(?:\d+(?:\.\d+)?/\d+(?:\.\d+)?\s*kV|\d+(?:\.\d+)?\s*kV|\d+/\d+\s*V|\d+\s*V))", re.I)

@dataclass
class Component:
    cores: Optional[int]
    section: str

@dataclass
class ModelAST:
    original: str
    prefix: Optional[str]
    product: Optional[str]
    grade: Optional[str]
    voltage: Optional[str]
    components: list[Component]
    core_expression: Optional[str]
    category: str
    unknown_tokens: list[str]

def decimal(value: Any, field: str = "quantity") -> Decimal:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field} must be a decimal-compatible value")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid {field}: {value!r}")
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result

def fmt(value: Decimal) -> str:
    s = format(value, "f")
    return s.rstrip("0").rstrip(".") if "." in s else s

def normalize_x(s: str) -> str:
    s = s.replace("＊", "×").replace("ｘ", "×")
    return re.sub(r"(?<=\d)\s*[xX*]\s*(?=\d)", "×", s)

def find_prefix(s: str) -> Optional[str]:
    m = re.match(r"^\s*([A-Za-z]+)(?=-)", s)
    if not m:
        return None
    p = m.group(1).upper()
    return p if p in PREFIXES else None

def find_product(s: str) -> Optional[str]:
    u = s.upper()
    for p in PRODUCTS_BY_LENGTH:
        if re.search(rf"(?<![A-Z]){re.escape(p)}(?=[\s\-0-9]|$)", u):
            return p
    for p in PRODUCTS_BY_LENGTH:
        if u.startswith(p) and len(u) > len(p) and u[len(p)].isdigit():
            return p
    return None

SINGLE_CORE_PRODUCTS = WIRE_PRODUCTS | {"BVV"}

def parse_components(expr: Optional[str], product: Optional[str]) -> list[Component]:
    if not expr:
        return []
    out = []
    for part in normalize_x(expr).replace(" ", "").split("+"):
        if "×" in part:
            a, b = part.split("×", 1)
            if not a.isdigit():
                return []
            out.append(Component(int(a), b))
        else:
            out.append(Component(1 if product in SINGLE_CORE_PRODUCTS else None, part))
    return out

def default_voltage(product: Optional[str], comps: list[Component]) -> Optional[str]:
    if product in POWER_PRODUCTS:
        return "0.6/1kV"
    if product in CONTROL_PRODUCTS:
        return "450/750V"
    if product in WIRE_PRODUCTS:
        if not comps:
            return None
        try:
            return "300/500V" if Decimal(comps[0].section) <= Decimal("1") else "450/750V"
        except InvalidOperation:
            return None
    if product in WIRE_300_500:
        return "300/500V"
    if product in PAIR_300_300:
        return "300/300V"
    return None

def parse_model(text: str) -> ModelAST:
    original = str(text or "").strip()
    s = normalize_x(original)
    if "网线" in original:
        return ModelAST(original, None, None, None, None, [], None, "weak-current", [])
    prefix, product = find_prefix(s), find_product(s)
    vm = VOLTAGE_RE.search(s)
    voltage = None
    no_voltage = s
    if vm:
        voltage = re.sub(r"\s+", "", vm.group("v"))
        voltage = voltage.replace("KV", "kV").replace("kv", "kV")
        no_voltage = s[:vm.start()] + " " + s[vm.end():]
    cm = CORE_RE.search(no_voltage)
    expr = normalize_x(cm.group("expr")).replace(" ", "") if cm else None
    no_core = no_voltage[:cm.start()] if cm else no_voltage
    comps = parse_components(expr, product)
    grade_m = re.search(r"(?<![A-Z0-9])B([12])(?![A-Z0-9])", s.upper())
    grade = f"B{grade_m.group(1)}" if grade_m else None
    remainder = no_core.upper()
    for token in (prefix, product, "B1", "B2"):
        if token:
            remainder = re.sub(re.escape(token), " ", remainder)
    remainder = re.sub(r"[\s\-_:：,，()（）]", "", remainder)
    unknown = [remainder] if remainder else []
    if product in POWER_PRODUCTS:
        category = "power"
    elif product in CONTROL_PRODUCTS:
        category = "control"
    elif product in WIRE_PRODUCTS or product == "BVV":
        category = "building-wire"
    elif product in PAIR_300_300 or product in {"RY","RYJ","RYY","RYYP"}:
        category = "communication/soft"
    elif product:
        category = "special"
    else:
        category = "other"
    voltage = voltage or default_voltage(product, comps)
    return ModelAST(original, prefix, product, grade, voltage, comps, expr, category, unknown)

def canonical_model(ast: ModelAST) -> Optional[str]:
    if ast.category == "weak-current":
        return ast.original
    if not ast.product:
        return None
    head = [x for x in (ast.prefix, ast.product, ast.grade, ast.voltage) if x]
    if not ast.components:
        return "-".join(head)
    rendered = []
    for c in ast.components:
        rendered.append(f"{c.cores}×{c.section}" if c.cores is not None else c.section)
    return "-".join(head) + " " + "+".join(rendered)

def exact_mapping(raw: str, mappings: list[dict[str, Any]], scope: str) -> Optional[dict[str, Any]]:
    key = normalize_x(raw).strip().upper()
    for m in mappings:
        src = normalize_x(str(m.get("source_model", ""))).strip().upper()
        if src == key and m.get("scope", "current-batch") in {scope, "global"} and m.get("authorization_ref"):
            return m
    return None

def validate_ast(ast: ModelAST) -> list[dict[str, str]]:
    findings = []
    if ast.category == "weak-current":
        return findings
    if not ast.product:
        findings.append({"code":"UNKNOWN_PRODUCT","severity":"HOLD","field":"model","message":"无法识别产品型号，保留原文并等待确认。"})
        return findings
    if ast.unknown_tokens:
        findings.append({"code":"UNKNOWN_TOKENS","severity":"HOLD","field":"model","message":f"型号中存在未解析字段：{ast.unknown_tokens}"})
    if ast.prefix and ast.prefix.startswith(("WDZ", "WDU")) and ast.product in PVC_PRODUCTS:
        findings.append({"code":"HALOGEN_FREE_PVC_CONFLICT","severity":"HOLD","field":"model","message":"低烟无卤前缀与当前识别的PVC材料产品代码存在冲突；需要完整、已授权的映射。"})
    if not ast.voltage:
        findings.append({"code":"VOLTAGE_UNRESOLVED","severity":"HOLD","field":"voltage","message":"未找到明确电压或适用的缺省电压规则。"})
    if len(ast.components) >= 2:
        main, aux = ast.components[0], ast.components[1]
        expected = AUX_SECTION_REFERENCE.get(main.section) if main.cores is not None and aux.cores is not None else None
        if expected and Decimal(aux.section) != Decimal(expected):
            findings.append({"code":"AUX_SECTION_REFERENCE_DEVIATION","severity":"WARN","field":"core_expression","message":f"主芯{main.section}mm²的采购参考辅芯为{expected}mm²，当前为{aux.section}mm²；仅提示，不自动改值。"})
    return findings

def status_of(findings: list[dict[str, str]]) -> str:
    order = {"PASS":0,"WARN":1,"HOLD":2,"BLOCK":3,"INCOMPLETE":4}
    return max((x["severity"] for x in findings), key=lambda x: order.get(x, 4)) if findings else "PASS"

def process_row(src: dict[str, Any], mappings: Optional[list[dict[str, Any]]] = None,
                scope: str = "current-batch", default_bale_length: str = "100") -> dict[str, Any]:
    mappings = mappings or []
    raw = str(src.get("model", src.get("model_text", ""))).strip()
    if not raw:
        raise ValueError("Each row requires model or model_text")
    rid = str(src.get("row_id") or "ROW-" + hashlib.sha1((raw+"|"+str(src.get("quantity"))).encode()).hexdigest()[:12].upper())
    mapping = exact_mapping(raw, mappings, scope)
    working = str(mapping["target_model"]) if mapping else raw
    ast = parse_model(working)
    findings = validate_ast(ast)
    quantity = decimal(src.get("quantity"))
    original_quantity, original_unit = quantity, str(src.get("unit", "m")).strip()
    unit, pack_length = original_unit, src.get("pack_length_m")
    if unit in {"扎", "捆"}:
        quantity *= decimal(pack_length if pack_length is not None else default_bale_length, "pack_length_m")
        unit = "m"
    elif unit in {"卷", "圈"} and pack_length is not None:
        quantity *= decimal(pack_length, "pack_length_m")
        unit = "m"
    color = str(src.get("color", "")).strip()
    color = COLOR_ALIASES.get(color, color)
    if color and color not in COLOR_ORDER:
        findings.append({"code":"UNKNOWN_COLOR","severity":"HOLD","field":"color","message":f"无法识别颜色：{color}"})
    model = canonical_model(ast) or working
    return {
        "row_id":rid,"source_id":str(src.get("source_id", "")),"raw_model":raw,
        "working_model":working,"model":model,"unit":unit,"quantity":fmt(quantity),
        "quantity_basis":src.get("quantity_basis", "source-defined"),"remark":str(src.get("remark", "") or ""),
        "color":color,"category":ast.category,"ast":asdict(ast),"findings":findings,
        "status":status_of(findings),"scope":src.get("scope", scope),
        "original_quantity":fmt(original_quantity),"original_unit":original_unit,
        "mapping_audit":({"source_model":raw,"target_model":working,"authorization_ref":mapping["authorization_ref"],"scope":mapping.get("scope",scope)} if mapping else None)
    }

def sort_key(row: dict[str, Any]):
    ranks = {"power":0,"special":1,"control":2,"building-wire":3,"communication/soft":4,"weak-current":5,"other":6}
    comps = row.get("ast", {}).get("components", [])
    section = Decimal(comps[0]["section"]) if comps else Decimal("0")
    core_count = sum(int(c.get("cores") or 1) for c in comps)
    return (ranks.get(row.get("category"), 9), -section, -core_count)

def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple, dict[str, Any]] = {}
    for idx, row in enumerate(rows):
        key = (row["model"], row["unit"], row["quantity_basis"], row["status"], row["scope"])
        if key not in groups:
            groups[key] = {"model":row["model"],"unit":row["unit"],"quantity_decimal":Decimal("0"),
                           "quantity_basis":row["quantity_basis"],"status":row["status"],"scope":row["scope"],
                           "category":row["category"],"ast":row["ast"],"first_index":idx,
                           "colors":{},"remarks":[],"source_rows":[],"findings":[]}
        g = groups[key]
        q = Decimal(row["quantity"])
        g["quantity_decimal"] += q
        if row["color"]:
            g["colors"][row["color"]] = g["colors"].get(row["color"], Decimal("0")) + q
        if row["remark"] and row["remark"] not in g["remarks"]:
            g["remarks"].append(row["remark"])
        g["source_rows"].append({"row_id":row["row_id"],"source_id":row["source_id"],"raw_model":row["raw_model"],
                                 "original_quantity":row["original_quantity"],"original_unit":row["original_unit"],
                                 "quantity_after_conversion":row["quantity"],"color":row["color"]})
        for f in row["findings"]:
            if f not in g["findings"]: g["findings"].append(f)
    out = []
    for g in groups.values():
        color_text = "".join(f"{c}{fmt(g['colors'][c])}" for c in COLOR_ORDER if c in g["colors"])
        remark = "｜".join(([color_text] if color_text else []) + g["remarks"])
        g["quantity"] = fmt(g.pop("quantity_decimal"))
        g["remark"] = remark
        g.pop("colors"); g.pop("remarks")
        out.append(g)
    return sorted(out, key=lambda x: (sort_key(x), x["first_index"]))

def render_tsv5(rows: list[dict[str, Any]]) -> str:
    lines = []
    for r in rows:
        fields = [str(r["model"]), str(r["unit"]), str(r["quantity"]), "", str(r.get("remark", ""))]
        fields = [x.replace("\t", " ").replace("\r", " ").replace("\n", " ") for x in fields]
        lines.append("\t".join(fields))
    return "\n".join(lines)

def apply_patch(rows: list[dict[str, Any]], patch: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = {"model", "quantity", "unit", "remark"}
    field, rid = patch.get("target_path"), patch.get("row_id")
    if field not in allowed: raise ValueError(f"Patch field not allowed: {field}")
    if not patch.get("authorization_ref"): raise ValueError("Patch requires authorization_ref")
    result = [dict(r) for r in rows]
    found = [r for r in result if r.get("row_id") == rid]
    if len(found) != 1: raise ValueError(f"Expected exactly one row for {rid}, found {len(found)}")
    target = found[0]
    if str(target.get(field)) != str(patch.get("before_value")):
        raise ValueError(f"Snapshot conflict for {rid}.{field}")
    after = patch.get("after_value")
    if field == "quantity": after = fmt(decimal(after, "patch quantity"))
    before = target.get(field)
    target[field] = after
    target.setdefault("patch_log", []).append({"target_path":field,"before_value":before,"after_value":after,
                                                "authorization_ref":patch["authorization_ref"],"patch_id":patch.get("patch_id")})
    return result

def release_gate(source_rows: list[dict[str, Any]], groups: list[dict[str, Any]], tsv: str) -> dict[str, Any]:
    errors = []
    ids = [r["row_id"] for r in source_rows]
    if not source_rows:
        errors.append("No source rows")
    if len(ids) != len(set(ids)):
        errors.append("Duplicate row_id")
    for r in source_rows:
        if r["status"] in {"HOLD", "BLOCK", "INCOMPLETE", "ERROR"}:
            errors.append(f"{r['row_id']} status={r['status']}")

    # Compare quantity conservation independently for each unit; never add
    # metres to rolls/pieces as if they were the same unit.
    source_by_unit: dict[str, Decimal] = {}
    group_by_unit: dict[str, Decimal] = {}
    for r in source_rows:
        source_by_unit[r["unit"]] = source_by_unit.get(r["unit"], Decimal("0")) + Decimal(r["quantity"])
    for r in groups:
        group_by_unit[r["unit"]] = group_by_unit.get(r["unit"], Decimal("0")) + Decimal(r["quantity"])
    if source_by_unit != group_by_unit:
        errors.append(f"Quantity conservation failed by unit: source={source_by_unit}, grouped={group_by_unit}")

    # If a group contains color detail, the colors must account for the full
    # group quantity. This prevents silently incomplete color allocation.
    for g in groups:
        colored_rows = [x for x in g["source_rows"] if x.get("color")]
        if colored_rows:
            color_total = sum((Decimal(x["quantity_after_conversion"]) for x in colored_rows), Decimal("0"))
            if color_total != Decimal(g["quantity"]):
                errors.append(f"Color allocation incomplete for {g['model']}: colors={color_total}, total={g['quantity']}")

    for n, line in enumerate(tsv.splitlines(), 1):
        if len(line.split("\t")) != 5:
            errors.append(f"TSV line {n} is not five columns")
    status = "HELD" if errors else ("RELEASED_WITH_WARNINGS" if any(r["status"] == "WARN" for r in source_rows) else "RELEASED")
    return {
        "status": status,
        "errors": errors,
        "source_row_count": len(source_rows),
        "aggregated_row_count": len(groups),
        "source_quantity_by_unit": {k: fmt(v) for k, v in source_by_unit.items()},
        "aggregated_quantity_by_unit": {k: fmt(v) for k, v in group_by_unit.items()},
        "engine_version": VERSION,
    }

def run_pipeline(payload: dict[str, Any]) -> dict[str, Any]:
    scope = payload.get("scope", "current-batch")
    rows = [process_row(r, payload.get("project_mappings", []), scope, str(payload.get("default_bale_length_m", "100"))) for r in payload.get("rows", [])]
    groups = aggregate_rows(rows)
    tsv = render_tsv5(groups)
    gate = release_gate(rows, groups, tsv)
    return {"engine_version":VERSION,"batch_id":payload.get("batch_id"),"scope":scope,
            "source_rows":rows,"aggregated_rows":groups,"tsv5":tsv,"release_gate":gate}

def main() -> int:
    ap = argparse.ArgumentParser(description="V30.0 deterministic cable-list core")
    ap.add_argument("--input", required=True, help="Input JSON")
    ap.add_argument("--output", help="TSV-5 output path (default: stdout)")
    ap.add_argument("--audit", help="Full audit JSON output path")
    args = ap.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = run_pipeline(payload)
    if args.output:
        Path(args.output).write_text(result["tsv5"] + ("\n" if result["tsv5"] else ""), encoding="utf-8")
    else:
        print(result["tsv5"])
    if args.audit:
        Path(args.audit).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    gate = result["release_gate"]
    print(f"[V30] {gate['status']} | source={gate['source_row_count']} | grouped={gate['aggregated_row_count']} | totals={gate['source_quantity_by_unit']}", file=sys.stderr)
    for e in gate["errors"]: print(f"[GATE] {e}", file=sys.stderr)
    return 0 if gate["status"] in {"RELEASED","RELEASED_WITH_WARNINGS"} else 2

if __name__ == "__main__":
    raise SystemExit(main())