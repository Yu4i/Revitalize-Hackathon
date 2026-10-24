"""ReFound website. Run with:  streamlit run app.py"""
import pandas as pd
import streamlit as st

from search import load_index, search_media

st.set_page_config(page_title="ReFound", page_icon="🔎", layout="centered")

st.title("🔎 ReFound")
st.subheader("Bring forgotten media back to life.")
st.write("Describe a movie, show, or game you barely remember.")

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

            text_col.markdown(f"### {row['title']} ({row['year']})")
            text_col.caption(f"{row['type']} · match score {row['score']:.2f}")
            text_col.write(row["description"])
            # TODO (Person 3): "Where is it now?" streaming links go here

            st.divider()

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

st.caption(
    "This product uses the TMDB API but is not endorsed or certified by TMDB."
)
