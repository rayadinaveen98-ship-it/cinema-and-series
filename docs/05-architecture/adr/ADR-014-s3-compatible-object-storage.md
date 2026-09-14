# ADR-014 — S3-Compatible Object Storage Boundary

**Status: ACCEPTED / LOCKED FOR V1**  
**Date: 2026-09-14**

## Context
Cinema and Series may need binary/object storage for:
- raw source snapshots when storage rights permit;
- source documents/evidence attachments;
- rights-approved artwork/media derivatives;
- import/export files;
- generated QA/report artifacts;
- backup artifacts.

These objects must not be stuffed into PostgreSQL, but storage-provider identity must not leak into the domain model.

Supabase Storage exposes an S3-compatible API, supports private/public file buckets and RLS-backed access. Its current S3 compatibility does **not** provide object versioning; deleted objects are permanently removed and are not restored by a database backup.

Sources reviewed:
- https://supabase.com/docs/guides/storage
- https://supabase.com/docs/guides/storage/s3/compatibility
- https://supabase.com/docs/guides/storage/s3/authentication
- https://supabase.com/docs/guides/platform/backups

## Decision
V1 uses an **internal ObjectStore abstraction with S3 semantics**.

The initial managed implementation may use **Supabase Storage through its S3-compatible interface**, but application/domain code must not depend directly on Supabase-specific bucket APIs when ordinary S3 semantics are sufficient.

## Storage is not canonical metadata
PostgreSQL remains authoritative for:
- object identity/metadata;
- checksum;
- source/provenance links;
- rights/publication state;
- retention/deletion state;
- bucket/key or storage locator;
- audit history.

Object storage holds bytes only.

A storage object cannot become a published Asset merely because it exists in a bucket.

## Object classes
Every stored object receives a storage/retention class.

### `EVIDENCE_CRITICAL`
Permitted raw source/evidence bytes that may be necessary to reproduce a claim or parser result.

### `RIGHTS_APPROVED_ASSET`
Artwork/media whose public/internal use basis is approved under Asset Engine policy.

### `QUARANTINE_ASSET`
Candidate media pending rights/security/review; never public.

### `REBUILDABLE_DERIVATIVE`
Thumbnails, resized images, search/export artifacts or other bytes that can be regenerated.

### `EXPORT_BACKUP`
Controlled exports/backups with their own encryption/retention policy.

Exact physical bucket layout may group classes, but access policies remain class-aware.

## Immutability / content-addressing
Because Supabase Storage currently does not support S3 object versioning, evidence-critical objects must use **immutable object keys** rather than overwrite-in-place.

Recommended key pattern includes:
- object class;
- CAS object/snapshot ID;
- content hash/checksum component where practical.

Once an evidence object is referenced by a SourceSnapshot/Claim, normal application paths must not overwrite those bytes.

A corrected/re-fetched payload creates a new object/snapshot.

## Integrity
For stored evidence/assets, PostgreSQL metadata records:
- cryptographic checksum (SHA-256 working default);
- byte length;
- MIME/content type as observed/validated;
- created/retrieved time;
- source/evidence association;
- storage class;
- rights/retention status;
- deletion/takedown status where applicable.

Integrity jobs may periodically verify stored object checksum/availability.

## Raw snapshot rights gate
`SourceSnapshot` does not imply that the complete source body may legally be retained.

Per-source policy decides snapshot mode:
- full permitted payload/object;
- structured permitted subset;
- hash + evidence locator only;
- transient processing with no retained body;
- reference URL/identifier only.

The ObjectStore may be skipped entirely for sources whose terms/rights do not permit retention.

## Access policy
- evidence-critical/raw buckets are private;
- quarantine is private and inaccessible to consumer clients;
- public rendering occurs only through Asset Engine-approved records;
- S3 root credentials are server-only and never exposed to browser/mobile clients;
- signed URLs/RLS may be used for authorized internal access;
- least privilege applies to worker credentials.

## Deletion / takedown
Deletion is a controlled domain action:
1. mark/review rights or retention decision;
2. preserve audit record and metadata required to explain deletion where legally permitted;
3. remove public projections/URLs;
4. delete bytes from primary storage;
5. propagate deletion to backup copies according to legal/retention policy;
6. prevent automatic re-import when source is blocked/taken down unless policy changes.

Because object deletion may be permanent, destructive object actions are protected operations.

## Backup implication
Database backups do not contain Storage object bytes. Object backup/mirroring is handled independently under ADR-015.

## Portability
The S3-compatible boundary allows migration to AWS S3, Cloudflare R2, Backblaze B2, MinIO or another compatible service without changing cinema-domain identities.

Provider-specific capabilities may be used only behind adapters and must not become required semantics unless a later ADR changes this decision.

## Rejected alternatives
- PostgreSQL bytea as default raw/media store;
- direct permanent URLs with no Asset metadata/rights record;
- overwrite-in-place evidence files;
- one public bucket for raw evidence and approved artwork;
- assuming database backups protect object bytes.

## Consequences
The abstraction adds modest code, but protects portability, rights isolation, immutable evidence and independent object recovery.
