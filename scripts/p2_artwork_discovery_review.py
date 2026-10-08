"""Generate a bounded, review-only artwork discovery artifact from supplied records.

No network access, production writes, or publication are performed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.p2_artwork_discovery import TitleIdentity, discover_candidates


def build_review(identity: TitleIdentity, records: list[dict], *, source_key: str, max_candidates: int) -> dict:
    candidates = discover_candidates(identity, records, source_key=source_key)
    top_score = candidates[0].match_score if candidates else None
    top = [c for c in candidates if c.match_score == top_score] if top_score is not None else []
    status = "NO_MATCH" if not candidates else ("AMBIGUOUS" if len(top) > 1 else "REVIEW")
    return {
        "title_id": identity.title_id,
        "title": identity.title,
        "year": identity.year,
        "language": identity.language,
        "territory": identity.territory,
        "source_key": source_key,
        "status": status,
        "candidate_count": min(len(candidates), max_candidates),
        "candidates": [
            {
                "source_asset_id": c.candidate.source_asset_id,
                "source_page_url": c.candidate.source_page_url,
                "delivery_url": c.candidate.delivery_url,
                "role": c.candidate.role,
                "match_score": c.match_score,
                "match_basis": c.match_basis,
                "language": c.candidate.language,
                "territory": c.candidate.territory,
                "license_identifier": c.candidate.license_identifier,
                "rights_evidence_url": c.candidate.rights_evidence_url,
            }
            for c in candidates[:max_candidates]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--identities", required=True)
    parser.add_argument("--records", required=True)
    parser.add_argument("--source-key", required=True, choices=("wikimedia_commons", "internet_archive"))
    parser.add_argument("--max-candidates", type=int, default=25)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if not 1 <= args.max_candidates <= 100:
        raise SystemExit("--max-candidates must be between 1 and 100")

    identities = json.loads(Path(args.identities).read_text(encoding="utf-8"))
    records = json.loads(Path(args.records).read_text(encoding="utf-8"))
    if not isinstance(identities, list) or not isinstance(records, list):
        raise SystemExit("identities and records must be JSON arrays")

    reviews = []
    for raw_identity in identities[:100]:
        identity = TitleIdentity(
            title_id=str(raw_identity["title_id"]),
            title=str(raw_identity["title"]),
            year=raw_identity.get("year"),
            language=raw_identity.get("language"),
            territory=raw_identity.get("territory", "IN"),
        )
        reviews.append(build_review(identity, records, source_key=args.source_key, max_candidates=args.max_candidates))

    output = {
        "contract": "P2.3_REVIEW_ONLY_V1",
        "read_only": True,
        "publication_performed": False,
        "production_writes_performed": False,
        "source_key": args.source_key,
        "identity_count": len(reviews),
        "reviews": reviews,
    }
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
