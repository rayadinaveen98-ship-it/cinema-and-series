#!/usr/bin/env python3
"""Conservatively revisit unresolved Indian film language evidence, source-only.

Never use this queue to write production D1, overwrite existing verified P364,
or treat a P407-only claim as original film language. Successful evidence
upgrades are checkpointed on the isolated source-automation branch.
"""
from __future__ import annotations

import argparse
import json
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from india_film_language_evidence import (
    CHUNK_SIZE, WikidataRateLimited, claim_qids, evidence_for, fetch_entities,
    load_films, read_state, save_json,
)

MAX_RECHECK = 25
ELIGIBLE = {
    "missing_claim", "unrecognized_language",
    "ambiguous_multilingual_or_conflicting", "single_language_evidence",
}


def clean_title(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def candidates(films: list[dict], state: dict) -> list[dict]:
    """Never automatically recheck mismatched, invalid, or P364-accepted rows."""
    by_qid = {film["qid"]: film for film in films}
    eligible = []
    for qid, old in state["records"].items():
        film = by_qid.get(qid)
        if not film or not isinstance(old, dict) or old.get("qid") != qid:
            continue
        if old.get("year") != film["year"] or clean_title(old.get("title")) != clean_title(film["title"]):
            continue
        if old.get("source_only") is not True or old.get("officially_verified") is not False:
            continue
        status = old.get("status")
        if status not in ELIGIBLE:
            continue
        if status == "single_language_evidence" and old.get("property") != "P407":
            # P364-accepted rows and unexpected statuses cannot be downgraded.
            continue
        eligible.append(film)
    return sorted(eligible, key=lambda item: item["qid"])


def select_round_robin(items: list[dict], cursor: str, limit: int) -> list[dict]:
    """Use a stable QID cursor so unresolved first-page films cannot starve later ones."""
    if not items or limit == 0:
        return []
    idx = next((i for i, item in enumerate(items) if item["qid"] > cursor), 0)
    rotated = items[idx:] + items[:idx]
    return rotated[:limit]


def run(stage: Path, checkpoint: Path, out_report: Path, max_films: int = MAX_RECHECK,
        fetcher: Callable[[list[str], str], dict] = fetch_entities) -> dict:
    if not 1 <= max_films <= MAX_RECHECK:
        raise ValueError("Recheck must remain bounded to 1..25 source films")
    films = load_films(stage)
    state = read_state(checkpoint)
    eligible = candidates(films, state)
    cursor = state.get("recheck_cursor_qid", "")
    if not isinstance(cursor, str):
        raise ValueError("Malformed review cursor")
    selected = select_round_robin(eligible, cursor, max_films)
    attempted = 0
    promoted = []
    deferred = 0
    halted = None
    for start in range(0, len(selected), CHUNK_SIZE):
        batch = selected[start:start + CHUNK_SIZE]
        try:
            entities = fetcher([f["qid"] for f in batch], "claims")
            if not isinstance(entities, dict):
                raise ValueError("Invalid Wikidata claims response")
            good = {}
            language_ids = set()
            for film in batch:
                qid = film["qid"]
                entity = entities.get(qid)
                if (not isinstance(entity, dict) or entity.get("missing") is not None
                        or (entity.get("id") and entity["id"] != qid)):
                    deferred += 1
                    continue
                good[qid] = entity
                language_ids |= claim_qids(entity, "P364") | claim_qids(entity, "P407")
            labels = {}
            for index in range(0, len(sorted(language_ids)), 50):
                ids = sorted(language_ids)[index:index + 50]
                response = fetcher(ids, "labels")
                if not isinstance(response, dict):
                    raise ValueError("Invalid language label response")
                labels.update(response)

            # Only improve to a new single, explicit original-film P364 claim.
            # Missing source entities and labels never become 'missing_claim'.
            replacements = {}
            for film in batch:
                qid = film["qid"]
                entity = good.get(qid)
                if entity is None:
                    continue
                required = claim_qids(entity, "P364") | claim_qids(entity, "P407")
                if required - labels.keys():
                    deferred += 1
                    continue
                newer = evidence_for(film, entity, labels)
                if (newer["status"] == "single_language_evidence"
                        and newer["property"] == "P364"
                        and isinstance(newer["language"], str)
                        and newer["language"].strip()):
                    before = state["records"][qid]
                    newer["recheck_previous"] = {
                        "status": before.get("status"),
                        "property": before.get("property"),
                        "language_qids": before.get("language_qids", []),
                    }
                    newer["rechecked_at"] = datetime.now(timezone.utc).isoformat()
                    replacements[qid] = newer

            state["records"].update(replacements)
            promoted.extend({"qid": qid, "language": value["language"]}
                            for qid, value in sorted(replacements.items()))
            # A cursor advances only after an entire batch is safely fetched.
            state["recheck_cursor_qid"] = batch[-1]["qid"]
            attempted += len(batch)
            save_json(checkpoint, state)
        except (WikidataRateLimited, urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, ValueError, OSError) as exc:
            limited = isinstance(exc, WikidataRateLimited) or (
                isinstance(exc, urllib.error.HTTPError) and exc.code in (429, 503))
            halted = "rate_limited" if limited else "source_error_" + type(exc).__name__
            print("INDIA_LANGUAGE_RECHECK_DEFERRED=" + json.dumps({
                "reason": halted, "detail": str(exc)[:140]
            }, sort_keys=True), flush=True)
            break
    report = {
        "schema": "india-language-source-recheck-v1",
        "source_only": True, "d1_reads": 0, "d1_writes": 0,
        "production_updates": 0, "official_verifications": 0,
        "source_eligible_before": len(eligible), "selected": len(selected),
        "attempted": attempted, "promoted_to_p364": len(promoted),
        "promotions": promoted,
        "deferred_entities": deferred,
        "still_unresolved": len(candidates(films, state)),
        "cursor_qid": state.get("recheck_cursor_qid", ""),
        "halted_reason": halted,
        "note": "Source-only P364 claim improvements; no production film or release-date changes.",
    }
    save_json(out_report, report)
    print("INDIA_LANGUAGE_SOURCE_RECHECK=" + json.dumps(report, sort_keys=True), flush=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out-report", type=Path, required=True)
    parser.add_argument("--max-films", type=int, default=MAX_RECHECK)
    args = parser.parse_args()
    report = run(args.stage, args.checkpoint, args.out_report, args.max_films)
    return 0 if (report["halted_reason"] in (None, "rate_limited")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
