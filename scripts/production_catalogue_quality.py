#!/usr/bin/env python3
"""Read-only production catalogue quality audit.

Consumes JSON output from `wrangler d1 execute --json` for the movie,
year-precision catalogue, and series projections. Produces machine-readable and
Markdown reports without mutating production data.

Coverage dimensions stay separate instead of being collapsed into a misleading
single score. Only structurally critical S0 findings are eligible to fail CI.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

QID_RE = re.compile(r"^Q\d+$", re.IGNORECASE)
UNKNOWN = {"", "unknown", "xx", "und", "n/a", "na", "none", "null"}
INDIA_PRIORITY_LANGUAGES = (
    "Telugu",
    "Tamil",
    "Malayalam",
    "Kannada",
    "Hindi",
    "Bengali",
    "Marathi",
    "Gujarati",
    "Punjabi",
)


def norm(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def known(value: object) -> bool:
    return norm(value) not in UNKNOWN


def valid_qid(value: object) -> bool:
    return bool(QID_RE.fullmatch(str(value or "").strip()))


def year_from_date(value: object) -> int | None:
    text = str(value or "").strip()
    if len(text) < 4 or not text[:4].isdigit():
        return None
    year = int(text[:4])
    return year if 1888 <= year <= 2200 else None


def load_d1_rows(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        rows: list[dict[str, Any]] = []
        for batch in payload:
            if isinstance(batch, dict) and isinstance(batch.get("results"), list):
                rows.extend(row for row in batch["results"] if isinstance(row, dict))
        return rows
    if isinstance(payload, dict):
        for key in ("results", "rows"):
            if isinstance(payload.get(key), list):
                return [row for row in payload[key] if isinstance(row, dict)]
    raise ValueError(f"{path}: unsupported D1 JSON shape")


def coverage(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "percent": round(100 * numerator / denominator, 2) if denominator else None,
    }


def finding(
    rule_id: str,
    severity: str,
    media_type: str,
    row: Mapping[str, Any] | None = None,
    **context: Any,
) -> dict[str, Any]:
    row = row or {}
    return {
        "rule_id": rule_id,
        "severity": severity,
        "media_type": media_type,
        "entity_id": str(row.get("id") or ""),
        "title": str(row.get("title") or ""),
        "context": context,
    }


def movie_projection(
    movies: list[dict[str, Any]], catalogue: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int]:
    exact_qids = {
        str(row.get("wikidata_qid") or "").upper()
        for row in movies
        if valid_qid(row.get("wikidata_qid"))
        and norm(row.get("title")) != norm(row.get("wikidata_qid"))
    }
    projected = [
        {**row, "_projection": "movie"}
        for row in movies
        if norm(row.get("title"))
        and norm(row.get("title")) != norm(row.get("wikidata_qid"))
    ]
    overlap = 0
    for row in catalogue:
        qid = str(row.get("wikidata_qid") or "").upper()
        if qid and qid in exact_qids:
            overlap += 1
            continue
        if norm(row.get("title")):
            projected.append({**row, "_projection": "catalogue"})
    return projected, overlap


def add_common_findings(
    findings: list[dict[str, Any]],
    rows: Iterable[dict[str, Any]],
    media_type: str,
    year_field: str | None,
) -> None:
    for row in rows:
        title = row.get("title")
        qid = row.get("wikidata_qid")
        if not norm(title):
            findings.append(finding("IDENTITY.BLANK_TITLE", "S0", media_type, row))
        elif qid and norm(title) == norm(qid):
            findings.append(
                finding("IDENTITY.QID_ONLY_TITLE", "S1", media_type, row, wikidata_qid=qid)
            )
        if not known(row.get("language_name")):
            findings.append(finding("METADATA.LANGUAGE_UNKNOWN", "S2", media_type, row))
        if not known(row.get("country_code")):
            findings.append(finding("METADATA.COUNTRY_UNKNOWN", "S2", media_type, row))
        if year_field and row.get(year_field) in (None, ""):
            findings.append(finding("METADATA.YEAR_UNKNOWN", "S2", media_type, row))


def duplicate_candidates(
    rows: Iterable[dict[str, Any]], media_type: str, year_getter
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        title = norm(row.get("title"))
        year = year_getter(row)
        if title and isinstance(year, int):
            groups[(title, year)].append(row)
    out: list[dict[str, Any]] = []
    for (_, year), group in groups.items():
        qids = sorted(
            {
                str(row.get("wikidata_qid")).upper()
                for row in group
                if valid_qid(row.get("wikidata_qid"))
            }
        )
        if len(group) > 1 and len(qids) > 1:
            out.append(
                finding(
                    "IDENTITY.POSSIBLE_DUPLICATE_TITLE_YEAR",
                    "S2",
                    media_type,
                    group[0],
                    year=year,
                    entity_count=len(group),
                    wikidata_qids=qids[:12],
                )
            )
    return out


def analyze_catalogue(
    movies: list[dict[str, Any]],
    catalogue: list[dict[str, Any]],
    series: list[dict[str, Any]],
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    films, overlap = movie_projection(movies, catalogue)
    shows = [row for row in series if norm(row.get("title"))]

    add_common_findings(findings, catalogue, "catalogue_movie", "release_year")
    add_common_findings(findings, shows, "series", "first_air_year")

    for row in movies:
        title = row.get("title")
        qid = row.get("wikidata_qid")
        if not norm(title):
            findings.append(finding("IDENTITY.BLANK_TITLE", "S0", "movie", row))
        elif qid and norm(title) == norm(qid):
            findings.append(
                finding("IDENTITY.QID_ONLY_TITLE", "S1", "movie", row, wikidata_qid=qid)
            )
        if not known(row.get("language_name")):
            findings.append(finding("METADATA.LANGUAGE_UNKNOWN", "S2", "movie", row))
        if not known(row.get("country_code")):
            findings.append(finding("METADATA.COUNTRY_UNKNOWN", "S2", "movie", row))
        if year_from_date(row.get("release_date")) is None:
            findings.append(
                finding(
                    "METADATA.RELEASE_DATE_INVALID",
                    "S1",
                    "movie",
                    row,
                    release_date=row.get("release_date"),
                )
            )

    for row in catalogue:
        if not known(row.get("source_url")):
            findings.append(finding("PROVENANCE.SOURCE_LOCATOR_MISSING", "S1", "catalogue_movie", row))

    for row in shows:
        if not known(row.get("source_url")):
            findings.append(finding("PROVENANCE.SOURCE_LOCATOR_MISSING", "S1", "series", row))
        first_year = row.get("first_air_year")
        last_year = row.get("last_air_year")
        if isinstance(first_year, int) and isinstance(last_year, int) and last_year < first_year:
            findings.append(
                finding(
                    "SERIES.IMPOSSIBLE_AIR_YEAR_ORDER",
                    "S0",
                    "series",
                    row,
                    first_air_year=first_year,
                    last_air_year=last_year,
                )
            )
        if norm(row.get("series_kind")) == "unknown":
            findings.append(finding("SERIES.KIND_UNKNOWN", "S2", "series", row))
        if norm(row.get("lifecycle_status")) == "unknown":
            findings.append(finding("SERIES.LIFECYCLE_UNKNOWN", "S3", "series", row))

    film_by_qid = {
        str(row.get("wikidata_qid")).upper(): row
        for row in films
        if valid_qid(row.get("wikidata_qid"))
    }
    show_by_qid = {
        str(row.get("wikidata_qid")).upper(): row
        for row in shows
        if valid_qid(row.get("wikidata_qid"))
    }
    for qid in sorted(set(film_by_qid) & set(show_by_qid)):
        movie = film_by_qid[qid]
        show = show_by_qid[qid]
        findings.append(
            {
                "rule_id": "IDENTITY.CROSS_TYPE_EXTERNAL_ID_COLLISION",
                "severity": "S0",
                "media_type": "cross_type",
                "entity_id": f"{movie.get('id', '')}|{show.get('id', '')}",
                "title": f"{movie.get('title', '')} / {show.get('title', '')}",
                "context": {"wikidata_qid": qid},
            }
        )

    findings.extend(
        duplicate_candidates(
            films,
            "movie",
            lambda row: year_from_date(row.get("release_date"))
            if row.get("_projection") == "movie"
            else row.get("release_year"),
        )
    )
    findings.extend(duplicate_candidates(shows, "series", lambda row: row.get("first_air_year")))

    film_count = len(films)
    show_count = len(shows)
    film_year_known = lambda row: (
        year_from_date(row.get("release_date")) is not None
        if row.get("_projection") == "movie"
        else isinstance(row.get("release_year"), int)
    )

    movie_coverage = {
        "identity_title": coverage(
            sum(
                1
                for row in films
                if norm(row.get("title")) and norm(row.get("title")) != norm(row.get("wikidata_qid"))
            ),
            film_count,
        ),
        "release_year": coverage(sum(1 for row in films if film_year_known(row)), film_count),
        "language": coverage(sum(1 for row in films if known(row.get("language_name"))), film_count),
        "country": coverage(sum(1 for row in films if known(row.get("country_code"))), film_count),
        "external_wikidata_id": coverage(sum(1 for row in films if valid_qid(row.get("wikidata_qid"))), film_count),
        "native_title": coverage(sum(1 for row in films if known(row.get("native_title"))), film_count),
        "provenance_locator": coverage(
            sum(
                1
                for row in films
                if known(row.get("release_date_source"))
                if row.get("_projection") == "movie"
                else known(row.get("source_url"))
            ),
            film_count,
        ),
        "poster_exact_movies": coverage(sum(1 for row in movies if known(row.get("poster_url"))), len(movies)),
    }
    series_coverage = {
        "identity_title": coverage(
            sum(
                1
                for row in shows
                if norm(row.get("title")) and norm(row.get("title")) != norm(row.get("wikidata_qid"))
            ),
            show_count,
        ),
        "first_air_year": coverage(sum(1 for row in shows if isinstance(row.get("first_air_year"), int)), show_count),
        "language": coverage(sum(1 for row in shows if known(row.get("language_name"))), show_count),
        "country": coverage(sum(1 for row in shows if known(row.get("country_code"))), show_count),
        "external_wikidata_id": coverage(sum(1 for row in shows if valid_qid(row.get("wikidata_qid"))), show_count),
        "native_title": coverage(sum(1 for row in shows if known(row.get("native_title"))), show_count),
        "provenance_locator": coverage(sum(1 for row in shows if known(row.get("source_url"))), show_count),
        "series_kind": coverage(
            sum(1 for row in shows if known(row.get("series_kind")) and norm(row.get("series_kind")) != "unknown"),
            show_count,
        ),
        "lifecycle_status": coverage(
            sum(
                1
                for row in shows
                if known(row.get("lifecycle_status")) and norm(row.get("lifecycle_status")) != "unknown"
            ),
            show_count,
        ),
    }

    priority = {language: {"movies": 0, "series": 0, "total": 0} for language in INDIA_PRIORITY_LANGUAGES}
    lookup = {norm(language): language for language in INDIA_PRIORITY_LANGUAGES}
    for row in films:
        language = lookup.get(norm(row.get("language_name")))
        if language:
            priority[language]["movies"] += 1
    for row in shows:
        language = lookup.get(norm(row.get("language_name")))
        if language:
            priority[language]["series"] += 1
    for values in priority.values():
        values["total"] = values["movies"] + values["series"]

    severity_counts = Counter(row["severity"] for row in findings)
    rule_counts = Counter(row["rule_id"] for row in findings)
    return {
        "schema_version": "catalogue-quality-v1",
        "counts": {
            "raw_movies": len(movies),
            "raw_catalogue_movies": len(catalogue),
            "catalogue_movie_overlap_removed": overlap,
            "projected_movies": film_count,
            "projected_series": show_count,
            "projected_total": film_count + show_count,
        },
        "coverage": {"movies": movie_coverage, "series": series_coverage},
        "india_priority_languages": priority,
        "verification_status": {
            "movies": dict(Counter(str(row.get("verification_status") or "unknown") for row in movies)),
            "catalogue_movies": dict(Counter(str(row.get("verification_status") or "unknown") for row in catalogue)),
            "series": dict(Counter(str(row.get("verification_status") or "unknown") for row in shows)),
        },
        "finding_summary": {
            "total": len(findings),
            "by_severity": {key: severity_counts.get(key, 0) for key in ("S0", "S1", "S2", "S3")},
            "by_rule": dict(sorted(rule_counts.items())),
        },
        "findings": findings,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    counts = report["counts"]
    summary = report["finding_summary"]
    lines = [
        "# Production Catalogue Quality V1",
        "",
        "This report is read-only. Coverage dimensions remain separate; there is no composite quality score.",
        "",
        "## Catalogue",
        "",
        f"- Projected movies: **{counts['projected_movies']:,}**",
        f"- Projected series: **{counts['projected_series']:,}**",
        f"- Combined projected titles: **{counts['projected_total']:,}**",
        f"- Year-catalogue rows suppressed by exact-movie Wikidata identity: **{counts['catalogue_movie_overlap_removed']:,}**",
        "",
        "## Findings",
        "",
        f"- S0 Critical: **{summary['by_severity']['S0']:,}**",
        f"- S1 High: **{summary['by_severity']['S1']:,}**",
        f"- S2 Medium: **{summary['by_severity']['S2']:,}**",
        f"- S3 Low: **{summary['by_severity']['S3']:,}**",
        "",
        "## Coverage dimensions",
        "",
        "| Dimension | Movies | Series |",
        "| --- | ---: | ---: |",
    ]

    def fmt(metric: Mapping[str, Any] | None) -> str:
        if not metric or metric.get("percent") is None:
            return "n/a"
        return f"{metric['percent']:.2f}% ({metric['numerator']:,}/{metric['denominator']:,})"

    dimensions = sorted(set(report["coverage"]["movies"]) | set(report["coverage"]["series"]))
    for dimension in dimensions:
        lines.append(
            f"| {dimension.replace('_', ' ')} | "
            f"{fmt(report['coverage']['movies'].get(dimension))} | "
            f"{fmt(report['coverage']['series'].get(dimension))} |"
        )

    lines.extend(
        [
            "",
            "## India priority-language catalogue counts",
            "",
            "| Language | Movies | Series | Total |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for language, values in report["india_priority_languages"].items():
        lines.append(
            f"| {language} | {values['movies']:,} | {values['series']:,} | {values['total']:,} |"
        )

    lines.extend(["", "## Findings by rule", "", "| Rule | Count |", "| --- | ---: |"])
    for rule_id, count in report["finding_summary"]["by_rule"].items():
        lines.append(f"| `{rule_id}` | {count:,} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--movies", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--series", required=True)
    parser.add_argument("--out-json", default="data/generated/catalogue-quality-v1.json")
    parser.add_argument("--out-md", default="data/generated/catalogue-quality-v1.md")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args()

    report = analyze_catalogue(
        load_d1_rows(args.movies),
        load_d1_rows(args.catalogue),
        load_d1_rows(args.series),
    )
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")

    severities = report["finding_summary"]["by_severity"]
    print(
        "CATALOGUE_QUALITY_V1="
        + json.dumps(
            {
                "movies": report["counts"]["projected_movies"],
                "series": report["counts"]["projected_series"],
                "total": report["counts"]["projected_total"],
                "s0": severities["S0"],
                "s1": severities["S1"],
                "s2": severities["S2"],
                "s3": severities["S3"],
            },
            sort_keys=True,
        )
    )
    return 2 if args.fail_on_critical and severities["S0"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
