#!/usr/bin/env python3
"""Audit Cinema and Series validation corpus primary-cohort coverage.

Research/QA tooling only. This script verifies every machine-readable validation
case is assigned exactly one valid primary cohort and reports progress against
the locked ~1,000-case quotas. Being below final quotas does not fail CI while
the corpus is still under construction; structural mismatches do.

Primary-cohort assignments are split across incremental CSV files matching
`corpus-primary-cohorts-*.csv`. This keeps the mapping maintainable as the corpus
grows toward ~1,000 cases while preserving duplicate/stale/missing detection
across the complete assignment set.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
CSV_GLOB = "corpus-primary-cohorts-*.csv"

TARGETS = {
    "india_identity_multilingual_localization": 180,
    "global_work_version_relationship": 100,
    "release_territory_certification_availability": 120,
    "series_season_episode_special_structure": 140,
    "people_credits_roles_music_identity": 100,
    "organizations_companies_platforms_rightsholders": 60,
    "historical_archive_preservation": 100,
    "upcoming_unreleased_production_lifecycle": 70,
    "source_conflict_canonicalization_provenance": 60,
    "search_transliteration_disambiguation": 70,
}


def discover_case_ids() -> set[str]:
    ids: set[str] = set()
    duplicates: list[str] = []
    for path in sorted(ROOT.glob("corpus-tranche-*.jsonl")):
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            data = json.loads(raw)
            case_id = data["case_id"]
            if case_id in ids:
                duplicates.append(f"{case_id} ({path.name}:{line_no})")
            ids.add(case_id)
    if duplicates:
        raise ValueError("duplicate case IDs across manifests: " + ", ".join(duplicates))
    return ids


def load_assignments() -> dict[str, str]:
    assignments: dict[str, str] = {}
    sources: dict[str, str] = {}
    duplicates: list[str] = []
    csv_paths = sorted(ROOT.glob(CSV_GLOB))
    if not csv_paths:
        raise ValueError(f"no primary-cohort CSV files found matching {CSV_GLOB}")

    for csv_path in csv_paths:
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            expected = {"case_id", "primary_cohort"}
            if set(reader.fieldnames or []) != expected:
                raise ValueError(f"unexpected CSV columns in {csv_path.name}: {reader.fieldnames}")
            for row_number, row in enumerate(reader, start=2):
                case_id = row["case_id"].strip()
                cohort = row["primary_cohort"].strip()
                location = f"{csv_path.name}:{row_number}"
                if case_id in assignments:
                    duplicates.append(f"{case_id} ({sources[case_id]}, {location})")
                    continue
                assignments[case_id] = cohort
                sources[case_id] = location

    if duplicates:
        raise ValueError("duplicate cohort assignment(s): " + ", ".join(sorted(duplicates)))
    return assignments


def main() -> int:
    try:
        manifest_ids = discover_case_ids()
        assignments = load_assignments()
    except Exception as exc:
        print(f"FAIL_QUOTA_AUDIT: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    missing = sorted(manifest_ids - assignments.keys())
    stale = sorted(assignments.keys() - manifest_ids)
    invalid = sorted((cid, cohort) for cid, cohort in assignments.items() if cohort not in TARGETS)

    if missing:
        errors.append("machine-readable cases missing primary cohort: " + ", ".join(missing))
    if stale:
        errors.append("CSV assignments without machine-readable case: " + ", ".join(stale))
    if invalid:
        errors.append("invalid primary cohorts: " + ", ".join(f"{cid}={cohort}" for cid, cohort in invalid))

    if errors:
        print("FAIL_QUOTA_AUDIT")
        for error in errors:
            print(f"- {error}")
        return 1

    counts = Counter(assignments.values())
    print("PASS_QUOTA_AUDIT")
    print(f"classified_cases={len(assignments)}")
    print(f"assignment_files={len(list(ROOT.glob(CSV_GLOB)))}")
    print("primary_cohort_progress:")
    for cohort, target in TARGETS.items():
        count = counts[cohort]
        remaining = max(target - count, 0)
        pct = count / target * 100
        print(f"- {cohort}: {count}/{target} ({pct:.1f}%), remaining={remaining}")

    print(f"target_total={sum(TARGETS.values())}")
    print(f"current_total={len(assignments)}")
    print(f"remaining_total={max(sum(TARGETS.values()) - len(assignments), 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
