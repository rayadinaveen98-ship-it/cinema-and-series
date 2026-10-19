"""Bounded Cloudflare D1 import overlap handling."""
import subprocess
import unittest

from scripts.retry_d1_busy import run_with_busy_retry, BUSY_MARKER


class D1BusyRetryTests(unittest.TestCase):
    def test_only_transient_import_busy_is_retried(self):
        outcomes = iter([
            subprocess.CompletedProcess(["wrangler"], 1, "", "ERROR " + BUSY_MARKER),
            subprocess.CompletedProcess(["wrangler"], 0, "Success\n", ""),
        ])
        calls, sleeps = [], []

        def run(command, **kwargs):
            calls.append((command, kwargs))
            return next(outcomes)

        rc = run_with_busy_retry(["wrangler"], max_retries=3, delay_seconds=2,
                                 runner=run, sleeper=sleeps.append)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(sleeps, [2])
        self.assertTrue(all(call[1].get("capture_output") for call in calls))

    def test_quota_7500_is_not_retried(self):
        calls, sleeps = [], []

        def run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 1, "", "D1_ERROR: daily row read limit [code: 7500]")

        rc = run_with_busy_retry(["wrangler"], runner=run, sleeper=sleeps.append)
        self.assertEqual(rc, 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(sleeps, [])

    def test_import_busy_retry_budget_is_finite(self):
        calls, sleeps = [], []

        def run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 1, "", BUSY_MARKER)

        rc = run_with_busy_retry(["wrangler"], max_retries=2, delay_seconds=4,
                                 runner=run, sleeper=sleeps.append)
        self.assertEqual(rc, 1)
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, [4, 8])

    def test_invalid_argument_budget_rejected(self):
        for attempts in [-1, 7]:
            with self.assertRaises(ValueError):
                run_with_busy_retry(["wrangler"], max_retries=attempts)
        with self.assertRaises(ValueError):
            run_with_busy_retry([])


if __name__ == "__main__":
    unittest.main()
