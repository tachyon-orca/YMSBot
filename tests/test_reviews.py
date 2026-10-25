import unittest
from unittest.mock import Mock, patch

import requests

# Tests never load production credentials or make live API requests.
with patch("dotenv.dotenv_values", return_value={"TMDB_READ_ACCESS_TOKEN": "test"}):
    import review_utils


class ImdbSearchTests(unittest.TestCase):
    @patch("review_utils.requests.get")
    def test_title_search_filters_and_preserves_order(self, get):
        get.return_value.content = b"""
        <section data-testid="find-results-section-title"><div><ul>
          <li><a href="/title/tt1234567/?ref_=fn">Movie</a></li>
          <li><a href="/title/tt1234567/">Duplicate</a></li>
          <li><a href="/title/tt2345678/">A Podcast</a></li>
          <li><a href="/title/tt3456789/">A Music Video</a></li>
          <li><a href="/name/nm1234567/">Person</a></li>
          <li><a href="/title/tt45678901/">TV Series</a></li>
          <li>No link</li>
        </ul></div></section>
        <section data-testid="find-results-section-name"><div><ul>
          <li><a href="/title/tt9999999/">Unrelated section</a></li>
        </ul></div></section>
        """
        self.assertEqual(review_utils._search_imdb("Film & TV?"), ["tt1234567", "tt45678901"])
        get.assert_called_once_with(
            "https://www.imdb.com/find/",
            params={"q": "Film & TV?"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        get.return_value.raise_for_status.assert_called_once_with()

    @patch("review_utils.requests.get")
    def test_no_results(self, get):
        get.return_value.content = b"<html><body>No results</body></html>"
        self.assertEqual(review_utils._search_imdb("missing"), [])

    @patch("review_utils.requests.get")
    def test_empty_response(self, get):
        get.return_value.content = b""
        with self.assertLogs(review_utils.LOGGER, level="WARNING"):
            self.assertEqual(review_utils._search_imdb("missing"), [])

    @patch("review_utils.requests.get")
    def test_tls_failure_never_retries_without_verification(self, get):
        get.side_effect = requests.exceptions.SSLError("untrusted certificate")
        with self.assertLogs(review_utils.LOGGER, level="WARNING"):
            self.assertEqual(review_utils._search_imdb("test"), [])
        self.assertEqual(get.call_count, 1)

    @patch("review_utils.requests.get")
    def test_http_error_is_handled(self, get):
        get.return_value.raise_for_status.side_effect = requests.HTTPError("403")
        with self.assertLogs(review_utils.LOGGER, level="WARNING"):
            self.assertEqual(review_utils._search_imdb("test"), [])


class ReviewLookupTests(unittest.TestCase):
    def setUp(self):
        # Exercise lookup behavior without reading assets or pulling the repository.
        self.reviews = review_utils.ReviewGetter.__new__(review_utils.ReviewGetter)
        self.reviews.ratings = {"tt1234567": {}}
        self.reviews.watchlist = {"tt2345678": {}}

    @patch("review_utils._search_imdb")
    def test_tmdb_rating_does_not_call_fallback(self, imdb):
        self.reviews._request = Mock(side_effect=[
            {"results": [{"media_type": "movie", "id": 42}]},
            {"imdb_id": "tt1234567"},
        ])
        self.assertEqual(self.reviews.find_rating("Movie"), ("rating", "tt1234567"))
        imdb.assert_not_called()

    @patch("review_utils._search_imdb", return_value=["tt2345678"])
    def test_empty_tmdb_uses_imdb_watchlist_result(self, imdb):
        self.reviews._request = Mock(return_value={"results": []})
        self.assertEqual(self.reviews.find_rating("Movie"), ("watchlist", "tt2345678"))
        imdb.assert_called_once_with("Movie")

    @patch("review_utils._search_imdb", return_value=["tt1234567"])
    def test_missing_tmdb_external_id_uses_fallback(self, imdb):
        self.reviews._request = Mock(side_effect=[
            {"results": [{"media_type": "tv", "id": 42}]},
            {"imdb_id": None},
        ])
        self.assertEqual(self.reviews.find_rating("Show"), ("rating", "tt1234567"))
        imdb.assert_called_once_with("Show")

    @patch("review_utils._search_imdb", return_value=[])
    def test_missing_title(self, imdb):
        self.reviews._request = Mock(return_value={"results": []})
        self.assertEqual(self.reviews.find_rating("missing"), (None, None))


if __name__ == "__main__":
    unittest.main()
