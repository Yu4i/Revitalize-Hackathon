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
if st.button("Find My Media", type="primary"):
    if not memory.strip():
        st.warning("Type something you remember first.")
    else:
        with st.spinner("Searching your memories..."):
            results = search_media(memory, media_type, year_range)

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

st.caption(
    "This product uses the TMDB API but is not endorsed or certified by TMDB."
)
