#!/usr/bin/env python3
"""Read-only, D1-free live Wikimedia VRT image verification."""
from __future__ import annotations
import json
from pathlib import Path
from rights_verified_poster_batch import POSTERS, verified_metadata

def main():
    ready, held = [], []
    for entry in POSTERS:
        try:
            source = verified_metadata(entry)
            ready.append({"title":entry["title"],"year":entry["year"],
                          "file":entry["file"],"ticket":entry["ticket"],
                          "license":source["license"],"dimensions":[source["width"],source["height"]],
                          "source_page":source["source"],"image_url":source["url"]})
        except (OSError,TimeoutError,ValueError,KeyError) as error:
            held.append({"title":entry["title"],"ticket":entry["ticket"],
                         "reason":str(error)[:170]})
    report={"source_checks":len(POSTERS),"license_and_permission_verified":len(ready),
            "ready":ready,"held":held,"database_reads":0,"database_writes":0,
            "publication_performed":False}
    path=Path("data/generated/vrt-source-preflight.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("VRT_SOURCE_PREFLIGHT="+json.dumps(report,sort_keys=True),flush=True)
    if len(ready)==0:
        raise SystemExit("No film posters passed source license checks; production must remain held.")

if __name__=="__main__":
    main()
