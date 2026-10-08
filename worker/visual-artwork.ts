type VisualArtwork = {
  posterUrl: string;
  sourceUrl: string | null;
  sourceName: "wikidata_commons";
};

type WikidataEntity = {
  claims?: {
    P18?: Array<{
      mainsnak?: {
        datavalue?: { value?: string };
      };
    }>;
  };
};

type WikidataResponse = { entities?: Record<string, WikidataEntity> };

type CommonsPage = {
  title?: string;
  imageinfo?: Array<{
    thumburl?: string;
    url?: string;
    descriptionurl?: string;
  }>;
};

type CommonsResponse = {
  query?: { pages?: Record<string, CommonsPage> };
};

const cache = new Map<string, { artwork: VisualArtwork; expiresAt: number }>();
const TTL_MS = 60 * 60 * 1000;

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    headers: {
      "Accept": "application/json",
      "User-Agent": "CinemaAndSeries/0.3 (visual artwork enrichment)",
    },
  });
  if (!response.ok) throw new Error(`visual artwork request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

function batches<T>(values: T[], size: number) {
  const output: T[][] = [];
  for (let i = 0; i < values.length; i += size) output.push(values.slice(i, i + size));
  return output;
}

export async function resolveVisualArtwork(qids: string[]): Promise<Map<string, VisualArtwork>> {
  const normalized = [...new Set(qids.filter((qid) => /^Q\d+$/.test(qid)))];
  const resolved = new Map<string, VisualArtwork>();
  const pending: string[] = [];
  const now = Date.now();

  for (const qid of normalized) {
    const hit = cache.get(qid);
    if (hit && hit.expiresAt > now) resolved.set(qid, hit.artwork);
    else pending.push(qid);
  }

  for (const batch of batches(pending, 25)) {
    try {
      const params = new URLSearchParams({
        action: "wbgetentities",
        ids: batch.join("|"),
        props: "claims",
        format: "json",
        origin: "*",
      });
      const wikidata = await getJson<WikidataResponse>(
        `https://www.wikidata.org/w/api.php?${params.toString()}`,
      );
      const filenameByQid = new Map<string, string>();

      for (const qid of batch) {
        const claims = wikidata.entities?.[qid]?.claims?.P18 ?? [];
        for (const claim of claims) {
          const filename = claim.mainsnak?.datavalue?.value?.trim();
          if (filename) {
            filenameByQid.set(qid, filename);
            break;
          }
        }
      }

      for (const commonsBatch of batches([...filenameByQid.entries()], 25)) {
        if (!commonsBatch.length) continue;
        const titleParam = commonsBatch.map(([, filename]) => `File:${filename}`).join("|");
        const params = new URLSearchParams({
          action: "query",
          titles: titleParam,
          prop: "imageinfo",
          iiprop: "url",
          iiurlwidth: "800",
          format: "json",
          origin: "*",
        });
        const commons = await getJson<CommonsResponse>(
          `https://commons.wikimedia.org/w/api.php?${params.toString()}`,
        );
        const pages = Object.values(commons.query?.pages ?? {});
        const byTitle = new Map<string, CommonsPage>();
        for (const page of pages) {
          if (page.title) byTitle.set(page.title.replace(/^File:/i, "").toLowerCase(), page);
        }

        for (const [qid, filename] of commonsBatch) {
          const page = byTitle.get(filename.replace(/_/g, " ").toLowerCase());
          const info = page?.imageinfo?.[0];
          const posterUrl = info?.thumburl || info?.url;
          if (!posterUrl) continue;
          const artwork: VisualArtwork = {
            posterUrl,
            sourceUrl: info.descriptionurl || `https://www.wikidata.org/wiki/${qid}`,
            sourceName: "wikidata_commons",
          };
          resolved.set(qid, artwork);
          cache.set(qid, { artwork, expiresAt: now + TTL_MS });
        }
      }
    } catch {
      // Visual artwork is best-effort. Catalogue data must still render without it.
    }
  }

  return resolved;
}
