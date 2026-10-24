"""Your childhood shelf: the most-loved shows and movies from when you were a kid.

Type a birth year and see the biggest titles from ages 5 to 12, laid out like
a video-store shelf. "Surprise me" pulls one tape off the shelf at random.
Uses data we already have (year, genres, popularity), so nothing new to fetch.
"""
import html
import random

import pandas as pd
import streamlit as st

from where_now import get_streaming_providers

FIRST_AGE, LAST_AGE = 5, 12          # the "childhood" window
PER_SHELF = 10                        # titles per shelf
PER_ROW = 5                           # posters per shelf row
# Kid-friendly genres. On TV, "Animation" alone lets in adult cartoons, so TV uses Kids/Family.
KID_GENRES = {"Movie": ("Animation", "Family"), "TV Show": ("Kids", "Family")}

SHELF_CSS = """
<style>
/* Each row of posters sits on a shelf ledge */
[class*="st-key-shelf-row-"] {
    border-bottom: 10px solid #3D2E66;
    border-radius: 0 0 4px 4px;
    padding: 0.5rem 0.25rem 0.75rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 0 -4px #120C22;
}
[class*="st-key-shelf-row-"] [data-testid="stImage"] img { border-radius: 4px; }
.lm-shelf-title { font-weight: 700; line-height: 1.2; margin: 0.35rem 0 0; }
.lm-shelf-year { color: #B9A9D9; margin: 0; }
.lm-shelf-head { font-family: 'Bungee', sans-serif; font-size: 1.3rem; margin: 0.5rem 0 0.75rem; }
.st-key-spotlight {
    background: #2A1F4A;
    border: 2px solid #4CC9F0 !important;
    border-radius: 6px;
}
</style>
"""


def childhood_titles(media: pd.DataFrame, birth_year: int, kind: str, kids_only: bool) -> pd.DataFrame:
    """The most popular titles of one type that came out between ages 5 and 12."""
    years = pd.to_numeric(media["year"], errors="coerce")
    picks = media[years.between(birth_year + FIRST_AGE, birth_year + LAST_AGE) & (media["type"] == kind)]
    if kids_only:
        picks = picks[picks["genres"].astype(str).str.contains("|".join(KID_GENRES.get(kind, ("Family",))), na=False)]
    if "popularity" in picks.columns:
        picks = picks.sort_values("popularity", ascending=False)
    return picks.head(PER_SHELF)


def _year_text(row) -> str:
    year = pd.to_numeric(row["year"], errors="coerce")
    return str(int(year)) if pd.notna(year) else ""


def _where_to_watch(container, row):
    """Streaming logos and link for one title (same rules as the search results)."""
    tmdb_id = row.get("tmdb_id", "")
    if not (pd.notna(tmdb_id) and str(tmdb_id).strip()):
        return
    providers = get_streaming_providers(row["tmdb_id"], row["type"])
    if not providers:
        return
    if "error" in providers:
        if providers["error"].startswith("Not streaming"):
            container.caption(f"_{providers['error']}_")
        return
    logos, seen = "", set()
    for category in ["flatrate", "rent", "buy"]:
        for p in providers.get(category, []):
            if p["provider_id"] not in seen:
                logos += f"![{p['provider_name']}](https://image.tmdb.org/t/p/w92{p['logo_path']}) "
                seen.add(p["provider_id"])
    if logos:
        container.markdown(logos)
    if providers.get("link"):
        container.markdown(f"[**Where to watch in Canada**]({providers['link']})")


def _shelf(titles: pd.DataFrame, name: str):
    """Posters in rows of 5, each row on its own shelf ledge."""
    for r in range(0, len(titles), PER_ROW):
        chunk = titles.iloc[r:r + PER_ROW]
        with st.container(key=f"shelf-row-{name}-{r}"):
            cols = st.columns(PER_ROW)
            for col, (_, row) in zip(cols, chunk.iterrows()):
                poster = row.get("poster_url", "")
                if poster:
                    col.image(poster)
                else:
                    col.markdown("### 📼")
                col.markdown(
                    f'<p class="lm-shelf-title">{html.escape(str(row["title"]))}</p>'
                    f'<p class="lm-shelf-year">{_year_text(row)}</p>',
                    unsafe_allow_html=True,
                )


def _spotlight(row):
    """One title pulled off the shelf, shown big with where to watch it."""
    with st.container(border=True, key="spotlight"):
        poster_col, text_col = st.columns([1, 2.4])
        poster = row.get("poster_url", "")
        if poster:
            poster_col.image(poster, width=150)
        text_col.markdown(
            '<span class="lm-sticker">Remember this one?</span><br>'
            f'<div class="lm-card-title">{html.escape(str(row["title"]))}</div>'
            f'<p class="lm-meta">{html.escape(str(row["type"]))}, {_year_text(row)}</p>',
            unsafe_allow_html=True,
        )
        text_col.write(row["description"])
        _where_to_watch(text_col, row)


def render_shelf(media: pd.DataFrame):
    st.markdown(SHELF_CSS, unsafe_allow_html=True)
    st.markdown("#### What were you watching as a kid?")

    col1, col2 = st.columns([1, 1.4])
    birth_year = col1.number_input(
        "Your birth year", min_value=1950, max_value=2020, value=None, step=1, placeholder="e.g. 2006"
    )
    kids_only = col2.toggle("Cartoons and family picks only", value=True)

    if birth_year is None:
        st.info("Enter your birth year to pull your childhood off the shelf.")
        return

    birth_year = int(birth_year)
    start, end = birth_year + FIRST_AGE, birth_year + LAST_AGE
    st.caption(f"Ages {FIRST_AGE} to {LAST_AGE}: everything that came out from {start} to {end}, most-loved first.")

    shows = childhood_titles(media, birth_year, "TV Show", kids_only)
    movies = childhood_titles(media, birth_year, "Movie", kids_only)
    pool = pd.concat([shows, movies])

    if pool.empty:
        st.info("Nothing on this shelf yet. Try turning off \"Cartoons and family picks only\", or a different year.")
        return

    # ---- Surprise me: pull one random tape off the shelf ----
    if st.button("Surprise me", type="primary", width="stretch"):
        st.session_state.spotlight = random.choice(pool.index.tolist())
    pick = st.session_state.get("spotlight")
    if pick in pool.index:  # only show it if it's on the current shelf
        _spotlight(pool.loc[pick])

    if not shows.empty:
        st.markdown('<p class="lm-shelf-head">Shows you grew up with</p>', unsafe_allow_html=True)
        _shelf(shows, "tv")
    if not movies.empty:
        st.markdown('<p class="lm-shelf-head">Movies you grew up with</p>', unsafe_allow_html=True)
        _shelf(movies, "movies")
