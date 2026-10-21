"""Paced Wikimedia source requests honor provider limits and fail closed."""
import io
import json
import unittest
import urllib.error

import scripts.wikimedia_paced_fetch as client


class Clock:
    def __init__(self):
        self.now = 5.0
        self.slept = []
    def tick(self):
        return self.now
    def sleep(self, duration):
        self.slept.append(duration)
        self.now += duration


class Response:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size):
        return json.dumps({"entities": {}}).encode("utf-8")


class WikimediaPacingTests(unittest.TestCase):
    def test_allowed_endpoint_returns_json_and_serializes_requests(self):
        clock=Clock()
        client._last_request = 0.0
        seen=[]
        def opener(req, timeout=0):
            seen.append((req.full_url, req.get_header("User-agent")))
            return Response()
        for n in (1,2):
            payload=client.fetch("https://www.wikidata.org/w/api.php",
                  {"action":"wbgetentities","ids":"Q1"},
                  sleep=clock.sleep,clock=clock.tick,open_url=opener)
            self.assertEqual(payload,{"entities":{}})
        self.assertEqual(len(seen),2)
        self.assertTrue(any(abs(t-1.0)<0.001 for t in clock.slept))
        self.assertTrue(all("CinemaAndSeries" in item[1] for item in seen))

    def test_429_respects_retry_after_before_retrying(self):
        clock=Clock()
        client._last_request = 0.0
        calls=[]
        def opener(req, timeout=0):
            calls.append(req.full_url)
            if len(calls)==1:
                raise urllib.error.HTTPError(req.full_url,429,"Too Many Requests",
                                             {"Retry-After":"8"},io.BytesIO(b""))
            return Response()
        result=client.fetch("https://en.wikipedia.org/w/api.php",{"action":"query"},
                            sleep=clock.sleep,clock=clock.tick,open_url=opener)
        self.assertEqual(result,{"entities":{}})
        self.assertEqual(len(calls),2)
        self.assertIn(8.0,clock.slept)

    def test_invalid_external_hosts_are_rejected(self):
        clock=Clock()
        for url in ("https://evil.org/w/api.php",
                    "http://en.wikipedia.org/w/api.php",
                    "https://en.wikipedia.org.evil.org/w/api.php",
                    "https://en.wikipedia.org/not-an-api"):
            with self.subTest(url=url),self.assertRaises(ValueError):
                client.fetch(url,{},sleep=clock.sleep,clock=clock.tick,
                             open_url=lambda *a,**k:Response())

    def test_unrecoverable_error_is_not_silenced(self):
        clock=Clock()
        client._last_request=0.0
        def blocked(req,timeout=0):
            raise urllib.error.HTTPError(req.full_url,403,"Forbidden",{},io.BytesIO(b""))
        with self.assertRaises(urllib.error.HTTPError):
            client.fetch("https://commons.wikimedia.org/w/api.php",{},
                         sleep=clock.sleep,clock=clock.tick,open_url=blocked)


if __name__=="__main__":
    unittest.main()
