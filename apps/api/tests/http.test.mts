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
