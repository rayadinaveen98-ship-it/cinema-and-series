import { test, expect } from '@playwright/test';

const films = Array.from({ length: 137 }, (_, i) => ({
  id: `movie-${i + 1}`,
  title: `Release ${String(i + 1).padStart(3, '0')}`,
  language: 'Telugu',
  countryCode: 'IN',
  releaseDate: '2027-01-12',
  releaseYear: 2027,
  datePrecision: 'year',
  verificationStatus: 'verified',
  releaseSourceName: 'Wikidata',
  releaseSource: 'wikidata',
  releaseSourceUrl: 'https://www.wikidata.org/wiki/Q1',
}));
const series = [{
  id: 'series-1', title: 'Example Series', language: 'Telugu', countryCode: 'IN',
  seriesKind: 'web_series', firstAirYear: 2026, lifecycleStatus: 'ongoing',
  verificationStatus: 'supported', sourceUrl: 'https://www.wikidata.org/wiki/Q1',
}];
const jsonHeaders = { 'content-type': 'application/json' };

async function mockApi(page, options = {}) {
  await page.route('**/api/catalogue-stats', async (route) => {
    if (options.countsFail) return route.fulfill({ status: 503, headers: jsonHeaders, body: JSON.stringify({ error: 'catalogue_daily_read_limit' }) });
    return route.fulfill({ status: 200, headers: jsonHeaders, body: JSON.stringify({ movies: 137, series: 1, total: 138 }) });
  });
  await page.route('**/api/movies?**', async (route) => {
    if (options.moviesFail) return route.fulfill({ status: 503, headers: jsonHeaders, body: JSON.stringify({ error: 'catalogue_daily_read_limit' }) });
    const u = new URL(route.request().url());
    const offset = Number(u.searchParams.get('offset') || 0);
    const limit = Number(u.searchParams.get('limit') || 60);
    const language = u.searchParams.get('language') || 'all';
    const q = u.searchParams.get('q') || '';
    const selected = films.filter(f => (language === 'all' || language.toLowerCase() === 'telugu' || language.toLowerCase() === 'te') && (!q || f.title.toLowerCase().includes(q.toLowerCase())));
    const items = selected.slice(offset, offset + limit);
    const payload = {
      movies: items,
      pagination: { limit, offset, total: selected.length, hasMore: offset + limit < selected.length },
      facets: { years: [{ value: '2027', count: 137 }], languages: [{ value: 'Telugu', count: 137 }], countries: [{ value: 'IN', count: 137 }] },
      stats: { total: 137, verified: 137, supported: 0, unconfirmed: 0, activeSources: 21 },
    };
    return route.fulfill({ status: 200, headers: jsonHeaders, body: JSON.stringify(payload) });
  });
  await page.route('**/api/series?**', async (route) => {
    const u = new URL(route.request().url());
    const limit = Number(u.searchParams.get('limit') || 60);
    const offset = Number(u.searchParams.get('offset') || 0);
    const payload = {
      series: series.slice(offset, offset + limit),
      pagination: { limit, offset, total: series.length, hasMore: false },
      facets: { years: [{ value: '2026', count: 1 }], languages: [{ value: 'Telugu', count: 1 }], countries: [{ value: 'IN', count: 1 }], kinds: [{ value: 'web_series', count: 1 }] },
    };
    return route.fulfill({ status: 200, headers: jsonHeaders, body: JSON.stringify(payload) });
  });
}

