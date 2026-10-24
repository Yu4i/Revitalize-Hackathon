"""Lost Media website. Run with:  streamlit run app.py"""
import html
import time

import pandas as pd
import streamlit as st

import retro_fx
from search import load_index, search_media
from shelf import render_shelf
from where_now import get_streaming_providers

APP_NAME = "Lost Media"
TAGLINE = "Bring forgotten media back to life."



# Must be the first Streamlit command on the page
st.set_page_config(page_title=APP_NAME, page_icon="📼", layout="centered")

# ---- Retro VHS styling ----
# Colours live in .streamlit/config.toml; this adds fonts, the stripe band,
# tape-box result cards and the "Top pick" sticker.
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bungee&family=Atkinson+Hyperlegible:wght@400;700&display=swap');

.stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea {
    font-family: 'Atkinson Hyperlegible', sans-serif;
}

/* Hide Streamlit's own menu and footer so it looks like a real product */
#MainMenu, footer, [data-testid="stAppDeployButton"] { visibility: hidden; }

/* Hero: chunky title over the tape-sleeve stripe band */
.lm-hero { margin: 0.5rem 0 1.75rem; }
.lm-title {
    font-family: 'Bungee', sans-serif;
    font-size: clamp(2.4rem, 9vw, 4.2rem);
    line-height: 1;
    color: #F3E9D2;
    letter-spacing: 0.02em;
    margin: 0 0 0.6rem;
}
.lm-stripes { display: grid; gap: 4px; transform: skewX(-20deg); margin: 0 0 1rem 0.6rem; }
.lm-stripes span { display: block; height: 7px; }
.lm-stripes span:nth-child(1) { background: #FF6B35; width: 96%; }
.lm-stripes span:nth-child(2) { background: #F72585; width: 88%; }
.lm-stripes span:nth-child(3) { background: #7B2CBF; width: 80%; }
.lm-stripes span:nth-child(4) { background: #4CC9F0; width: 72%; }
.lm-tagline { font-size: 1.2rem; color: #B9A9D9; margin: 0; }

/* Main button: dark text on magenta for readable contrast */
button[kind="primary"], [data-testid="stBaseButton-primary"] {
    color: #1A1230 !important;
    font-weight: 700;
}

/* Tabs in the retro font */
[data-testid="stTabs"] button p { font-family: 'Bungee', sans-serif; font-size: 1rem; }

/* Result cards, styled like tape boxes on a shelf */
[class*="st-key-card-"] {
    background: #2A1F4A;
    border: 2px solid #3D2E66 !important;
    border-radius: 6px;
}
[class*="st-key-card-0-"] { border-color: #F72585 !important; }
[class*="st-key-card-"] [data-testid="stImage"] img { border-radius: 4px; }
[class*="st-key-card-"] .stMarkdown img,
[class*="st-key-spotlight"] .stMarkdown img { height: 34px; border-radius: 8px; margin: 0 4px 4px 0; }

.lm-sticker {
    display: inline-block;
    background: #FF6B35;
    color: #1A1230;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 3px;
    transform: rotate(-3deg);
    margin-bottom: 0.4rem;
}
.lm-card-title { font-family: 'Bungee', sans-serif; font-size: 1.35rem; line-height: 1.2; margin: 0.1rem 0 0.2rem; }
.lm-meta { color: #B9A9D9; margin: 0 0 0.5rem; }
.lm-chip {
    display: inline-block;
    border: 1px solid #7B2CBF;
    border-radius: 999px;
    padding: 1px 10px;
    margin: 0 6px 6px 0;
    color: #F3E9D2;
}
</style>
""",
    unsafe_allow_html=True,
)

# Retro effects: grid floor, PLAY boot screen, typewriter, static, rewind loader, glitch
retro_fx.inject()
retro_fx.boot_screen()

st.markdown(
    f"""
<div class="lm-hero">
  <div class="lm-title" role="heading" aria-level="1">{APP_NAME}</div>
  <div class="lm-stripes" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
  <p class="lm-tagline">{TAGLINE}</p>
</div>
""",
    unsafe_allow_html=True,
)

media, _ = load_index()

find_tab, shelf_tab = st.tabs(["Find a lost show", "Your childhood shelf"])

# ======================= Tab 2: Your childhood shelf =======================
with shelf_tab:
    render_shelf(media)

# ======================= Tab 1: Find a lost show =======================
with find_tab:
    # ---- Search state ----
    # Streamlit re-runs this whole file on every click, which would forget
    # everything. st.session_state survives re-runs, so the clues live there.
    if "clues" not in st.session_state:
        st.session_state.clues = []

    memory = st.text_area(
        "What do you remember?",
        key="memory",
        placeholder="A cartoon about a boy who found a watch that turned him into aliens...",
    )

    # ---- Filters (tucked away; most people won't need them) ----
    with st.expander("Narrow it down by type or year"):
        col1, col2 = st.columns(2)
        media_type = col1.selectbox("Type", ["All"] + sorted(media["type"].unique()))
        years = pd.to_numeric(media["year"], errors="coerce").dropna().astype(int)
        first, last = int(years.min()), int(years.max())
        year_range = col2.slider("Came out between", first, last, (first, last))

    if st.button("Find it", type="primary", width="stretch"):
        if memory.strip():
            st.session_state.clues = [memory.strip()]  # a new search starts fresh
        else:
            st.warning("Type something you remember first.")

    # ---- Results ----
    if st.session_state.clues:
        query = ". ".join(st.session_state.clues)
        search_key = (query, media_type, tuple(year_range))
        if st.session_state.get("last_search") != search_key:
            # A new search: show the VHS rewind loader, then reveal the results
            loader = st.empty()
            retro_fx.show_rewind(loader)
            results = search_media(query, media_type, year_range)
            time.sleep(retro_fx.REWIND_SECONDS)
            loader.empty()
            st.session_state.last_search = search_key
            st.session_state.search_id = st.session_state.get("search_id", 0) + 1
        else:
            # Same search as before (e.g. the page refreshed): no loader
            results = search_media(query, media_type, year_range)

        if len(st.session_state.clues) > 1:
            chips = "".join(f'<span class="lm-chip">{html.escape(c)}</span>' for c in st.session_state.clues)
            st.markdown(f"Your clues: {chips}", unsafe_allow_html=True)

        # ---- Add more clues (above the results) ----
        st.markdown("#### Remember more? Add a clue")
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

        st.subheader("Possible matches")
        if results.empty:
            st.info("No matches. Try loosening the filters or adding more detail.")
        else:
            for i, (_, row) in enumerate(results.iterrows()):
                # A new key per search makes the top card replay its glitch reveal
                with st.container(border=True, key=f"card-{i}-s{st.session_state.search_id}"):
                    poster_col, text_col = st.columns([1, 2.4])

                    poster = row.get("poster_url", "")
                    if poster:
                        poster_col.image(poster, width=150)
                    else:
                        poster_col.markdown("### 📼")

                    # Show "2004", not "2004.0" (and nothing if the year is unknown)
                    year = pd.to_numeric(row["year"], errors="coerce")
                    year_text = f", {int(year)}" if pd.notna(year) else ""

                    sticker = '<span class="lm-sticker">Top pick</span><br>' if i == 0 else ""
                    text_col.markdown(
                        f'{sticker}<div class="lm-card-title">{html.escape(str(row["title"]))}</div>'
                        f'<p class="lm-meta">{html.escape(str(row["type"]))}{year_text}</p>',
                        unsafe_allow_html=True,
                    )
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
                        if providers.get("link"):
                            text_col.markdown(f"[**Where to watch in Canada**]({providers['link']})")

st.divider()
st.caption(
    "This product uses the TMDB API but is not endorsed or certified by TMDB. "
    "Streaming data by JustWatch."
)
