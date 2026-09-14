# Multilingual Production & Version Model

**Status: WORKING**  
**Derived from validation cases:** VC-0021..VC-0024, VC-0060

## Problem
Indian and world cinema regularly produce cases that cannot be represented by one `original_language` field plus a list of dubs.

A film may be:
- simultaneously shot/performed in multiple languages;
- partially re-shot for another language;
- fully dubbed after photography;
- released under different official titles by language/territory;
- marketed as `bilingual`/`multilingual` even when the physical production process is mixed;
- certified differently by territory/language.

Cinema and Series must preserve the evidence instead of forcing every language into `original` vs `dub` too early.

## Locked conceptual distinction

### Work
The durable creative-production identity.

### Language realization / Version
A realization of the Work associated with a materially meaningful audio/performance/language configuration.

Working `version_kind` vocabulary:
- `production_language_realization`
- `dubbed_language_realization`
- `alternate_language_realization`
- `alternate_cut`
- `restoration`
- `broadcast_edit`
- `censorship_edit`
- `other`

The exact physical table/enums remain unfrozen until schema freeze.

## Rules

1. **Simultaneously filmed languages do not automatically create separate Works.**
   - Baahubali Telugu/Tamil is the benchmark.
2. **A dub does not create a new Work.**
3. **A remake creates a new Work even when it shares title/director/cast elements.**
4. **Marketing labels such as bilingual/pan-India/multilingual are claims, not identity rules.**
5. **Language classification may be disputed.** Preserve source claims and route ambiguous cases to review.
6. **Version language and release territory are separate.** A Hindi Version can have many territory ReleaseEvents.
7. **Localized title does not imply localized Work identity.**
8. **Original-language metadata may be plural.** V1 must not require exactly one `original_language_id` as the only truth representation.

## Suggested conceptual fields

`Version`
- version_id
- work_id
- version_kind
- primary_audio_language(s)
- production_language_realization flag/classification
- parent_version_id where derived
- evidence/claims
- runtime where version-specific
- certification linkage where version-specific

`TitleName`
- work_id or version_id context
- name
- language
- script
- territory/market where applicable
- title_kind (`official`, `working`, `localized`, `transliterated`, `alias`, `historical`)
- effective_from / effective_to
- provenance

## Identity guidance

### Strong evidence for same Work / different Version
- same production project and financing;
- same principal photography with language-specific takes;
- same production company explicitly describing simultaneous-language production;
- dubbed audio derived from an existing language realization.

### Evidence for separate Work
- producer/rightsholder explicitly calls it a remake/new adaptation;
- separate production cycle/project identity;
- materially independent principal photography intended as a new creative production;
- separate rights/remake agreement.

## Review trigger
Send to human review when:
- sources disagree on whether a language track was dubbed or separately filmed;
- only marketing language (`bilingual`, `multilingual`, `pan-India`) exists without production evidence;
- different language versions have substantial cast/scene differences that may cross the Version/Work boundary.

## V1 acceptance cases
- Baahubali Telugu/Tamil + Hindi/Malayalam dubs.
- Jersey Telugu Work + Hindi dub + Hindi remake.
- Saaho ambiguity must remain claim-based until adjudicated.
- Kingdom/Saamraajya title localization must not duplicate the Work.

## Non-goal
V1 does not need to algorithmically determine the exact percentage of scenes re-shot per language. It must preserve enough evidence and structure to avoid false Work creation and false dub/remake classification.
