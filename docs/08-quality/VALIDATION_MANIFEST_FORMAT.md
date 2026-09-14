# Validation Manifest Format & Adjudication Workflow

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

The Markdown corpus documents explain cases for humans. The machine-readable validation manifest is the executable contract used later by schema/engine tests.

Schema: `validation/validation-case.schema.json`

## Why both formats exist

### Research narrative
Human-readable Markdown retains historical context, source nuance, disagreements and reasoning.

### Validation manifest
Machine-readable cases encode stable assertions such as:
- two records must remain different identities;
- a dub must stay under one Work;
- a release reschedule must preserve both dates;
- a search query must resolve the same Work;
- a low-confidence merge must route to review;
- provider Parts must not create fake Seasons.

The manifest never replaces evidence/reasoning; it references and operationalizes it.

## Case lifecycle

`seed -> evidence_upgrade_needed/open_adjudication -> gold_candidate -> gold`

Possible exit:

`retired_with_reason`

A case may be retired only when the expected benchmark itself is proven wrong, duplicated beyond value, or falls outside frozen scope. Engine failure is not a valid retirement reason.

## Gold requirements
A case becomes `gold` only when:
1. the tested domain is in V1 scope;
2. evidence is competent enough for the risk level;
3. high-risk identity decisions have corroboration or authoritative evidence;
4. expected outcome is explicitly adjudicated;
5. assertions are machine-readable;
6. no unresolved model defect invalidates the expected representation;
7. source licensing is not confused with source evidentiary usefulness;
8. reviewer/adjudication metadata is recorded.

## Risk policy

### Critical
False result could corrupt identity graph or cause large cascade.
Examples: Work merge/split, Person merge, Series-run merge.

Preferred evidence: A/A or A/B independent corroboration where practical.

### High
Wrong result materially distorts relationships/version/release history.
Examples: remake vs dub, Work vs Version, production-language realization.

Preferred evidence: at least one A/B source plus corroboration for ambiguity.

### Medium
Wrong result affects metadata/search but is readily reversible.
Examples: title locale classification, runtime of a known Version.

### Low
Presentation or low-impact metadata behavior.

## Assertion design
Assertions test semantics, not implementation details.

Good:
`Jersey Telugu and Jersey Hindi remake -> different_identity`

Bad:
`rows have different postgres UUID values`

Good:
`Hindi-dubbed Jersey -> same Work as Telugu 2019`

Bad:
`version_id starts with foo_`

This keeps the benchmark portable across implementation changes.

## Example

```json
{
  "case_id": "VC-0004",
  "title": "Jersey remake vs dub",
  "status": "gold_candidate",
  "cohorts": ["india", "remake_vs_dub", "identity"],
  "risk_level": "critical",
  "entities": [
    {"local_ref":"telugu_work","entity_kind":"work","label":"Jersey (2019 Telugu)"},
    {"local_ref":"hindi_remake","entity_kind":"work","label":"Jersey (2022 Hindi)"},
    {"local_ref":"hindi_dub","entity_kind":"version","label":"Jersey 2019 Hindi-dubbed version"}
  ],
  "evidence": [
    {
      "evidence_id":"e1",
      "grade":"A",
      "source_name":"Bombay High Court record",
      "source_kind":"legal_record",
      "url":"https://indiankanoon.org/doc/50714159/",
      "supports":["Hindi remake is distinct from Hindi-dubbed Telugu film"]
    }
  ],
  "expected_outcome": {
    "telugu_vs_hindi_remake":"different_work",
    "telugu_vs_hindi_dub":"same_work_different_version"
  },
  "assertions": [
    {
      "assertion_id":"a1",
      "domain":"identity",
      "operator":"different_identity",
      "subject_ref":"telugu_work",
      "object_ref":"hindi_remake",
      "expected":true
    },
    {
      "assertion_id":"a2",
      "domain":"identity",
      "operator":"same_identity",
      "subject_ref":"telugu_work",
      "object_ref":"hindi_dub",
      "expected":"work_identity"
    }
  ]
}
```

## Benchmark result categories
When implementation testing begins, each assertion can result in:
- `PASS`
- `FAIL_MODEL`
- `FAIL_ENGINE`
- `FAIL_DATA`
- `BLOCKED_EVIDENCE`
- `NOT_IMPLEMENTED`

Do not collapse these into one generic failure rate.

## Freeze rule
V1 cannot be frozen merely because the manifest reaches ~1,000 cases. The corpus must also meet cohort quotas, evidence/adjudication requirements and critical-domain pass thresholds defined in QA documentation.
