#!/usr/bin/env python3
"""Data Foundation V2: immutable 20-film correction proposal, NOT a write.

Uses only saved production D1 snapshot + 6048-review and 80-live-recheck artifacts.
No network, no Cloudflare credentials, no SQL, no live D1 reads, no D1 writes.
The output contains exact before/after/rollback values and preconditions for
a *future owner-reviewed process*. No source-independent language confirmation
is represented or fabricated here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_catalogue_quality import load_d1_rows, movie_projection, norm, known

LANGUAGES = (
    "Hindi", "Tamil", "Malayalam", "Telugu", "Kannada",
    "Bengali", "Odia", "Marathi", "Punjabi", "Gujarati",
)
PER_LANGUAGE = 2
SCHEMA = "data-foundation-v2-20-film-dryrun-v1"
CSV_FIELDS = (
    "wikidata_qid", "source_id", "title", "release_year",
    "country_code", "existing_language", "proposed_language",
    "source_language_qid", "source_language_label", "original_language_source",
    "independent_confirmation", "state", "rollback_to",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def stable_hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def build(review: dict, live: dict, movies: list[dict],
          catalogue: list[dict], series: list[dict]) -> dict:
    require(review.get("schema") == "foundation-v2-language-review-v1"
            and review.get("d1_writes") == 0
            and review.get("publication_performed") is False
            and review.get("automatic_corrections") == 0,
            "Original evidence review is not immutable/source-only")
    require(live.get("schema") == "data-foundation-v2-live-p364-sample-v1"
            and live.get("d1_reads") == 0 and live.get("d1_writes") == 0
            and live.get("automatically_approved") == 0
            and live.get("sql_generated") is False
            and live.get("source_error_batches") == 0
            and live.get("sample_count") == 80
            and live.get("population_proposals") == 6048,
            "Live corroboration audit is incomplete or mutable")

    films, overlap = movie_projection(movies, catalogue)
    require(len(films) == 51872 and len(series) == 18303
            and overlap == 998, "Production snapshot does not match frozen baseline")
    unknown = sum(not known(x.get("language_name")) for x in films)
    unknown += sum(not known(x.get("language_name")) for x in series)
    require(unknown == 50380, "Unknown language coverage drift")

    # Exact-date rows outrank year-only rows if an overlap exists.
    index = {}
    for row in films:
        qid = str(row.get("wikidata_qid") or "")
        if qid:
            require(qid not in index, "Ambiguous duplicate QID in canonical film view")
            index[qid] = row
    proposals = {row["wikidata_qid"]: row for row in review["proposals"]}
    require(len(proposals) == len(review["proposals"]) == 6048,
            "Frozen source proposals unexpectedly changed")

    by_language = defaultdict(list)
    seen_sample_qids = set()
    for sample in live.get("review_queue") or []:
        qid = sample.get("wikidata_qid")
        require(isinstance(qid, str) and qid not in seen_sample_qids,
                "Duplicate or missing sampled QID")
        seen_sample_qids.add(qid)
        if sample.get("decision") != "SOURCE_RECHECK_PASSED_REVIEW_REQUIRED":
            continue
        old = proposals.get(qid)
        require(old is not None and sample.get("source_id") == old.get("source_id")
                and sample.get("proposed_language") == old.get("proposed_language")
                and sample.get("title") == old.get("title")
                and sample.get("year") == old.get("year")
                and sample.get("source_url") == old.get("source_url")
                and sample.get("claim_property") == "P364"
                and sample.get("review_only") is True
                and sample.get("production_written") is False,
                "Rechecked sample is inconsistent with frozen proposal")
        require(str(sample["year"]) in str(sample.get("source_years", "")).split(",")
                and str(sample.get("language_qid") or "").startswith("Q")
                and known(sample.get("source_language")),
                "Live source lacks year or original-language evidence")
        if sample["proposed_language"] in LANGUAGES:
            by_language[sample["proposed_language"]].append(sample)

    chosen = []
    for language in LANGUAGES:
        records = sorted(by_language[language], key=lambda r: (
            int(r["year"]), r["wikidata_qid"]))
        require(len(records) >= 8, "Insufficient 80-film sample for " + language)
        # Choose midpoints from earlier and later half of the eight-item sample.
        chosen.extend([records[2], records[6]])
    require(len(chosen) == 20 and len({r["wikidata_qid"] for r in chosen}) == 20,
            "20-film selection drift")

    items = []
    for sample in chosen:
        qid = sample["wikidata_qid"]
        frozen = index.get(qid)
        require(frozen is not None and frozen["_projection"] == "catalogue",
                "Selected film no longer maps to a unique year-only source identity")
        old = proposals[qid]
        require(str(frozen.get("id")) == old["source_id"]
                and frozen.get("title") == old["title"]
                and frozen.get("release_year") == old["year"]
                and norm(frozen.get("language_name")) == norm(old["current_language"])
                and not known(frozen.get("language_name"))
                and frozen.get("country_code") == "IN",
                "Frozen production before-value disagrees with original review")

        before = {
            "table": "catalogue_titles",
            "id": str(frozen["id"]), "wikidata_qid": qid,
            "title": frozen["title"], "release_year": frozen["release_year"],
            "country_code": frozen["country_code"],
            "language_name": frozen["language_name"],
        }
        proposed = {"language_name": sample["proposed_language"]}
        items.append({
            "before": before,
            "proposed": proposed,
            "rollback": {"restore_language_name": before["language_name"],
                         "only_if_language_equals": proposed["language_name"],
                         "only_if_id_qid_title_year_unchanged": True},
            "evidence": {
                "original_language": "Wikidata P364",
                "language_qid": sample["language_qid"],
                "language_source_label": sample["source_language"],
                "live_source_years": sample["source_years"],
                "source_url": sample["source_url"],
                "original_review_run": 39760123503,
                "live_recheck_run": 39761744390,
            },
            "source_independent_confirmation": "NOT_YET_OBTAINED",
            "current_database_value_revalidated_after_snapshot": False,
            "human_approval": False,
            "status": "HOLD_PENDING_INDEPENDENT_SOURCE_AND_FRESH_PRODUCTION_PRECONDITION",
            "precondition_fingerprint_sha256": stable_hash(before),
        })
    return {
        "schema": SCHEMA,
        "baseline_snapshot": {
            "production_quality_run": 39758915343,
            "frozen_total_titles": 70175,
            "frozen_films": len(films), "frozen_series": len(series),
            "unknown_language_titles": unknown,
        },
        "selection": "two year-stratified current Wikidata-rechecked titles per each of 10 languages",
        "population_proposals": len(proposals),
        "sample_rechecked": len(seen_sample_qids),
        "batch_size": len(items),
        "ready_for_production_write": False,
        "production_writes": 0, "production_reads": 0,
        "new_titles": 0, "sql_generated": False,
        "no_poster_or_ui_changes": True,
        "required_before_any_future_write": [
            "Independently corroborate each original language beyond Wikidata P364",
            "Requery current production row to ensure ID, QID, title, year and Unknown language remain unchanged",
            "Review every before/after value and rollback plan",
            "Take verified restorably backed-up pre-write records",
            "Obtain explicit owner authorization in a separate reviewed PR",
            "Perform guarded small batch and independent after-count validation",
        ],
        "items": items,
        "batch_sha256": stable_hash([x["before"] for x in items]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for item in ("review", "live", "movies", "catalogue", "series",
                 "out", "csv", "markdown"):
        parser.add_argument("--" + item, type=Path, required=True)
    args = parser.parse_args()
    result = build(
        json.loads(args.review.read_text(encoding="utf-8")),
        json.loads(args.live.read_text(encoding="utf-8")),
        load_d1_rows(args.movies),
        load_d1_rows(args.catalogue),
        load_d1_rows(args.series),
    )
    for target in (args.out, args.csv, args.markdown):
        target.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    with args.csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for item in result["items"]:
            before, after, evidence = item["before"], item["proposed"], item["evidence"]
            writer.writerow({
                "wikidata_qid": before["wikidata_qid"],
                "source_id": before["id"], "title": before["title"],
                "release_year": before["release_year"],
                "country_code": before["country_code"],
                "existing_language": before["language_name"],
                "proposed_language": after["language_name"],
                "source_language_qid": evidence["language_qid"],
                "source_language_label": evidence["language_source_label"],
                "original_language_source": evidence["source_url"],
                "independent_confirmation": item["source_independent_confirmation"],
                "state": item["status"],
                "rollback_to": item["rollback"]["restore_language_name"],
            })
    lines = [
        "# Data Foundation V2 — 20-film correction review",
        "",
        "**DRY RUN — NOT APPROVED TO WRITE PRODUCTION.**",
        "",
        f"- Frozen production baseline: **{result['baseline_snapshot']['frozen_total_titles']:,}** titles",
        f"- Source-only proposals: **{result['population_proposals']:,}**",
        f"- Passed Wikidata live sample: **{result['sample_rechecked']}**",
        f"- Prepared before/after/rollback manifests: **{result['batch_size']}**",
        "- Live D1 reads/writes: **0 / 0**",
        "- Independent original-language confirmation: **not yet completed**",
        "",
        "| Language | Films prepared |",
        "|---|---:|",
    ]
    for language in LANGUAGES:
        lines.append(f"| {language} | 2 |")
    lines += [
        "",
        "All rows remain **held** until source-independent corroboration, fresh "
        "production preflight, verified backup/restore, and explicit owner approval.",
        "This output is a review artifact, NOT executable migration SQL.",
    ]
    args.markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("FOUNDATION_DRYRUN_20=" + json.dumps({
        "batch_size": result["batch_size"],
        "sample_rechecked": result["sample_rechecked"],
        "production_reads": result["production_reads"],
        "production_writes": result["production_writes"],
        "ready_for_production_write": result["ready_for_production_write"],
        "sha256": result["batch_sha256"],
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
