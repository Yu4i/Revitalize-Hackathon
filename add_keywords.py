"""Add TMDB keywords to media.csv.

TMDB descriptions are short blurbs that skip the details people remember
(Up's never mentions balloons). Each title's keywords fill that gap,
e.g. Up -> "balloon, flying house, old man, wilderness explorer, ...".
search.py already reads a "keywords" column if it exists.

Setup: a .env file containing TMDB_TOKEN=your_read_access_token
Run:   python add_keywords.py
Then:  python rebuild_embeddings.py

Safe to re-run: it only fetches titles that don't have keywords yet.
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TMDB_TOKEN")
API = "https://api.themoviedb.org/3"
MAX_KEYWORDS = 20


def fetch_keywords(tmdb_id, media_type) -> str:
    kind = "movie" if media_type == "Movie" else "tv"
    headers = {"Authorization": f"Bearer {TOKEN}", "accept": "application/json"}
    for attempt in range(4):
        try:
            r = requests.get(f"{API}/{kind}/{int(tmdb_id)}/keywords", headers=headers, timeout=20)
        except requests.RequestException:
            time.sleep(1 + attempt)
            continue
        if r.status_code == 429:  # rate limited: wait and retry
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code == 404:  # title removed from TMDB
            return ""
        r.raise_for_status()
        data = r.json()
        items = data.get("keywords") or data.get("results") or []  # movies vs TV
        return ", ".join(k["name"] for k in items[:MAX_KEYWORDS])
    return ""


def main():
    if not TOKEN:
        raise SystemExit("Missing TMDB_TOKEN. Put it in a .env file (not .env.example!).")

    media = pd.read_csv("media.csv")
    for col in ("tmdb_id", "type"):
        if col not in media.columns:
            raise SystemExit(f"media.csv has no '{col}' column, so keywords can't be looked up.")
    if "keywords" not in media.columns:
        media["keywords"] = ""
    media["keywords"] = media["keywords"].fillna("")

    todo = media.index[(media["keywords"] == "") & media["tmdb_id"].notna()].tolist()
    print(f"Fetching keywords for {len(todo)} of {len(media)} titles...")

    done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(fetch_keywords, media.at[i, "tmdb_id"], media.at[i, "type"]): i for i in todo}
        for job in as_completed(jobs):
            media.at[jobs[job], "keywords"] = job.result()
            done += 1
            if done % 250 == 0:
                print(f"  {done}/{len(todo)}")

    media.to_csv("media.csv", index=False)
    found = (media["keywords"] != "").sum()
    print(f"Done! {found}/{len(media)} titles now have keywords.")
    sample = media[media["keywords"] != ""].head(3)
    for _, row in sample.iterrows():
        print(f"  {row['title']}: {row['keywords'][:80]}...")
    print("Next: python rebuild_embeddings.py")


if __name__ == "__main__":
    main()
