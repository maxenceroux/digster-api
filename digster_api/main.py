import os
from typing import Any, Dict, List

from fastapi import FastAPI

from digster_api.digster_db import DigsterDB
from digster_api.models import Listen
from digster_api.selenium_scrapper import SeleniumScrapper
from digster_api.spotify_controller import SpotifyController

app = FastAPI()


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Hello World"}


@app.get("/spotify_user_info")
def get_spotify_user_info() -> Dict[str, Any]:
    scrapper = SeleniumScrapper(
        str(os.environ.get("SPOTIFY_USER")),
        str(os.environ.get("SPOTIFY_PWD")),
        str(os.environ.get("CHROME_DRIVER")),
    )
    token = scrapper.get_token()
    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_CLIENT_ID")),
        client_secret=str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    user = spotify_client.get_user_info(token)
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    db.upsert_user(user)
    return user


@app.get("/get_recently_played_tracks")
def get_recently_played_tracks() -> List[Listen]:
    scrapper = SeleniumScrapper(
        str(os.environ.get("SPOTIFY_USER")),
        str(os.environ.get("SPOTIFY_PWD")),
        str(os.environ.get("CHROME_DRIVER")),
    )
    token = scrapper.get_token()
    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_CLIENT_ID")),
        client_secret=str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    user_id = spotify_client.get_user_info(token).get("id")
    tracks = spotify_client.get_recently_played(token, limit=10)
    listens = []
    for item in tracks["recently_played"]:
        item.update({"user_id": user_id})
        listens.append(Listen(**item))
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    db.insert_listens(listens)
    return listens
