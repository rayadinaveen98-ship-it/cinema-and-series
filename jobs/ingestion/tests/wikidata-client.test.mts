import test from 'node:test';
import assert from 'node:assert/strict';
import { SourceFetchError, WikidataReadOnlyClient } from '../src/wikidata-client.ts';

const agent='CinemaAndSeriesPilot/0.1 (https://github.com/rayadinaveen98-ship-it/cinema-and-series)';
const json=(id:string,lastrevid=123)=>new Response(JSON.stringify({
  entities:{[id]:{id,type:'item',lastrevid,labels:{en:{language:'en',value:'Synthetic Film'}}}}
}),{status:200,headers:{'Content-Type':'application/json; charset=utf-8'}});

test('fetches explicit Q-entity and exposes unverified raw snapshot without publishing',async()=>{
  const requests:string[]=[];
  const client=new WikidataReadOnlyClient({
    userAgent:agent,now:()=>new Date('2026-11-18T05:00:00Z'),
    fetcher:async (url,init)=>{
      requests.push(String(url));
      assert.equal(init?.redirect,'error');
      assert.equal((init?.headers as Record<string,string>)['User-Agent'],agent);
      return json('Q123');
    }
  });
  const snapshots=await client.fetchEntities(['Q123']);
  assert.equal(snapshots.length,1);
  assert.deepEqual(requests,['https://www.wikidata.org/wiki/Special:EntityData/Q123.json']);
  assert.equal(snapshots[0]?.sourceId,'wikidata:Q123');
  assert.equal(snapshots[0]?.canonicalSourceUrl,'https://www.wikidata.org/wiki/Q123');
  assert.equal(snapshots[0]?.retrievedAt,'2026-11-18T05:00:00.000Z');
  assert.equal(snapshots[0]?.revisionId,123);
  assert.equal(snapshots[0]?.rawEntity.type,'item');
  assert.equal('isVerifiedPremiere' in snapshots[0]!,false);
});
test('enforces pacing between requests without any parallel source requests',async()=>{
  const pauses:number[]=[];
  let count=0;
  const client=new WikidataReadOnlyClient({
    userAgent:agent,minimumIntervalMs:1500,
    pause:async ms=>{pauses.push(ms);},
    fetcher:async()=>json('Q'+(++count))
  });
  const output=await client.fetchEntities(['Q1','Q2']);
  assert.equal(output.length,2);
  assert.deepEqual(pauses,[1500]);
  assert.equal(count,2);
});
test('honors 429 Retry-After and stops batch rather than hammering the API',async()=>{
  let calls=0;
  const client=new WikidataReadOnlyClient({
    userAgent:agent,pause:async()=>{},
    fetcher:async()=>{
      calls++;
      return new Response('',{status:429,headers:{'Retry-After':'120'}});
    }
  });
  await assert.rejects(client.fetchEntities(['Q1','Q2']),error=>{
    assert.ok(error instanceof SourceFetchError);
    assert.equal(error.code,'SOURCE_BACKOFF_REQUIRED');
    assert.equal(error.retryAfterSeconds,120);
    return true;
  });
  assert.equal(calls,1);
});
test('stops at 503 and requires backoff without retry storm',async()=>{
  const client=new WikidataReadOnlyClient({
    userAgent:agent,fetcher:async()=>new Response('',{status:503})
  });
  await assert.rejects(client.fetchEntities(['Q1']),/SOURCE_BACKOFF_REQUIRED/);
});
test('rejects impersonated entity identities and unrelated entity types',async()=>{
  const mismatch=new WikidataReadOnlyClient({
    userAgent:agent,fetcher:async()=>json('Q999')
  });
  await assert.rejects(mismatch.fetchEntities(['Q1']),/SOURCE_IDENTITY_MISMATCH/);
  const other=new WikidataReadOnlyClient({
    userAgent:agent,
    fetcher:async()=>new Response(JSON.stringify({entities:{Q1:{id:'Q1',type:'lexeme'}}}),
      {headers:{'Content-Type':'application/json'}})
  });
  await assert.rejects(other.fetchEntities(['Q1']),/SOURCE_IDENTITY_MISMATCH/);
});
test('refuses absent contact user-agent, unsafe Q identifiers and aggressive pacing',async()=>{
  assert.throws(()=>new WikidataReadOnlyClient({userAgent:'node-fetch'}),/DESCRIPTIVE_USER_AGENT_REQUIRED/);
  assert.throws(()=>new WikidataReadOnlyClient({userAgent:agent,minimumIntervalMs:100}),/RATE_LIMIT_TOO_AGGRESSIVE/);
  const client=new WikidataReadOnlyClient({userAgent:agent,fetcher:async()=>json('Q1')});
  for(const ids of [[],['Q0'],['Q1','Q1'],['Q1;DROP'],['Q1','Q2','Q3','Q4','Q5','Q6']]){
    await assert.rejects(client.fetchEntities(ids),/INVALID_ENTITY_BATCH/);
  }
});
test('rejects unexpected MIME, malformed JSON and oversized source bodies',async()=>{
  const cases:[Response,string][]=[
    [new Response('<html/>',{headers:{'Content-Type':'text/html'}}),'UNEXPECTED_RESPONSE_TYPE'],
    [new Response('{broken',{headers:{'Content-Type':'application/json'}}),'INVALID_SOURCE_JSON'],
    [new Response('{}',{headers:{'Content-Type':'application/json','Content-Length':'1048577'}}),'SOURCE_RESPONSE_TOO_LARGE']
  ];
  for(const [response,code] of cases) {
    const client=new WikidataReadOnlyClient({userAgent:agent,fetcher:async()=>response});
    await assert.rejects(client.fetchEntities(['Q1']),new RegExp(code));
  }
});
