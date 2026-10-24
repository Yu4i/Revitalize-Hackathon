import os
import requests
import streamlit as st
from dotenv import load_dotenv

#load local environment variables from .env if  running locally
load_dotenv()

@st.cache_data(ttl=86400)
def get_streaming_providers(tmdb_id, media_type):
    token = os.getenv("TMDB_TOKEN")
    if not token:
        try:
            token = st.secrets.get("TMDB_TOKEN")
        except Exception:
            pass
            
    if not token:
        return {"error": "Local debug: Token is completely blank."}

    endpoint = "movie" if media_type == "Movie" else "tv"
    url = f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}/watch/providers"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": f"API Rejected: {response.status_code} - {response.text}"}
            
        ca_data = response.json().get("results", {}).get("CA")
        if not ca_data:
            return {"error": "Not streaming in Canada right now"}
            
        return {
            "flatrate": ca_data.get("flatrate", []),
            "rent": ca_data.get("rent", []),
            "buy": ca_data.get("buy", []),
            "link": ca_data.get("link")
        }
    except Exception as e:
        return {"error": f"Crash: {str(e)}"}