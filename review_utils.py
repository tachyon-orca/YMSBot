import json
import os
import re
from datetime import datetime

import git
import inflect
import requests
from dotenv import dotenv_values
from PyMovieDb import IMDB

secrets = dotenv_values(".env")
access_token = secrets["TMDB_READ_ACCESS_TOKEN"]


ban_list = ["tt4686132", "tt0072725"]


def correct_date(date_string):
    if re.fullmatch(r"\d{2} \w{3} \d{4}", date_string):
        return datetime.strptime(date_string, r"%d %b %Y").strftime(r"%b %d %Y")
    return date_string


class ReviewGetter:
    def __init__(self):
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        self.imdb = IMDB()
        self.inflection = inflect.engine()
        self.repo = git.Repo(".")
        self.last_modified = dict()
        with open("assets/YMS_ratings.json") as f:
            self.ratings = json.load(f)
        self.last_modified["ratings"] = os.path.getmtime("assets/YMS_ratings.json")
        with open("assets/YMS_videos.json") as f:
            self.videos = json.load(f)
        self.last_modified["videos"] = os.path.getmtime("assets/YMS_videos.json")
        with open("assets/YMS_watchlist.json") as f:
            self.watchlist = json.load(f)
        self.last_modified["watchlist"] = os.path.getmtime("assets/YMS_watchlist.json")

    def _request(self, url):
        response = requests.get(url, headers=self.headers)
        return response.json()

    def _refresh_assets(self):
        self.repo.remotes.origin.pull()
        for asset, lmtime in self.last_modified.items():
            asset_file = f"assets/YMS_{asset}.json"
            if os.path.getmtime(asset_file) > lmtime:
                with open(asset_file) as f:
                    setattr(self, asset, json.load(f))
                self.last_modified[asset] = os.path.getmtime(asset_file)

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

    def process_query(self, title, embed_title_link=False):
        self._refresh_assets()
        if re.match(r"tt\d{7}\d*", title):
            imdb_id = title
            if imdb_id in self.ratings:
                rec_type = "rating"
            elif imdb_id in self.watchlist:
                rec_type = "watchlist"
            else:
                rec_type, imdb_id = None, None
        else:
            rec_type, imdb_id = self.find_rating(title)
        if imdb_id is None:
            return "I didn't find YMS's rating for that title."

        if rec_type == "watchlist":
            rating = self.watchlist[imdb_id]
        else:
            rating = self.ratings[imdb_id]

        if imdb_id not in ban_list:
            if "title" not in rating or rating["title"] == "":
                title = title.title()
            else:
                title = rating["title"]
            if rating.get("release_date", "") != "":
                title += " ({})".format(rating["release_date"][:4])

            if embed_title_link:
                title = f"[{title}](https://www.imdb.com/title/{imdb_id}/)"

            if rec_type == "watchlist":
                return "Adum has not rated {} yet, but he added it to his watchlist on {}.".format(
                    title, correct_date(rating["review_date"])
                )
            else:
                resp = "Adum gave {}".format(title)

        else:
            resp = "I can't say the title of that movie, but "
            if rec_type == "watchlist":
                return resp + "Adum added it to his watchlist on {}.".format(
                    correct_date(rating["review_date"])
                )
            else:
                resp += "Adum gave it"

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
