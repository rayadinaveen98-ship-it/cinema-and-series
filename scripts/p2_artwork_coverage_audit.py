#!/usr/bin/env python3
"""Read-only P2 artwork coverage audit over a normalized JSON snapshot.

This utility is intentionally offline: it does not query D1, call external
services, discover artwork, approve rights, or emit production mutation SQL.
It only summarizes evidence already present in the supplied snapshot.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

AUDIT_VERSION = "p2-artwork-coverage-audit-v2"

PUBLIC_PAIRINGS = {
    "OPEN_LICENSE_VERIFIED": "OPEN_LICENSE",
    "PUBLIC_DOMAIN_VERIFIED": "PUBLIC_DOMAIN",
    "PROVIDER_LICENSED": "PROVIDER_CONTRACT",
    "RIGHTS_APPROVED": "RIGHTSHOLDER_PERMISSION",
    "PROMOTIONAL_PERMISSION_VERIFIED": "PROMOTIONAL_PERMISSION",
}

PUBLICATION_STATES = {
    "DISCOVERED",
    "PENDING_REVIEW",
    *PUBLIC_PAIRINGS.keys(),
    "REJECTED",
    "EXPIRED",
    "TAKEDOWN_PENDING",
    "TAKEN_DOWN",
}
RIGHTS_BASES = {
    "OPEN_LICENSE",
    "PUBLIC_DOMAIN",
    "PROVIDER_CONTRACT",
    "RIGHTSHOLDER_PERMISSION",
    "PROMOTIONAL_PERMISSION",
    "PLATFORM_EMBED_AUTHORIZATION",
    "NO_RIGHTS_BASIS",
}
HOSTING_MODES = {
    "SELF_HOSTED",
    "PROVIDER_CDN",
    "EXTERNAL_ALLOWED",
    "REFERENCE_ONLY",
    "EMBED_ONLY",
}
MEDIA_TYPES = {"movie", "series"}
PUBLIC_IMAGE_HOSTING_MODES = {"SELF_HOSTED", "PROVIDER_CDN", "EXTERNAL_ALLOWED"}
IMAGE_ROLES = {"poster", "backdrop"}


def _nonempty(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _https_url(value: Any) -> bool:
    text = _nonempty(value)
    if not text:
        return False
    parsed = urlparse(text)
    return parsed.scheme == "https" and bool(parsed.netloc)


def title_identity(record: dict[str, Any]) -> tuple[str, str, str]:
    media_type = _nonempty(record.get("media_type"))
    source_table = _nonempty(record.get("source_table"))
    source_id = _nonempty(record.get("source_id"))
    if media_type not in MEDIA_TYPES:
        raise ValueError(f"invalid media_type: {media_type!r}")
    if not source_table or not source_id:
        raise ValueError("title identity requires source_table and source_id")
    return media_type, source_table, source_id


def validate_candidate_record(record: dict[str, Any]) -> None:
    source_key = _nonempty(record.get("source_key"))
    role = _nonempty(record.get("presentation_role"))
    state = _nonempty(record.get("publication_state"))
    basis = _nonempty(record.get("rights_basis"))
    hosting_mode = _nonempty(record.get("hosting_mode"))

    if not source_key:
        raise ValueError("candidate requires source_key")
    if role not in IMAGE_ROLES:
        raise ValueError(f"invalid presentation_role: {role!r}")
    if state not in PUBLICATION_STATES:
        raise ValueError(f"invalid publication_state: {state!r}")
    if basis not in RIGHTS_BASES:
        raise ValueError(f"invalid rights_basis: {basis!r}")
    if hosting_mode not in HOSTING_MODES:
        raise ValueError(f"invalid hosting_mode: {hosting_mode!r}")

    source_asset_id = _nonempty(record.get("source_asset_id"))
    source_page_url = _nonempty(record.get("source_page_url"))
    if not source_asset_id and not source_page_url:
        raise ValueError("candidate requires source_asset_id or source_page_url")


def candidate_identity(record: dict[str, Any]) -> tuple[str, ...]:
    source_key = _nonempty(record.get("source_key")) or ""
    source_asset_id = _nonempty(record.get("source_asset_id"))
    source_page_url = _nonempty(record.get("source_page_url")) or ""
    delivery_url = _nonempty(record.get("delivery_url")) or ""
    role = _nonempty(record.get("presentation_role")) or ""
    if source_asset_id:
        return source_key, "asset", source_asset_id, role
    return source_key, "url", source_page_url, delivery_url, role


def publishability_failures(record: dict[str, Any]) -> tuple[str, ...]:
    """Return deterministic audit-only reasons a candidate cannot count as public.

    These checks classify supplied normalized evidence only. They do not approve
    rights or implement the future production selector.
    """
    state = _nonempty(record.get("publication_state"))
    basis = _nonempty(record.get("rights_basis"))
    hosting_mode = _nonempty(record.get("hosting_mode"))
    role = _nonempty(record.get("presentation_role"))
    failures: list[str] = []

    if PUBLIC_PAIRINGS.get(state) != basis:
        failures.append("state_rights_pairing")
    if hosting_mode not in PUBLIC_IMAGE_HOSTING_MODES:
        failures.append("hosting_mode")
    if role not in IMAGE_ROLES:
        failures.append("presentation_role")
    if record.get("ambiguous_link") is True:
        failures.append("ambiguous_link")
    if record.get("link_exact") is not True:
        failures.append("exact_link_unverified")
    if not _nonempty(record.get("rights_verified_at")):
        failures.append("rights_verification_missing")
    if record.get("validity_eligible") is not True or record.get("expired") is True:
        failures.append("validity_unverified")
    if record.get("takedown_clear") is not True or record.get("takedown") is True:
        failures.append("takedown_unverified")
    if record.get("territory_eligible") is not True:
        failures.append("territory_unverified")
    if not _https_url(record.get("delivery_url")):
        failures.append("delivery_url")

    attribution_required = record.get("attribution_required")
    if not isinstance(attribution_required, bool):
        failures.append("attribution_requirement_unknown")
    elif attribution_required and not _nonempty(record.get("attribution_text")):
        failures.append("attribution_missing")

    return tuple(failures)


def is_publishable_image_candidate(record: dict[str, Any]) -> bool:
    return not publishability_failures(record)


def _coverage_bucket() -> dict[str, int]:
    return {
        "titles": 0,
        "with_candidate": 0,
        "with_publishable_poster": 0,
        "with_publishable_backdrop": 0,
        "with_any_publishable_artwork": 0,
        "fallback_only": 0,
    }


def _rate(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) if denominator else 0.0, 6)


def _add_rates(bucket: dict[str, int]) -> dict[str, int | float]:
    total = bucket["titles"]
    return {
        **bucket,
        "candidate_coverage_rate": _rate(bucket["with_candidate"], total),
        "publishable_poster_rate": _rate(bucket["with_publishable_poster"], total),
        "publishable_backdrop_rate": _rate(bucket["with_publishable_backdrop"], total),
        "any_publishable_artwork_rate": _rate(bucket["with_any_publishable_artwork"], total),
        "fallback_only_rate": _rate(bucket["fallback_only"], total),
    }


def build_report(payload: dict[str, Any]) -> dict[str, Any]:
    titles = payload.get("titles")
    candidates = payload.get("candidates")
    if not isinstance(titles, list) or not isinstance(candidates, list):
        raise ValueError("snapshot must contain list fields: titles and candidates")

    title_records: dict[tuple[str, str, str], dict[str, Any]] = {}
    for raw in titles:
        if not isinstance(raw, dict):
            raise ValueError("every title must be an object")
        key = title_identity(raw)
        if key in title_records:
            raise ValueError(f"duplicate title identity: {key}")
        title_records[key] = raw

    candidates_by_title: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    source_counts: Counter[str] = Counter()
    publishable_source_counts: Counter[str] = Counter()
    rights_counts: Counter[str] = Counter()
    candidate_fingerprints: Counter[tuple[str, ...]] = Counter()
    rejection_reasons: Counter[str] = Counter()
    attribution_required = 0
    territory_restricted = 0
    ambiguous_links = 0
    rejected_or_no_rights = 0
    publishable_candidates = 0

    for raw in candidates:
        if not isinstance(raw, dict):
            raise ValueError("every candidate must be an object")
        key = title_identity(raw)
        if key not in title_records:
            raise ValueError(f"candidate references unknown title identity: {key}")
        validate_candidate_record(raw)
        candidates_by_title[key].append(raw)

        source_key = _nonempty(raw.get("source_key")) or "unknown"
        source_counts[source_key] += 1
        candidate_fingerprints[candidate_identity(raw)] += 1

        if raw.get("ambiguous_link") is True:
            ambiguous_links += 1
        state = _nonempty(raw.get("publication_state"))
        basis = _nonempty(raw.get("rights_basis"))
        if state == "REJECTED" or basis == "NO_RIGHTS_BASIS":
            rejected_or_no_rights += 1

        failures = publishability_failures(raw)
        rejection_reasons.update(failures)
        if not failures:
            publishable_candidates += 1
            publishable_source_counts[source_key] += 1
            rights_counts[basis or "unknown"] += 1
            if raw.get("attribution_required") is True:
                attribution_required += 1
            restrictions = raw.get("territory_restrictions")
            if isinstance(restrictions, list) and restrictions:
                territory_restricted += 1

    overall = _coverage_bucket()
    by_media_type: dict[str, dict[str, int]] = defaultdict(_coverage_bucket)
    by_language: dict[str, dict[str, int]] = defaultdict(_coverage_bucket)

    for key, title in title_records.items():
        media_type = key[0]
        language = _nonempty(title.get("language")) or "unknown"
        linked = candidates_by_title.get(key, [])
        publishable = [item for item in linked if is_publishable_image_candidate(item)]
        has_candidate = bool(linked)
        has_poster = any(_nonempty(item.get("presentation_role")) == "poster" for item in publishable)
        has_backdrop = any(_nonempty(item.get("presentation_role")) == "backdrop" for item in publishable)
        has_any = has_poster or has_backdrop

        for bucket in (overall, by_media_type[media_type], by_language[language]):
            bucket["titles"] += 1
            bucket["with_candidate"] += int(has_candidate)
            bucket["with_publishable_poster"] += int(has_poster)
            bucket["with_publishable_backdrop"] += int(has_backdrop)
            bucket["with_any_publishable_artwork"] += int(has_any)
            bucket["fallback_only"] += int(not has_any)

    duplicate_occurrences = sum(count - 1 for count in candidate_fingerprints.values() if count > 1)
    candidate_count = len(candidates)
    largest_source = source_counts.most_common(1)[0] if source_counts else (None, 0)
    largest_publishable_source = (
        publishable_source_counts.most_common(1)[0] if publishable_source_counts else (None, 0)
    )

    return {
        "audit_version": AUDIT_VERSION,
        "read_only": True,
        "input": {
            "titles": len(title_records),
            "candidates": candidate_count,
        },
        "coverage": _add_rates(overall),
        "coverage_by_media_type": {
            key: _add_rates(value) for key, value in sorted(by_media_type.items())
        },
        "coverage_by_language": {
            key: _add_rates(value) for key, value in sorted(by_language.items())
        },
        "candidates": {
            "publishable_image_candidates": publishable_candidates,
            "publishable_candidate_rate": _rate(publishable_candidates, candidate_count),
            "ambiguous_link_candidates": ambiguous_links,
            "ambiguous_link_rate": _rate(ambiguous_links, candidate_count),
            "rejected_or_no_rights_basis_candidates": rejected_or_no_rights,
            "rejected_or_no_rights_basis_rate": _rate(rejected_or_no_rights, candidate_count),
            "duplicate_candidate_occurrences": duplicate_occurrences,
            "duplicate_candidate_rate": _rate(duplicate_occurrences, candidate_count),
            "publishable_assets_requiring_attribution": attribution_required,
            "publishable_assets_with_territory_restrictions": territory_restricted,
        },
        "publishability_rejection_reasons": dict(sorted(rejection_reasons.items())),
        "by_source": {
            source: {
                "candidates": count,
                "publishable": publishable_source_counts.get(source, 0),
            }
            for source, count in sorted(source_counts.items())
        },
        "publishable_by_rights_basis": dict(sorted(rights_counts.items())),
        "provider_concentration": {
            "largest_candidate_source": largest_source[0],
            "largest_candidate_source_count": largest_source[1],
            "largest_candidate_source_share": _rate(largest_source[1], candidate_count),
            "largest_publishable_source": largest_publishable_source[0],
            "largest_publishable_source_count": largest_publishable_source[1],
            "largest_publishable_source_share": _rate(
                largest_publishable_source[1], publishable_candidates
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="normalized JSON snapshot")
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    report = build_report(payload)
    rendered = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
