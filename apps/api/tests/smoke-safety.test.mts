import test from 'node:test';
import assert from 'node:assert/strict';
import {
  validateSmokeUrl, readonlyAssertions, READABLE_TABLES, SMOKE_ROLE
} from '../smoke/safety.ts';

const safe='postgresql://cinema_api_reader:synthetic_pass_123@ep-synthetic.ap-southeast-1.aws.neon.tech/cinema_pilot?sslmode=require';
test('smoke connection guard only permits the isolated Neon reader role',()=>{
  assert.equal(validateSmokeUrl(safe),safe);
  for(const bad of [
    undefined,
    '',
    safe.replace('cinema_api_reader','cinema_owner'),
    safe.replace('cinema_pilot','other_database'),
    safe.replace('ep-synthetic.ap-southeast-1.aws.neon.tech','localhost'),
    safe.replace('.neon.tech','.neon.tech.evil.invalid'),
    safe.replace('sslmode=require','sslmode=disable'),
    safe.replace('postgresql:','https:'),
    safe.replace('synthetic_pass_123','short')
  ]) {
    assert.throws(()=>validateSmokeUrl(bad),/SMOKE_DATABASE_/);
  }
});
const allowed=()=>READABLE_TABLES.map(table_name=>({
  table_name,reader_role:SMOKE_ROLE,
  can_read:true,can_insert:false,can_update:false,can_delete:false,
  can_truncate:false,can_reference:false,can_trigger:false,
  can_create_schema:false,is_admin:false,can_read_sensitive:false
}));
test('reader privilege check requires all and only the safe read model',()=>{
  assert.doesNotThrow(()=>readonlyAssertions(allowed()));
  assert.throws(()=>readonlyAssertions(allowed().slice(1)),/SMOKE_READONLY_PERMISSIONS_INCOMPLETE/);
  for(const [field,value] of [
    ['reader_role','cinema_owner'],
    ['can_read',false],['can_insert',true],['can_update',true],
    ['can_delete',true],['can_truncate',true],
    ['can_reference',true],['can_trigger',true],
    ['can_create_schema',true],['is_admin',true],
    ['can_read_sensitive',true],['table_name','non_catalogue']
  ] as const) {
    const rows=allowed();
    rows[0]={...rows[0]!,[field]:value};
    assert.throws(()=>readonlyAssertions(rows),/SMOKE_READONLY_PERMISSION_VIOLATION/);
  }
});
test('no duplicate scope checks can substitute for a missing required table',()=>{
  const rows=allowed();
  rows[0]={...rows[1]!};
  assert.throws(()=>readonlyAssertions(rows),/SMOKE_READONLY_PERMISSION_VIOLATION/);
});
