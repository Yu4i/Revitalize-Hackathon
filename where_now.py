import os
import requests
import streamlit as st
from dotenv import load_dotenv

#load local environment variables from .env if  running locally
load_dotenv()

@st.cache_data(ttl=86400) # cache the results for 24 hours to keep the app fast
def get_streaming_providers(tmdb_id, media_type):
    #try getting the token locally first, then fallback to Streamlit secrets
    token = os.getenv("TMDB_TOKEN")
    if not token:
        try:
            token = st.secrets["TMDB_TOKEN"]
        except Exception:
            return None

    #TMDB uses diffrent URLs for movies vs TV shows
    endpoint = "movie" if media_type == "Movie" else "tv"
    url = f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}/watch/providers"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer [token]"

    }

    try:
        response = requests.get(url, headers = headers)
        if response.status_code != 200:
            return None

        data = response.json()

        #look specifically for Canadian (CA) streaming rights
        ca_data = data,get("results", {}).get("CA")

        if not ca_data:
            return {"error": "Not streaming in Canada right now"}

        # return the streaming, renting, buying options, and the TMDB link
        return {
            "flatrate": ca_data.get("flatrate", []),
            "rent": ca_data.get("rent", []),
            "buy": ca_data.get("buy", []),
            "link": ca_data.get("Link")
        }

    except requests.RequestException:
        #If the API crashes or is slowm fail 
        return None