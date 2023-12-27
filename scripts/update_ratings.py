import json

import fire
import requests
from dotenv import dotenv_values
from tqdm import tqdm

secrets = dotenv_values(".env")
access_token = secrets["TMDB_READ_ACCESS_TOKEN"]


headers = {"accept": "application/json", "Authorization": f"Bearer {access_token}"}


def _request(url):
    response = requests.get(url, headers=headers)
    return response.json()


def get_movie_id(imdb_id):
    conv = f"https://api.themoviedb.org/3/find/{imdb_id}?external_source=imdb_id"
    response = _request(conv)
    results = []
    for r in response.values():
        results.extend(r)
    if len(results) == 0:
        return None, None
    result = results[0]
    movie_id = result["id"]
    return movie_id, result

def get_info(movie_id, meta):
    metadata = dict()
    match meta["media_type"]:
        case "movie":
            metadata["title"] = meta["title"]
            metadata["release_date"] = meta["release_date"]
            metadata["original_title"] = meta.get("original_title", "")
        case "tv":
            metadata["title"] = meta["name"]
            metadata["release_date"] = meta["first_air_date"]
            metadata["original_title"] = meta.get("original_name", "")
        case "tv_episode":
            metadata["episode_title"] = meta["name"]
            metadata["release_date"] = meta["air_date"]
            show_meta = _request(f"https://api.themoviedb.org/3/tv/{meta['show_id']}")
            metadata["title"] = show_meta["name"]
            metadata["original_title"] = show_meta.get("original_name", "")

    url = f"https://api.themoviedb.org/3/movie/{movie_id}/alternative_titles?country=US"
    alt_titles = _request(url).get("titles", [])
    alt_titles = [t["title"] for t in alt_titles if t["type"] not in ["Working Title"]]
    metadata["alt_titles"] = alt_titles
    return metadata


def main(basefile, updated):
    with open(basefile) as fin:
        base = json.load(fin)
    with open(updated) as fin:
        updated = json.load(fin)
    
    for entry in tqdm(updated):
        imdb_id = entry["id"]
        if imdb_id not in base:
            movie_id, meta = get_movie_id(imdb_id)
            if movie_id is None:
                metadata = dict()
            else:
                metadata = get_info(movie_id, meta)
            base[imdb_id] = {"review_date": entry["date"], "rating": entry["rating"], **metadata}
    
    with open(basefile, "w") as fout:
        json.dump(base, fout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    fire.Fire(main)