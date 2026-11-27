#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V30.1 deterministic cable-list kernel; candidate, not production-certified."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
import argparse, hashlib, json, re, sys

VERSION = "30.1.0"
PREFIXES = tuple(sorted({"WDZBN","WDZCN","WDZAN","WDZB","WDZN","WDZC","WDZ","WDU","ZRA","ZRB","ZRC","ZCN","ZB","ZC","ZA","ZR","N"}, key=len, reverse=True))
PRODUCTS = tuple(sorted({"RYJSP","RYJYP","RYJY","RYJS","RYJP","RYSP","RVVSP","RVVPS","RVVP","RVV","RVSP","RVS","RV","RYYSP","RYYP","RYY","RYS","RYJ","RY","YJLV","YJLY","YJV","YJY","BYJR","BYJS","BYJ","BYR","BVR","BVV","BV","KVVRP","KVVR","KVVP","KVV","KYYP","KYJY","KYY","JHS","BBTRZ","BTTZ","YTTWY"}, key=len, reverse=True))
COLOR_ORDER = ("黄", "绿", "红", "蓝", "双")
COLOR_ALIASES = {"地线":"双", "黄绿":"双", "黄绿双色":"双", "双色":"双"}
POWER_PRODUCTS = {"YJV","YJY","YJLV","YJLY","JHS"}
WIRE_PRODUCTS = {"BV","BVR","BYJ","BYR","BYJR","BYJS"}
VOLTAGE_DEFAULTS = {"BVV":"300/500V", "RVV":"300/500V", "RVVP":"300/300V", "RVS":"300/300V", "RYJS":"300/300V", "BVR":"450/750V", "BV":"450/750V", "BYJ":"450/750V"}

class ValidationError(ValueError): pass

def D(v: Any, field="value") -> Decimal:
    if isinstance(v, bool) or v is None: raise ValidationError(f"{field}: missing or invalid")
    try: x=Decimal(str(v))
    except (InvalidOperation, ValueError): raise ValidationError(f"{field}: invalid decimal {v!r}")
    if not x.is_finite(): raise ValidationError(f"{field}: non-finite decimal")
    return x

def fmt(x: Decimal) -> str:
    s=format(x,"f")
    return s.rstrip("0").rstrip(".") if "." in s else s

def normalize_x(s: str) -> str:
    s=s.replace("＊","×").replace("ｘ","×")
    return re.sub(r"(?<=\d)\s*[xX*]\s*(?=\d)","×",s)

@dataclass
class ParsedModel:
    original: str
    prefix: str|None
    product: str|None
    voltage: str|None
    grade: str|None
    armor: str|None
    expression: str|None
    components: list[dict[str,Any]]
    status: str
    findings: list[dict[str,str]]

