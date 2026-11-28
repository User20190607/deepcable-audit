#!/usr/bin/env python3
"""Extract cable-related user messages as unreviewed candidates.

This tool never promotes assistant output to a gold label. It preserves the
verbatim user message and source identifiers. It intentionally does not infer
expected normalized output.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, re
from pathlib import Path

CABLE_SIGNAL = re.compile(
    r"(?:\\b(?:WDZ[A-Z0-9-]*|ZC-|ZR-|YJV|YJY|YJLHY|BYJ|BVR|BVV|RVV|RVVP|RVSP|RVS|RYJS|KVV|KVVP|VV|BTTRZ|BBTRZ|BTTZ|PV1F)\\b|"
    r"\\d+\\s*[×xX*]\\s*\\d+(?:\\.\\d+)?|\\b\\d+(?:\\.\\d+)?\\s*(?:mm2|mm²|平方))",
    re.IGNORECASE,
)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--conversation-title", default=None)
    args = ap.parse_args()
    raw = args.source.read_bytes()
    source_hash = hashlib.sha256(raw).hexdigest()
    payload = json.loads(raw.decode("utf-8"))
    if isinstance(payload, list) and payload:
        conversation = payload[0]
    else:
        conversation = payload
    messages = conversation.get("chat", {}).get("history", {}).get("messages", {})
    ordered = sorted(messages.values(), key=lambda m: m.get("timestamp", 0))
    rows = []
    for message in ordered:
        if message.get("role") != "user":
            continue
        content = message.get("content") or ""
        if not isinstance(content, str) or len(content.strip()) < 8:
            continue
        if len(content) > 12000 and ("系统提示词" in content or "规则" in content[:300]):
            continue
        if not CABLE_SIGNAL.search(content):
            continue
        ts = message.get("timestamp")
        iso = dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat() if ts else None
        rows.append({
            "candidate_id": f"CAND-{len(rows)+1:04d}",
            "source": {
                "source_file": args.source.name,
                "source_sha256": source_hash,
                "conversation_title": args.conversation_title or conversation.get("title"),
                "conversation_id": conversation.get("id"),
                "message_id": message.get("id"),
                "timestamp_unix": ts,
                "timestamp_utc": iso,
                "role": "user",
                "attachment_count": len(message.get("files") or []),
            },
            "input": {"raw_text": content},
            "adjudication": {
                "status": "UNREVIEWED", "authority": "UNRESOLVED",
                "decision_message_ids": [], "decision_text": "",
                "expected": None, "reason": None, "reviewer": None, "reviewed_at": None,
            },
            "labels": {
                "expected_standardized_rows": None, "expected_status": None,
                "expected_transformations": None, "expected_quantity_by_unit": None,
                "expected_tsv5": None,
            },
            "quality": {
                "split": "unassigned", "risk_tags": ["needs-adjudication"],
                "duplicate_of": None, "notes": ["Lexical extraction only; not a gold label."],
            },
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(x, ensure_ascii=False) + "\\n" for x in rows), encoding="utf-8")
    print(json.dumps({"source_sha256": source_hash, "messages": len(ordered), "candidates": len(rows), "output": str(args.output)}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
