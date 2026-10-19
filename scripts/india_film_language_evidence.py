#!/usr/bin/env python3
"""Collect Wikidata film-language claims without reading or writing Cloudflare D1.

Uses the existing conflict-checked Wikidata film-identity staging SQLite file. P364 is
preferred for films, P407 is used only if P364 is absent; conflicting or
multi-language evidence is held for human review, never guessed. Output is an
evidence queue, NOT an update file and NOT verified/official metadata.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

QID = re.compile(r"^Q[1-9][0-9]*$")
API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "CinemaAndSeriesFilmLanguageSource/0.1 (https://github.com/rayadinaveen98-ship-it/cinema-and-series; CC0 film metadata)"
CHUNK_SIZE = 25
MAX_PER_RUN = 500
SCHEMA = "india-film-language-evidence-v1"

# These are display choices, not country-to-language guesses. Nonmatching
# languages are kept as unsupported evidence, never silently coerced.
LANGUAGE_LABELS = {
    "telugu": "Telugu", "tamil": "Tamil", "hindi": "Hindi",
    "malayalam": "Malayalam", "kannada": "Kannada",
    "bengali": "Bengali", "bangla": "Bengali",
    "marathi": "Marathi", "punjabi": "Punjabi",
    "gujarati": "Gujarati", "odia": "Odia", "oriya": "Odia",
    "assamese": "Assamese", "bhojpuri": "Bhojpuri",
    "english": "English", "urdu": "Urdu", "sanskrit": "Sanskrit",
    "nepali": "Nepali", "konkani": "Konkani", "sindhi": "Sindhi",
    "kashmiri": "Kashmiri", "manipuri": "Manipuri",
    "maithili": "Maithili", "dogri": "Dogri",
    "japanese": "Japanese", "french": "French", "arabic": "Arabic",
    "persian": "Persian", "german": "German", "spanish": "Spanish",
}


def load_films(path: Path) -> list[dict]:
    with sqlite3.connect(str(path)) as conn:
        rows = conn.execute(
            "SELECT qid,title,year FROM films "
            "WHERE year_conflict=0 AND title_conflict=0 "
            "ORDER BY year DESC,qid"
        ).fetchall()
    return [{"qid": qid, "title": title, "year": year} for qid, title, year in rows]


def read_state(path: Path) -> dict:
    if not path.is_file():
        return {"schema": SCHEMA, "records": {}}
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("schema") != SCHEMA or not isinstance(state.get("records"), dict):
        raise ValueError("Unsupported language evidence checkpoint")
    return state


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    tmp.replace(path)


def fetch_entities(qids: list[str], props: str) -> dict:
    if not qids or len(qids) > 50 or any(not QID.fullmatch(x) for x in qids):
        raise ValueError("Unsafe Wikidata entity lookup batch")
    params = urllib.parse.urlencode({
        "action": "wbgetentities", "ids": "|".join(qids),
        "props": props, "languages": "en", "format": "json", "maxlag": "5",
    })
    req = urllib.request.Request(
        API + "?" + params,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=35) as response:
        payload = json.loads(response.read(5_000_000).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid Wikidata JSON response")
    if isinstance(payload.get("error"), dict):
        raise ValueError("Wikidata API error: " + str(payload["error"].get("code") or "unknown"))
    if not isinstance(payload.get("entities"), dict):
        raise ValueError("Invalid Wikidata entities response")
    received = payload["entities"]
    if set(qids) - set(received):
        raise ValueError("Wikidata response omitted requested entity IDs")
    return received


def claim_qids(entity: dict, property_id: str) -> set[str]:
    claims = (entity.get("claims") or {}).get(property_id) or []
    values = set()
    for claim in claims:
        if claim.get("rank") == "deprecated":
            continue
        snak = claim.get("mainsnak") or {}
        if snak.get("snaktype") not in (None, "value"):
            continue
        qid = (snak.get("datavalue") or {}).get("value")
        if isinstance(qid, dict) and QID.fullmatch(str(qid.get("id") or "")):
            values.add(qid["id"])
    return values


def evidence_for(film: dict, entity: dict, language_entities: dict) -> dict:
    original = claim_qids(entity, "P364")
    general = claim_qids(entity, "P407")
    property_id = "P364" if original else "P407"
    chosen = original if original else general
    output = {
        "qid": film["qid"], "title": film["title"], "year": film["year"],
        "source_url": "https://www.wikidata.org/wiki/" + film["qid"],
        "property": property_id if chosen else None,
        "language_qids": sorted(original | general),
        "source_only": True, "officially_verified": False,
        "status": "missing_claim", "language": None,
    }
    if not chosen:
        return output
    if len(chosen) > 1 or (original and general and not general.issubset(original)):
        output["status"] = "ambiguous_multilingual_or_conflicting"
        return output
    language_id = next(iter(chosen))
    label = (((language_entities.get(language_id) or {}).get("labels") or {}).get("en") or {}).get("value")
    canonical = LANGUAGE_LABELS.get(str(label or "").strip().casefold())
    if not canonical:
        output["status"] = "unrecognized_language"
        return output
    output["status"] = "single_language_evidence"
    output["language"] = canonical
    return output


def run(stage: Path, checkpoint: Path, max_films: int, out_report: Path,
        out_proposals: Path, fetcher: Callable[[list[str], str], dict] = fetch_entities,
        cooldown: float = 0.5) -> dict:
    if not 1 <= max_films <= MAX_PER_RUN:
        raise ValueError("Source batch outside 1..500 bound")
    films = load_films(stage)
    state = read_state(checkpoint)
    pending = [film for film in films if film["qid"] not in state["records"]][:max_films]
    checked = 0
    halted = None
    for start in range(0, len(pending), CHUNK_SIZE):
        batch = pending[start:start + CHUNK_SIZE]
        ids = [item["qid"] for item in batch]
        try:
            entities = fetcher(ids, "claims")
            if set(ids) - set(entities):
                raise ValueError("Incomplete Wikidata film-claim batch; checkpoint unchanged")
            needed = set()
            for item in batch:
                entity = entities.get(item["qid"]) or {}
                needed.update(claim_qids(entity, "P364"))
                needed.update(claim_qids(entity, "P407"))
            labels = {}
            for index in range(0, len(sorted(needed)), 50):
                subset = sorted(needed)[index:index + 50]
                if subset:
                    labels.update(fetcher(subset, "labels"))
            # Never checkpoint a missing/deleted film entity as a film with
            # genuinely missing language metadata.
            if any(not isinstance(entities[item["qid"]], dict)
                   or entities[item["qid"]].get("missing") is not None
                   for item in batch):
                raise ValueError("Missing Wikidata film identity; checkpoint unchanged")
            for film in batch:
                state["records"][film["qid"]] = evidence_for(
                    film, entities.get(film["qid"]) or {}, labels
                )
            checked += len(batch)
            save_json(checkpoint, state)
            if cooldown:
                time.sleep(cooldown)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                ValueError, OSError) as exc:
            # Never mark a failed API batch as checked. Next run resumes from it.
            halted = ("rate_limited" if isinstance(exc, urllib.error.HTTPError)
                      and exc.code in (429, 503) else "source_error_" + type(exc).__name__)
            break
    records = [state["records"][f["qid"]] for f in films if f["qid"] in state["records"]]
    summary = dict(Counter(row["status"] for row in records))
    proposals = [row for row in records if row["status"] == "single_language_evidence"]
    # A single P407 claim is useful discovery evidence, but not a film's
    # explicitly asserted original language (P364). Keep the counts distinct.
    strict_original = [row for row in proposals if row["property"] == "P364"]
    general_only = [row for row in proposals if row["property"] == "P407"]
    report = {
        "schema": SCHEMA, "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Wikidata CC0 P364/P407 film-language statements",
        "production_d1_access": False, "production_updates": 0,
        "stage_qualified_qids": len(films), "checked_this_run": checked,
        "cumulative_checked_qids": len(records),
        "pending_qids": len(films) - len(records),
        "proposed_single_language": len(proposals),
        "strict_p364_original_language": len(strict_original),
        "general_p407_only_language": len(general_only),
        "status_counts": summary, "halted_reason": halted,
        "note": "Evidence proposals only. No release-date, official, or D1 language claims.",
    }
    save_json(out_report, report)
    save_json(out_proposals, {"schema": SCHEMA, "proposals": proposals})
    print("INDIA_FILM_LANGUAGE_SOURCE=" + json.dumps(report, sort_keys=True), flush=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--max-films", type=int, default=400)
    parser.add_argument("--out-report", type=Path, required=True)
    parser.add_argument("--out-proposals", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.stage, args.checkpoint, args.max_films,
                 args.out_report, args.out_proposals)
    return 0 if result["checked_this_run"] or result["pending_qids"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
