"""ReFound search engine.

Turns every title's description into an embedding (a list of numbers that
captures its meaning), then finds the titles closest in meaning to what the
user remembers. Well-known titles get a small boost, because people
half-remember famous things far more often than obscure ones.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer

HERE = Path(__file__).parent
MODEL_NAME = "all-MiniLM-L6-v2"

# How much fame counts compared with meaning. 0 = ignore fame entirely.
# Tune it with:  python evaluate.py --boost 0,0.05,0.1,0.15,0.2
POPULARITY_BOOST = 0.25

# Use the real database once build_dataset.py has created it,
# otherwise fall back to the 8-title sample so the app always runs.
FULL_DATA = HERE / "media.csv"
SAMPLE_DATA = HERE / "sample_media.csv"
EMBEDDINGS = HERE / "embeddings.npy"


def read_media(path) -> pd.DataFrame:
    """Read the media table, filling blanks in text columns with ''."""
    media = pd.read_csv(path)
    for col in media.columns:
        if not pd.api.types.is_numeric_dtype(media[col]):
            media[col] = media[col].fillna("")
    return media


def popularity_scores(media: pd.DataFrame) -> np.ndarray:
    """0 to 1 per title, from TMDB vote counts (log scale). All zeros if unknown."""
    if "vote_count" not in media.columns:
        return np.zeros(len(media))
    votes = np.log1p(pd.to_numeric(media["vote_count"], errors="coerce").fillna(0).clip(lower=0))
    top = votes.max()
    return (votes / top).to_numpy() if top > 0 else np.zeros(len(media))


def searchable_text(row) -> str:
    """Everything we know about a title, as one string for the AI to read."""
    fields = ("title", "genres", "keywords", "description")
    return ". ".join(
        str(row[f]) for f in fields if f in row and pd.notna(row[f]) and str(row[f]).strip()
    )


@st.cache_resource(show_spinner="Loading the AI model (first run downloads it)...")
def load_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


@st.cache_resource(show_spinner="Loading the media database...")
def load_index():
    """Load the media table and its embeddings (computed once, then cached)."""
    data_file = FULL_DATA if FULL_DATA.exists() else SAMPLE_DATA
    media = read_media(data_file)
    media["popularity"] = popularity_scores(media)

    # Fast path: embeddings pre-computed by build_dataset.py / rebuild_embeddings.py.
    # Only used if they match this data AND this model (models differ in size).
    if data_file == FULL_DATA and EMBEDDINGS.exists():
        embeddings = np.load(EMBEDDINGS)
        model_size = load_model().encode("test").shape[-1]
        if len(embeddings) == len(media) and embeddings.shape[1] == model_size:
            return media, embeddings

    # Slow path: compute them now (fine for small data)
    texts = media.apply(searchable_text, axis=1).tolist()
    embeddings = load_model().encode(texts, normalize_embeddings=True)
    return media, embeddings


def search_media(query: str, media_type: str = "All", year_range=None, top_k: int = 5):
    """Return the top_k titles that best match the user's memory."""
    media, embeddings = load_index()
    query_vec = load_model().encode(query, normalize_embeddings=True)

    # Vectors are normalized, so a dot product = cosine similarity (-1 to 1).
    # Then add a small bonus for well-known titles.
    results = media.copy()
    results["score"] = embeddings @ query_vec + POPULARITY_BOOST * results["popularity"]

    if media_type != "All":
        results = results[results["type"] == media_type]

    if year_range:
        low, high = year_range
        years = pd.to_numeric(results["year"], errors="coerce")
        results = results[years.between(low, high) | years.isna()]

    return results.sort_values("score", ascending=False).head(top_k)
