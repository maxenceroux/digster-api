import logging
from digster_api.spotify_controller import SpotifyController
from digster_api.digster_db import DigsterDB
from digster_api.worker import (
    fetch_albums_genres_worker,
    fetch_albums_color_worker,
)
import os
from dotenv import load_dotenv

load_dotenv()


def fetch_albums_data(user_id: str):
    logging.info("INSERTING USER ALBUMS")
    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_CLIENT_ID")),
        client_secret=str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        user_id = str(user_id)
        user_tokens = db.get_user_spotify_tokens(user_id)
        limit = 50
        offset = 0
        while True:
            results = spotify_client.get_user_saved_albums_limit(
                tokens=user_tokens, limit=limit, offset=offset
            )
            print(
                f"Getting first {offset+50} out of {results.get('total_albums')} albums"
            )
            if not results.get("albums"):
                break
            for alb in results.get("albums"):
                artist_id = db.insert_artist(
                    spotify_id=alb.get("artist_spotify_id"),
                    name=alb.get("artist_name"),
                )
                album_id = db.insert_album(
                    spotify_id=alb.get("spotify_id"),
                    artist_id=artist_id,
                    type=alb.get("type"),
                    upc_id=alb.get("upc_id"),
                    label=alb.get("label"),
                    name=alb.get("name"),
                    release_date=alb.get("release_date"),
                    image_url=alb.get("image_url"),
                    genres=alb.get("genres"),
                    total_tracks=alb.get("total_tracks"),
                    popularity=alb.get("popularity"),
                )
                db.insert_user_album(user_id, album_id, alb.get("added_at"))
            offset += limit
        fetch_albums_genres_worker.delay()
        fetch_albums_color_worker.delay()
