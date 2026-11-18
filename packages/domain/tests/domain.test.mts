import test from 'node:test';
import assert from 'node:assert/strict';
import {
  normalizeSearchKey, isValidISODate, isValidMonthDay, validateStagedTitle,
  resolveTitleIdentity, findOnThisDay, recommendTitles, classifyOffer
} from '../src/index.ts';

const premiere = (date: string, verification = 'verified', kind = 'original_premiere') =>
  ({ date, verification, kind, sourceRecordId: 'source-row-1' });
const titles = [
  { id: 'A', type: 'movie', originalTitle: 'Test Telugu Film', originalLanguages: ['te'],
    genres: ['action','drama'], status: 'published', externalIds: ['sample:id-1'],
    releaseEvents: [premiere('2020-02-29'), premiere('2020-05-03','verified','ott_premiere')] },
  { id: 'B', type: 'movie', originalTitle: 'Test Tamil Film', originalLanguages: ['ta'],
    genres: ['drama'], status: 'published', externalIds: ['sample:id-2'],
    alternativeTitles: ['Telugu Film'], releaseEvents: [premiere('2018-02-28')] },
  { id: 'C', type: 'series', originalTitle: 'Test Global Series', originalLanguages: ['en'],
    genres: ['mystery'], status: 'published', externalIds: ['sample:id-3'],
    releaseEvents: [premiere('2024-02-29','unverified'), premiere('2024-02-29','verified','territory_theatrical')] },
  { id: 'D', type: 'movie', originalTitle: 'Unpublished Film', originalLanguages: ['te'],
    genres: ['action'], status: 'staged', externalIds: ['sample:id-4'],
    releaseEvents: [premiere('2016-02-29')] }
];
const staged = {
  type:'movie', sourceId:'wikidata:Q123', sourceUrl:'https://www.wikidata.org/wiki/Q123',
  originalTitle:'Example', originalLanguages:['te'], genres:['drama'], releaseEvents:[premiere('2020-02-29')]
};

test('Unicode normalization preserves non-Latin scripts while matching case and punctuation', () => {
  assert.equal(normalizeSearchKey('  RRR: The FILM! '), 'rrr the film');
  assert.equal(normalizeSearchKey('  తెలుగు  సినిమా '), 'తెలుగు సినిమా');
});
test('strict Gregorian dates accept real leap days', () => {
  assert.equal(isValidISODate('2020-02-29'), true);
  assert.equal(isValidISODate('2000-02-29'), true);
  assert.equal(isValidMonthDay(2,29), true);
});
test('strict Gregorian dates reject rollover and non-leap dates', () => {
  for (const date of ['2021-02-29','2024-04-31','1900-02-29','2020-13-01','2020-2-09','not-a-date']) {
    assert.equal(isValidISODate(date), false, date);
  }
});
test('rejects malformed staged data and untrusted source URLs', () => {
  assert.equal(validateStagedTitle({...staged,sourceUrl:'http://example.com'}).ok, false);
  assert.equal(validateStagedTitle({...staged,originalLanguages:[]}).ok, false);
  assert.equal(validateStagedTitle({...staged,type:'game'}).ok, false);
  assert.equal(validateStagedTitle(null).ok, false);
});
test('accepts structurally complete staged record, but does not assert factual verification', () => {
  const response=validateStagedTitle(staged);
  assert.equal(response.ok,true);
  assert.equal(response.record?.originalTitle,'Example');
});
test('invalid release event blocks staging', () => {
  assert.equal(validateStagedTitle({...staged,releaseEvents:[premiere('2023-02-29')]}).ok, false);
});
test('exact external ID matches canonical title', () => {
  assert.deepEqual(resolveTitleIdentity({...staged,sourceId:'sample:id-1'},titles as any),
    {decision:'matched',titleId:'A'});
});
test('same title without authoritative shared ID is sent for review, never auto-merged', () => {
  const result=resolveTitleIdentity({...staged,originalTitle:'Test Telugu Film'},titles as any);
  assert.equal(result.decision,'review');
});
test('alternative alias ambiguity is review-only', () => {
  const result=resolveTitleIdentity({...staged,originalTitle:'Telugu Film'},titles as any);
  assert.equal(result.decision,'review');
});
test('new distinct source identity is not falsely attached to existing movie', () => {
  assert.deepEqual(resolveTitleIdentity(staged,titles as any),{decision:'new',candidateIds:[]});
});
test('On This Day includes verified original premieres and not OTT or region events', () => {
  assert.deepEqual(findOnThisDay(titles as any,2,29).map(x=>x.titleId),['A']);
  assert.deepEqual(findOnThisDay(titles as any,5,3),[]);
});
test('historical release view validates month/day and limits', () => {
  assert.throws(()=>findOnThisDay(titles as any,2,30),RangeError);
  assert.throws(()=>findOnThisDay(titles as any,2,29,101),RangeError);
});
test('deterministic recommendations honor original language and selected genres', () => {
  const result=recommendTitles(titles as any,{languages:['te-IN'],genres:['drama']});
  assert.deepEqual(result.map(x=>x.titleId),['A','B']);
  assert.deepEqual(result[0]?.reasons,['language','genre']);
});
test('staged records and unrelated languages never receive recommendation results', () => {
  assert.deepEqual(recommendTitles(titles as any,{languages:['ml'],genres:[]}),[]);
});
test('provider offer freshness never turns unverified or expired into current availability', () => {
  const now=new Date('2026-11-18T00:00:00Z');
  const base={providerCode:'provider',territory:'IN',verification:'verified',lastVerifiedAt:'2026-11-17T00:00:00Z'};
  assert.equal(classifyOffer(base as any,now),'recently_verified');
  assert.equal(classifyOffer({...base,lastVerifiedAt:'2026-09-01T00:00:00Z'} as any,now),'stale');
  assert.equal(classifyOffer({...base,verification:'unverified'} as any,now),'unverified');
  assert.equal(classifyOffer({...base,expiresAt:'2026-11-01T00:00:00Z'} as any,now),'expired');
  assert.equal(classifyOffer({...base,lastVerifiedAt:'2026-12-01T00:00:00Z'} as any,now),'unverified');
});
