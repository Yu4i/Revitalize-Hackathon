# 🔎 ReFound

**Bring forgotten media back to life.** Describe a movie or TV show you barely remember, and ReFound finds it, shows you the poster, and tells you where you can watch it today.

Built in 36 hours for the "Revitalize" hackathon.

## How it works
ReFound uses an open-source AI model ([Sentence Transformers](https://www.sbert.net/), `all-MiniLM-L6-v2`) to turn every title's description into an *embedding*: a list of numbers that captures its meaning. Your memory gets turned into an embedding too, and ReFound returns the titles closest in meaning. So "a kid with a watch that turns him into aliens" finds *Ben 10* even though none of those words are in its description.

## Run it on your Mac
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
The first run downloads the AI model (about 90 MB), so give it a minute.

Without `media.csv` the app uses an 8-title sample. To build the real database, see `build_dataset.py`.

## Files
| File | What it does |
|---|---|
| `app.py` | The website (Streamlit) |
| `search.py` | The matching engine |
| `build_dataset.py` | Downloads titles from TMDB and pre-computes embeddings |
| `sample_media.csv` | Tiny test dataset |
| `media.csv`, `embeddings.npy` | The real database (created by `build_dataset.py`) |

## Team
See [TEAM_PLAN.md](TEAM_PLAN.md).

## Credits
- Movie and TV data and posters: [TMDB](https://www.themoviedb.org/). This product uses the TMDB API but is not endorsed or certified by TMDB.
- Embedding model: [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (Apache 2.0)
