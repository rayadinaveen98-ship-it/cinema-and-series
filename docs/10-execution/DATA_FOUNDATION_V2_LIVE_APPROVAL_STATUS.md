# Cinema & Series — Data Foundation V2 final prewrite result (22 Oct 2026)

## Verified read-only run

[GitHub workflow #39806879485](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/39806879485)
**succeeded**, following merged [PR #197](https://github.com/rayadinaveen98-ship-it/cinema-and-series/pull/197).

- Production catalogue freeze: **ACTIVE**
- Original catalogue baseline: **70,175 titles** (51,872 films / 18,303 series)
- Current full-column rows rechecked: **20**
- Proposed existing-film language updates supported for further review: **17**
- Held/disputed film identities: **3**
- Changes to production D1: **0**
- Read-only production Time Travel bookmark: **captured**, raw bookmark not disclosed
- Encryption key `FOUNDATION_BACKUP_KEY_B64`: **not configured**
- Complete encrypted recovery snapshot: **NOT YET CREATED**
- Owner write approval: **NOT GRANTED**

The workflow artifact `foundation-v2-final-17-review-approval-package`
contains only row fingerprints, title/year and language metadata, and
approval-gate status. It includes **neither the plaintext full database rows
nor the raw bookmark**.

## Exact 17-film language correction candidates

All currently have `Unknown` stored as their language. These are proposed
`Unknown → language` corrections, **not yet applied**.

| Wikidata ID | Existing film | Year | Proposed language |
|---|---|---:|---|
| Q11037173 | Mera Muqaddar | 1988 | Hindi |
| Q48671161 | Mirror Game | 2017 | Hindi |
| Q16311224 | Nee Sirithal Naan Sirippen | 1979 | Tamil |
| Q18602695 | Vashyamanthram | 1989 | Malayalam |
| Q38805227 | Lechmi | 2017 | Malayalam |
| Q18128318 | Murali Krishnudu | 1988 | Telugu |
| Q30645676 | Jaya Janaki Nayaka | 2017 | Telugu |
| Q17078270 | Nishyabda | 1998 | Kannada |
| Q39073510 | Jani | 2017 | Kannada |
| Q21161228 | Jekhane Ashray | 2009 | Bengali |
| Q64768301 | Shankar Mudi | 2019 | Bengali |
| Q21334837 | Ishq Tu Hi Tu | 2015 | Odia |
| Q19824575 | A Paying Ghost | 2015 | Marathi |
| Q105756400 | Wagherya | 2018 | Marathi |
| Q58411339 | Bhajjo Veero Ve | 2018 | Punjabi |
| Q28127631 | Polam Pol | 2016 | Gujarati |
| Q77890237 | Montu Ni Bittu | 2019 | Gujarati |

## Three films that MUST remain held

| Wikidata ID | Existing film | Stored year | Problem |
|---|---|---:|---|
| Q20967570 | Asurakulam | 2017 | Conflicting release-year evidence |
| Q20649744 | Saadey CM Saab | 2015 | Independent release records support 2016 |
| Q109519684 | Mr. Romeo | 2021 | Weak independent film identity disambiguation |

## Mandatory recovery requirement, before correction approval

The missing step is establishing an owner-held, recoverable encryption key.

Create **32 random bytes in base64** on the owner's personal computer; add it
as GitHub Actions secret `FOUNDATION_BACKUP_KEY_B64` and retain a second copy
in a secure password manager. See
[DATA_FOUNDATION_V2_FINAL_APPROVAL.md](DATA_FOUNDATION_V2_FINAL_APPROVAL.md).

Only after the key is configured should the user manually rerun
`Data Foundation V2 — Final Read Only Approval Preflight`. It must produce
a real **AES-256-GCM sealed, decryptable complete row backup**, with the
owner verifying a local decryption. A bookmark captured hours earlier is NOT
a substitute for a fresh bookmark immediately before a write.

Even after those checks, no production changes may occur without a separately
reviewed, **explicitly owner-approved** 17-film correction operation. The
70,175-record ingestion/poster/UI freeze remains active.
