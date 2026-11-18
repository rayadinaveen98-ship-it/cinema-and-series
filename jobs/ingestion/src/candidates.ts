import type { TransactionSql } from 'postgres';
import type { CatalogueTitle } from '@cinema/domain';

/**
 * Indexed candidate discovery: match only incoming Wikidata IDs and likely name/alias
 * collisions. Never load the entire catalogue. No auto-merge or auto-publish.
 *
 * Exact identities are looked up using external_ids PRIMARY KEY (source_key,external_id);
 * names use existing lower(original_title)/lower(display_title) pg_trgm indexes.
 * Results are consumed by the conservative pure-domain identity resolver.
 *
 * If a batch has more than 600 potential matches, fail closed pending reviewer
 * intervention; never silently truncate ambiguous matches.
 */
export async function readCandidateIdentities(
  tx: TransactionSql,
  records: readonly unknown[]
): Promise<CatalogueTitle[]> {
  const externalIds:string[]=[];
  const names:string[]=[];
  for (const candidate of records) {
    if (!candidate || typeof candidate!=='object' || Array.isArray(candidate)) continue;
    const record=candidate as Record<string,unknown>;
    if (typeof record.sourceId==='string' && /^wikidata:Q[1-9][0-9]*$/.test(record.sourceId)) {
      externalIds.push(record.sourceId.slice('wikidata:'.length));
    }
    if (typeof record.originalTitle==='string' && record.originalTitle.trim().length>0 &&
        record.originalTitle.length<=300) {
      names.push(record.originalTitle.trim().toLowerCase());
    }
  }
  const ids=[...new Set(externalIds)];
  const keys=[...new Set(names)];
  if (!ids.length && !keys.length) return [];

  const rows=await tx`
    WITH matches AS (
      SELECT e.title_id AS id
      FROM external_ids e
      WHERE e.source_key='wikidata'
        AND e.external_id = ANY(${tx.array(ids,'text')}::text[])
      UNION
      SELECT t.id FROM titles t
      WHERE lower(t.original_title) = ANY(${tx.array(keys,'text')}::text[])
      UNION
      SELECT l.title_id AS id FROM title_localizations l
      WHERE lower(l.display_title) = ANY(${tx.array(keys,'text')}::text[])
      UNION
      SELECT t.id FROM titles t
      JOIN unnest(${tx.array(keys,'text')}::text[]) AS q(name)
        ON lower(t.original_title) % q.name
      UNION
      SELECT l.title_id AS id FROM title_localizations l
      JOIN unnest(${tx.array(keys,'text')}::text[]) AS q(name)
        ON lower(l.display_title) % q.name
    )
    SELECT t.id::text AS id, t.title_type AS type,
           t.original_title AS original_title, t.publication_status AS status,
           COALESCE(
             (SELECT array_agg(e.source_key || ':' || e.external_id ORDER BY e.source_key,e.external_id)
              FROM external_ids e WHERE e.title_id=t.id),
             ARRAY[]::text[]
           ) AS external_ids,
           COALESCE(
             (SELECT array_agg(l.display_title ORDER BY l.display_title)
              FROM title_localizations l WHERE l.title_id=t.id),
             ARRAY[]::text[]
           ) AS alternate_titles
    FROM titles t
    INNER JOIN matches m ON m.id=t.id
    WHERE t.publication_status IN ('published','staged')
    ORDER BY t.id LIMIT 601
  `;
  if (rows.length>600) throw new Error('AMBIGUOUS_CANDIDATE_LIMIT_EXCEEDED');
  return rows.map(row=>({
    id:String(row.id),
    type:row.type==='series'?'series' as const:'movie' as const,
    originalTitle:String(row.original_title),
    originalLanguages:[],
    genres:[],
    status:row.status==='published'?'published' as const:'staged' as const,
    externalIds:row.external_ids as string[],
    alternativeTitles:row.alternate_titles as string[],
    releaseEvents:[]
  }));
}
