import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluateBatch } from '../src/stage.ts';

const title = (id='wikidata:Q123',name='Synthetic Original',type='movie') => ({
  type,sourceId:id,sourceUrl:'https://www.wikidata.org/wiki/'+id.split(':')[1],
  originalTitle:name,originalLanguages:['te'],genres:['action'],
  releaseEvents:[{
    date:'2020-02-29',kind:'original_premiere',
    territory:'IN',verification:'unverified',sourceRecordId:'synthetic-source-record'
  }]
});
const existing=[{
  id:'00000000-0000-4000-8000-000000000001',
  type:'movie',originalTitle:'Canonical Title',originalLanguages:['te'],
  genres:['drama'],status:'published',externalIds:['wikidata:Q456'],
  alternativeTitles:['Alternate Name'],releaseEvents:[]
}];

test('valid new source always enters review, never publication',()=>{
  const x=evaluateBatch([title()],[]);
  assert.equal(x.reviewNew,1);
  assert.equal(x.quarantined,0);
  assert.equal(x.decisions[0]?.disposition,'needs_new_review');
});
test('preflight is deterministic but does not claim persistent write idempotency',()=>{
  const batch=[title(),title('wikidata:Q457','Another Synthetic')];
  assert.deepEqual(evaluateBatch(batch,existing as any),evaluateBatch(batch,existing as any));
});
test('repeated source ID in a batch is quarantined',()=>{
  const x=evaluateBatch([title(),title()],[]);
  assert.equal(x.reviewNew,1);
  assert.equal(x.quarantined,1);
  assert.deepEqual(x.decisions[1]?.issues,['DUPLICATE_IN_BATCH']);
});
test('authoritative external ID matches existing title but still requires review',()=>{
  const x=evaluateBatch([title('wikidata:Q456','Renamed Canonical Title')],existing as any);
  assert.equal(x.reviewExisting,1);
  assert.deepEqual(x.decisions[0]?.possibleTitleIds,[existing[0].id]);
});
test('conflicting media type is quarantined even with exact identifier',()=>{
  const x=evaluateBatch([title('wikidata:Q456','Conflicting Series','series')],existing as any);
  assert.equal(x.quarantined,1);
  assert.deepEqual(x.decisions[0]?.issues,['CANONICAL_TITLE_TYPE_CONFLICT']);
});
test('alias match without shared authoritative source ID requires manual review',()=>{
  const x=evaluateBatch([title('wikidata:Q999','Alternate Name')],existing as any);
  assert.equal(x.reviewExisting,1);
  assert.deepEqual(x.decisions[0]?.issues,['AMBIGUOUS_TITLE_ALIAS']);
});
test('source impersonation or inconsistent canonical IDs are quarantined',()=>{
  const samples=[
    {...title(),sourceUrl:'https://www.wikidata.org.evil.example/wiki/Q123'},
    {...title(),sourceUrl:'https://www.wikidata.org/wiki/Q999'},
    {...title(),sourceUrl:'https://www.wikidata.org/wiki/Q123?redirect=1'},
    {...title(),sourceId:'unreviewed:Q123'}
  ];
  for(const item of samples){
    assert.equal(evaluateBatch([item],[]).quarantined,1,item.sourceUrl);
  }
});
test('bad calendar date or media type never reaches human review list',()=>{
  const bad={...title(),releaseEvents:[{...title().releaseEvents[0],date:'2021-02-29'}]};
  assert.equal(evaluateBatch([bad],[]).quarantined,1);
  assert.equal(evaluateBatch([title('wikidata:Q123','Fake','game')],[]).quarantined,1);
});
test('per-batch limit protects against accidental large imports',()=>{
  assert.throws(()=>evaluateBatch(Array.from({length:41},()=>title()),[]),RangeError);
});
test('empty batch returns no candidates',()=>{
  assert.deepEqual(evaluateBatch([],[]),{
    total:0,reviewNew:0,reviewExisting:0,quarantined:0,decisions:[]
  });
});