def parse_model(raw: str) -> ParsedModel:
    s=normalize_x(str(raw or "").strip()); u=s.upper(); prefix=None; product=None; findings=[]
    for p in PREFIXES:
        if u.startswith(p) and len(u)>len(p):
            tail=u[len(p):]
            if tail.startswith("-") or any(tail.startswith(x) for x in PRODUCTS):
                prefix=p; s=s[len(p):].lstrip("- "); u=s.upper(); break
    for p in PRODUCTS:
        if u.startswith(p) and (len(u)==len(p) or u[len(p)] in "- _0123456789"):
            product=p; s=s[len(p):].lstrip("- "); u=s.upper(); break
    if product is None:
        for p in PRODUCTS:
            if re.search(rf"(?<![A-Z]){p}(?=[\s\-0-9]|$)",u): product=p; break
    vm=re.search(r"(?<![\w.])(\d+(?:\.\d+)?/\d+(?:\.\d+)?\s*kV|\d+(?:\.\d+)?\s*kV|\d+/\d+\s*V|\d+\s*V)",s,re.I)
    voltage=re.sub(r"\s+","",vm.group(1)).replace("KV","kV").replace("kv","kV") if vm else None
    if vm: s=s[:vm.start()]+" "+s[vm.end():]
    gm=re.search(r"(?<![A-Z0-9])B([12])(?![A-Z0-9])",s.upper()); grade=f"B{gm.group(1)}" if gm else None
    am=re.search(r"(?<!\d)(22|23)(?!\d)",s); armor=am.group(1) if am else None
    cm=re.search(r"((?:\d+\s*×\s*)?\d+(?:\.\d+)?(?:\s*\+\s*\d+\s*×\s*\d+(?:\.\d+)?)*)(?:\s*(?:mm²|mm2|平方))?\s*$",s,re.I)
    expr=normalize_x(cm.group(1)).replace(" ","") if cm else None; comps=[]
    if expr:
        for part in expr.split("+"):
            if "×" in part:
                a,b=part.split("×",1); comps.append({"cores":int(a),"section":b})
            else: comps.append({"cores":1 if product in WIRE_PRODUCTS or product=="BVV" else None,"section":part})
    if not product: findings.append({"code":"UNKNOWN_PRODUCT","severity":"HOLD","message":"产品型号无法可靠识别"})
    if product in POWER_PRODUCTS and voltage is None:
        findings.append({"code":"VOLTAGE_UNRESOLVED","severity":"HOLD","message":"电力电缆未提供电压等级；不得仅凭产品代号盲目补全"})
    if voltage is None and product in VOLTAGE_DEFAULTS: voltage=VOLTAGE_DEFAULTS[product]
    if prefix and prefix.startswith(("WDZ","WDU")) and product in {"YJV","BV","BVR","BVV","RV","RVV","RVVP"}:
        findings.append({"code":"HALOGEN_FREE_PVC_CONFLICT","severity":"HOLD","message":"无卤前缀与PVC产品体系冲突，须经明确映射授权"})
    status="HOLD" if any(x["severity"]=="HOLD" for x in findings) else "PASS"
    return ParsedModel(str(raw),prefix,product,voltage,grade,armor,expr,comps,status,findings)

def canonical_model(p: ParsedModel) -> str|None:
    if not p.product: return None
    head=[x for x in (p.prefix,p.product+(p.armor or ""),p.grade,p.voltage) if x]
    if not p.components: return "-".join(head)
    expr="+".join((f"{c['cores']}×{c['section']}" if c["cores"] is not None else c["section"]) for c in p.components)
    return "-".join(head)+" "+expr

def validate_conductors(cable: dict[str,Any], reviewed_profiles: dict[str,Any]) -> dict[str,Any]:
    roles=cable.get("conductor_roles")
    if not roles: return {"status":"HOLD","code":"CONDUCTOR_FUNCTION_UNKNOWN","message":"必须提供N/PE/PEN功能映射"}
    results=[]
    for c in roles:
        role=c.get("role")
        if role not in {"N","PE","PEN"}: continue
        profile=reviewed_profiles.get(c.get("profile_id")) if c.get("profile_id") else None
        if not profile or profile.get("review_status")!="APPROVED" or not profile.get("standard_id") or not profile.get("clause"):
            results.append({"role":role,"status":"BLOCKED","reason":"缺少已审核的标准规则档案及条款证据"}); continue
        required=D(profile.get("required_section_mm2"),"required_section_mm2"); actual=D(c.get("section_mm2"),"section_mm2")
        results.append({"role":role,"actual_section_mm2":fmt(actual),"required_section_mm2":fmt(required),"standard_id":profile["standard_id"],"clause":profile["clause"],"status":"PASS" if actual>=required else "FAIL"})
    if not results: return {"status":"HOLD","code":"NO_N_PE_PEN_ROLE","message":"未识别到需要核验的N/PE/PEN导体"}
    overall="FAIL" if any(x["status"]=="FAIL" for x in results) else "BLOCKED" if any(x["status"]=="BLOCKED" for x in results) else "PASS"
    return {"status":overall,"results":results}

