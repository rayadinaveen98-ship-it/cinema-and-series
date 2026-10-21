"""Evidence and exact matching guards for first CC-licensed film poster."""
import tempfile
import unittest
from pathlib import Path

from scripts.publish_commons_permissioned_pilot import (
    LICENSE_URL, match_existing, fetch_commons_image, build_sql, parse_d1, ASSET_ID
)


class PermissionedFirstPosterTests(unittest.TestCase):
    def test_requires_unique_existing_title_year_qid(self):
        film={"id":"m-1","title":"The Indian Priest","wikidata_qid":"Q1001","release_year":2016,"country_code":"IN"}
        self.assertEqual(match_existing([film],[])["source_table"],"movies")
        other={"id":"c-2","title":"The Indian Priest","wikidata_qid":"Q1001","release_year":2016,"country_code":"IN"}
        self.assertEqual(match_existing([film],[other])["id"],"m-1")
        self.assertIsNone(match_existing([film],[{**other,"wikidata_qid":"Q2222"}]))
        self.assertIsNone(match_existing([{**film,"release_year":2015}],[]))
        self.assertIsNone(match_existing([{"id":"m-2","title":"The Indian Priest","release_year":2016,"wikidata_qid":None}],[]))

    def test_only_vrt_file_license_and_image_cdn_is_trusted(self):
        def fake(url, params):
            self.assertEqual(params["titles"],"File:The Indian Priest Film Poster.jpg")
            return {"query":{"pages":{"12":{"title":"File:The Indian Priest Film Poster.jpg",
                "imageinfo":[{"thumburl":"https://thumb.wikimedia.org/thumb/Indian_Priest.jpg",
                "thumbwidth":680,"thumbheight":890,"extmetadata":{
                    "LicenseShortName":{"value":"CC BY-SA 4.0"},
                    "LicenseUrl":{"value":LICENSE_URL}}}]}}}}
        image=fetch_commons_image(fake)
        self.assertEqual(image["width"],680)
        self.assertEqual(image["height"],890)
        self.assertTrue(image["url"].startswith("https://thumb.wikimedia.org/"))
        self.assertEqual(image["vrt_ticket"],"2024032810002841")
        def counterfeit(url, params):
            output=fake(url,params)
            output["query"]["pages"]["12"]["imageinfo"][0]["extmetadata"]["LicenseShortName"]["value"]="Non-free"
            return output
        with self.assertRaises(ValueError):
            fetch_commons_image(counterfeit)

    def test_insert_only_full_evidence_and_correct_link(self):
        row={"id":"movie-100","title":"The Indian Priest","wikidata_qid":"Q1001","release_year":2016,"source_table":"movies"}
        media={"url":"https://upload.wikimedia.org/wikipedia/commons/film.jpg","width":680,"height":890}
        sql=build_sql(row,media)
        self.assertIn("INSERT OR IGNORE INTO artwork_assets",sql)
        self.assertIn("INSERT OR IGNORE INTO title_artwork_links",sql)
        self.assertIn(ASSET_ID,sql)
        self.assertIn("OPEN_LICENSE_VERIFIED",sql)
        self.assertIn("VRT 2024032810002841",sql)
        self.assertIn("CC BY-SA 4.0",sql)
        self.assertIn("AND wikidata_qid='Q1001'",sql)
        self.assertNotIn("UPDATE",sql)
        self.assertNotIn("DELETE",sql)
        self.assertNotIn("CREATE TABLE",sql)

    def test_d1_errors_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"rows.json"
            p.write_text('[{"success":false,"error":"quota"}]')
            with self.assertRaises(ValueError):
                parse_d1(p)


if __name__=="__main__":
    unittest.main()