test('Home has truthful counts and three usable content rails', async ({ page }) => {
  await mockApi(page);
  await page.goto('/#/');
  await expect(page.getByRole('heading', { name: 'Release 001' })).toBeVisible();
  await expect(page.getByText('138 titles and growing')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Series to discover' })).toBeVisible();
  const seriesCard = page.locator('.home-page .series-poster').first();
  const badge = await seriesCard.locator('.kind-pill').boundingBox();
  const fallbackTitle = await seriesCard.locator('.poster-placeholder-title').boundingBox();
  expect(badge).toBeTruthy();
  expect(fallbackTitle).toBeTruthy();
  expect(badge.y + badge.height).toBeLessThan(fallbackTitle.y);
  await page.screenshot({ path: `artifacts/browser-results/home-${test.info().project.name}.png`, fullPage: true });
});

test('Quota outage is shown as retry, not zero-title catalogue', async ({ page }) => {
  await mockApi(page, { moviesFail: true, countsFail: true });
  await page.goto('/#/');
  await expect(page.getByText('Catalogue totals unavailable')).toBeVisible();
  await expect(page.getByText('0 titles and growing')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Retry' }).first()).toBeVisible();
});

test('Upcoming paginates past 80 results and resets when filter changes', async ({ page }) => {
  await mockApi(page);
  await page.goto('/#/upcoming');
  await expect(page.getByText('Showing 60 of 137 upcoming movies')).toBeVisible();
  await page.getByRole('button', { name: 'Load more releases' }).click();
  await expect(page.getByText('Showing 120 of 137 upcoming movies')).toBeVisible();
  await page.getByRole('button', { name: 'Load more releases' }).click();
  await expect(page.getByText('Showing 137 of 137 upcoming movies')).toBeVisible();
  await page.getByLabel('Language').selectOption('Telugu');
  await expect(page.getByText('Showing 60 of 137 upcoming movies')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Release 137' })).toHaveCount(0);
  await page.screenshot({ path: `artifacts/browser-results/upcoming-${test.info().project.name}.png`, fullPage: true });
});

test('Movie details trap focus and restore focus to opener on Escape', async ({ page }) => {
  await mockApi(page);
  await page.goto('/#/movies');
  const card = page.getByRole('button', { name: /Release 001/ }).first();
  await card.click();
  const dialog = page.getByRole('dialog', { name: 'Release 001' });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Close movie details' })).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(dialog.getByRole('link', { name: /Wikidata film record/ })).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(dialog.getByRole('button', { name: 'Close movie details' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(card).toBeFocused();
});

test('Series details and disclosures remain keyboard accessible', async ({ page }) => {
  await mockApi(page);
  await page.goto('/#/series');
  await page.getByRole('button', { name: /Example Series/ }).first().click();
  const dialog = page.getByRole('dialog', { name: 'Example Series' });
  await expect(dialog.getByRole('button', { name: 'Close series details' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await page.getByRole('button', { name: /Filters/ }).click();
  await expect(page.getByRole('button', { name: /Filters/ })).toHaveAttribute('aria-expanded', 'true');
  await expect(page.getByRole('combobox', { name: 'Format' })).toBeVisible();
  await page.getByRole('button', { name: /Filters/ }).click();
  await expect(page.getByRole('combobox', { name: 'Format' })).toBeHidden();
});

test('Responsive navigation and focusable controls stay within the viewport', async ({ page }) => {
  await mockApi(page);
  await page.goto('/#/movies');
  await expect(page.getByRole('searchbox', { name: 'Search movies' })).toBeVisible();
  const isMobile = page.viewportSize().width <= 920;
  const nav = isMobile
    ? page.getByRole('navigation', { name: 'Mobile navigation' })
    : page.getByRole('navigation', { name: 'Primary navigation' });
  await expect(nav).toBeVisible();
  const dimensions = await page.evaluate((mobile) => ({
    scroll: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth,
    labelSize: parseFloat(getComputedStyle(document.querySelector(mobile ? '.mobile-nav-v2 small' : '.primary-links a')).fontSize),
  }), isMobile);
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.viewport + 1);
  expect(dimensions.labelSize).toBeGreaterThanOrEqual(isMobile ? 12 : 13);
  await page.screenshot({ path: `artifacts/browser-results/movies-${test.info().project.name}.png`, fullPage: true });
});

test('Poster placeholders and year-only source dates are visibly accurate', async ({ page }) => {
  await mockApi(page);
  await page.goto('/#/movies');
  const firstCard = page.locator('.media-grid .media-card').first();
  await expect(firstCard.locator('.poster-placeholder')).toBeVisible();
  await expect(firstCard.locator('.poster-placeholder-brand')).toHaveText('CINEMA & SERIES');
  await expect(firstCard.locator('.poster-placeholder-title')).toHaveText('Release 001');
  await firstCard.click();
  const dialog = page.getByRole('dialog', { name: 'Release 001' });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByText('2027 · Exact date unconfirmed', { exact: false })).toBeVisible();
  await expect(dialog.locator('.detail-fallback-letter')).toBeVisible();
  const widths = await page.evaluate(() => ({ content: document.documentElement.scrollWidth, viewport: document.documentElement.clientWidth }));
  expect(widths.content).toBeLessThanOrEqual(widths.viewport + 1);
  await page.screenshot({ path: `artifacts/browser-results/details-${test.info().project.name}.png` });
});

test('Unknown country and failed remote poster use honest fallback copy', async ({ page }) => {
  await mockApi(page);
  await page.route('**/api/movies?**', async route => {
    const payload = {
      movies: [{
        id: 'broken-poster', title: 'A Very Long Telugu English Film Title That Needs To Wrap Across Multiple Lines',
        language: 'Telugu', releaseYear: 2026, datePrecision: 'year',
        verificationStatus: 'supported', posterUrl: '/images/unavailable-film-poster.png'
      }],
      pagination: { limit: 60, offset: 0, total: 1, hasMore: false },
      facets: { years: [], languages: [], countries: [] }
    };
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });
  });
  await page.route('**/images/unavailable-film-poster.png', route => route.fulfill({ status: 404, body: '' }));
  await page.goto('/#/movies');
  const card = page.locator('.media-grid .media-card').first();
  await expect(card.locator('.poster-placeholder')).toBeVisible();
  await card.click();
  const modal = page.getByRole('dialog', { name: /A Very Long Telugu English Film Title/ });
  await expect(modal.getByText('Country unknown', { exact: false }).first()).toBeVisible();
  await expect(modal.getByText('2026 · Exact date unconfirmed', { exact: false })).toBeVisible();
  await page.screenshot({ path: `artifacts/browser-results/long-title-${test.info().project.name}.png` });
});