def process_row(src: dict[str,Any], reviewed_profiles=None) -> dict[str,Any]:
    raw=str(src.get("model",src.get("model_text",""))).strip()
    if not raw: raise ValidationError("model is required")
    rid=str(src.get("row_id") or "ROW-"+hashlib.sha256((raw+str(src.get("quantity"))).encode()).hexdigest()[:12])
    q=D(src.get("quantity"),"quantity"); unit=str(src.get("unit","m")); orig_q=q; orig_unit=unit
    findings=[]; pack=src.get("pack_length_m")
    if unit in {"卷","圈","PCS","pc","件","扎","捆"}:
        if pack is None: findings.append({"code":"PACK_LENGTH_UNCONFIRMED","severity":"HOLD","message":"包装换算缺少已确认的单卷/单件长度"})
        else: q*=D(pack,"pack_length_m"); unit="m"
    if unit=="m" and q!=q.to_integral_value(): findings.append({"code":"FRACTIONAL_METRE","severity":"HOLD","message":"米数必须为整数；不得静默取整"})
    p=parse_model(raw); findings.extend(p.findings); conductor_validation=None
    if p.product in POWER_PRODUCTS and len(p.components)>1:
        roles=src.get("conductor_roles")
        if not roles:
            conductor_validation={"status":"HOLD","code":"AUX_CONDUCTOR_ROLE_UNRESOLVED","message":"复合截面导体功能未明确；不得按芯数或截面比例推断"}
            findings.append({"code":"AUX_CONDUCTOR_ROLE_UNRESOLVED","severity":"HOLD","message":conductor_validation["message"]})
        else:
            conductor_validation=validate_conductors({"conductor_roles":roles},reviewed_profiles or {})
            if conductor_validation["status"]!="PASS":
                sev="BLOCK" if conductor_validation["status"] in {"FAIL","BLOCKED"} else "HOLD"
                findings.append({"code":"CONDUCTOR_VALIDATION_"+conductor_validation["status"],"severity":sev,"message":"N/PE/PEN导体校验未通过或缺少已审核证据"})
    remark=str(src.get("remark","") or ""); loss=src.get("production_loss_m")
    if loss is not None:
        note=f"生产损耗{fmt(D(loss,'production_loss_m'))}m（不计入采购数量）"
        if note not in remark: remark=(remark+"；" if remark else "")+note
    color=COLOR_ALIASES.get(str(src.get("color","")).strip(),str(src.get("color","")).strip())
    if color and color not in COLOR_ORDER: findings.append({"code":"UNKNOWN_COLOR","severity":"HOLD","message":f"未知颜色：{color}"})
    status="BLOCK" if any(f["severity"]=="BLOCK" for f in findings) else "HOLD" if any(f["severity"]=="HOLD" for f in findings) else "WARN" if findings else "PASS"
    return {"row_id":rid,"raw_model":raw,"model":canonical_model(p) or raw,"unit":unit,"quantity":fmt(q),"original_quantity":fmt(orig_q),"original_unit":orig_unit,"pack_length_m":str(pack) if pack is not None else None,"color":color,"remark":remark,"status":status,"findings":findings,"parsed":asdict(p),"conductor_validation":conductor_validation}

def aggregate_rows(rows, sort_mode="model"):
    groups={}
    for i,r in enumerate(rows):
        key=(r["model"],r["unit"],r["status"])
        if key not in groups: groups[key]={"model":r["model"],"unit":r["unit"],"quantity":Decimal(0),"status":r["status"],"first_index":i,"colors":{},"remarks":[],"source_rows":[]}
        g=groups[key]; g["quantity"]+=D(r["quantity"])
        if r["color"]: g["colors"][r["color"]]=g["colors"].get(r["color"],Decimal(0))+D(r["quantity"])
        if r["remark"] and r["remark"] not in g["remarks"]: g["remarks"].append(r["remark"])
        g["source_rows"].append(r["row_id"])
    out=[]
    for g in groups.values():
        colors="".join(c+fmt(g["colors"][c]) for c in COLOR_ORDER if c in g["colors"])
        g["quantity"]=fmt(g["quantity"]); g["remark"]="；".join(([colors] if colors else [])+g["remarks"])
        g.pop("colors"); g.pop("remarks"); out.append(g)
    if sort_mode=="source": out.sort(key=lambda x:x["first_index"])
    elif sort_mode=="model": out.sort(key=lambda x:(x["model"],x["first_index"]))
    else: raise ValidationError("sort_mode must be source or model")
    return out

def render_tsv5(rows):
    return "\n".join("\t".join([r["model"],r["unit"],r["quantity"],"",r.get("remark","")]) for r in rows)

