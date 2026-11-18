/** Preserve Unicode scripts; avoid transliteration or conflating unrelated titles. */
export function normalizeSearchKey(input: string): string {
  return input
    .normalize('NFKC')
    .toLocaleLowerCase()
    .replace(/[\p{P}\p{S}]+/gu, ' ')
    .replace(/\s+/gu, ' ')
    .trim();
}

export function languageRoot(input: string): string {
  return input.trim().toLowerCase().split('-')[0] ?? '';
}

export function isLanguageTag(value: unknown): value is string {
  return typeof value === 'string' &&
    /^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$/i.test(value);
}

export function isCountryCode(value: unknown): value is string {
  return typeof value === 'string' && /^[A-Z]{2}$/.test(value);
}
