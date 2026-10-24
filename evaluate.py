"""Score ReFound's search against test_memories.csv.

  python evaluate.py
      Tests the real app search (search.py) exactly as users get it.

  python evaluate.py --model all-mpnet-base-v2
      Experiment: tries a different AI model without changing the app.
      The first run per model is slow (it embeds every title), then cached.

  python evaluate.py --fields genres,description
      Experiment: changes which columns the AI reads (default:
      title,genres,keywords,description).

  python evaluate.py --boost 0,0.05,0.1,0.15,0.2
      Experiment: compares how much fame should count (needs vote_count in
      media.csv; see add_popularity.py). Prints one summary line per value.

Combine any of the experiment flags. For each memory it prints where the
right answer ranked out of ALL titles, so "miss (#47)" means the search found
it but ranked it too low, and "NOT IN DATABASE" means it's a data problem.
"""
import argparse
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from search import FULL_DATA, MODEL_NAME, POPULARITY_BOOST, SAMPLE_DATA, popularity_scores, read_media

DEFAULT_FIELDS = "title,genres,keywords,description"


def normalize(title: str) -> str:
    """'Pokémon' -> 'pokemon', 'Monsters, Inc.' -> 'monstersinc'."""
    text = unicodedata.normalize("NFKD", str(title)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.lower())


def load_tests() -> pd.DataFrame:
    # utf-8-sig strips the invisible marker some editors add to the start of a file
    tests = pd.read_csv("test_memories.csv", encoding="utf-8-sig").fillna("")
    tests.columns = [c.strip().lower() for c in tests.columns]
    needed = {"memory", "answer", "also_accept", "difficulty"}
    if not needed.issubset(tests.columns):
        raise SystemExit(
            f"test_memories.csv needs the columns {sorted(needed)}\n"
            f"but its first line has: {list(tests.columns)}\n"
            "Re-download test_memories.csv and don't open it in Numbers or Excel."
        )
    return tests


def app_ranker(media):
    """Rank every title using the real app search (its own model and boost)."""
    from search import search_media

    return lambda query: search_media(query, top_k=len(media))["title"].tolist()


def experiment_ranker(media, model_name, fields, boost):
    """Rank every title with any model, chosen columns and popularity boost."""
    from sentence_transformers import SentenceTransformer

    fields = [f.strip() for f in fields.split(",") if f.strip()]
    texts = media.apply(
        lambda r: ". ".join(
            str(r[f]) for f in fields if f in r and pd.notna(r[f]) and str(r[f]).strip()
        ),
        axis=1,
    ).tolist()

    model = SentenceTransformer(model_name)
    stamp = int(FULL_DATA.stat().st_mtime) if FULL_DATA.exists() else 0
    cache = Path(".cache") / f"{model_name.replace('/', '_')}__{'-'.join(fields)}__{len(media)}_{stamp}.npy"
    if cache.exists():
        embeddings = np.load(cache)
    else:
        print(f"Embedding {len(texts)} titles with {model_name} (cached after this)...")
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True)
        cache.parent.mkdir(exist_ok=True)
        np.save(cache, embeddings)

    titles = media["title"].tolist()
    fame = popularity_scores(media)
    query_cache = {}

    def make(b):
        def rank(query):
            if query not in query_cache:
                query_cache[query] = model.encode(query, normalize_embeddings=True)
            scores = embeddings @ query_cache[query] + b * fame
            return [titles[i] for i in np.argsort(-scores)]
        return rank

    return {b: make(b) for b in boost}


def run(tests, rank_all, top, verbose):
    rows = []
    for _, t in tests.iterrows():
        accepted = {normalize(t["answer"])}
        accepted |= {normalize(a) for a in t["also_accept"].split(";") if a.strip()}

        titles = rank_all(t["memory"])
        rank = next((i + 1 for i, title in enumerate(titles) if normalize(title) in accepted), None)

        if rank is None:
            mark, status = "NOT IN DATABASE", "missing"
        elif rank <= top:
            mark, status = f"#{rank}", "hit"
        else:
            mark, status = f"miss (#{rank})", "low"

        if verbose:
            print(f"{mark:>15}  [{t['difficulty']:<6}] {t['answer']}")
            if rank != 1:
                print(f"{'':>17}got: {', '.join(titles[:3])}")
        rows.append({"difficulty": t["difficulty"], "rank": rank, "status": status})
    return pd.DataFrame(rows)


def summary(scores, top):
    total = len(scores)
    top1 = (scores["rank"] == 1).sum()
    hits = (scores["status"] == "hit").sum()
    levels = " ".join(
        f"{(g['status'] == 'hit').sum()}/{len(g)}"
        for level in ("easy", "medium", "hard")
        if len(g := scores[scores["difficulty"] == level])
    )
    return top1, hits, total, levels


def print_full_summary(scores, top):
    top1, hits, total, _ = summary(scores, top)
    print("\n" + "=" * 44)
    print(f"Top 1 accuracy:  {top1}/{total}  ({top1 / total:.0%})")
    print(f"Top {top} accuracy:  {hits}/{total}  ({hits / total:.0%})")
    for level in ("easy", "medium", "hard"):
        group = scores[scores["difficulty"] == level]
        if len(group):
            print(f"  {level:<7} {(group['status'] == 'hit').sum()}/{len(group)}")
    print(f"Ranked too low:   {(scores['status'] == 'low').sum()}  (search problem)")
    print(f"Not in database:  {(scores['status'] == 'missing').sum()}  (data problem: tell Person 2)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=5, help="what counts as a hit")
    parser.add_argument("--model", help="try a different model, e.g. all-mpnet-base-v2")
    parser.add_argument("--fields", help=f"columns to read (default {DEFAULT_FIELDS})")
    parser.add_argument("--boost", help="popularity boost(s) to try, e.g. 0,0.1,0.2")
    args = parser.parse_args()

    media = read_media(FULL_DATA if FULL_DATA.exists() else SAMPLE_DATA)
    tests = load_tests()

    if not (args.model or args.fields or args.boost):
        print(f"APP SEARCH  model={MODEL_NAME}  boost={POPULARITY_BOOST}  ({len(media)} titles)\n")
        print_full_summary(run(tests, app_ranker(media), args.top, verbose=True), args.top)
        return

    model = args.model or MODEL_NAME
    fields = args.fields or DEFAULT_FIELDS
    boosts = [float(b) for b in (args.boost or str(POPULARITY_BOOST)).split(",")]
    if any(boosts) and "vote_count" not in media.columns:
        print("Note: media.csv has no vote_count column, so the boost does nothing.")
        print("      Run python add_popularity.py first.\n")

    print(f"EXPERIMENT  model={model}  fields={fields}  ({len(media)} titles)\n")
    rankers = experiment_ranker(media, model, fields, boosts)

    if len(boosts) == 1:
        print_full_summary(run(tests, rankers[boosts[0]], args.top, verbose=True), args.top)
        return

    print(f"{'boost':>6}  {'top 1':>6}  {f'top {args.top}':>6}   easy/medium/hard")
    for b in boosts:
        top1, hits, total, levels = summary(run(tests, rankers[b], args.top, verbose=False), args.top)
        print(f"{b:>6.2f}  {top1 / total:>6.0%}  {hits / total:>6.0%}   {levels}")


if __name__ == "__main__":
    main()
