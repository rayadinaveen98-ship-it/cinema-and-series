# Catalogue data integrity and licensing policy

## Non-negotiable semantics

- A title is a canonical movie or series, not a language-specific duplicate.
- Original spoken/production languages are kept separately from localized names and dubbed-audio offers.
- Release events carry kind, date, territory and source provenance. On This Day defaults to verified original_premiere only.
- OTT providers are territory-specific availability offers, not permanent universal facts. Expired or stale verification cannot imply availability today.
- Genres are controlled normalized codes; records may have incomplete or ambiguous genres pending verification.

## Identity policy

An exact matching approved external identifier may link incoming data to a title. Name/year similarity may suggest candidates for human review but must NEVER automatically merge two unrelated titles.

## Publication rule

For production titles require a publishable source reference, valid canonical identity, original title, type, and verified claims used in a public surface. Unknown fields remain unknown. Valid JSON is not equal to factually verified metadata.

## Ingestion policy

Each connector requires a license review, rate-limit/user-agent policy, bounded batching, checkpointing, source reference, idempotency and a backoff policy. Quarantine conflicting or ambiguous fields; do not silently overwrite previously verified data. Wikidata is an initial candidate, subject to service usage policies. TVmaze and OTT-provider data require a separate license/terms review.

## Test data

All initial automated test examples are SYNTHETIC and may not be published to public catalogue. The real-world pilot has STARTED with 1 curated and provenance-linked RRR record. The remaining approximately 59 cross-language pilot records are not yet verified or ingested.

## Privacy

Guest-first preferences remain on-device. No advertising identifier, account email or viewing history is collected in this stage. No secrets or production credentials are committed.

## Unverified source-pointer rule

A staged source reference is **not** evidence that Wikidata was fetched or independently checked. Staging references store `retrieved_at = NULL`. Only a separately verified fetch may record an actual retrieval timestamp and elevate field verification. Review tickets are mandatory; the staging writer has no publication code path.

## Wikidata source adapter — initial safe scope

Wikidata's linked data interface is treated as raw unverified source evidence only. The tested client explicitly names Q-IDs; performs no discovery crawl or production writes; uses an identifiable User-Agent; sends at most five sequential source requests with conservative one-second gaps; stops on 429/503 and exposes Retry-After. Source references and CC0 facts do not automatically establish that P577 is an original theatrical premiere or that an OTT offer is currently available. Before live usage, review API rate-limit and access policies and configure source-contact/observability appropriately.

## Claim precision and original-premiere evidence

Wikidata property P577 represents a publication/release date and may contain several release-related dates. It is never, by itself, permission to mark a film's original theatrical premiere as verified. Extract only exact Gregorian day precision from its Wikibase time values as an **unverified observation**. Do not coerce month/year precision to a calendar day or confuse a festival screening, regional release or OTT date with a first theatrical premiere. Field-level editorial verification requires corroborating release kind and territory from acceptable sources.

Original-language property P364 and genre property P136 use Wikidata entity identifiers: they are not equivalent to the app's normalized language and genre codes without an explicit checked mapping. Review qualification is stage-only, not a publication decision. All current-content streaming offers require separately sourced territory-specific verification.
