#!/usr/bin/env python3
"""Run a guarded 17-film D1 recovery rehearsal in ONE disposable REMOTE QA database.

Not a production migration. Requires an explicit GitHub run ID; creates a
uniquely named staging D1, checks its UUID against production, uses a temporary
Wrangler config that binds ONLY that staging UUID, and deletes only that exact
newly created database in a finally block. No live catalogue queries/writes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from foundation_filebacked_rollback import validated_rows, load_d1_rows_from_response

PRODUCTION = "cinema-and-series"
PREFIX = "foundation-v2-qa-"
SOURCE = "Wikidata P364 (REMOTE_QA_ONLY)"
QID = re.compile(r"Q[1-9][0-9]*\Z")
UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z")
FIELDS = ("id", "wikidata_qid", "title", "release_year", "country_code", "language_name")
EXPECTED_HELD = {"Q20967570", "Q109519684", "Q20649744"}


def require(condition: bool, message: str):
    if not condition:
        raise ValueError(message)


def stage_name(run_id: str, attempt: str) -> str:
    require(re.fullmatch(r"[1-9][0-9]{5,14}", run_id) is not None, "Invalid GitHub run ID")
    require(re.fullmatch(r"[1-9][0-9]{0,3}", attempt) is not None, "Invalid GitHub run attempt")
    return f"{PREFIX}{run_id}-{attempt}"


def sql_literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    require(isinstance(value, str) and len(value) <= 1000, "Invalid SQL fixture literal")
    return "'" + value.replace("'", "''") + "'"


def state_from_inputs(packet: dict, review: dict, raw: list[dict]) -> dict:
    eligible, held = validated_rows(packet, review, raw)
    current = load_d1_rows_from_response(raw)
    require(len(current) == 20 and len(eligible) == 17 and len(held) == 3, "Frozen review drift")
    require({x["before"]["wikidata_qid"] for x in held} == EXPECTED_HELD, "Held identity drift")
    require(all(QID.fullmatch(r["wikidata_qid"]) for r in current), "Invalid saved ID")
    return {"eligible": eligible, "held": held, "original": current}


def guarded_sql(rows: list[dict], *, reverse: bool = False) -> str:
    statements = []
    ordered = list(reversed(rows)) if reverse else list(rows)
    for item in ordered:
        before = item["before"]
        require(before["language_name"] == "Unknown" and before["country_code"] == "IN", "Unexpected before")
        core = " AND ".join(f"{k}={sql_literal(before[k])}" for k in FIELDS[:5])
        url = "https://www.wikidata.org/wiki/" + before["wikidata_qid"]
        if reverse:
            condition = (f"{core} AND language_name={sql_literal(item['after'])} "
                         f"AND language_source={sql_literal(SOURCE)} "
                         f"AND language_source_url={sql_literal(url)}")
            new = (f"language_name={sql_literal(before['language_name'])},"
                   "language_source=NULL,language_source_url=NULL")
        else:
            condition = (f"{core} AND language_name IS {sql_literal(before['language_name'])} "
                         "AND language_source IS NULL AND language_source_url IS NULL")
            new = (f"language_name={sql_literal(item['after'])},"
                   f"language_source={sql_literal(SOURCE)},"
                   f"language_source_url={sql_literal(url)}")
        statements.extend([
            "INSERT INTO qa_guard(value) SELECT 1 WHERE NOT EXISTS "
            f"(SELECT 1 FROM catalogue_titles WHERE {condition})",
            f"UPDATE catalogue_titles SET {new} WHERE {condition}",
        ])
    return ";\n".join(statements) + ";\n"


def sql_statements(path: Path) -> list[str]:
    txt = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines()
                    if not line.lstrip().startswith("--"))
    commands = [command.strip() for command in txt.split(";") if command.strip()]
    require(bool(commands) and all(re.match(r"^(?:CREATE|ALTER)\s", c, flags=re.I)
                                    for c in commands), "Unexpected trusted migration statement")
    return commands


def seed_sql(original: list[dict]) -> str:
    require(len(original) == 20, "Only 20 saved film rows may be seeded")
    combined = list(original) + [{
        "id": "foundation-unrelated-qa", "wikidata_qid": "Q999999999",
        "title": "Unrelated sentinel", "release_year": 1975,
        "country_code": "IN", "language_name": "Tamil",
    }]
    statements = []
    for row in combined:
        require(QID.fullmatch(row["wikidata_qid"]) is not None, "Unsafe source QID")
        vals = [row[k] for k in FIELDS]
        vals += ["foundation-staging-qa", "https://www.wikidata.org/wiki/" + row["wikidata_qid"]]
        statements.append(
            "INSERT INTO catalogue_titles"
            "(id,wikidata_qid,title,release_year,country_code,language_name,source_category,source_url)"
            " VALUES(" + ",".join(map(sql_literal, vals)) + ")"
        )
    return ";\n".join(statements) + ";\n"


def wrangler(*args: str, check: bool = True) -> str:
    done = subprocess.run(["npx", "wrangler", *args],
                          text=True, capture_output=True, check=False,
                          timeout=170, env=os.environ.copy())
    if done.returncode != 0 and check:
        details = (done.stderr + "\n" + done.stdout)[-1800:]
        token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
        if token:
            details = details.replace(token, "[redacted]")
        raise RuntimeError(f"Wrangler {args[0]} operation failed ({done.returncode}): {details}")
    return done.stdout if done.returncode == 0 else ""


def all_databases() -> list[dict]:
    result = json.loads(wrangler("d1", "list", "--json"))
    require(isinstance(result, list), "Unexpected D1 list payload")
    return result


def database_identity(item: dict) -> str:
    value = item.get("uuid") or item.get("id")
    require(isinstance(value, str) and UUID.fullmatch(value) is not None, "Invalid D1 UUID")
    return value.lower()


def lookup(rows: list[dict], name: str) -> str | None:
    matches = [x for x in rows if x.get("name") == name]
    require(len(matches) <= 1, "Duplicate D1 database names")
    return database_identity(matches[0]) if matches else None


def stage_config(path: Path, name: str, uuid: str) -> None:
    require(name.startswith(PREFIX) and name != PRODUCTION, "Not a staging DB name")
    require(UUID.fullmatch(uuid) is not None, "Not a valid staging UUID")
    config = {
        "name": "foundation-v2-staging-only",
        "main": "./src/foundation-staging-dummy.js",
        "compatibility_date": "2026-09-16",
        "d1_databases": [{"binding": "DB", "database_name": name, "database_id": uuid}],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def parse_query(payload: str) -> list[dict]:
    decoded = json.loads(payload)
    require(isinstance(decoded, list) and decoded and all(
        isinstance(part, dict) and part.get("success") is True for part in decoded
    ), "Remote staging D1 query did not report success")
    rows = []
    for block in decoded:
        result = block.get("results")
        if isinstance(result, list):
            rows.extend(result)
    return rows


def execute(name: str, config: Path, *, command: str | None = None,
            file: Path | None = None) -> str:
    require(name.startswith(PREFIX) and name != PRODUCTION, "Refusing non-staging D1 execution")
    require((command is None) != (file is None), "Must provide exactly one SQL input")
    args = ["d1", "execute", name, "--remote", "--config", str(config), "--json", "--yes"]
    args += ["--command", command] if command is not None else ["--file", str(file)]
    return wrangler(*args)


def full_rows(name: str, config: Path) -> list[dict]:
    results = parse_query(execute(name, config,
                 command="SELECT * FROM catalogue_titles ORDER BY wikidata_qid;"))
    require(len(results) == 21, "Staging D1 row count is not 21")
    return results


def same(a: list[dict], b: list[dict], label: str):
    require(a == b, "Staging D1 invariant failed: " + label)


def write_stage(name: str, config: Path, root: Path, filename: str, content: str):
    path = root / filename
    path.write_text(content, encoding="utf-8")
    execute(name, config, file=path)


def results_index(rows: list[dict]) -> dict[str, dict]:
    return {r["wikidata_qid"]: r for r in rows}


def run_cases(name: str, config: Path, fixture: dict, root: Path) -> dict:
    for path in (Path("migrations/0017_year_precision_catalogue.sql"),
                 Path("migrations/0027_catalogue_title_language_provenance.sql")):
        for sql in sql_statements(path):
            execute(name, config, command=sql)
    execute(name, config,
            command="CREATE TABLE qa_guard(value INTEGER NOT NULL CHECK(value=0));")
    write_stage(name, config, root, "seed-staging.sql", seed_sql(fixture["original"]))
    baseline = full_rows(name, config)
    original_map = results_index(baseline)
    require(all(all(original_map[r["wikidata_qid"]][k] == r[k] for k in FIELDS)
                for r in fixture["original"]), "Staging seed disagrees with saved production values")
    fwd = guarded_sql(fixture["eligible"])
    rev = guarded_sql(fixture["eligible"], reverse=True)

    write_stage(name, config, root, "forward-qa.sql", fwd)
    after = full_rows(name, config)
    indexed = results_index(after)
    require(all(indexed[x["before"]["wikidata_qid"]]["language_name"] == x["after"]
                and indexed[x["before"]["wikidata_qid"]]["language_source"] == SOURCE
                for x in fixture["eligible"]), "Staging forward did not update all 17")
    require(all(indexed[x["before"]["wikidata_qid"]]["language_name"] == "Unknown"
                for x in fixture["held"]), "A held film was edited")
    require(indexed["Q999999999"]["language_name"] == "Tamil", "Unrelated film changed")
    write_stage(name, config, root, "reverse-qa.sql", rev)
    same(full_rows(name, config), baseline, "17-record forward/inverse did not restore")

    # Force stale record LAST. Test that the whole staging batch rolls back.
    last = fixture["eligible"][-1]["before"]["wikidata_qid"]
    execute(name, config, command=(
        "UPDATE catalogue_titles SET language_name='Concurrent edit' "
        f"WHERE wikidata_qid={sql_literal(last)};"))
    before_stale = full_rows(name, config)
    failed = False
    try:
        write_stage(name, config, root, "stale-qa.sql", fwd)
    except RuntimeError:
        failed = True
    require(failed, "Stale staging D1 forward batch did not fail")
    same(full_rows(name, config), before_stale, "D1 batch left partial forward edits")
    execute(name, config, command=(
        "UPDATE catalogue_titles SET language_name='Unknown' "
        f"WHERE wikidata_qid={sql_literal(last)};"))

    write_stage(name, config, root, "forward-again.sql", fwd)
    first = fixture["eligible"][0]["before"]["wikidata_qid"]
    execute(name, config, command=(
        "UPDATE catalogue_titles SET language_name='Newer third-party edit' "
        f"WHERE wikidata_qid={sql_literal(first)};"))
    before_inverse = full_rows(name, config)
    inverse_failed = False
    try:
        write_stage(name, config, root, "conflicted-inverse.sql", rev)
    except RuntimeError:
        inverse_failed = True
    require(inverse_failed, "Conflicted staging D1 inverse batch did not fail")
    same(full_rows(name, config), before_inverse, "D1 inverse erased a newer edit")

    return {
        "schema": "foundation-v2-disposable-remote-d1-v1",
        "tested_existing_film_rows": 20, "reviewed_language_changes": 17,
        "disputed_films_untouched": 3, "unrelated_record_untouched": True,
        "seed_row_count": 21, "before_sha256": hashlib.sha256(
            json.dumps(baseline, sort_keys=True).encode("utf-8")).hexdigest(),
        "staging_forward_and_inverse": True, "stale_batch_atomic": True,
        "competing_edit_inverse_atomic": True, "production_d1_reads": 0,
        "production_d1_writes": 0, "production_d1_name_never_bound": True,
        "staging_d1_was_created": True, "staging_d1_deleted": False,
        "production_correction_authorized": False,
        "cloudflare_time_travel_restore_tested": False,
        "notes": "Disposable REMOTE staging D1, not a full production clone or production migration.",
    }


def cleanup_exact_stage(state: Path) -> bool:
    if not state.exists():
        return True
    record = json.loads(state.read_text(encoding="utf-8"))
    name, uid, prod_id = record["name"], record["uuid"], record["production_uuid"]
    require(re.fullmatch(r"foundation-v2-qa-[1-9][0-9]{5,14}-[1-9][0-9]{0,3}", name)
            and uid != prod_id and name != PRODUCTION, "Unsafe staging deletion request")
    actual = lookup(all_databases(), name)
    if actual is None:
        return True
    require(actual == uid, "Staging UUID changed; refusing deletion")
    wrangler("d1", "delete", name, "--skip-confirmation")
    require(lookup(all_databases(), name) is None, "Staging deletion not confirmed")
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["run", "cleanup"])
    for key in ("packet", "review", "current", "output", "state", "config", "root"):
        p.add_argument("--" + key, type=Path)
    args = p.parse_args()
    require(args.state is not None, "--state is mandatory")
    if args.mode == "cleanup":
        if cleanup_exact_stage(args.state):
            print("FOUNDATION_STAGING_CLEANUP=verified_absent")
        return
    require(all(getattr(args, k) is not None for k in
                ("packet", "review", "current", "output", "config", "root")),
            "All staging run inputs required")
    require(os.environ.get("CLOUDFLARE_ACCOUNT_ID")
            and os.environ.get("CLOUDFLARE_API_TOKEN"),
            "Missing Cloudflare staging permissions")
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    reviewed = json.loads(args.review.read_text(encoding="utf-8"))
    raw = json.loads(args.current.read_text(encoding="utf-8"))
    fixture = state_from_inputs(packet, reviewed, raw)
    freeze = json.loads(Path("ops/data-foundation-v2-freeze.json").read_text())
    require(freeze["active"] is True, "Data Foundation freeze must remain active")
    name = stage_name(os.environ["GITHUB_RUN_ID"], os.environ.get("GITHUB_RUN_ATTEMPT", "1"))
    args.root.mkdir(parents=True, exist_ok=True)
    rows = all_databases()
    prod_id = lookup(rows, PRODUCTION)
    require(prod_id is not None, "Production identity is unavailable: no staging operations allowed")
    require(lookup(rows, name) is None, "Stage already exists, refusing to assume ownership")
    # Workers Free allows at most ten databases; leave at least one spare slot.
    require(len(rows) <= 8, "D1 account capacity is too tight for a temporary QA database")
    result = None
    problem = None
    stage_id = None
    deleted = False
    try:
        try:
            wrangler("d1", "create", name, "--location=apac", "--update-config=false")
        finally:
            # Capture identity even if create command reported an error *after*
            # the control plane provisioned the scratch DB.
            stage_id = lookup(all_databases(), name)
            if stage_id is not None:
                require(stage_id != prod_id, "Staging UUID equals production UUID")
                args.state.parent.mkdir(parents=True, exist_ok=True)
                args.state.write_text(json.dumps({
                    "name": name, "uuid": stage_id, "production_uuid": prod_id,
                    "github_run_id": os.environ["GITHUB_RUN_ID"],
                }, indent=2) + "\n", encoding="utf-8")
        require(stage_id is not None, "Temporary staging D1 was not created")
        stage_config(args.config, name, stage_id)
        result = run_cases(name, args.config, fixture, args.root)
    except Exception as exc:
        problem = exc
    finally:
        if args.state.exists():
            try:
                deleted = cleanup_exact_stage(args.state)
            except Exception as exc:
                if problem is None:
                    problem = exc
                print("WARNING: exact staging cleanup could not be verified", file=sys.stderr)
        if result is not None:
            result["staging_d1_deleted"] = deleted
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if problem is not None:
        raise problem
    require(deleted, "QA D1 cleanup unverified")
    print("FOUNDATION_REMOTE_STAGING=" + json.dumps({
        "reviewed_film_changes": 17, "held": 3, "forward_inverse": True,
        "stale_batch_atomic": True, "competing_edit_inverse_atomic": True,
        "temporary_database_deleted": deleted, "production_writes": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
