import test from 'node:test';
import assert from 'node:assert/strict';
import {createApp} from '../src/index.ts';
import type {CatalogueRepository, TitleSummary} from '../src/contracts.ts';

const rrr:TitleSummary={
  id:'7fe240ab-0b6f-4691-a614-a56a90422022',
  originalTitle:'Synthetic Test Film',type:'movie',year:2022
};
let lastCall='';
const fake:CatalogueRepository={
  async list(options) { lastCall=JSON.stringify(options); return {items:[rrr],nextCursor:null}; },
  async detail(id) {
    lastCall='detail:'+id;
    if (id!==rrr.id) return null;
    return {...rrr,genres:['action'],originalLanguages:['te'],
      alternateTitles:[],releases:[],providers:[]};
  },
  async search(q,limit) { lastCall='search:'+q+':'+limit; return [rrr]; },
  async onThisDay(options) { lastCall='history:'+JSON.stringify(options); return [{...rrr,originalPremiereDate:'2022-03-25'}]; },
  async languages() {return [{code:'te',name:'Telugu'}];},
  async genres() {return [{code:'action',name:'Action'}];},
  async recommend(prefs,limit){lastCall='recommend:'+JSON.stringify({prefs,limit});return [{...rrr,score:8,reasons:['language','genre']}];},
  async similar(id,limit){lastCall='similar:'+id+':'+limit;return id===rrr.id?[]:null;},
};
const app=createApp(()=>fake);
const env={DATABASE_URL:'postgresql://synthetic.invalid/test'};
const request=(url:string,init?:RequestInit,bindings=env)=>
  app.request('http://localhost'+url,init,bindings);

test('health endpoint is clearly liveness, not production readiness',async()=>{
  const res=await app.request('/v1/health');
  assert.equal(res.status,200);
  assert.equal((await res.json()).catalogueReady,false);
});
test('missing database binding returns controlled 503 rather than dummy catalogue',async()=>{
  const res=await app.request('/v1/titles',undefined,{});
  assert.equal(res.status,503);
  assert.equal((await res.json()).error.code,'DATABASE_UNAVAILABLE');
});
test('catalogue listing returns bounded cursor page and validates language',async()=>{
  const res=await request('/v1/titles?limit=5&language=te-IN&type=movie');
  assert.equal(res.status,200);
  assert.equal((await res.json()).data[0].id,rrr.id);
  assert.equal(JSON.parse(lastCall).language,'te-in');
});
test('invalid limit, cursor and type return 400 before database access',async()=>{
  for(const url of ['/v1/titles?limit=0','/v1/titles?limit=999','/v1/titles?cursor=oops','/v1/titles?type=game']){
    assert.equal((await request(url)).status,400,url);
  }
});
test('search uses validated query and safe response shape',async()=>{
  assert.equal((await request('/v1/search?q=R')).status,400);
  const res=await request('/v1/search?q=RRR');
  assert.equal(res.status,200);
  assert.equal(lastCall,'search:RRR:20');
});
test('historical release requires actual valid calendar day',async()=>{
  for(const url of ['/v1/releases/on-this-day?month=2&day=30',
                    '/v1/releases/on-this-day?month=0&day=25',
                    '/v1/releases/on-this-day?month=3',
                    '/v1/releases/on-this-day?month=2&day=29&limit=101']){
    assert.equal((await request(url)).status,400,url);
  }
  assert.equal((await request('/v1/releases/on-this-day?month=2&day=29')).status,200);
});
test('title details return 404 for missing canonical UUID and 400 for invalid ID',async()=>{
  assert.equal((await request('/v1/titles/hello')).status,400);
  assert.equal((await request('/v1/titles/00000000-0000-4000-8000-000000000001')).status,404);
  const res=await request('/v1/titles/'+rrr.id);
  assert.equal((await res.json()).data.originalLanguages[0],'te');
});
test('reference directories expose controlled language/genre lists',async()=>{
  assert.equal((await request('/v1/languages')).status,200);
  assert.equal((await request('/v1/genres')).status,200);
});
test('unexpected repository exception exposes no internal content',async()=>{
  const failing=createApp(()=>({...fake,async search(){throw new Error('PRIVATE_DATABASE_URL')}}));
  const res=await failing.request('/v1/search?q=RRR',undefined,env);
  assert.equal(res.status,500);
  assert.equal(JSON.stringify(await res.json()).includes('PRIVATE_DATABASE_URL'),false);
});
test('unknown route returns structured 404',async()=>{
  assert.equal((await request('/v1/does-not-exist')).status,404);
});


test('recommendations accept validated guest-only languages and genres without persistence',async()=>{
  const res=await request('/v1/recommendations?limit=3',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({languages:['te-IN','te'],genres:['action']})
  });
  assert.equal(res.status,200);
  const data=await res.json();
  assert.equal(data.data[0].score,8);
  assert.equal(res.headers.get('cache-control'),'no-store');
  assert.deepEqual(JSON.parse(lastCall.slice('recommend:'.length)),{
    prefs:{languages:['te'],genres:['action']},limit:3
  });
});

test('malformed, empty, oversized, or extra-field recommendation payloads are rejected',async()=>{
  const cases=[
    {languages:[],genres:[]},
    {languages:['not-a-language-code'],genres:['action']},
    {languages:['te'],genres:['ACTIon']},
    {languages:'te',genres:[]},
    {languages:['te'],genres:[],userId:'tracking-id'},
    {languages:['te'],genres:[],extra:'x'.repeat(5000)}
  ];
  for(const input of cases) {
    const res=await request('/v1/recommendations',{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)
    });
    assert.ok([400,413].includes(res.status),JSON.stringify(input).slice(0,100));
  }
  const unsupported=await request('/v1/recommendations',{
    method:'POST',headers:{'Content-Type':'text/plain'},body:'hello'
  });
  assert.equal(unsupported.status,400);
  const malformed=await request('/v1/recommendations',{
    method:'POST',headers:{'Content-Type':'application/json'},body:'{broken'
  });
  assert.equal(malformed.status,400);
  const badLimit=await request('/v1/recommendations?limit=500',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({languages:['te'],genres:[]})
  });
  assert.equal(badLimit.status,400);
});

test('related-title endpoint validates UUID, bounds size and handles missing titles',async()=>{
  const bad=await request('/v1/titles/hello/similar');
  assert.equal(bad.status,400);
  const tooMany=await request('/v1/titles/'+rrr.id+'/similar?limit=99');
  assert.equal(tooMany.status,400);
  const notFound=await request('/v1/titles/00000000-0000-4000-8000-000000000001/similar');
  assert.equal(notFound.status,404);
  const ok=await request('/v1/titles/'+rrr.id+'/similar?limit=5');
  assert.equal(ok.status,200);
  assert.deepEqual((await ok.json()).data,[]);
  assert.equal(lastCall,'similar:'+rrr.id+':5');
});

test('recommendations return controlled 503 with no database configuration',async()=>{
  const res=await app.request('/v1/recommendations',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({languages:['te'],genres:[]})
  },{});
  assert.equal(res.status,503);
});
