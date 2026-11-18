import test from 'node:test';
import assert from 'node:assert/strict';
import { inspectWikidataFields, compareStagedFields } from '../src/field-evidence.ts';
import type { WikidataSnapshot } from '../src/wikidata-client.ts';

const calendar='http://www.wikidata.org/entity/Q1985727';
const dateClaim=(time:string,precision=11,calendarmodel=calendar,rank='normal')=>({
  id:'Q123$ABC',rank,
  mainsnak:{snaktype:'value',datavalue:{
    type:'time',value:{time,precision,calendarmodel,before:0,after:0,timezone:0}
  }},
  references:[{snaks:{}}]
});
const itemClaim=(id:string)=>({
  mainsnak:{snaktype:'value',datavalue:{
    type:'wikibase-entityid',value:{id,'entity-type':'item'}
  }}
});
const create=(overrides:Record<string,unknown>={}):WikidataSnapshot=>({
  sourceId:'wikidata:Q123',
  canonicalSourceUrl:'https://www.wikidata.org/wiki/Q123',
  retrievedAt:'2026-11-18T05:50:00.000Z',
  revisionId:771,
  rawEntity:{
    id:'Q123',type:'item',
    labels:{en:{value:'Synthetic Telugu Cinema'},te:{value:'సింథటిక్ సినిమా'}},
    claims:{
      P577:[dateClaim('+2022-03-25T00:00:00Z')],
      P364:[itemClaim('Q8097')],
      P136:[itemClaim('Q188473')]
    },
    ...overrides
  }
});
const candidate=(verification:'unverified'|'verified'='unverified')=>({
  sourceId:'wikidata:Q123',
  sourceUrl:'https://www.wikidata.org/wiki/Q123',
  originalTitle:'Synthetic Telugu Cinema',
  type:'movie' as const,originalLanguages:['te'],genres:['action'],
  releaseEvents:[{date:'2022-03-25',kind:'original_premiere' as const,
    verification,sourceRecordId:'synthetic-proof'}]
});

test('extracts source observations without declaring original premiere or streaming facts verified',()=>{
  const report=inspectWikidataFields(create());
  assert.equal(report.sourceId,'wikidata:Q123');
  assert.deepEqual(report.publicationDates,[{
    date:'2022-03-25',statementId:'Q123$ABC',
    referenceCount:1,status:'wikidata_publication_date_only'
  }]);
  assert.deepEqual(report.originalLanguageItems,['Q8097']);
  assert.deepEqual(report.genreItems,['Q188473']);
  assert.equal(report.labels.te,'సింథటిక్ సినిమా');
  assert.equal(report.publishable,false);
  assert.equal(report.originalPremiereVerified,false);
  assert.deepEqual(compareStagedFields(candidate(),report),{
    sourceId:'wikidata:Q123',
    labelObserved:true,
    publicationDateMatches:[true],
    sourceLanguageIdsUnmapped:true,sourceGenreIdsUnmapped:true,
    problems:[],originalPremiereVerified:false,streamingVerified:false,publishable:false
  });
});

test('P577 lacks an original-theatrical event assertion even if source day matches',()=>{
  const report=inspectWikidataFields(create());
  const comparison=compareStagedFields(candidate('verified'),report);
  assert.equal(comparison.publicationDateMatches[0],true);
  assert.equal(comparison.originalPremiereVerified,false);
  assert.ok(comparison.problems.includes('PREVERIFIED_RELEASE_NEEDS_INDEPENDENT_EVIDENCE'));
});

test('rejects month/year precision and non-Gregorian dates as exact day observations',()=>{
  const result=inspectWikidataFields(create({claims:{
    P577:[
      dateClaim('+2022-03-01T00:00:00Z',10),
      dateClaim('+2022-01-01T00:00:00Z',9),
      dateClaim('+2022-03-25T00:00:00Z',11,'http://www.wikidata.org/entity/Q1985786'),
      dateClaim('+2021-02-29T00:00:00Z'),
      dateClaim('+2022-03-25T12:00:00Z')
    ]
  }}));
  assert.deepEqual(result.publicationDates,[]);
  assert.ok(result.issues.includes('P577_NOT_EXACT_GREGORIAN_DAY'));
});

test('multiple publication dates need review and cannot be silently assigned as first premiere',()=>{
  const report=inspectWikidataFields(create({claims:{
    P577:[
      dateClaim('+2022-03-25T00:00:00Z'),
      dateClaim('+2022-04-01T00:00:00Z')
    ]
  }}));
  assert.deepEqual(report.publicationDates.map(x=>x.date),['2022-03-25','2022-04-01']);
  assert.ok(report.issues.includes('MULTIPLE_P577_DATES_REVIEW_REQUIRED'));
  assert.equal(report.originalPremiereVerified,false);
});

test('source entity ID mismatch is refused before comparison',()=>{
  assert.throws(()=>inspectWikidataFields(create({id:'Q999'})),/SOURCE_SNAPSHOT_IDENTITY_INVALID/);
  assert.throws(()=>compareStagedFields({
    ...candidate(),sourceId:'wikidata:Q999'
  },inspectWikidataFields(create())),/CANDIDATE_SOURCE_MISMATCH/);
});

test('unmatched title and publication date stay flagged, never become verified',()=>{
  const result=compareStagedFields({
    ...candidate(),originalTitle:'Fabricated Alias',
    releaseEvents:[{...candidate().releaseEvents[0],date:'2022-05-20'}]
  },inspectWikidataFields(create()));
  assert.equal(result.labelObserved,false);
  assert.deepEqual(result.publicationDateMatches,[false]);
  assert.ok(result.problems.includes('TITLE_LABEL_NOT_CORROBORATED'));
  assert.ok(result.problems.includes('NO_MATCHING_EXACT_P577_DATE'));
  assert.equal(result.publishable,false);
});

test('unsupported, deprecated and excessive Wikibase source claims do not create facts',()=>{
  const report=inspectWikidataFields(create({claims:{
    P577:[
      dateClaim('+2022-03-25T00:00:00Z',11,calendar,'deprecated'),
      {mainsnak:{snaktype:'somevalue'}}
    ],
    P364:Array.from({length:41},()=>itemClaim('Q8097')),
    P136:[itemClaim('Q188473'),itemClaim('Q188473'),itemClaim('invalid')]
  }}));
  assert.deepEqual(report.publicationDates,[]);
  assert.ok(report.issues.includes('UNSUPPORTED_P577_SNAK'));
  assert.ok(report.issues.includes('UNBOUNDED_CLAIMS_P364'));
  assert.deepEqual(report.originalLanguageItems,[]);
  assert.deepEqual(report.genreItems,['Q188473']);
});

test('does not convert Wikidata genre/language item IDs into our ISO genre and language labels',()=>{
  const report=inspectWikidataFields(create());
  assert.equal(report.originalLanguageItems[0],'Q8097');
  assert.equal(report.genreItems[0],'Q188473');
  assert.equal(compareStagedFields(candidate(),report).sourceLanguageIdsUnmapped,true);
  assert.equal(report.publishable,false);
});
