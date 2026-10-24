"""Score ReFound's search against test_memories.csv.

  python evaluate.py
      Tests the real app search (search.py) exactly as users get it.

  python evaluate.py --model all-mpnet-base-v2
      Experiment: tries a different AI model without changing the app.
      The first run per model is slow (it embeds every title), then cached.

  python evaluate.py --fields genres,description
      Experiment: changes which columns the AI reads (default:
      title,genres,keywords,description). Combine with --model if you like.

For each memory it prints where the right answer ranked out of ALL titles,
so "miss (#47)" means the search found it but ranked it too low, and
"NOT IN DATABASE" means it's a data problem, not a search problem.
"""
import argparse
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_FIELDS = "title,genres,keywords,description"


def normalize(title: str) -> str:
    """'Pokémon' -> 'pokemon', 'Monsters, Inc.' -> 'monstersinc'."""
    text = unicodedata.normalize("NFKD", str(title)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.lower())


def load_media() -> pd.DataFrame:
    path = "media.csv" if Path("media.csv").exists() else "sample_media.csv"
    return pd.read_csv(path).fillna("")


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
    """Rank every title using the real app search."""
    from search import search_media

    def rank(query):
        return search_media(query, top_k=len(media))["title"].tolist()

    return rank


def experiment_ranker(media, model_name, fields):
    """Rank every title with any Sentence Transformers model + chosen columns."""
    from sentence_transformers import SentenceTransformer

    fields = [f.strip() for f in fields.split(",") if f.strip()]
    texts = media.apply(
        lambda r: ". ".join(str(r[f]) for f in fields if f in r and str(r[f]).strip()),
        axis=1,
    ).tolist()

    model = SentenceTransformer(model_name)
    stamp = int(Path("media.csv").stat().st_mtime) if Path("media.csv").exists() else 0
    cache = Path(".cache") / f"{model_name.replace('/', '_')}__{'-'.join(fields)}__{len(media)}_{stamp}.npy"
    if cache.exists():
        embeddings = np.load(cache)
    else:
        print(f"Embedding {len(texts)} titles with {model_name} (cached after this)...")
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True)
        cache.parent.mkdir(exist_ok=True)
        np.save(cache, embeddings)

    titles = media["title"].tolist()

    def rank(query):
        scores = embeddings @ model.encode(query, normalize_embeddings=True)
        return [titles[i] for i in np.argsort(-scores)]

    return rank


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=5, help="what counts as a hit")
    parser.add_argument("--model", help="try a different model, e.g. all-mpnet-base-v2")
    parser.add_argument("--fields", help=f"columns to read (default {DEFAULT_FIELDS})")
    args = parser.parse_args()

    media = load_media()
    tests = load_tests()

    if args.model or args.fields:
        from search import MODEL_NAME

        model = args.model or MODEL_NAME
        fields = args.fields or DEFAULT_FIELDS
        print(f"EXPERIMENT  model={model}  fields={fields}\n")
        rank_all = experiment_ranker(media, model, fields)
    else:
        print(f"APP SEARCH  ({len(media)} titles)\n")
        rank_all = app_ranker(media)

    rows = []
    for _, t in tests.iterrows():
        accepted = {normalize(t["answer"])}
        accepted |= {normalize(a) for a in t["also_accept"].split(";") if a.strip()}

        titles = rank_all(t["memory"])
        rank = next((i + 1 for i, title in enumerate(titles) if normalize(title) in accepted), None)

        if rank is None:
            mark, status = "NOT IN DATABASE", "missing"
        elif rank <= args.top:
            mark, status = f"#{rank}", "hit"
        else:
            mark, status = f"miss (#{rank})", "low"

        print(f"{mark:>15}  [{t['difficulty']:<6}] {t['answer']}")
        if rank != 1:
            print(f"{'':>17}got: {', '.join(titles[:3])}")
        rows.append({"difficulty": t["difficulty"], "rank": rank, "status": status})

    scores = pd.DataFrame(rows)
    total = len(scores)
    top1 = (scores["rank"] == 1).sum()
    hits = (scores["status"] == "hit").sum()

    print("\n" + "=" * 44)
    print(f"Top 1 accuracy:  {top1}/{total}  ({top1 / total:.0%})")
    print(f"Top {args.top} accuracy:  {hits}/{total}  ({hits / total:.0%})")
    for level in ("easy", "medium", "hard"):
        group = scores[scores["difficulty"] == level]
        if len(group):
            print(f"  {level:<7} {(group['status'] == 'hit').sum()}/{len(group)}")
    print(f"Ranked too low:   {(scores['status'] == 'low').sum()}  (search problem)")
    print(f"Not in database:  {(scores['status'] == 'missing').sum()}  (data problem: tell Person 2)")


if __name__ == "__main__":
    main()
