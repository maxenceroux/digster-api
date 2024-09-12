import asyncio
from datetime import datetime
import time
from typing import Any, Dict, Optional, Sequence


from celery import Celery
import os
import logging
from digster_api.digster_db import DigsterDB
from digster_api.dominant_color_finder import ColorFinder
from digster_api.models import Album, Artist, Genre, Style, UserAlbum
from digster_api.discogs_controller import DiscogsController
from digster_api.spotify_controller import SpotifyController

celery_color = Celery(__name__)
celery_genre = Celery(__name__)
celery_color.conf.broker_url = os.environ.get(
    "CELERY_BROKER_URL", "redis://localhost:6379"
)
celery_color.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379"
)
celery_genre.conf.broker_url = os.environ.get(
    "CELERY_BROKER_URL", "redis://localhost:6379"
)
celery_genre.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379"
)


async def get_albums_dominant_color():
    albums_query = f"""
    SELECT image_url, id
    FROM albums
    WHERE albums.primary_color is null
    
    """
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        albums = db.run_select_query(albums_query)
        print(len(albums))
        cf = ColorFinder()
        i = 1
        for album in albums:
            print(
                f"getting colors {i} out of {len(albums)}, {round(i/len(albums)*100,1)}%"
            )
            try:
                dominant_color = cf.get_dominant_color(album["image_url"])
            except Exception:
                dominant_color = ["#FFFFF", "#00000"]
            try:
                db.update_color_album(album["id"], dominant_color)
            except:
                print("could not update album color")
            db.update_fetched_colors_date(album["id"])
            i += 1
    return True


async def get_album_genres():
    ungenred_albums = f"""
    SELECT distinct ALBUMS.ID,
	ARTISTS.NAME ARTIST_NAME,
	ALBUMS.NAME ALBUM_NAME
    FROM ALBUMS
    LEFT JOIN ARTISTS ON ARTISTS.ID = ARTIST_ID
    WHERE FETCHED_GENRES_DATE IS NULL
    """
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        ungenred_albums_dict = db.run_select_query(ungenred_albums)
        print(len(ungenred_albums_dict))
        discogs_client = DiscogsController(
            user_token=str(os.environ.get("DISCOGS_TOKEN"))
        )
        i = 1
        for ungenred_album in ungenred_albums_dict:
            print(
                f"getting genres {i} out of {len(ungenred_albums_dict)}, {round(i/len(ungenred_albums_dict)*100,1)}% - {ungenred_album['album_name']}, {ungenred_album['artist_name']}"
            )
            album_tags = discogs_client.get_album_genre(
                ungenred_album["album_name"], ungenred_album["artist_name"]
            )
            if album_tags:
                if album_tags.get("genres"):
                    for genre in album_tags.get("genres"):
                        genre_id = db.insert_genre(genre)
                        album_genre = {
                            "genre_id": genre_id,
                            "album_id": ungenred_album["id"],
                        }
                        db.insert_album_genre(album_genre)
                if album_tags.get("styles"):
                    for style in album_tags.get("styles"):
                        style_id = db.insert_style(style)
                        album_style = {
                            "style_id": style_id,
                            "album_id": ungenred_album["id"],
                        }
                        db.insert_album_style(album_style)
            db.update_fetched_genres_date(ungenred_album["id"])
            i += 1


@celery_genre.task(name="fetch_albums_genres")
def fetch_albums_genres_worker():
    logging.info("Getting genres")
    asyncio.run(get_album_genres())
    return True


@celery_color.task(name="fetch_albums_color")
def fetch_albums_color_worker():
    logging.info("INSERTING COLORS")
    asyncio.run(get_albums_dominant_color())
    return True


@celery_color.task(name="fetch_album_data")
def fetch_album_data_worker(user_id):
    asyncio.run(fetch_albums_data(user_id))
    # fetch_albums_genres_worker.delay()
    # fetch_albums_color_worker.delay()
    return True
