# Localization & Transliteration Specification — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

Cinema and Series must preserve how cinema is actually named across languages, scripts, territories and release versions. Localization exists for correctness first and search/display convenience second.

## Core rules

1. Native/original text is never overwritten by transliteration.
2. Language and script are separate dimensions.
3. A translated title is not automatically an officially used release title.
4. A romanization is not automatically an official English title.
5. Multiple legitimate original titles are allowed for multilingual productions.
6. Every sourced title/name form can carry territory, language, script, usage type and provenance.
7. Search normalization is derived; it must never become canonical display data.

## Name types

Initial controlled vocabulary:
- ORIGINAL
- OFFICIAL_LOCALIZED
- OFFICIAL_INTERNATIONAL
- RELEASE_TITLE
- TRANSLATED
- TRANSLITERATION
- ROMANIZATION
- WORKING_TITLE
- FORMER_TITLE
- ALTERNATE
- SHORT_TITLE
- SORT_TITLE
- CREDITED_AS
- STAGE_NAME

Provider-specific types map into this vocabulary while retaining raw source type.

## Required Name attributes

- owner entity;
- text;
- language nullable when unknown;
- script nullable/derived where safe;
- territory nullable;
- name type;
- preferred flag scoped by locale/context;
- official/unofficial status based on evidence;
- valid from/to nullable;
- source/Claim.

## Original title policy

For a straightforward single-language film:
- preserve exact official/native title;
- store common romanization separately;
- localized release titles are separate Names.

For genuinely multilingual productions:
- multiple original titles/language associations may coexist when evidence supports them;
- no language is arbitrarily demoted solely to fit one `original_title` column.

For historical films:
- source orthography and contemporary spelling should be preservable;
- modern normalized/transliterated forms are separate Names.

## Script model

Use a normalized script vocabulary compatible with ISO 15924 where feasible.

Examples relevant to Indian cinema include:
- Telugu
- Tamil
- Devanagari
- Malayalam
- Kannada
- Bengali
- Gujarati
- Gurmukhi
- Odia
- Latin
- Arabic-derived scripts where relevant

Script detection may be deterministic for many strings but must support mixed-script titles.

## Language model

Do not depend only on ISO 639-1 because many world languages lack two-letter codes.

Language vocabulary should support:
- internal stable language ID;
- ISO 639-1 when available;
- ISO 639-2/3 where appropriate;
- BCP 47-compatible locale usage for UI/API;
- aliases/native names.

## Transliteration

Transliteration serves search/accessibility, not historical truth.

Potential forms:
- source-provided official romanization;
- established common romanization;
- deterministic system-generated transliteration;
- manually corrected preferred romanization.

Store origin/type so users/search know the difference.

### Generated transliteration
A generated transliteration is a DerivedFact/SearchArtifact, not a source-backed official title.

It can be regenerated when transliteration rules improve.

## Search aliases

The search system can create non-display aliases for:
- punctuation-insensitive forms;
- whitespace variants;
- transliteration variants;
- common phonetic variants;
- numerals vs spelled/roman numeral forms;
- diacritic-insensitive forms.

These aliases must not appear as official titles unless independently sourced.

## India-specific examples of required behavior

A Telugu title should be discoverable through:
- Telugu script;
- established Latin-script title;
- reasonable transliteration variant;
- official English/international title if any.

A dubbed Hindi title should not overwrite the Telugu original title.

A Tamil/Telugu simultaneous production can have multiple original-language title forms linked to one Work/Versions when identity evidence supports that structure.

## Person names

Person name system must support:
- native-script name;
- canonical professional name;
- stage name;
- birth/former name where appropriate and publicly sourced;
- initials;
- alternate spellings;
- transliterations;
- work-specific `credited_as`.

Search should find `credited_as` forms without changing Person canonical identity.

## Organization names

Support:
- legal/current name;
- brand/banner name;
- former name;
- localized/native name;
- abbreviations;
- transliterations.

Rename history does not automatically create a new Organization.

## Locale-aware display selection

Client requests can specify locale/preferences.

A versioned display-title policy can consider:
1. official localized title in requested locale/territory;
2. original title if readable/appropriate;
3. official international/English title;
4. preferred romanization;
5. fallback source title.

The UI may show both display and original title, e.g.:

```text
Display: Rangasthalam
Original: రంగస్థలం
```

Policy must be deterministic and configurable by locale.

## API principles

Never return only one lossy title string when richer data is requested.

Conceptual API object:

```json
{
  "display_title": "...",
  "original_titles": [...],
  "localized_titles": [...],
  "aliases": [...]
}
```

Search/API can filter names by language, script, territory and type.

## Data-quality checks

Flag:
- same exact Name duplicated without contextual distinction;
- romanization marked as original native title;
- language incompatible with obvious script without mixed-script explanation;
- localized title without territory/language context where required;
- generated transliteration accidentally marked OFFICIAL;
- title change that silently deletes prior Working/Former title;
- person name collision incorrectly resolved by spelling alone.

## Validation corpus requirements

Include:
- Telugu/Tamil/Malayalam/Kannada/Hindi/Bengali and other Indian scripts;
- Japanese/Chinese/Korean titles;
- Arabic/Cyrillic examples;
- multilingual titles mixing Latin + native script;
- title containing numerals/symbols;
- names with diacritics;
- stage names/initials;
- working-title changes;
- different official release titles by territory;
- one title with several common romanizations.

## Lock criteria

Move to LOCKED only when:
- language/script reference strategy is chosen;
- display-title fallback policy is deterministic;
- generated vs official transliteration cannot be confused;
- search test corpus achieves target recall across Indian scripts;
- API representation does not force one title/language field;
- source adapters preserve original provider text and context.
