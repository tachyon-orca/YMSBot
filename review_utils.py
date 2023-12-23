import json
from datetime import datetime

import inflect
import requests
from dotenv import dotenv_values
from PyMovieDb import IMDB


secrets = dotenv_values(".env")
access_token = secrets["TMDB_READ_ACCESS_TOKEN"]


class ReviewGetter:
    def __init__(self):
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        self.imdb = IMDB()
        self.inflection = inflect.engine()
        with open("assets/YMS_ratings.json") as f:
            self.ratings = json.load(f)
        with open("assets/YMS_videos.json") as f:
            self.videos = json.load(f)

    def _request(self, url):
        response = requests.get(url, headers=self.headers)
        return response.json()

    def find_rating(self, title):
        results = self._request(
            f"https://api.themoviedb.org/3/search/multi?query={title}&page=1"
        )
        results = results.get("results", [])
        if len(results) == 0:
            results = json.loads(self.imdb.search(title))
            results = results.get("results", [])
            if len(results) == 0:
                return None
            else:
                results = [res["id"] for res in results]
        else:
            imdb_ids = []
            for res in results:
                match res.get("media_type", ""):
                    case "movie":
                        iid = self._request(
                            f"https://api.themoviedb.org/3/movie/{res['id']}/external_ids"
                        )
                        imdb_ids.append(iid["imdb_id"])
                    case "tv":
                        iid = self._request(
                            f"https://api.themoviedb.org/3/tv/{res['id']}/external_ids"
                        )
                    case _:
                        continue
            results = imdb_ids

        for imdb_id in results:
            if imdb_id in self.ratings:
                return imdb_id
        return None

    def process_query(self, title):
        imdb_id = self.find_rating(title)
        if imdb_id is None:
            return "I didn't find YMS's rating for that title."

        rating = self.ratings[imdb_id]
        resp = "Adum rated {}".format(rating["title"])
        if rating.get("release_date", "") != "":
            resp += " ({})".format(rating["release_date"][:4])
        if rating["rating"].isnumeric():
            resp += (" a" if rating["rating"] != "8" else " an") + " {}/10".format(
                rating["rating"]
            )
        else:
            resp += " {}".format(self.inflection.a(rating["rating"])) + "/10"

        if rating["review_date"] != "":
            resp += " on {}.".format(
                datetime.strptime(rating["review_date"], r"%Y-%m-%d").strftime(
                    r"%B %d, %Y"
                )
            )
        else:
            resp += "."
        if imdb_id not in self.videos:
            return resp

        review = self.videos[imdb_id]["reviews"][0]
        resp += " Checkout his review here: {}".format(review["url"])
        return resp
