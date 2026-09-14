#!/usr/bin/env python3
"""Report progress against locked pre-freeze multilingual search floors.

This is a construction-time audit: structural errors fail CI, but being below the
final 500-query/language floors does not fail until the freeze gate is activated.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

TOTAL_TARGET = 500
LANGUAGE_TARGETS = {
    "te": 60,
    "ta": 60,
    "ml": 50,
    "kn": 50,
    "bn": 40,
    "gu": 20,
    "pa": 20,
}
DEVANAGARI_TARGET = 80


def main() -> int:
    seen: set[str] = set()
    languages: Counter[str] = Counter()
    scripts: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    total = 0

    try:
        manifests = sorted(ROOT.glob("queries-*.jsonl"))
        if not manifests:
            raise ValueError("no queries-*.jsonl manifests found")
        for path in manifests:
            for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                raw = raw.strip()
                if not raw or raw.startswith("#"):
                    continue
                item = json.loads(raw)
                qid = item["query_id"]
                if qid in seen:
                    raise ValueError(f"duplicate query_id {qid} at {path.name}:{line_no}")
                seen.add(qid)
                total += 1
                if item.get("language_code"):
                    languages[item["language_code"]] += 1
                if item.get("script_code"):
                    scripts[item["script_code"]] += 1
                classes[item["query_class"]] += 1
    except Exception as exc:
        print(f"FAIL_SEARCH_FLOOR_AUDIT: {exc}", file=sys.stderr)
        return 1

    print("PASS_SEARCH_FLOOR_AUDIT")
    print(f"total={total}/{TOTAL_TARGET}, remaining={max(TOTAL_TARGET-total,0)}")
    print("language_floor_progress:")
    for code, target in LANGUAGE_TARGETS.items():
        count = languages[code]
        print(f"- {code}: {count}/{target}, remaining={max(target-count,0)}")
    deva = scripts["Deva"]
    print(f"- Devanagari script combined: {deva}/{DEVANAGARI_TARGET}, remaining={max(DEVANAGARI_TARGET-deva,0)}")
    print("query_classes=" + json.dumps(dict(sorted(classes.items())), ensure_ascii=False))
    print("scripts=" + json.dumps(dict(sorted(scripts.items())), ensure_ascii=False))
    print("languages=" + json.dumps(dict(sorted(languages.items())), ensure_ascii=False))
    print("NOTE: mixed/global/Latin collision-fuzzy breadth remains a semantic audit, not inferred from language_code alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
