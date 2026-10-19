#!/usr/bin/env python3
"""Retry only Cloudflare's transient overlapping-D1-import rejection.

Do not retry daily read/write quota exhaustion, syntax errors, network
failures or arbitrary Wrangler errors: those must remain visible in CI.
Uses subprocess argument arrays (no shell) and a bounded wait.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time

BUSY_MARKER = "Currently processing a long-running import. Cannot start another import"
MAX_ALLOWED_RETRIES = 6


def run_with_busy_retry(command: list[str], max_retries: int = 4,
                        delay_seconds: int = 15, runner=None, sleeper=None) -> int:
    if not command or not 0 <= max_retries <= MAX_ALLOWED_RETRIES or not 0 <= delay_seconds <= 60:
        raise ValueError("Missing command or invalid retry budget")
    runner = runner or subprocess.run
    sleeper = sleeper or time.sleep
    for attempt in range(max_retries + 1):
        result = runner(command, text=True, capture_output=True, check=False)
        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        if result.returncode == 0:
            if result.stdout:
                print(result.stdout, end="" if result.stdout.endswith("\n") else "\n", flush=True)
            if result.stderr:
                print(result.stderr, end="" if result.stderr.endswith("\n") else "\n",
                      file=sys.stderr, flush=True)
            return 0
        busy = BUSY_MARKER.lower() in combined.lower()
        if not busy or attempt == max_retries:
            if result.stdout:
                print(result.stdout, file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return result.returncode or 1
        wait = delay_seconds * (attempt + 1)
        print(f"D1 import already in progress; retry {attempt + 1}/{max_retries} in {wait}s",
              file=sys.stderr, flush=True)
        sleeper(wait)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--delay-seconds", type=int, default=15)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("Missing Wrangler command after --")
    return run_with_busy_retry(command, args.max_retries, args.delay_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
