import test from "node:test";
import assert from "node:assert/strict";
import { appendUniquePage, cataloguePageSearch, readCataloguePage } from "../src/catalogue-pages.ts";

test("Upcoming can reach all 137 titles through bounded pages instead of stopping at 80", () => {
  const records = Array.from({ length: 137 }, (_, index) => ({ id: `film-${index}` }));
  let loaded = [];
  for (let page = 0; page < 3; page++) {
    const search = new URLSearchParams(cataloguePageSearch({ scope: "upcoming", from: "2026-10-18", language: "te" }, 60, page));
    assert.equal(search.get("offset"), String(page * 60));
    assert.equal(search.get("limit"), "60");
    assert.equal(search.get("scope"), "upcoming");
    assert.equal(search.get("language"), "te");
    loaded = appendUniquePage(loaded, records.slice(page * 60, (page + 1) * 60), page);
  }
  assert.equal(loaded.length, 137);
  assert.equal(loaded.at(-1).id, "film-136");
});

test("New filters always start at zero and cannot override bounded paging", () => {
  const changed = new URLSearchParams(cataloguePageSearch({
    scope: "upcoming", language: "hi", to: "2026-11-16", offset: "99999", limit: "99999",
  }, 60, 0));
  assert.equal(changed.get("language"), "hi");
  assert.equal(changed.get("to"), "2026-11-16");
  assert.equal(changed.get("offset"), "0");
  assert.equal(changed.get("limit"), "60");
  assert.deepEqual(appendUniquePage([{ id: "old" }], [{ id: "new" }], 0), [{ id: "new" }]);
  assert.throws(() => cataloguePageSearch({}, 300, 0), RangeError);
  assert.throws(() => cataloguePageSearch({}, 60, -1), RangeError);
});

test("Overlapping pages do not repeat cards", () => {
  assert.deepEqual(
    appendUniquePage([{ id: "1" }, { id: "2" }], [{ id: "2" }, { id: "3" }, { id: "3" }], 1),
    [{ id: "1" }, { id: "2" }, { id: "3" }],
  );
});

test("D1 503 is an explicit readable error instead of a silent empty list", async () => {
  const response = new Response(JSON.stringify({ error: "catalogue_daily_read_limit" }), {
    status: 503, headers: { "Content-Type": "application/json" },
  });
  await assert.rejects(readCataloguePage(response), /daily database limit/);
  await assert.rejects(readCataloguePage(new Response("failure", { status: 500 })), /could not load/);
});

test("Successful empty results are distinct from failure and stale pages are marked", async () => {
  const empty = await readCataloguePage(new Response(JSON.stringify({ movies: [], pagination: { total: 0, hasMore: false } })));
  assert.equal(empty.movies.length, 0);
  assert.equal(empty.pagination.total, 0);
  const cached = await readCataloguePage(new Response(JSON.stringify({ movies: [{ id: "cached" }] }), {
    headers: { "X-Catalogue-Cache": "stale-on-quota" },
  }));
  assert.equal(cached.staleDuringQuota, true);
  assert.equal(cached.movies[0].id, "cached");
});

test("Compact rails skip global metadata; full browse first page keeps it", () => {
  const firstFull = new URLSearchParams(cataloguePageSearch({ scope: "all", meta: "0" }, 60, 0, true));
  assert.equal(firstFull.has("meta"), false);
  const firstRail = new URLSearchParams(cataloguePageSearch({ scope: "upcoming" }, 14, 0, false));
  assert.equal(firstRail.get("meta"), "0");
  assert.equal(firstRail.get("limit"), "14");
  const nextFull = new URLSearchParams(cataloguePageSearch({ scope: "all" }, 60, 1, true));
  assert.equal(nextFull.get("meta"), "0");
  assert.equal(nextFull.get("offset"), "60");
});
