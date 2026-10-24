"""Download movies and TV shows from TMDB and build ReFound's search index.

Setup (once):
  1. Get a free key: themoviedb.org > Settings > API > "API Read Access Token"
  2. Create a file called .env next to this script containing:
       TMDB_TOKEN=paste_your_read_access_token_here

Run:
  python build_dataset.py              # ~2,000+ titles, a few minutes
  python build_dataset.py --pages 100  # more titles, takes longer

Creates media.csv and embeddings.npy. Commit both so the deployed app has them.
"""
import argparse
import os
import time

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TMDB_TOKEN")
API = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w342"

# Nostalgia skews toward cartoons and family content, so we pull extra of those.
EXTRA_GENRES = {
    "movie": ["16", "10751"],  # Animation, Family
    "tv": ["16", "10762"],     # Animation, Kids
}


def get(path, **params):
    headers = {"Authorization": f"Bearer {TOKEN}", "accept": "application/json"}
    for attempt in range(3):
        r = requests.get(f"{API}{path}", headers=headers, params=params, timeout=20)
        if r.status_code == 429:  # rate limited: wait and retry
            time.sleep(2 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()


def genre_names(kind):
    return {g["id"]: g["name"] for g in get(f"/genre/{kind}/list", language="en")["genres"]}


def fetch(kind, pages, with_genres=None):
    """kind is 'movie' or 'tv'. Pulls the most-voted (best-known) titles first."""
    rows = []
    names = genre_names(kind)
    for page in range(1, pages + 1):
        params = {"sort_by": "vote_count.desc", "page": page, "language": "en-US"}
        if with_genres:
            params["with_genres"] = with_genres
        data = get(f"/discover/{kind}", **params)
        for item in data["results"]:
            if not item.get("overview"):
                continue  # nothing to search on
            date = item.get("release_date") or item.get("first_air_date") or ""
            rows.append({
                "title": item.get("title") or item.get("name"),
                "year": date[:4],
                "type": "Movie" if kind == "movie" else "TV Show",
                "description": item["overview"].replace("\n", " "),
                "genres": " ".join(names.get(g, "") for g in item.get("genre_ids", [])),
                "poster_url": POSTER_BASE + item["poster_path"] if item.get("poster_path") else "",
                "tmdb_id": item["id"],
            })
        if page >= data.get("total_pages", page):
            break
        time.sleep(0.05)  # be polite to the API
    print(f"  {kind} {with_genres or 'all'}: {len(rows)} titles")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=50, help="20 titles per page")
    args = parser.parse_args()

    if not TOKEN:
        raise SystemExit("Missing TMDB_TOKEN. Put it in a .env file (see top of this script).")

    print("Downloading from TMDB...")
    rows = []
    for kind in ("movie", "tv"):
        rows += fetch(kind, args.pages)
        for genre in EXTRA_GENRES[kind]:
            rows += fetch(kind, args.pages // 2, with_genres=genre)

    media = pd.DataFrame(rows).drop_duplicates(subset=["type", "tmdb_id"])
    media = media.reset_index(drop=True)
    print(f"{len(media)} unique titles")

    print("Computing embeddings (this is the slow part)...")
    from sentence_transformers import SentenceTransformer
    from search import MODEL_NAME, searchable_text

    model = SentenceTransformer(MODEL_NAME)
    texts = media.fillna("").apply(searchable_text, axis=1).tolist()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    media.to_csv("media.csv", index=False)
    np.save("embeddings.npy", embeddings.astype(np.float32))
    print("Done! Created media.csv and embeddings.npy")


if __name__ == "__main__":
    main()
