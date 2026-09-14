# ADR-010 — Control Room Authentication & RBAC

**Status: ACCEPTED / LOCKED FOR V1**  
**Date: 2026-09-14**

## Context
The Control Room can merge/split identities, approve sources, adjudicate conflicts, manage rights decisions and alter canonical facts through evidence-backed claims. It therefore needs stronger authorization boundaries than the public product.

Supabase Auth currently supports custom access-token claims through Auth Hooks, and those claims can be consumed by PostgreSQL Row Level Security policies. This fits our Postgres-first architecture while keeping human identity/session management out of custom application code.

Source reviewed:
- https://supabase.com/docs/guides/api/custom-claims-and-role-based-access-control-rbac

## Decision
V1 uses **Supabase Auth for human Control Room authentication**, with **custom role/permission claims + PostgreSQL RLS** as the primary authorization enforcement model.

The application service layer also performs permission checks for business actions, but database RLS remains a defense-in-depth boundary rather than trusting only UI/API routing.

## Human roles
Initial role model:

### `owner`
- full Control Room access;
- manage human roles/permissions;
- activate/suspend production sources;
- perform protected identity/source/system actions;
- emergency operational controls.

### `admin`
- broad administrative/review access;
- manage most source/jobs/system workflows;
- approve high-risk canonical actions within policy;
- cannot transfer ownership or bypass immutable audit rules.

### `editor`
- create/edit evidence-backed claims;
- maintain metadata;
- propose identity/relationship corrections;
- cannot directly perform protected merge/split/source-policy actions unless separately permitted.

### `reviewer`
- adjudicate assigned review queues;
- accept/reject candidate claims/relationships within granted domains;
- cannot alter system/source policy.

### `viewer`
- read-only Control Room visibility where permitted.

These are role bundles. Fine-grained **permissions**, not role-name checks alone, control sensitive actions.

## Permission examples
Expected permissions include:
- `catalog.read`
- `claim.create`
- `claim.review`
- `identity.merge.propose`
- `identity.merge.execute`
- `identity.split.execute`
- `canonical.override`
- `source.read`
- `source.activate`
- `source.suspend`
- `asset.review`
- `job.retry`
- `job.cancel`
- `audit.read`
- `user_role.manage`
- `system.emergency_control`

Exact list will be frozen with Control Room API contracts.

## Protected actions
The following must never be authorized merely because a client sends the correct HTTP request:
- merge/split canonical identities;
- production-source activation;
- rights override/publication approval;
- destructive administrative operations;
- permission/role escalation.

They require server-side permission checks and database enforcement/audit as applicable.

Whether V1 requires **two-person approval** for selected protected actions remains a separate product/operations decision. This ADR does not force a second human in a single-owner early deployment, but the action model must support proposal/approval separation later.

## Custom claims
Role/permission context is issued in the user's JWT through a controlled auth-hook mechanism.

Do not trust user-editable metadata for privileges.

Role tables, permission tables and auth-hook SQL are migration-controlled.

## RLS
RLS policies protect privileged schemas/tables by permission and actor context.

Guidelines:
- default-deny privileged writes;
- public/consumer clients never receive Control Room write privileges;
- source/claims/audit tables are not writable directly by a browser simply because a user is authenticated;
- critical writes normally flow through server-side domain commands;
- audit actor ID is captured for privileged changes.

## Service/machine identities
Ingestion workers are **not** modeled as human `admin` users.

Machine actors receive dedicated least-privilege credentials/service identities for their domains. They must be distinguishable in audit records from human actors.

Expected machine actor classes:
- acquisition worker;
- parser worker;
- identity/canonicalization worker;
- quality worker;
- projection/index worker;
- CI/migration deployer.

## Public consumer authentication
This ADR does not require consumer accounts in V1. If watchlists/library/accounts enter scope, public user auth may reuse Supabase Auth but through separate permissions/RLS and public API contracts.

## Portability boundary
Supabase Auth is an initial identity/session provider, not a data-domain dependency.

Domain records reference stable internal actor/user IDs and authorization permissions; they do not embed opaque provider behavior into movie/series identity.

If auth is replaced later, canonical cinema data remains unaffected.

## Security requirements
- MFA should be enabled/required for owner/admin when product support/environment permits;
- short-lived access tokens + secure refresh/session handling;
- no service-role key exposed to browser/mobile clients;
- secrets outside Git;
- audit authentication/authorization failures where useful;
- account disabling must immediately remove effective privileged access as far as token lifetime allows.

## Rejected alternatives
- one shared admin password;
- browser carrying Supabase service-role credentials;
- UI-only authorization;
- role stored only in mutable client metadata;
- every worker using the same unrestricted database credential.

## Consequences
This uses managed auth product features while preserving authorization in Postgres/domain policy. It adds RLS/policy complexity, but the Control Room is too powerful for a weaker model.
