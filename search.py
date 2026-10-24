"""ReFound search engine.

Turns every title's description into an embedding (a list of numbers that
captures its meaning), then finds the titles closest in meaning to what the
user remembers.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer

HERE = Path(__file__).parent
MODEL_NAME = "all-MiniLM-L6-v2"

# Use the real database once build_dataset.py has created it,
# otherwise fall back to the 8-title sample so the app always runs.
FULL_DATA = HERE / "media.csv"
SAMPLE_DATA = HERE / "sample_media.csv"
EMBEDDINGS = HERE / "embeddings.npy"


def searchable_text(row) -> str:
    """Everything we know about a title, as one string for the AI to read."""
    fields = ("title", "genres", "keywords", "description")
    return ". ".join(str(row[f]) for f in fields if f in row and str(row[f]).strip())


@st.cache_resource(show_spinner="Loading the AI model (first run downloads it)...")
def load_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


@st.cache_resource(show_spinner="Loading the media database...")
def load_index():
    """Load the media table and its embeddings (computed once, then cached)."""
    data_file = FULL_DATA if FULL_DATA.exists() else SAMPLE_DATA
    media = pd.read_csv(data_file).fillna("")

    # Fast path: embeddings pre-computed by build_dataset.py
    if data_file == FULL_DATA and EMBEDDINGS.exists():
        embeddings = np.load(EMBEDDINGS)
        if len(embeddings) == len(media):
            return media, embeddings

    # Slow path: compute them now (fine for small data)
    texts = media.apply(searchable_text, axis=1).tolist()
    embeddings = load_model().encode(texts, normalize_embeddings=True)
    return media, embeddings


def search_media(query: str, media_type: str = "All", year_range=None, top_k: int = 5):
    """Return the top_k titles whose meaning is closest to the user's memory."""
    media, embeddings = load_index()
    query_vec = load_model().encode(query, normalize_embeddings=True)

    # Vectors are normalized, so a dot product = cosine similarity (-1 to 1)
    results = media.copy()
    results["score"] = embeddings @ query_vec

    if media_type != "All":
        results = results[results["type"] == media_type]

    if year_range:
        low, high = year_range
        years = pd.to_numeric(results["year"], errors="coerce")
        results = results[years.between(low, high) | years.isna()]

    return results.sort_values("score", ascending=False).head(top_k)
