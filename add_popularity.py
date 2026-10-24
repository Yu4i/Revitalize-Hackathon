"""Add TMDB vote counts to media.csv, so famous titles can rank above obscure ones.

Vote count = how many TMDB users rated a title. Toy Story has tens of
thousands; an obscure cartoon has a handful. search.py uses it (on a log
scale) as a small bonus on top of the meaning match.

Setup: a .env file containing TMDB_TOKEN=your_read_access_token
Run:   python add_popularity.py
No need to rebuild embeddings afterwards: popularity doesn't change them.

Safe to re-run: it only fetches titles that don't have a vote count yet.
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


def fetch_votes(tmdb_id, media_type):
    kind = "movie" if media_type == "Movie" else "tv"
    headers = {"Authorization": f"Bearer {TOKEN}", "accept": "application/json"}
    for attempt in range(4):
        try:
            r = requests.get(f"{API}/{kind}/{int(tmdb_id)}", headers=headers, timeout=20)
        except requests.RequestException:
            time.sleep(1 + attempt)
            continue
        if r.status_code == 429:  # rate limited: wait and retry
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code == 404:  # title removed from TMDB
            return 0
        r.raise_for_status()
        return r.json().get("vote_count", 0)
    return None  # gave up; a re-run will try again


def main():
    if not TOKEN:
        raise SystemExit("Missing TMDB_TOKEN. Put it in a .env file (not .env.example!).")

    media = pd.read_csv("media.csv")
    for col in ("tmdb_id", "type"):
        if col not in media.columns:
            raise SystemExit(f"media.csv has no '{col}' column, so vote counts can't be looked up.")
    if "vote_count" not in media.columns:
        media["vote_count"] = pd.NA

    todo = media.index[media["vote_count"].isna() & media["tmdb_id"].notna()].tolist()
    print(f"Fetching vote counts for {len(todo)} of {len(media)} titles...")

    done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(fetch_votes, media.at[i, "tmdb_id"], media.at[i, "type"]): i for i in todo}
        for job in as_completed(jobs):
            media.at[jobs[job], "vote_count"] = job.result()
            done += 1
            if done % 250 == 0:
                print(f"  {done}/{len(todo)}")

    media["vote_count"] = pd.to_numeric(media["vote_count"], errors="coerce").astype("Int64")
    media.to_csv("media.csv", index=False)

    known = media["vote_count"].notna().sum()
    print(f"Done! {known}/{len(media)} titles now have a vote count.")
    for _, row in media.sort_values("vote_count", ascending=False).head(3).iterrows():
        print(f"  {row['title']}: {row['vote_count']:,} votes")
    print("Next: python evaluate.py --boost 0,0.05,0.1,0.15,0.2")


if __name__ == "__main__":
    main()
