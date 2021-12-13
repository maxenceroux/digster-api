import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from fastapi import FastAPI

from digster_api.digster_db import DigsterDB
from digster_api.models import Listen, Track
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


@app.get("/get_tracks_info")
def get_tracks_info() -> Sequence[Optional[Track]]:
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    untracked_tracks_query = """
    SELECT DISTINCT TRACK_ID
    FROM LISTENS
    LEFT JOIN TRACKS ON TRACKS.SPOTIFY_ID = LISTENS.TRACK_ID
    WHERE TRACKS.SPOTIFY_ID IS NULL
    """
    untracked_tracks_dict = db.run_select_query(untracked_tracks_query)
    untracked_tracks = [
        result_tuple["track_id"] for result_tuple in untracked_tracks_dict
    ]
    if not untracked_tracks:
        return []
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
    tracks_info = spotify_client.get_tracks_info(
        token=token, track_ids=untracked_tracks
    )
    tracks_features = spotify_client.get_tracks_attributes(
        token=token, track_ids=untracked_tracks
    )
    tracks_dict = [
        {**features, **infos}
        for features, infos in zip(
            tracks_info["tracks_info"],
            tracks_features["audio_features"],
        )
    ]
    tracks = []
    for track in tracks_dict:
        track.update({"created_at": datetime.now()})
        tracks.append(Track(**track))
    print(tracks)
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    db.insert_tracks(tracks)
    return tracks
