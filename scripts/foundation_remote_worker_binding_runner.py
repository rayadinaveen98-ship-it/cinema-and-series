#!/usr/bin/env python3
"""Manual-only, ephemeral Worker Binding remote D1 canary on synthetic QA rows.

NEVER bind or query the production D1 database. The only Cloudflare D1 name
usable for write SQL starts with foundation-v2-qa-<run ID>-<attempt>, must be
NEWLY CREATED by this run, UUID checked against production, and cleaned up.
The temporary worker is remote-dev preview only; no production deployment.

This runner deliberately submits the actual test POST only ONCE. Ambiguous
network responses cause cleanup, never a retry of changes.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import tempfile
from pathlib import Path
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from foundation_remote_staging_d1 import (
    PREFIX, PRODUCTION, UUID, stage_name, all_databases, lookup,
    cleanup_exact_stage, wrangler, require, execute, sql_literal
)

MIGRATIONS = (
    "migrations/0017_year_precision_catalogue.sql",
    "migrations/0027_catalogue_title_language_provenance.sql",
    "migrations/0018_series_catalogue.sql",
    "migrations/0019_series_language_provenance.sql",
    "migrations/0020_series_first_air_year_provenance.sql",
)
RESULT_SCHEMA = "foundation-v2-worker-binding-scratch-probe-v2"
# These are intentionally allowlisted, non-sensitive diagnostic labels.
# NEVER log exception messages, D1 bindings, SQL, UUIDs, secrets, or configs.
SAFE_PHASES = frozenset((
    "identity_checks", "scratch_create", "schema_initialize",
    "scratch_proof", "preview_start", "preview_ready",
    "probe_seed", "probe_film", "probe_series", "probe_stale",
    "probe_conflict", "probe_finish", "scratch_cleanup", "completed",
))
def stage_log(label: str) -> None:
    require(label in SAFE_PHASES, "Invalid diagnostic stage label")
    print("FOUNDATION_REMOTE_CANARY_STAGE=" + label, flush=True)

def safe_failure_diagnostic(label: str, cleanup_confirmed: bool,
                            error: BaseException) -> dict:
    """Only bounded categorical status, never an exception string."""
    require(label in SAFE_PHASES, "Invalid diagnostic stage label")
    category = ("timeout" if isinstance(error, subprocess.TimeoutExpired)
                else "network_or_io" if isinstance(error, OSError)
                else "validation_or_remote_rejection"
                if isinstance(error, ValueError)
                else "unclassified")
    return {
        "schema": "foundation-v2-remote-worker-canary-safe-diagnostic-v1",
        "outcome": "not_verified",
        "last_stage": label,
        "failure_category": category,
        "exact_scratch_cleanup_confirmed": bool(cleanup_confirmed),
        "remote_worker_binding_passed": False,
        "production_corrections_authorized": False,
        "contains_private_data": False,
    }

ENDPOINT = "http://127.0.0.1:8787/__foundation_staging_probe"


def safe_config(name: str, stage_uuid: str, prod_uuid: str, token: str) -> dict:
    require(re.fullmatch(r"foundation-v2-qa-[1-9][0-9]{5,14}-[1-9][0-9]{0,3}", name)
            is not None and name != PRODUCTION and
            UUID.fullmatch(stage_uuid) and UUID.fullmatch(prod_uuid) and
            stage_uuid.lower() != prod_uuid.lower(),
            "Refusing malformed or production-equivalent stage")
    require(len(token) >= 32, "Ephemeral access token missing")
    return {
        "name": "foundation-v2-ephemeral-probe",
        "main": str(Path("scripts/foundation_staging_worker_probe.mjs").resolve()),
        "compatibility_date": "2026-09-16",
        "compatibility_flags": ["nodejs_compat"],
        "workers_dev": False,
        "d1_databases": [{
            "binding": "DB",
            "database_name": name,
            "database_id": stage_uuid,
        }],
        "vars": {
            "FOUNDATION_ONLY_MODE": "isolated-nonproduction-D1",
            "FOUNDATION_STAGE_NAME": name,
            "FOUNDATION_STAGE_UUID": stage_uuid,
            "FOUNDATION_PRODUCTION_UUID": prod_uuid,
            "FOUNDATION_EPHEMERAL_TOKEN": token,
        },
    }


def parse_migrations(path: Path) -> list[str]:
    import re
    source = "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("--")
    )
    statements = [x.strip() for x in source.split(";") if x.strip()]
    require(bool(statements), "Empty trusted schema fixture")
    require(all(re.match(
        r"^(?:(?:CREATE|ALTER)\s|UPDATE series_titles\s+SET language_source\b)",
        sql, flags=re.IGNORECASE
    ) for sql in statements), "Unexpected D1 migration operation")
    return statements


def assert_remote_scratch_config(stage: str, config: Path) -> None:
    """Mandatory on-disk binding proof before ANY remote scratch SQL."""
    require(re.fullmatch(
        r"foundation-v2-qa-[1-9][0-9]{5,14}-[1-9][0-9]{0,3}",
        stage) is not None, "Remote stage name not an exact scratch identity")
    try:
        cfg = json.loads(config.read_text(encoding="utf-8"))
        binding = cfg["d1_databases"]
        vars_ = cfg["vars"]
        require(isinstance(binding, list) and len(binding) == 1,
                "Exactly one D1 binding is required")
        item = binding[0]
        require(item["binding"] == "DB" and item["database_name"] == stage,
                "Wrong scratch binding name")
        require(UUID.fullmatch(item["database_id"]) is not None
                and UUID.fullmatch(vars_["FOUNDATION_PRODUCTION_UUID"]) is not None
                and item["database_id"].lower() ==
                    vars_["FOUNDATION_STAGE_UUID"].lower()
                and item["database_id"].lower() !=
                    vars_["FOUNDATION_PRODUCTION_UUID"].lower()
                and vars_["FOUNDATION_STAGE_NAME"] == stage
                and vars_["FOUNDATION_ONLY_MODE"] ==
                    "isolated-nonproduction-D1",
                "Remote scratch configuration identity mismatch")
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Remote scratch config missing validated D1 identity") from exc


def seed_schema_only(stage: str, config: Path) -> None:
    """Use ONE bounded remote invocation for the complete trusted schema.

    Earlier sequential invocations caused dozens of Wrangler process startups
    and network round trips. This fixed-script batch contains only allowlisted
    CREATE/ALTER and one trusted series-language provenance UPDATE. No user
    supplied metadata, production records, secrets, or live bindings are used.
    """
    assert_remote_scratch_config(stage, config)
    statements = [
        stmt for migration in MIGRATIONS
        for stmt in parse_migrations(Path(migration))
    ]
    require(statements and len(statements) <= 60,
            "Unexpected full scratch migration statement count")
    source = ";\\n".join(statements) + ";\\n"
    config.parent.mkdir(parents=True, exist_ok=True)
    scratch_sql = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".sql",
                prefix="foundation-only-schema-", dir=config.parent,
                delete=False) as file:
            scratch_sql = Path(file.name)
            file.write(source)
        scratch_sql.chmod(0o600)
        proc = subprocess.run(
            ["npx", "wrangler", "d1", "execute", stage,
             "--remote", "--config", str(config),
             "--yes", "--json", "--file", str(scratch_sql)],
            capture_output=True, text=True, timeout=170,
        )
        require(proc.returncode == 0,
                "Isolated staging full-schema initialization failed")
    finally:
        if scratch_sql is not None:
            scratch_sql.unlink(missing_ok=True)


def bind_scratch_proof(stage: str, config: Path, stage_uuid: str,
                       token: str) -> None:
    """Proof is CREATED on the scratch DB only, never on the live database.

    The Worker refuses ALL mutations unless the bound DB contains this exact
    stage name, its UUID and ephemeral nonce. Environment variables alone
    are not enough to prove the D1 binding is not production.
    """
    require(stage.startswith(PREFIX) and stage != PRODUCTION and
            UUID.fullmatch(stage_uuid) and len(token) >= 32,
            "Refusing unsafe scratch marker")
    assert_remote_scratch_config(stage, config)
    execute(stage, config, command=(
        "CREATE TABLE foundation_v2_stage_proof("
        "id INTEGER PRIMARY KEY CHECK(id=1),"
        "stage_name TEXT NOT NULL,stage_uuid TEXT NOT NULL,"
        "access_nonce TEXT NOT NULL,"
        "stage_phase TEXT NOT NULL DEFAULT 'new');"
    ))
    execute(stage, config, command=(
        "INSERT INTO foundation_v2_stage_proof(id,stage_name,stage_uuid,access_nonce)"
        " VALUES (1," + ",".join(map(sql_literal,(stage,stage_uuid,token))) + ");"
    ))


def once_remote_probe(config: Path, token: str) -> dict:
    command = [
        "npx", "wrangler", "dev", "--remote", "--config", str(config),
        "--ip", "127.0.0.1", "--port", "8787",
    ]
    stage_log("preview_start")
    proc = subprocess.Popen(
        command, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        ready = False
        for _ in range(45):
            require(proc.poll() is None, "Remote preview worker failed to start")
            try:
                # Only health-poll unauthorized GET requests; zero DB writes.
                urllib.request.urlopen(ENDPOINT, timeout=3)
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    ready = True
                    break
            except (urllib.error.URLError, TimeoutError):
                pass
            time.sleep(1)
        require(ready, "Remote preview was not accessible as isolated worker")
        stage_log("preview_ready")
        payload = None
        # Free Workers: 50 D1 read subrequests per invocation. This test
        # deliberately splits the four write/rollback checks into ordered
        # HTTP invocations with stage_phase stored INSIDE scratch D1.
        # Each phase is issued ONCE and is never retried after uncertainty.
        phases = ("seed", "film", "series", "stale", "conflict", "finish")
        for phase in phases:
            stage_log("probe_" + phase)
            req = urllib.request.Request(
                ENDPOINT, data=b"{}", method="POST",
                headers={
                    "Content-Type": "application/json",
                    "x-foundation-ephemeral-token": token,
                    "x-foundation-probe-phase": phase,
                }
            )
            try:
                with urllib.request.urlopen(req, timeout=140) as response:
                    payload = json.loads(response.read(20000))
            except Exception:
                raise ValueError(
                    "Remote scratch D1 phase returned ambiguous/failed response; no retry")
            require(payload.get("schema") == RESULT_SCHEMA and
                    payload.get("phase") == phase and
                    payload.get("phase_passed") is True and
                    payload.get("production_database_writes") == 0 and
                    payload.get("production_corrections_authorized") is False,
                    "Scratch phase verification failed; stop without retry")
        require(payload is not None and payload.get("stage_completed") is True,
                "Remote scratch phase sequence did not finish")
        required = (
            "actual_worker_d1_batch_forward_inverse",
            "original_rows_fully_restored",
            "stale_last_row_atomic_abort",
            "competing_edit_inverse_atomic_abort",
            "unrelated_sentinel_untouched",
        )
        require(all(payload.get(key) is True for key in required) and
                payload.get("production_database_queries") == 0 and
                payload.get("production_database_writes") == 0 and
                payload.get("production_corrections_authorized") is False and
                payload.get("synthetic_scratch_records") == 8,
                "Actual remote Worker D1 guard invariants failed")
        return payload
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    freeze = json.loads(Path("ops/data-foundation-v2-freeze.json").read_text())
    require(freeze.get("active") is True and
            freeze.get("baseline", {}).get("total") == 70175,
            "Frozen 70,175-title catalogue changed")
    require(os.environ.get("CLOUDFLARE_ACCOUNT_ID") and
            os.environ.get("CLOUDFLARE_API_TOKEN"),
            "No remote preview credentials")
    name = stage_name(
        os.environ["GITHUB_RUN_ID"], os.environ.get("GITHUB_RUN_ATTEMPT", "1")
    )
    stage_log("identity_checks")
    existing = all_databases()
    prod_uuid = lookup(existing, PRODUCTION)
    require(prod_uuid is not None, "Production ID unavailable for isolation check")
    require(lookup(existing, name) is None,
            "Scratch stage already exists; refusing to assume ownership")
    require(len(existing) <= 8, "No conservative scratch database capacity")
    require(not any(db.get("name", "").startswith(PREFIX) for db in existing),
            "Existing orphan staging DB must be reviewed separately")

    stage_uuid = None
    problem = None
    outcome = None
    deleted = False
    last_stage = "scratch_create"
    args.config.parent.mkdir(parents=True, exist_ok=True)
    try:
        try:
            stage_log(last_stage)
            wrangler("d1", "create", name, "--location=apac",
                     "--update-config=false")
        finally:
            stage_uuid = lookup(all_databases(), name)
            if stage_uuid is not None:
                require(stage_uuid != prod_uuid,
                        "New scratch database is production database UUID")
                args.state.parent.mkdir(parents=True, exist_ok=True)
                args.state.write_text(json.dumps({
                    "name": name, "uuid": stage_uuid,
                    "production_uuid": prod_uuid,
                    "github_run_id": os.environ["GITHUB_RUN_ID"],
                }, indent=2) + "\n", encoding="utf-8")
        require(stage_uuid, "Scratch D1 could not be safely created")
        token = secrets.token_urlsafe(48)
        config = safe_config(name, stage_uuid, prod_uuid, token)
        args.config.write_text(json.dumps(config, indent=2) + "\n",
                               encoding="utf-8")
        args.config.chmod(0o600)
        last_stage = "schema_initialize"
        stage_log(last_stage)
        seed_schema_only(name, args.config)
        last_stage = "scratch_proof"
        stage_log(last_stage)
        bind_scratch_proof(name, args.config, stage_uuid, token)
        last_stage = "preview_start"
        outcome = once_remote_probe(args.config, token)
        last_stage = "completed"
        stage_log(last_stage)
    except Exception as exc:
        problem = exc
    finally:
        if args.state.exists():
            try:
                deleted = cleanup_exact_stage(args.state)
            except Exception as exc:
                if problem is None:
                    problem = exc
        # Always erase the temporary preview config containing a secret token.
        args.config.unlink(missing_ok=True)

    if problem is not None or not deleted or outcome is None:
        error = problem if problem is not None else ValueError(
            "Unverified scratch cleanup or probe result")
        # The stage is intentionally categorical: no strings from D1/HTTP/
        # Wrangler are serialized into logs or the diagnostic artifact.
        safe_label = last_stage if last_stage in SAFE_PHASES else "identity_checks"
        diagnostic = safe_failure_diagnostic(safe_label, deleted, error)
        diagnostic_path = args.output.with_name("safe-failure-diagnostic.json")
        diagnostic_path.write_text(json.dumps(diagnostic, indent=2) + "\n",
                                   encoding="utf-8")
        print("FOUNDATION_REMOTE_CANARY_FAILURE=" + safe_label, flush=True)
        print("FOUNDATION_REMOTE_CANARY_CLEANUP_CONFIRMED=" +
              str(bool(deleted)).lower(), flush=True)
        raise ValueError("Remote canary failed; inspect safe stage diagnostics")
    # No worker secrets, full rows, staging UUID or production UUID are archived.
    report = {
        **outcome,
        "disposable_remote_staging_d1_deleted": True,
        "production_sql_executed": False,
        "production_corrections_authorized": False,
        "production_database_writes": 0,
        "remote_worker_binding_verified": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n",
                           encoding="utf-8")
    print("FOUNDATION_REMOTE_WORKER_CANARY=passed_scratch_deleted_zero_production_writes")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("FOUNDATION_REMOTE_WORKER_CANARY=failed_closed_review_scratch_cleanup")
        raise SystemExit(1)
