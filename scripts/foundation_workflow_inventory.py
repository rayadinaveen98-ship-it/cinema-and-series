#!/usr/bin/env python3
"""Credential-free, static GitHub Actions trigger/permission inventory.

No network, Cloudflare SDK, D1 binding, deployment or GitHub mutation.
This is a conservative *inventory*, not a security certification of jobs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

TOP = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s|$)")
TRIGGER = re.compile(r"^  ([A-Za-z_][A-Za-z0-9_-]*):(?:\s|$)")
CRON = re.compile(r"""\bcron:\s*["']?([^"'\n#]+)""")
FLAGS = ("schedule", "workflow_run", "push", "pull_request",
         "workflow_dispatch", "workflow_call", "repository_dispatch")


def inspect_workflow(path: Path) -> dict:
    body = path.read_text(encoding="utf-8")
    source = body.splitlines()
    inside = False
    on_section = []
    for line in source:
        if line.startswith("on:"):
            inside = True
            on_section.append(line)
            continue
        if inside and TOP.match(line):
            inside = False
        if inside:
            on_section.append(line)
    block = "\n".join(on_section)
    triggers = sorted(set(m.group(1) for l in on_section
                          if (m := TRIGGER.match(l))))
    # Inline top-level on: [schedule] is not silently treated as safe.
    inline_unsupported = bool(on_section and
        len(on_section[0].strip()) > len("on:"))
    has_cloudflare_token = "secrets.CLOUDFLARE_API_TOKEN" in body
    has_d1_command = bool(re.search(r"\bd1\s+execute\b|wrangler\s+deploy\b",
                                    body, re.IGNORECASE))
    has_freeze = "data-foundation-v2-freeze.json" in body
    return {
        "path": str(path.as_posix()),
        "trigger_names": triggers,
        "cron_expressions": sorted(set(x.strip() for x in CRON.findall(block))),
        "scheduled": "schedule" in triggers,
        "workflow_chained": "workflow_run" in triggers,
        "push_triggered": "push" in triggers,
        "manual": "workflow_dispatch" in triggers,
        "cloudflare_token_reference": has_cloudflare_token,
        "d1_or_deploy_command_text": has_d1_command,
        "explicit_freeze_file_reference": has_freeze,
        "needs_manual_review": (
            "schedule" in triggers or "workflow_run" in triggers
            or "repository_dispatch" in triggers
            or (has_cloudflare_token and ("push" in triggers or
                                          "workflow_dispatch" in triggers))
            or inline_unsupported or not triggers),
        "trigger_parser_uncertain": inline_unsupported or not triggers,
        "scope": "static_workflow_source_only",
    }


def inventory(root: Path) -> dict:
    workflows = sorted(root.glob("*.yml")) + sorted(root.glob("*.yaml"))
    assert workflows, "No workflow files; cannot complete inventory"
    items = [inspect_workflow(p) for p in workflows]
    for item in items:
        item["path"] = item["path"].replace(str(root.as_posix()) + "/", "")
    return {
        "schema": "foundation-v2-workflow-inventory-v1",
        "kind": "static_audit_not_execution_or_security_attestation",
        "workflows_inspected": len(items),
        "scheduled_workflows": sum(x["scheduled"] for x in items),
        "workflow_run_chains": sum(x["workflow_chained"] for x in items),
        "push_workflows": sum(x["push_triggered"] for x in items),
        "manual_workflows": sum(x["manual"] for x in items),
        "cloudflare_credential_references": sum(
            x["cloudflare_token_reference"] for x in items),
        "manual_review_queue_count": sum(x["needs_manual_review"] for x in items),
        "parser_uncertain_count": sum(
            x["trigger_parser_uncertain"] for x in items),
        "no_production_d1_data_access": True,
        "entries": items,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path,
                   default=Path(".github/workflows"))
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = inventory(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n",
                        encoding="utf-8")
    print("FOUNDATION_WORKFLOW_INVENTORY=" + json.dumps({
        "inspected": result["workflows_inspected"],
        "scheduled": result["scheduled_workflows"],
        "workflow_run_chains": result["workflow_run_chains"],
        "cloudflare_credential_references":
            result["cloudflare_credential_references"],
        "manual_review_queue": result["manual_review_queue_count"],
        "parser_uncertain": result["parser_uncertain_count"],
        "production_d1_queries": 0,
    }))


if __name__ == "__main__":
    main()
