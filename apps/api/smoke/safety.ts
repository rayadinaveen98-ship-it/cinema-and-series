/**
 * No connection is opened until this guard approves an explicitly scoped Neon
 * reader URL. A smoke runner must never use the catalogue owner credential.
 * Keep secrets exclusively in process environment, never in logs or repository.
 */
export const SMOKE_ROLE = 'cinema_api_reader';
export const SMOKE_DATABASE = 'cinema_pilot';

export function validateSmokeUrl(value: string | undefined): string {
  if (!value) throw new Error('SMOKE_DATABASE_URL_MISSING');
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error('SMOKE_DATABASE_URL_INVALID');
  }
  const username = decodeURIComponent(url.username);
  const database = decodeURIComponent(url.pathname.slice(1));
  const hostname = url.hostname.toLowerCase();
  if (
    url.protocol !== 'postgresql:' &&
    url.protocol !== 'postgres:'
  ) throw new Error('SMOKE_DATABASE_PROTOCOL_FORBIDDEN');
  if (!hostname.endsWith('.neon.tech') ||
      hostname === '.neon.tech' ||
      url.port !== '' ||
      username !== SMOKE_ROLE ||
      database !== SMOKE_DATABASE ||
      url.password.length < 8 ||
      url.hash !== '' ||
      (url.searchParams.get('sslmode') !== 'require' &&
       url.searchParams.get('sslmode') !== 'verify-full')
  ) {
    throw new Error('SMOKE_DATABASE_SCOPE_FORBIDDEN');
  }
  return value;
}

export const READABLE_TABLES = [
  'titles','title_languages','title_genres','title_localizations',
  'genres','languages','release_events','series_debuts',
  'source_records','streaming_offers','providers'
] as const;

/** Check all read-model relations; never approve INSERT/UPDATE/DELETE/DDL. */
export function readonlyAssertions(rows: readonly Record<string,unknown>[]): void {
  if (rows.length !== READABLE_TABLES.length) {
    throw new Error('SMOKE_READONLY_PERMISSIONS_INCOMPLETE');
  }
  const found = new Set<string>();
  for (const row of rows) {
    const table = row.table_name;
    if (typeof table !== 'string' || !READABLE_TABLES.includes(table as typeof READABLE_TABLES[number]) ||
        found.has(table) || row.reader_role !== SMOKE_ROLE || row.can_read !== true ||
        row.can_insert !== false || row.can_update !== false ||
        row.can_delete !== false || row.can_truncate !== false ||
        row.can_reference !== false || row.can_trigger !== false ||
        row.can_create_schema !== false || row.is_admin !== false ||
        row.can_read_sensitive !== false) {
      throw new Error('SMOKE_READONLY_PERMISSION_VIOLATION');
    }
    found.add(table);
  }
}
