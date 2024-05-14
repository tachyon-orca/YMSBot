import json

import pandas as pd


priority = [
    "YMS Watches",
    "Adum & Pals",
    "YMS",
    "Review",
    "Top 10",
    "Thoughts on",
    "MISC",
    "Quickie",
    "Film Festival",
    "Oscars",
]


def get_series(title):
    if title == "YMS: Kimba the White Lion":
        return "Kimba"
    elif title.startswith("Quickie:"):
        return "Quickie"
    elif title.startswith("Adum & Pals:"):
        return "Adum & Pals"
    elif "Festival" in title or "FF" in title:
        return "Film Festival"
    elif "Best Picture" in title:
        return "Oscars"
    elif title.startswith("YMS:"):
        return "YMS"
    elif title.startswith("YMS Watches:"):
        return "YMS Watches"
    elif title.endswith(" - YMS"):
        return "Review"
    elif title.startswith("Top 10") and "corrections" not in title.lower():
        return "Top 10"
    elif title.startswith("Thoughts on"):
        return "Thoughts on"
    else:
        return "MISC"


def main():
    with open("../assets/YMS_ratings.json") as fin:
        ratings = json.load(fin)
    videos = pd.read_csv("YMS_videos.csv")

    reviews = dict()
    for _, row in videos.iterrows():
        imdb_id = row["IMDB ID"]
        if imdb_id not in ratings:
            print(row)
            continue
        if imdb_id not in reviews:
            reviews[imdb_id] = {
                "title": row["Title"],
                "reviews": [],
            }
        reviews[imdb_id]["reviews"].append((row["Video Title"], row["Video Link"]))

    for imdb_id, review in reviews.items():
        review["reviews"] = [
            {"series": get_series(r[0]), "title": r[0], "url": r[1]}
            for r in review["reviews"]
        ]
        if len(review["reviews"]) > 1:
            vids = [(priority.index(r["series"]), r) for r in review["reviews"]]
            vids = sorted(vids, key=lambda x: x[0])
            if len(set([r[0] for r in vids])) != len(vids):
                print(imdb_id, vids)
            review["reviews"] = [r[1] for r in vids]

    with open("../assets/YMS_videos.json", "w") as fout:
        json.dump(reviews, fout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
