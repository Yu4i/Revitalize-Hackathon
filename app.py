"""ReFound website. Run with:  streamlit run app.py"""
import pandas as pd
import streamlit as st

from search import load_index, search_media
from where_now import get_streaming_providers

# Must be the first Streamlit command on the page
st.set_page_config(page_title="Lost Media", page_icon="", layout="centered")

st.title("Lost Media")
st.subheader("Bring forgotten media back to life.")
st.write("Describe a movie or show you barely remember.")

media, _ = load_index()

# ---- Filters ----
col1, col2 = st.columns(2)
media_type = col1.selectbox("What type?", ["All"] + sorted(media["type"].unique()))

years = pd.to_numeric(media["year"], errors="coerce").dropna().astype(int)
first, last = int(years.min()), int(years.max())
year_range = col2.slider("Roughly when did it come out?", first, last, (first, last))

memory = st.text_area(
    "What do you remember?",
    placeholder="A cartoon about a boy who found a watch that turned him into aliens...",
)

# ---- Search ----
# Streamlit re-runs this whole file on every click, which would forget
# everything. st.session_state survives re-runs, so the clues live there.
if "clues" not in st.session_state:
    st.session_state.clues = []

if st.button("Find My Media", type="primary"):
    if memory.strip():
        st.session_state.clues = [memory.strip()]  # a new search starts fresh
    else:
        st.warning("Type something you remember first.")

# ---- Add more clues ----
    st.markdown("#### Not it? Add another clue")
    with st.form("more_clues", clear_on_submit=True):
        clue = st.text_input(
            "Anything else you remember?",
            placeholder="It was animated / there was a talking cat / it came out in the 90s",
        )
        add_clue = st.form_submit_button("Search again")

    if add_clue and clue.strip():
        st.session_state.clues.append(clue.strip())
        st.rerun()

    if st.button("Start over"):
        st.session_state.clues = []
        st.rerun()


if st.session_state.clues:
    query = ". ".join(st.session_state.clues)
    with st.spinner("Searching your memories..."):
        results = search_media(query, media_type, year_range)

    if len(st.session_state.clues) > 1:
        st.caption("Your clues: " + " · ".join(st.session_state.clues))

    st.subheader("Possible matches")
    if results.empty:
        st.info("No matches. Try loosening the filters or adding more detail.")
    else:
        for _, row in results.iterrows():
            poster_col, text_col = st.columns([1, 3])

            poster = row.get("poster_url", "")
            if poster:
                poster_col.image(poster, width=140)
            else:
                poster_col.markdown("### 🎞️")

            # Show "2004", not "2004.0" (and nothing if the year is unknown)
            year = pd.to_numeric(row["year"], errors="coerce")
            year_text = f" ({int(year)})" if pd.notna(year) else ""
            text_col.markdown(f"### {row['title']}{year_text}")
            text_col.caption(f"{row['type']} · match score {row['score']:.2f}")
            text_col.write(row["description"])

            # ---- Where is it now? ----
            providers = None
            tmdb_id = row.get("tmdb_id", "")
            if pd.notna(tmdb_id) and str(tmdb_id).strip():  # the sample data has no TMDB ids
                providers = get_streaming_providers(row["tmdb_id"], row["type"])

            if not providers:
                pass  # no data: show nothing
            elif "error" in providers:
                # Only show the friendly message; technical errors stay hidden from users
                if providers["error"].startswith("Not streaming"):
                    text_col.caption(f"_{providers['error']}_")
            else:
                if providers.get("link"):
                    text_col.markdown(f"[**Watch Options (Canada)**]({providers['link']})")

                logos_md = ""
                seen_ids = set()
                # combine streaming, renting, and buying options without duplicate logos
                for category in ["flatrate", "rent", "buy"]:
                    for p in providers.get(category, []):
                        if p["provider_id"] not in seen_ids:
                            img_url = f"https://image.tmdb.org/t/p/w92{p['logo_path']}"
                            logos_md += f"![{p['provider_name']}]({img_url}) "
                            seen_ids.add(p["provider_id"])

                if logos_md:
                    text_col.markdown(logos_md)

            st.divider()

    
st.caption(
    "This product uses the TMDB API but is not endorsed or certified by TMDB. "
    "Streaming data by JustWatch."
)
