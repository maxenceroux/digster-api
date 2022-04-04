import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from fastapi import FastAPI

from digster_api.digster_db import DigsterDB
from digster_api.models import Album, Artist, Genre, Listen, Style, Track, UserAlbum
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
    token = scrapper.get_spotify_token()
    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_CLIENT_ID")),
        client_secret=str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    user = spotify_client.get_user_info(token)
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    db.upsert_user(user)
    return user


@app.post("/recently_played_tracks/")
def get_recently_played_tracks(after: int, before: int) -> List[Listen]:
    scrapper = SeleniumScrapper(
        str(os.environ.get("SPOTIFY_USER")),
        str(os.environ.get("SPOTIFY_PWD")),
        str(os.environ.get("CHROME_DRIVER")),
    )
    token = scrapper.get_spotify_token()
    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_CLIENT_ID")),
        client_secret=str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    user_id = spotify_client.get_user_info(token).get("id")
    tracks = spotify_client.get_recently_played(token, after=after)
    listens = []
    is_before = True
    while tracks.get("next_url") and is_before:
        for item in tracks["recently_played"]:
            if int(item.get("listened_at").timestamp() * 1000) > before:
                is_before = False
                break
            item.update({"user_id": user_id})
            listens.append(Listen(**item))
        next_url = tracks.get("next_url")
        tracks = spotify_client.get_recently_played(token, url=next_url)
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    db.insert_listens(listens)
    return listens

@app.get("/saved_albums")
def get_saved_albums():
    scrapper = SeleniumScrapper(
        str(os.environ.get("SPOTIFY_USER")),
        str(os.environ.get("SPOTIFY_PWD")),
        str(os.environ.get("CHROME_DRIVER")),
    )
    token = scrapper.get_spotify_token()
    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_USER")),
        client_secret=str(os.environ.get("SPOTIFY_PASSWORD")),
    )
    user_id = spotify_client.get_user_info(token).get("id")
    results=spotify_client.get_user_saved_albums(token=token ,user_spotify_id=user_id)
    albums = results.get("albums")
    user_albums = results.get("user_albums")
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    for user_album in user_albums:
        if db.session.query(UserAlbum.id).filter_by(user_spotify_id=user_album.get("user_spotify_id")).filter_by(album_spotify_id=user_album.get("album_spotify_id")).first() is None:
            db.insert_user_album(user_album)
    insert_untracked_albums()
    insert_untracked_artists()
    return albums


@app.get("/tracks_info")
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
    token = scrapper.get_spotify_token()
    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_CLIENT_ID")),
        client_secret=str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    for i in range(0, len(untracked_tracks), 49):
        accepted_len_untracked_tracks = untracked_tracks[i : i + 49]
        tracks_info = spotify_client.get_tracks_info(
            token=token, track_ids=accepted_len_untracked_tracks
        )
        tracks_features = spotify_client.get_tracks_attributes(
            token=token, track_ids=accepted_len_untracked_tracks
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
        db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
        db.insert_tracks(tracks)
    return tracks


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
        result_tuple["album_spotify_id"] for result_tuple in untracked_albums_dict
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

@app.get("/genres")
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
        OR ALBUM_GENRES.ID IS NULL
    """
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    ungenred_albums_dict = db.run_select_query(ungenred_albums)
    scrapper = SeleniumScrapper(
        str(os.environ.get("SPOTIFY_USER")),
        str(os.environ.get("SPOTIFY_PWD")),
        str(os.environ.get("CHROME_DRIVER")),
    )
    
    album_genres_styles = scrapper.get_album_genres(ungenred_albums_dict)

    
    for album_genre_style in album_genres_styles:
        
        for genre in album_genre_style["genres"]:
            if db.session.query(Genre.id).filter_by(genre=genre).first() is None:
                db.insert_genre(genre)
            genre_id = db.session.query(Genre.id).filter_by(genre=genre).first()[0]
            album_genre = {"genre_id":genre_id, "album_id":album_genre_style["album_id"]}
            db.insert_album_genre(album_genre)
        for style in album_genre_style["styles"]:
            if db.session.query(Style.id).filter_by(style=style).first() is None:
                db.insert_style(style)
            style_id = db.session.query(Style.id).filter_by(style=style).first()[0]
            album_style = {"style_id":style_id, "album_id":album_genre_style["album_id"]}
            db.insert_album_style(album_style)

    return album_genres_styles
