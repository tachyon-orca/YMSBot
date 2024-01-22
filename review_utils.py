import json
import re
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
        with open("assets/YMS_watchlist.json") as f:
            self.watchlist = json.load(f)

    def _request(self, url):
        response = requests.get(url, headers=self.headers)
        return response.json()

    def find_rating(self, title):
        results = self._request(
            f"https://api.themoviedb.org/3/search/multi?query={title}&page=1"
        )
        results = results.get("results", [])
        if len(results) > 0:
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
                        imdb_ids.append(iid["imdb_id"])
                    case _:
                        continue
            results = imdb_ids

        results = [r for r in results if r is not None]
        if len(results) == 0:
            results = json.loads(self.imdb.search(title))
            results = results.get("results", [])
            if len(results) == 0:
                return None, None
            else:
                results = [res["id"] for res in results]

        for imdb_id in results:
            if imdb_id in self.ratings:
                return "rating", imdb_id
            elif imdb_id in self.watchlist:
                return "watchlist", imdb_id
        return None, None

    def process_query(self, title):
        rec_type, imdb_id = self.find_rating(title)
        if imdb_id is None:
            return "I didn't find YMS's rating for that title."

        if rec_type == "watchlist":
            rating = self.watchlist[imdb_id]
        else:
            rating = self.ratings[imdb_id]

        if "title" not in rating or rating["title"] == "":
            title = title.title()
        else:
            title = rating["title"]
        if rating.get("release_date", "") != "":
            title += " ({})".format(rating["release_date"][:4])

        if rec_type == "watchlist":
            return "Adum has not rated {} yet, but he added it to his watchlist on {}.".format(
                title, rating["review_date"]
            )
        else:
            resp = "Adum gave {}".format(title)

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
        match review["series"]:
            case "Kimba":
                resp += " Check out YMS's Kimbaspiracy video here: {}".format(
                    review["url"]
                )
            case "Top 10":
                title = review["title"]
                title = re.sub(r"\([^\)]*\)", "", title).strip().lower()
                resp += " It was one of YMS's {}. Check out the video here: {}".format(
                    title, review["url"]
                )
            case "Adum & Pals":
                resp += " Check out the Adum & Pals here: {}".format(review["url"])
            case _:
                resp += " Check out his review here: {}".format(review["url"])
        return resp
