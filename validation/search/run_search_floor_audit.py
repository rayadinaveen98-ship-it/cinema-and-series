#!/usr/bin/env python3
"""Report progress against locked pre-freeze multilingual search floors.

This is a construction-time audit: structural errors fail CI. Numeric floors are
reported continuously and the audit emits an explicit READY/INCOMPLETE freeze
status without making corpus growth commits fail while the benchmark is being
built.
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
MIXED_GLOBAL_LATIN_TARGET = 120

# Section 8 of SEARCH_QUALITY_BENCHMARK_V1 groups mixed/global/Latin,
# collision and fuzzy behavior into one breadth floor. A query qualifies when it
# materially exercises Latin-script discovery OR an explicitly adversarial
# search class/tag. The union is counted once per query_id.
ADVERSARIAL_CLASSES = {
    "minor_typo",
    "same_title_collision",
    "generated_spelling_variant",
    "generated_transliteration",
    "person_alias",
}
ADVERSARIAL_TAGS = {
    "global",
    "same_title_collision",
    "identity_collision",
    "fuzzy",
    "typo",
    "transliteration",
    "romanized",
    "collision",
}


def main() -> int:
    seen: set[str] = set()
    languages: Counter[str] = Counter()
    scripts: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    breadth_reasons: Counter[str] = Counter()
    mixed_global_latin_ids: set[str] = set()
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

                language = item.get("language_code")
                script = item.get("script_code")
                query_class = item["query_class"]
                tags = set(item.get("tags", []))

                if language:
                    languages[language] += 1
                if script:
                    scripts[script] += 1
                classes[query_class] += 1

                qualifies = False
                if script == "Latn":
                    breadth_reasons["latin_script"] += 1
                    qualifies = True
                if query_class in ADVERSARIAL_CLASSES:
                    breadth_reasons[f"class:{query_class}"] += 1
                    qualifies = True
                matched_tags = tags & ADVERSARIAL_TAGS
                if matched_tags:
                    for tag in sorted(matched_tags):
                        breadth_reasons[f"tag:{tag}"] += 1
                    qualifies = True
                if qualifies:
                    mixed_global_latin_ids.add(qid)
    except Exception as exc:
        print(f"FAIL_SEARCH_FLOOR_AUDIT: {exc}", file=sys.stderr)
        return 1

    mixed_global_latin = len(mixed_global_latin_ids)
    language_ready = all(languages[code] >= target for code, target in LANGUAGE_TARGETS.items())
    freeze_floor_ready = (
        total >= TOTAL_TARGET
        and language_ready
        and scripts["Deva"] >= DEVANAGARI_TARGET
        and mixed_global_latin >= MIXED_GLOBAL_LATIN_TARGET
    )

    print("PASS_SEARCH_FLOOR_AUDIT")
    print(f"freeze_floor_status={'READY' if freeze_floor_ready else 'INCOMPLETE'}")
    print(f"total={total}/{TOTAL_TARGET}, remaining={max(TOTAL_TARGET-total,0)}")
    print("language_floor_progress:")
    for code, target in LANGUAGE_TARGETS.items():
        count = languages[code]
        print(f"- {code}: {count}/{target}, remaining={max(target-count,0)}")
    deva = scripts["Deva"]
    print(f"- Devanagari script combined: {deva}/{DEVANAGARI_TARGET}, remaining={max(DEVANAGARI_TARGET-deva,0)}")
    print(
        f"- mixed/global/Latin collision-fuzzy: {mixed_global_latin}/{MIXED_GLOBAL_LATIN_TARGET}, "
        f"remaining={max(MIXED_GLOBAL_LATIN_TARGET-mixed_global_latin,0)}"
    )
    print("mixed_global_latin_reason_counts=" + json.dumps(dict(sorted(breadth_reasons.items())), ensure_ascii=False))
    print("query_classes=" + json.dumps(dict(sorted(classes.items())), ensure_ascii=False))
    print("scripts=" + json.dumps(dict(sorted(scripts.items())), ensure_ascii=False))
    print("languages=" + json.dumps(dict(sorted(languages.items())), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())