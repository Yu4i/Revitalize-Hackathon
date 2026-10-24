# ReFound team plan

**Goal:** someone types a fuzzy memory of a movie or show, and ReFound finds it, shows the poster, and says where to watch it today.

**Rule #1:** ship something working first, then improve it. Two finished features beat five half-built ones.

---

## Everyone: setup (do this first, ~30 min)

1. **Accept the GitHub invite** (check your email or github.com/notifications).
2. **Install the tools** (skip any you already have):
   - **Python 3.12** from [python.org/downloads](https://www.python.org/downloads/). 3.12 is the safest version for the AI libraries.
   - **VS Code** from [code.visualstudio.com](https://code.visualstudio.com/)
   - **Git**: open the Terminal app and run `xcode-select --install`
3. **Clone the repo in VS Code:** press `Cmd+Shift+P`, type **Git: Clone**, choose **Clone from GitHub**, sign in, and pick **Yu4i/Revitalize-Hackathon**. Open it when asked.
4. **Open the VS Code terminal** (`Ctrl+backtick`) and run:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
5. In the browser tab that opens, type *"a kid found a watch that turned him into aliens"*. **Ben 10 should come first.** If it does, you're set up. ✅

Every time you reopen the project, run `source .venv/bin/activate` before anything else.

---

## How we work with Git (every task)

1. Pull the latest code: **Source Control panel ▸ ... ▸ Pull** (or `git pull`)
2. Make a branch: click the branch name in the bottom-left corner ▸ **Create new branch** ▸ name it like `data/tmdb-import` or `ui/posters`
3. Code, then in **Source Control** write a short message and click **Commit**, then **Publish Branch** / **Sync**
4. On GitHub, click **Compare & pull request**. A teammate reviews and clicks **Approve**, then **Squash and merge**.
5. Merge small and often (every 2 to 3 hours). Never commit `.env`.

---

## Person 1 (repo owner): Setup and Search Brain

**Tonight**
1. Unzip the starter files into your cloned repo folder (replace the existing README).
2. Make a branch `setup/starter`, commit everything, push, and open a pull request. Ask a teammate to approve and merge. This is everyone's practice run.
3. Make sure both teammates can complete the setup steps above.

**During the hackathon**
4. **Build a test list:** write 20 realistic fuzzy memories with the right answer for each (e.g. *"show about a sponge who lives under the sea"* ▸ SpongeBob). Once the real data is in, check how many land in the top 5. This is your scoreboard, and it makes a great slide.
5. **Tune the search** in `search.py`:
   - Try the bigger model `all-mpnet-base-v2` (more accurate, slower). Compare with your test list. Keep whichever wins.
   - Try changing what goes into `searchable_text()`, e.g. leaving the title out.
6. **"Add more clues" button:** after results show, let the user type an extra detail ("it was animated", "there was a talking cat") that gets added to their original memory before searching again. Look up `st.session_state` in the Streamlit docs to remember the first memory.

**Learn:** [Streamlit "Get started" tutorial](https://docs.streamlit.io/get-started), [Sentence Transformers quickstart](https://www.sbert.net/docs/quickstart.html)

---

## Person 2: Data

Your job is the database. Search quality depends almost entirely on it.

1. **Get a TMDB key:** sign up at [themoviedb.org](https://www.themoviedb.org/signup), then go to **Settings ▸ API**, request a free developer key, and copy the **API Read Access Token** (the long one).
2. In the project folder, copy `.env.example` to a new file named `.env` and paste the token after `TMDB_TOKEN=`.
3. Make a branch `data/tmdb-import`, then run:
   ```bash
   python build_dataset.py
   ```
   This downloads about 2,000 to 3,000 movies and shows (with extra cartoons and kids' TV, since that's what people are nostalgic about) and creates `media.csv` and `embeddings.npy`.
4. Run `streamlit run app.py` and test some memories. Commit `media.csv` and `embeddings.npy` (**not** `.env`), push, and open a pull request.
5. **Grow it:** run `python build_dataset.py --pages 150` for many more titles. Check that the app still starts quickly, then open another PR.
6. **Clean it:** open `media.csv` and look for junk (missing years, non-English titles, very short descriptions). Add filters in `build_dataset.py` to remove them.
7. **Stretch:** add TMDB *keywords* for each title (the `/movie/{id}/keywords` endpoint) into a `keywords` column. The search already uses that column if it exists, and keywords like "time travel" or "talking animal" help a lot.

**Learn:** [TMDB API getting started](https://developer.themoviedb.org/docs/getting-started), [pandas in 10 minutes](https://pandas.pydata.org/docs/user_guide/10min.html)

---

## Person 3: Face and Ship

Your job is that judges can open the app on their phone and love it.

1. **Deploy in the first hour**, even with the sample data:
   - Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub, click **Create app**, pick the repo, branch `main`, file `app.py`, and deploy.
   - Every merge to `main` updates the live site automatically. If the deploy fails, tell the team right away: it's much easier to fix now than at hour 35.
   - When Person 2 has a TMDB token, add it in the app's **Settings ▸ Secrets** as `TMDB_TOKEN = "..."`.
2. **"Where is it now?"** This is what makes ReFound *revitalize* media. Create `where_now.py` with a function that takes a `tmdb_id` and type and calls:
   - `/movie/{id}/watch/providers` or `/tv/{id}/watch/providers`
   - Read `results["CA"]["flatrate"]` for streaming services in Canada (also check `rent` and `buy`). Each provider has a name and a `logo_path`.
   - Show the logos under each result where `app.py` says `TODO (Person 3)`.
   - Read the key with `st.secrets["TMDB_TOKEN"]` online, or from `.env` locally.
   - TMDB's streaming data comes from JustWatch, so add *"Streaming data by JustWatch"* in the footer.
   - Use `@st.cache_data` on the function so the same title isn't looked up twice.
3. **Polish the look:** app name and tagline, nice result cards, test on your phone.
4. **Own the demo:** write a 3-minute demo script with 3 great example searches, make a few slides (problem, demo, how the AI works, what's next), and practise it twice.

**Learn:** [Streamlit Community Cloud deploy guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app), [TMDB watch providers](https://developer.themoviedb.org/reference/movie-watch-providers)

---

## Stretch (whoever finishes first): Akinator mode
When search returns several close matches, an AI (e.g. the free Gemini API) looks at the top 10 and asks **one yes/no question** that best splits them ("Was it animated?"). The answer re-ranks the list. Repeat until one title clearly wins. Only start this after milestones 1 to 3 are live.

---

## Milestones
| By hour | Done when |
|---|---|
| 2 | Everyone runs the app locally, and it's deployed on Streamlit Cloud |
| 8 | Real TMDB data is live on the deployed site |
| 16 | Posters, where-to-watch, and "add more clues" all work |
| 26 | Stretch: Akinator mode |
| 32 | **Code freeze.** Bug fixes only |
| 36 | Demo practised twice and project submitted |
