"""Parser tests for Firecrawl v2 search responses. No network."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from firecrawl_client import SCRAPE_URL, SEARCH_URL, scrape_body, search_web_results


class TestFirecrawlV2(unittest.TestCase):
    def test_scrape_body_is_fresh(self):
        body = scrape_body("https://example.com")
        self.assertEqual(body["url"], "https://example.com")
        self.assertEqual(body["formats"], ["markdown"])
        self.assertEqual(body["maxAge"], 0)

    def test_scrape_body_keeps_caller_fields(self):
        body = scrape_body("https://example.com", onlyMainContent=True, timeout=120000)
        self.assertEqual(body["maxAge"], 0)
        self.assertIs(body["onlyMainContent"], True)
        self.assertEqual(body["timeout"], 120000)

    def test_urls_are_v2(self):
        self.assertEqual(SCRAPE_URL, "https://api.firecrawl.dev/v2/scrape")
        self.assertEqual(SEARCH_URL, "https://api.firecrawl.dev/v2/search")
        self.assertNotIn("/v1/", SCRAPE_URL)
        self.assertNotIn("/v1/", SEARCH_URL)

    def test_search_reads_web_group(self):
        payload = {
            "success": True,
            "data": {
                "web": [
                    {
                        "url": "https://a.example/post",
                        "title": "A post",
                        "description": "snippet",
                    }
                ]
            },
        }
        hits = search_web_results(payload)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["url"], "https://a.example/post")
        self.assertEqual(hits[0]["title"], "A post")
        self.assertEqual(hits[0]["description"], "snippet")

    def test_search_does_not_read_other_groups(self):
        payload = {
            "data": {
                "news": [{"url": "https://news.example"}],
                "images": [{"url": "https://img.example"}],
            }
        }
        self.assertEqual(search_web_results(payload), [])

    def test_missing_data_is_empty(self):
        self.assertEqual(search_web_results(None), [])
        self.assertEqual(search_web_results({}), [])
        self.assertEqual(search_web_results({"data": None}), [])
        self.assertEqual(search_web_results({"data": {}}), [])
        self.assertEqual(search_web_results({"data": {"web": None}}), [])
        self.assertEqual(search_web_results({"success": True, "data": {"web": []}}), [])

    def test_v1_flat_list_is_an_error(self):
        with self.assertRaises(TypeError):
            search_web_results({"data": [{"url": "https://old.example"}]})

    def test_non_object_body_is_an_error(self):
        with self.assertRaises(TypeError):
            search_web_results(["not", "a", "dict"])

    def test_web_must_be_a_list(self):
        with self.assertRaises(TypeError):
            search_web_results({"data": {"web": {"url": "https://x.example"}}})


if __name__ == "__main__":
    unittest.main()
