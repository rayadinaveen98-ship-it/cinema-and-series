#!/usr/bin/env python3
"""Accelerate already-qualified Indian film language evidence, SOURCE ONLY.

Runs the existing rate-limited, checkpoint-atomic 500-film collector several
times per CI run. Never accesses D1 or publishes a language field. Does not
increase per-request API fanout; respects upstream 429/maxlag deferrals.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import india_film_language_evidence as source

SCHEMA = "india-film-source-accelerator-v1"


def accelerate(stage: Path, checkpoint: Path, report_file: Path,
               proposals_file: Path, accelerator_file: Path,
               *, max_passes: int = 8, per_pass: int = 500,
               rest_between_passes: float = 2.0,
               run_fn=source.run, sleep_fn=time.sleep) -> dict:
    if not 1 <= max_passes <= 8:
        raise ValueError("At most 8 bounded source passes allowed")
    if not 1 <= per_pass <= source.MAX_PER_RUN:
        raise ValueError("Each source pass must remain <=500 QIDs")
    if not 0 <= rest_between_passes <= 60:
        raise ValueError("Invalid inter-pass source cooldown")
    checked = 0
    completed = 0
    halt = None
    last = None
    for i in range(max_passes):
        last = run_fn(
            stage, checkpoint, per_pass, report_file, proposals_file,
            selection="decade-balanced")
        if last.get("schema") != source.SCHEMA or last.get("production_updates") != 0:
            raise ValueError("Source result is not source-only")
        if last.get("production_d1_access") is not False:
            raise ValueError("Source collector must never access D1")
        added = last.get("checked_this_run")
        if not isinstance(added, int) or not 0 <= added <= per_pass:
            raise ValueError("Out-of-range checked identity count")
        checked += added
        completed += 1
        reason = last.get("halted_reason")
        if reason:
            halt = reason
            break
        if last.get("pending_qids") == 0:
            halt = "all_staged_source_qids_checked"
            break
        if added == 0:
            halt = "no_progress_or_incomplete_identity"
            break
        if i < max_passes - 1 and rest_between_passes:
            sleep_fn(rest_between_passes)
    if last is None:
        raise AssertionError("No source evidence pass executed")
    combined = {
        **last,
        "checked_this_run": checked,
        "last_pass_checked": last["checked_this_run"],
        "passes_completed": completed,
        "halted_reason": halt if halt not in ("all_staged_source_qids_checked",) else None,
        "source_selection": "decade-balanced-accelerated",
    }
    source.save_json(report_file, combined)
    audit = {
        "schema": SCHEMA,
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "production_d1_access": False, "d1_reads": 0, "d1_writes": 0,
        "production_updates": 0, "source_requests_respect_upstream_maxlag": True,
        "max_films_per_pass": per_pass, "max_passes": max_passes,
        "passes_completed": completed, "checked_this_run": checked,
        "cumulative_checked_qids": last["cumulative_checked_qids"],
        "remaining_source_qids": last["pending_qids"],
        "strict_original_language_evidence": last["strict_p364_original_language"],
        "halted_reason": halt,
        "checkpoint_persisted": checkpoint.is_file(),
        "source_only": True,
        "note": "Source-stage evidence; not yet cross-matched or published in production.",
    }
    source.save_json(accelerator_file, audit)
    print("FOUNDATION_SOURCE_ACCELERATOR=" + json.dumps(audit,sort_keys=True),flush=True)
    return audit


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("stage", "checkpoint", "out-report", "out-proposals", "out-accelerator"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--max-passes", type=int, default=8)
    args=p.parse_args()
    result=accelerate(
        args.stage,args.checkpoint,args.out_report,args.out_proposals,
        args.out_accelerator,max_passes=args.max_passes)
    if result["halted_reason"] and result["halted_reason"].startswith("source_error_"):
        return 1
    return 0


if __name__=="__main__":
    raise SystemExit(main())
