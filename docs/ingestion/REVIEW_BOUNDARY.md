# Quality review boundary — approved stage-only implementation

Status: built/tested in isolated PR. Not production authentication, publication or human UI.

## Flow

1. Curated candidate references enter stage preflight, source allowlist and identity check.
2. Atomic staging transaction records source pointer, raw candidate, issue codes, review ticket and audit. No canonical titles are changed.
3. Editor's trusted internal process may choose reject or qualify on **new** candidates.
4. For qualification: reviewer note required, a previously actually fetched source timestamp and matching source entity snapshot required. Ambiguous/canonical conflicts are not permitted to qualify.
5. Qualifying sets staging review_status=validated and ticket status=resolved, not titles.publication_status. No title is added to public API.
6. A separate source-by-field evidence review and authenticated publication workflow must be designed, implemented and certified before any batch can become a public movie or series.

## Safety gates

- No public route for staging or reviewing.
- Caller-supplied reviewerCode is a label, **not authenticated identity**. Must add service authorization/RBAC before deployment.
- Missing snapshot, malformed note, non-open review, and ambiguous alias are denied.
- PostgreSQL row locks guarantee exactly one result under reviewer races.
- Audit records only code/decision/ID, not the review note text.
- Never mark P577 as an original theatrical premiere merely because it exists in source JSON.
- No real external requests or hosted staging calls were made during this review implementation.

## Further proof

- Controlled ingest pipeline with an approved source account/rate-limit budget.
- Real manual field-level review and operator identity.
- Publication dry-run and atomic rollback/correction tests on disposable PostgreSQL.
- Large-catalogue candidate-index EXPLAIN, >10k records and non-Latin title collision tests.
