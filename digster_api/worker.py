import asyncio
from datetime import datetime
from typing import Any, Dict, Optional, Sequence


from celery import Celery
import os
import logging
from digster_api.digster_db import DigsterDB
from digster_api.dominant_color_finder import ColorFinder
from digster_api.models import Album, Artist, Genre, Style, UserAlbum
from digster_api.selenium_scrapper import SeleniumScrapper

from digster_api.spotify_controller import SpotifyController

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get(
    "CELERY_BROKER_URL", "redis://localhost:6379"
)
celery.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379"
)


def get_albums_dominant_color():
    albums_query = f"""
    SELECT image_url, id
    FROM albums
    WHERE albums.primary_color is null
    
    """
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    albums = db.run_select_query(albums_query)
    cf = ColorFinder()
    for album in albums:
        print(album["image_url"])
        try:
            dominant_color = cf.get_dominant_color(album["image_url"])
        except Exception:
            dominant_color = ["#FFFFF", "#00000"]
        db.update_color_album(album["id"], dominant_color)
    db.close_conn()
    return albums_query


def get_album_genres():
    ungenred_albums = f"""
    SELECT ALBUMS.ID,
	ARTISTS.NAME ARTIST_NAME,
	ALBUMS.NAME ALBUM_NAME
    FROM ALBUMS
    LEFT JOIN ARTISTS ON ARTISTS.SPOTIFY_ID = ARTIST_ID
    LEFT JOIN ALBUM_STYLES ON ALBUMS.ID = ALBUM_STYLES.ALBUM_ID
    LEFT JOIN ALBUM_GENRES ON ALBUMS.ID = ALBUM_GENRES.ALBUM_ID
    WHERE ALBUM_STYLES.ID IS NULL
        and ALBUM_GENRES.ID IS NULL
    """
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    ungenred_albums_dict = db.run_select_query(ungenred_albums)
    scrapper = SeleniumScrapper(
        str(os.environ.get("SPOTIFY_USER")),
        str(os.environ.get("SPOTIFY_PWD")),
        str(os.environ.get("CHROME_DRIVER")),
    )

    chunk_size = 20
    chunks = [
        ungenred_albums_dict[x : x + chunk_size]
        for x in range(0, len(ungenred_albums_dict), chunk_size)
    ]
    for chunk in chunks:
        album_genres_styles = scrapper.get_album_genres(chunk)
        for album_genre_style in album_genres_styles:
            for genre in album_genre_style["genres"]:
                if (
                    db.session.query(Genre.id).filter_by(genre=genre).first()
                    is None
                ):
                    db.insert_genre(genre)
                genre_id = (
                    db.session.query(Genre.id)
                    .filter_by(genre=genre)
                    .first()[0]
                )
                album_genre = {
                    "genre_id": genre_id,
                    "album_id": album_genre_style["album_id"],
                }
                db.insert_album_genre(album_genre)
            for style in album_genre_style["styles"]:
                if (
                    db.session.query(Style.id).filter_by(style=style).first()
                    is None
                ):
                    db.insert_style(style)
                style_id = (
                    db.session.query(Style.id)
                    .filter_by(style=style)
                    .first()[0]
                )
                album_style = {
                    "style_id": style_id,
                    "album_id": album_genre_style["album_id"],
                }
                db.insert_album_style(album_style)

    return album_genres_styles


def insert_untracked_albums():
    untracked_albums_query = f"""
    SELECT DISTINCT ALBUM_SPOTIFY_ID
    FROM USER_ALBUMS
    LEFT JOIN ALBUMS ON USER_ALBUMS.ALBUM_SPOTIFY_ID = ALBUMS.SPOTIFY_ID
    WHERE ALBUMS.SPOTIFY_ID IS NULL and ALBUM_SPOTIFY_ID is not null
    
    """
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    spotify_client = SpotifyController(
        str(os.environ.get("SPOTIFY_CLIENT_ID")),
        str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    spotify_token = spotify_client.get_unauth_token()
    untracked_albums_dict = db.run_select_query(untracked_albums_query)
    untracked_albums = [
        result_tuple["album_spotify_id"]
        for result_tuple in untracked_albums_dict
    ]
    if not untracked_albums:
        return []
    albums = []

    all_albums: Dict[str, Any] = {}
    all_albums["albums"] = []
    for i in range(0, len(untracked_albums), 10):
        accepted_len_untracked_albums = untracked_albums[i : i + 10]

        albums_info = spotify_client.get_albums_info(
            token=spotify_token, album_ids=accepted_len_untracked_albums
        )

        if albums_info.get("albums"):
            for album in albums_info.get("albums"):
                album.update({"created_at": datetime.now()})
                albums.append(Album(**album))
    db.insert_albums(albums)
    db.close_conn()
    return True


def insert_untracked_artists() -> Sequence[Optional[Artist]]:
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    untracked_artists_query = """
    SELECT DISTINCT ARTIST_ID
    FROM ALBUMS
    LEFT JOIN ARTISTS ON ALBUMS.ARTIST_ID = ARTISTS.SPOTIFY_ID
    WHERE ARTISTS.SPOTIFY_ID IS NULL
    """
    untracked_artists_dict = db.run_select_query(untracked_artists_query)
    untracked_artists = [
        result_tuple["artist_id"] for result_tuple in untracked_artists_dict
    ]
    if not untracked_artists:
        return []

    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_CLIENT_ID")),
        client_secret=str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    spotify_token = spotify_client.get_unauth_token()
    for i in range(0, len(untracked_artists), 49):
        accepted_len_untracked_artists = untracked_artists[i : i + 49]
        artists_info = spotify_client.get_artists_info(
            token=spotify_token, artist_ids=accepted_len_untracked_artists
        )
        artists = []
        for artist in artists_info["artists"]:
            artist.update({"created_at": datetime.now()})
            artists.append(Artist(**artist))
        db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
        db.insert_artists(artists)
    return artists


async def fetch_albums_data(token: str):
    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_USER")),
        client_secret=str(os.environ.get("SPOTIFY_PASSWORD")),
    )
    user_id = spotify_client.get_user_info(token).get("id")
    results = spotify_client.get_user_saved_albums(
        token=token, user_spotify_id=user_id
    )
    albums = results.get("albums")
    user_albums = results.get("user_albums")
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    for user_album in user_albums:
        if (
            db.session.query(UserAlbum.id)
            .filter_by(user_spotify_id=user_album.get("user_spotify_id"))
            .filter_by(album_spotify_id=user_album.get("album_spotify_id"))
            .first()
            is None
        ):
            db.insert_user_album(user_album)
    logging.info("INSERTING ALBUMS")
    insert_untracked_albums()
    logging.info("INSERTING ARTISTS")
    insert_untracked_artists()
    logging.info("INSERTING GENRES")
    get_album_genres()
    logging.info("INSERTING COLORS")
    get_albums_dominant_color()


@celery.task(name="fetch_artist_data")
def fetch_album_data_worker(token):
    asyncio.run(fetch_albums_data(token))
    return True
