"""Re-compute embeddings.npy from media.csv, without re-downloading anything.

Run this after:
  - add_keywords.py
  - changing MODEL_NAME in search.py
  - changing searchable_text() in search.py

Then commit media.csv + embeddings.npy so the live site gets them.
"""
import numpy as np
from sentence_transformers import SentenceTransformer

from search import EMBEDDINGS, FULL_DATA, MODEL_NAME, read_media, searchable_text

media = read_media(FULL_DATA)
texts = media.apply(searchable_text, axis=1).tolist()

print(f"Embedding {len(texts)} titles with {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)
embeddings = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True)

np.save(EMBEDDINGS, embeddings.astype(np.float32))
print(f"Saved {EMBEDDINGS.name}: {embeddings.shape[0]} titles x {embeddings.shape[1]} numbers each")
