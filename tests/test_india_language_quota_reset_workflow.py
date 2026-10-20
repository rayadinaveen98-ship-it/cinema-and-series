"""Static safety contract for the one-time 2026-10-20 D1 reset workflow."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT / ".github/workflows/india-film-language-quota-reset-20261020.yml"


class OneTimeFilmLanguageRecoveryContract(unittest.TestCase):
    def test_exact_one_day_guard_before_every_production_step(self):
        body=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('date -u +%F', body)
        self.assertIn('== "2026-10-20"', body)
        self.assertIn('echo "allowed=false"', body)
        self.assertIn("steps.window.outputs.allowed == 'true'",body)
        self.assertIn('cron: "17 0 20 10 *"',body)
        self.assertIn("  push:\n    branches: [main]",body)
        self.assertIn('".github/workflows/india-film-language-quota-reset-20261020.yml"',body)
        self.assertIn("cancel-in-progress: false",body)

    def test_source_is_immutable_and_writes_require_fresh_reconciliation(self):
        body=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("c352657c5113f3126c50e02ad0c4a71f8e2e8c21",body)
        self.assertIn('len(source["records"])==1200',body)
        self.assertIn("--max-updates 1000",body)
        self.assertIn("unknown-before.json",body)
        self.assertIn("language-*.sql",body)
        self.assertIn("language_source='wikidata:P364'",body)
        self.assertIn("INDIA_LANGUAGE_RESET_VERIFIED=",body)
        self.assertIn("INDIA_LANGUAGE_PROVENANCE_SCHEMA_READY=true",body)
        self.assertIn("npx wrangler d1 migrations apply cinema-and-series --remote",body)
        self.assertIn("verified-report.json",body)

    def test_provenance_migration_is_additive(self):
        schema=(ROOT/"migrations/0027_catalogue_title_language_provenance.sql").read_text()
        self.assertIn("ADD COLUMN language_source TEXT",schema)
        self.assertIn("ADD COLUMN language_source_url TEXT",schema)
        self.assertNotIn("UPDATE catalogue_titles",schema)
        self.assertNotIn("DROP TABLE",schema)


if __name__ == "__main__":
    unittest.main()
