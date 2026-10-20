#!/usr/bin/env python3
"""One-time bounded expansion of the existing Indian-film source checkpoint.

This step talks to Wikipedia only. It does not connect to Cloudflare D1.
The later production step reuses exact-QID/identity-guarded, insert-only SQL.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from india_daily_autopilot import source_step, eligible_queue_items

MAX_PASSES = 8


def gather_new_years(state: dict, passes: int = MAX_PASSES, source_fn=source_step) -> dict:
    if state.get("schema_version") != 1 or not isinstance(state.get("queue"), dict):
        raise ValueError("Must use persisted cinema Indian-film state")
    if not 1 <= passes <= MAX_PASSES:
        raise ValueError("Wave pass count out of range")
    original_queue = len(state["queue"])
    original_eligible = len(eligible_queue_items(state["queue"]))
    waves = []
    for _ in range(passes):
        if state.get("scan", {}).get("finished"):
            break
        before = copy.deepcopy(state["scan"])
        report = source_fn(state)
        if not isinstance(report, dict):
            raise ValueError("Malformed Wikipedia discovery response")
        waves.append(report)
        if report.get("wikipedia_rate_limited"):
            break
        if report.get("failed_categories", 0):
            # If one of the seven year categories failed temporarily, preserve
            # useful discovered records but revisit those years next pass.
            state["scan"] = before
            break
        if report.get("status") == "completed" and not report.get("new_source_qids"):
            break
    return {
        "waves": waves,
        "wave_count": len(waves),
        "source_qids_before": original_queue,
        "source_qids_after": len(state["queue"]),
        "new_source_qids": len(state["queue"])-original_queue,
        "eligible_category_items_before": original_eligible,
        "eligible_category_items_after": len(eligible_queue_items(state["queue"])),
        "read_only_source_discovery": True,
        "production_titles_added": 0,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--passes",type=int,default=MAX_PASSES)
    args=p.parse_args()
    state=json.loads(args.state.read_text(encoding="utf-8"))
    outcome=gather_new_years(state,args.passes)
    args.state.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("NEXT_INDIA_SOURCE_WAVE="+json.dumps(outcome,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