def apply_patch(row, patch, reviewed_profiles=None):
    allowed={"model","quantity","unit","color","remark","pack_length_m","production_loss_m"}
    field=patch.get("field")
    if field not in allowed or not patch.get("authorization_ref"): raise ValidationError("invalid or unauthorized patch")
    if str(row.get(field,""))!=str(patch.get("before_value","")): raise ValidationError("patch snapshot conflict")
    changed=dict(row); changed[field]=patch.get("after_value")
    result=process_row(changed,reviewed_profiles)
    result["patch_audit"]={"field":field,"before":patch.get("before_value"),"after":patch.get("after_value"),"authorization_ref":patch["authorization_ref"],"revalidated":True}
    return result

def release_gate(raw_rows, processed_rows, groups, tsv):
    errors=[]
    raw_map={str(r.get("row_id")):r for r in raw_rows}; proc_map={r["row_id"]:r for r in processed_rows}
    if len(raw_rows)!=len(processed_rows): errors.append("SOURCE_ROW_COUNT_MISMATCH")
    if len(raw_map)!=len(raw_rows) or len(proc_map)!=len(processed_rows): errors.append("DUPLICATE_ROW_ID")
    if set(raw_map)!=set(proc_map): errors.append("SOURCE_IDENTITY_MISMATCH")
    expected={}
    for rid,src in raw_map.items():
        r=proc_map.get(rid)
        if not r: continue
        if r["status"] in {"HOLD","BLOCK","BLOCKED"}: errors.append(f"ROW_NOT_RELEASEABLE:{rid}:{r['status']}")
        q=D(src.get("quantity")); u=str(src.get("unit","m")); pack=src.get("pack_length_m")
        if u in {"卷","圈","PCS","pc","件","扎","捆"}:
            if pack is None: errors.append(f"MISSING_PACK_LENGTH:{rid}"); continue
            q*=D(pack); u="m"
        if u=="m" and q!=q.to_integral_value(): errors.append(f"NON_INTEGER_METRE:{rid}")
        if r["unit"]!=u or D(r["quantity"])!=q: errors.append(f"SOURCE_TO_PROCESSED_QUANTITY_MISMATCH:{rid}")
        if r["original_unit"]!=str(src.get("unit","m")) or D(r["original_quantity"])!=D(src.get("quantity")): errors.append(f"SOURCE_SNAPSHOT_MISMATCH:{rid}")
        expected[u]=expected.get(u,Decimal(0))+q
    actual={}
    for g in groups: actual[g["unit"]]=actual.get(g["unit"],Decimal(0))+D(g["quantity"])
    if expected!=actual: errors.append("AGGREGATION_CONSERVATION_FAILED")
    for n,line in enumerate(tsv.splitlines(),1):
        if len(line.split("\t"))!=5: errors.append(f"TSV5_COLUMN_COUNT:{n}")
    return {"status":"HELD" if errors else "RELEASED","errors":errors,"source_rows":len(raw_rows),"processed_rows":len(processed_rows),"groups":len(groups),"source_to_processed_totals":{k:fmt(v) for k,v in expected.items()},"aggregated_totals":{k:fmt(v) for k,v in actual.items()},"engine_version":VERSION}

def run_pipeline(payload):
    raw=[dict(r) for r in payload.get("rows",[])]
    for i,r in enumerate(raw):
        if not r.get("row_id"):
            seed=str(r.get("model",r.get("model_text","")))+"|"+str(r.get("quantity"))+"|"+str(i)
            r["row_id"]="SRC-"+hashlib.sha256(seed.encode()).hexdigest()[:12]
    profiles=payload.get("conductor_profiles",{}); processed=[process_row(r,profiles) for r in raw]
    groups=aggregate_rows(processed,payload.get("sort_mode","model")); tsv=render_tsv5(groups)
    gate=release_gate(raw,processed,groups,tsv)
    return {"engine_version":VERSION,"batch_id":payload.get("batch_id"),"source_rows":processed,"aggregated_rows":groups,"tsv5":tsv,"release_gate":gate}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--output"); ap.add_argument("--audit"); a=ap.parse_args()
    payload=json.loads(Path(a.input).read_text(encoding="utf-8")); result=run_pipeline(payload)
    if a.output: Path(a.output).write_text(result["tsv5"]+"\n",encoding="utf-8")
    else: print(result["tsv5"])
    if a.audit: Path(a.audit).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"[V30.1] {result['release_gate']['status']} {result['release_gate']['errors']}",file=sys.stderr)
    return 0 if result["release_gate"]["status"]=="RELEASED" else 2
if __name__=="__main__": raise SystemExit(main())
