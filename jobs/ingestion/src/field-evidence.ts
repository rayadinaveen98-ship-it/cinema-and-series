import { isValidISODate } from '@cinema/domain';
import type { StagedTitle } from '@cinema/domain';
import type { WikidataSnapshot } from './wikidata-client.ts';

type Data = Record<string,unknown>;
const obj=(v:unknown):v is Data => typeof v==='object' && v!==null && !Array.isArray(v);
const gregorian='http://www.wikidata.org/entity/Q1985727';
const qId=/^Q[1-9][0-9]*$/;

export interface ObservedDate {
  date:string;
  statementId:string|null;
  referenceCount:number;
  status:'wikidata_publication_date_only';
}
export interface FieldEvidence {
  sourceId:string;
  revisionId:number|null;
  labels:Record<string,string>;
  publicationDates:ObservedDate[];
  originalLanguageItems:string[];
  genreItems:string[];
  issues:string[];
  originalPremiereVerified:false;
  streamingVerified:false;
  publishable:false;
}

function claimRows(e:Data,key:string,issues:string[]):unknown[] {
  if(!obj(e.claims) || e.claims[key]===undefined)return [];
  const rows=e.claims[key];
  if(!Array.isArray(rows) || rows.length>40) {
    issues.push('UNBOUNDED_CLAIMS_'+key);
    return [];
  }
  return rows;
}
function extractItems(e:Data,key:string,issues:string[]):string[] {
  const ids=new Set<string>();
  for(const row of claimRows(e,key,issues)) {
    if(!obj(row) || row.rank==='deprecated' || !obj(row.mainsnak))continue;
    const snak=row.mainsnak;
    if(snak.snaktype!=='value' || !obj(snak.datavalue) ||
       snak.datavalue.type!=='wikibase-entityid' || !obj(snak.datavalue.value))continue;
    const value=snak.datavalue.value;
    if(value['entity-type']==='item' && typeof value.id==='string' && qId.test(value.id))ids.add(value.id);
  }
  return [...ids].sort();
}
function exactDay(value:unknown):string|null {
  if(!obj(value) || value.precision!==11 || value.calendarmodel!==gregorian ||
     (value.before!==undefined && value.before!==0) ||
     (value.after!==undefined && value.after!==0) ||
     typeof value.time!=='string')return null;
  const match=/^\+(\d{4})-(\d{2})-(\d{2})T00:00:00Z$/.exec(value.time);
  if(!match)return null;
  const date=match[1]+'-'+match[2]+'-'+match[3];
  return isValidISODate(date)?date:null;
}

export function inspectWikidataFields(snapshot:WikidataSnapshot):FieldEvidence {
  if(!/^wikidata:Q[1-9][0-9]*$/.test(snapshot.sourceId) ||
     !obj(snapshot.rawEntity) ||
     snapshot.rawEntity.id!==snapshot.sourceId.slice(9) ||
     snapshot.rawEntity.type!=='item' ||
     !Number.isFinite(Date.parse(snapshot.retrievedAt))) {
    throw new Error('SOURCE_SNAPSHOT_IDENTITY_INVALID');
  }
  const entity=snapshot.rawEntity;
  const issues:string[]=[];
  const labels:Record<string,string>={};
  if(obj(entity.labels)) {
    const rows=Object.entries(entity.labels);
    if(rows.length>300)issues.push('UNBOUNDED_LABELS');
    else for(const [language,label] of rows) {
      if(/^[a-z]{2,3}(?:-[a-z0-9-]{2,35})?$/i.test(language) &&
         obj(label) && typeof label.value==='string' &&
         label.value.trim().length>0 && label.value.length<=300)
        labels[language.toLowerCase()]=label.value.trim();
    }
  }
  const publicationDates:ObservedDate[]=[];
  for(const row of claimRows(entity,'P577',issues)) {
    if(!obj(row) || row.rank==='deprecated' || !obj(row.mainsnak))continue;
    const snak=row.mainsnak;
    if(snak.snaktype!=='value' || !obj(snak.datavalue) ||
       snak.datavalue.type!=='time') {
      issues.push('UNSUPPORTED_P577_SNAK');
      continue;
    }
    const date=exactDay(snak.datavalue.value);
    if(!date) {
      issues.push('P577_NOT_EXACT_GREGORIAN_DAY');
      continue;
    }
    publicationDates.push({
      date,statementId:typeof row.id==='string'?row.id:null,
      referenceCount:Array.isArray(row.references)?Math.min(row.references.length,100):0,
      status:'wikidata_publication_date_only'
    });
  }
  publicationDates.sort((a,b)=>a.date.localeCompare(b.date));
  if(new Set(publicationDates.map(x=>x.date)).size>1)
    issues.push('MULTIPLE_P577_DATES_REVIEW_REQUIRED');
  return {
    sourceId:snapshot.sourceId,revisionId:snapshot.revisionId,
    labels,publicationDates,
    originalLanguageItems:extractItems(entity,'P364',issues),
    genreItems:extractItems(entity,'P136',issues),
    issues:[...new Set(issues)],
    originalPremiereVerified:false,streamingVerified:false,publishable:false
  };
}

export interface EditorialComparison {
  sourceId:string;
  labelObserved:boolean;
  publicationDateMatches:boolean[];
  sourceLanguageIdsUnmapped:boolean;
  sourceGenreIdsUnmapped:boolean;
  problems:string[];
  originalPremiereVerified:false;
  streamingVerified:false;
  publishable:false;
}

/** Never upgrades unverified P577 dates to original theatrical premieres. */
export function compareStagedFields(candidate:StagedTitle,proof:FieldEvidence):EditorialComparison {
  if(candidate.sourceId!==proof.sourceId)throw new Error('CANDIDATE_SOURCE_MISMATCH');
  const normalized=(s:string)=>s.normalize('NFKC').trim().toLocaleLowerCase('en');
  const labelObserved=Object.values(proof.labels).some(x=>normalized(x)===normalized(candidate.originalTitle));
  const dates=new Set(proof.publicationDates.map(x=>x.date));
  const publicationDateMatches=candidate.releaseEvents.map(x=>dates.has(x.date));
  const problems=[...proof.issues];
  if(!labelObserved)problems.push('TITLE_LABEL_NOT_CORROBORATED');
  if(publicationDateMatches.some(x=>!x))problems.push('NO_MATCHING_EXACT_P577_DATE');
  if(candidate.releaseEvents.some(x=>x.verification==='verified'))
    problems.push('PREVERIFIED_RELEASE_NEEDS_INDEPENDENT_EVIDENCE');
  return {
    sourceId:proof.sourceId,labelObserved,publicationDateMatches,
    sourceLanguageIdsUnmapped:proof.originalLanguageItems.length>0,
    sourceGenreIdsUnmapped:proof.genreItems.length>0,
    problems,originalPremiereVerified:false,streamingVerified:false,publishable:false
  };
}
