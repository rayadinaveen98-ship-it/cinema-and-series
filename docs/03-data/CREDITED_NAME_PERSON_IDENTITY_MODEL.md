# Credited Name & Person Identity Model

**Status: WORKING**  
**Derived from validation cases:** VC-0019, VC-0084..VC-0089

## Core rule
**A displayed credit string is not a Person primary key.**

Film/series credits can contain stage names, birth names, pseudonyms, shared pseudonyms, initials, transliterations, misspellings, historical names and deliberate disavowal names. Cinema and Series must preserve what appeared in the credit while separately resolving who the underlying contributor(s) were when evidence supports it.

## Entities / concepts

### Person
Durable real-person identity where known.

### PersonName
A name associated with a Person.

Suggested name kinds:
- `professional`
- `birth`
- `legal`
- `stage`
- `pseudonym`
- `former`
- `alternate_spelling`
- `transliteration`
- `native_script`

Fields should support language, script, effective time and provenance.

### Credit
The contribution relationship between Work/Version/Episode and contributor.

### CreditedAs
The exact or normalized display string used by the source/on-screen credit for that contribution.

A Credit may resolve to:
- one Person;
- multiple Persons;
- no resolved Person yet;
- a deliberately unresolved collective/pseudonym identity.

## Benchmark examples

### Alan Smithee
One credit string has historically represented different directors. Therefore `Alan Smithee` must never be globally merged into one real Person merely because the string matches.

### Roderick Jaynes
One pseudonymous credited identity can represent more than one actual Person (Joel and Ethan Coen). The model must allow one displayed credit to resolve to multiple contributors where evidence supports it.

### Stage names
Rajinikanth, Mammootty, Emma Stone and Michael Keaton demonstrate that public/professional names and birth/legal names can coexist for one Person without producing duplicate people.

### Version-specific pseudonym
The television edit of `Dune (1984)` demonstrates that a different Version can expose a different credited-as string while underlying authorship/person identity remains linked through evidence.

## Identity-resolution rules

Strong merge signals for Person identity:
- authoritative external IDs;
- official biography/agency/union records;
- consistent birth/biographical data;
- explicit evidence of stage-name/pseudonym equivalence;
- stable professional relationships plus corroboration.

Weak signals that are never sufficient alone:
- identical name string;
- same profession;
- same country/language;
- overlapping active years;
- social/web popularity.

## Same-name people
CAS must support two or more Persons with the exact same display name. Search disambiguation should use profession, known-for works, years, region and portrait where rights permit.

## Historical correctness
Do not rewrite historical credits to a person's current/preferred name. Store:
- canonical Person identity;
- exact credited-as value;
- source/version context.

Consumer UI may show the canonical name while exposing `credited as …` when relevant.

## Unknown contributor
An unresolved credit string remains a valid CreditObservation/Claim. We do not fabricate a Person merely to satisfy a non-null foreign key.

## V1 acceptance criteria
1. same credited name can map to different Persons by context;
2. one credited pseudonym can resolve to multiple Persons;
3. one Person can have multiple time/language/script-aware names;
4. Version-specific credits preserve their displayed names;
5. identical person names do not auto-merge;
6. search aliases never mutate credit history.
