"""Score ReFound's search against test_memories.csv.

Run:  python evaluate.py
      python evaluate.py --top 10        (count a hit anywhere in the top 10)

Prints where the right answer ranked for each memory, then the overall
accuracy. Run it before and after every search change to see if it helped.
"""
import argparse
import re
import unicodedata

import pandas as pd

from search import search_media


def normalize(title: str) -> str:
    """'Pokémon' -> 'pokemon', 'Monsters, Inc.' -> 'monstersinc'."""
    text = unicodedata.normalize("NFKD", str(title)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.lower())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

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
    rows = []

    for _, t in tests.iterrows():
        accepted = {normalize(t["answer"])}
        accepted |= {normalize(a) for a in t["also_accept"].split(";") if a.strip()}

        results = search_media(t["memory"], top_k=args.top)
        titles = results["title"].tolist()
        rank = next((i + 1 for i, title in enumerate(titles) if normalize(title) in accepted), None)

        mark = f"#{rank}" if rank else "miss"
        print(f"{mark:>5}  [{t['difficulty']:<6}] {t['answer']}")
        if rank != 1:
            print(f"        got: {', '.join(titles[:3])}")
        rows.append({"difficulty": t["difficulty"], "rank": rank})

    scores = pd.DataFrame(rows)
    total = len(scores)
    top1 = (scores["rank"] == 1).sum()
    topn = scores["rank"].notna().sum()

    print("\n" + "=" * 40)
    print(f"Top 1 accuracy:  {top1}/{total}  ({top1 / total:.0%})")
    print(f"Top {args.top} accuracy:  {topn}/{total}  ({topn / total:.0%})")
    for level in ("easy", "medium", "hard"):
        group = scores[scores["difficulty"] == level]
        if len(group):
            print(f"  {level:<7} {group['rank'].notna().sum()}/{len(group)}")


if __name__ == "__main__":
    main()
