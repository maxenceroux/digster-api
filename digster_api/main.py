import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence


from digster_api.worker import fetch_album_data_worker


from fastapi import FastAPI, Request, HTTPException, BackgroundTasks

from digster_api.digster_db import DigsterDB
from digster_api.models import (
    AlbumRecRequest,
    Listen,
    Track,
)
from digster_api.selenium_scrapper import SeleniumScrapper
from digster_api.spotify_controller import SpotifyController
from digster_api.bg_tasks import fetch_albums_data
from digster_api.mailjet_client import MailJetClient
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

import requests

origins = [
    "http://localhost:3000",
]
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CLIENT_ID = "b45b68c4c7a0421589605adf1e1a7626"
CLIENT_SECRET = "9f629374960a45aa8268eab3a9dbe18b"
REDIRECT_URI = "http://localhost:8000/callback"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPE = ["user-library-read", "user-library-modify"]
# In-memory storage for tokens; use a database for persistent storage
user_tokens = {}


@app.get("/login")
async def login():
    auth_query_parameters = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPE),
        "redirect_uri": REDIRECT_URI,
    }
    url_args = "&".join(
        [f"{key}={val}" for key, val in auth_query_parameters.items()]
    )
    auth_url = f"{AUTH_URL}/?{url_args}"
    return RedirectResponse(auth_url)


@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")

    if code is None:
        raise HTTPException(
            status_code=400, detail="Code not found in the request"
        )

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    r = requests.post(TOKEN_URL, data=token_data)

    if r.status_code != 200:
        raise HTTPException(
            status_code=r.status_code, detail="Failed to fetch tokens"
        )

    token_info = r.json()
    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")
    sp_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_CLIENT_ID")),
        client_secret=str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    user = sp_client.get_user_info(access_token)
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        db.insert_user(user, access_token, refresh_token)
    return RedirectResponse(f"http://localhost:3000?user_id={user.get('id')}")


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Hello World"}


@app.get("/spotify_user_info")
def get_spotify_user_info(token: str) -> Dict[str, Any]:
    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_CLIENT_ID")),
        client_secret=str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    user = spotify_client.get_user_info(token)
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    db.upsert_user(user)
    db.close_conn()
    return user


@app.post("/album_rec")
def send_album_rec(request: AlbumRecRequest):
    try:
        with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
            user = db.get_user_info(request.user_id)

        mj_client = MailJetClient(
            os.environ.get("MAILJET_API_KEY"),
            os.environ.get("MAILJET_API_SECRET"),
        )
        variables = {
            "user_url": f"https://open.spotify.com/user{request.user_id}",
            "sp_user_name": user.display_name if user else None,
            "image_url": request.album_image_url,
            "album_name": request.album_name,
            "artist_name": request.artist_name,
            "album_url": request.album_url,
        }
        return mj_client.send_templated_email(
            "hello@fck-algos.com",
            request.recipient_email,
            request.recipient_name,
            6273301,
            "Someone wants to share an album with you!",
            variables,
        )
    except Exception as e:
        print(e)
        raise (e)


@app.put("/album")
def save_album(user_id: str, album_id: str):
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        user_id = str(user_id)
        user_tokens = db.get_user_spotify_tokens(user_id)
    spotify_client = SpotifyController(
        client_id=str(os.environ.get("SPOTIFY_CLIENT_ID")),
        client_secret=str(os.environ.get("SPOTIFY_CLIENT_SECRET")),
    )
    try:
        spotify_client.save_album(user_tokens, album_id)
    except Exception as e:
        raise e


@app.post("/allow_fetching")
def set_allow_fetching(user_id: str) -> Dict[str, Any]:
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    query = f"SELECT has_allowed_fetching FROM USERS WHERE id = '{user_id}'"
    actual_fetching = db.run_select_query(query)[0]["has_allowed_fetching"]
    if actual_fetching:
        new_fetching = False
    else:
        new_fetching = True
    db.update_fetching_allowance(user_id, new_fetching)
    db.close_conn()
    return new_fetching


@app.get("/user_info")
def get_spotify_user_info(user_id: str) -> Dict[str, Any]:
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    query = f"""
    SELECT USERS.DISPLAY_NAME,
	USERS.IMAGE_URL,
	USERS.ID,
    USERS.HAS_ALLOWED_FETCHING,
	COALESCE(FOLLOWING.COUNT,
		0) AS FOLLOWING_COUNT,
	COALESCE(FOLLOWER.COUNT,
		0) AS FOLLOWER_COUNT,
	COALESCE(ALBUMS_COUNT.COUNT,
		0) AS ALBUMS_COUNT
FROM USERS
LEFT JOIN
	(SELECT FOLLOWER_ID,
			COUNT(*)
		FROM FOLLOWS
		WHERE FOLLOWER_ID = '{user_id}'
        AND IS_FOLLOWING IS TRUE
		GROUP BY FOLLOWER_ID) AS FOLLOWING ON FOLLOWER_ID = ID
LEFT JOIN
	(SELECT FOLLOWING_ID,
			COUNT(*)
		FROM FOLLOWS
		WHERE FOLLOWING_ID = '{user_id}'
        AND IS_FOLLOWING IS TRUE
		GROUP BY FOLLOWING_ID) AS FOLLOWER ON FOLLOWING_ID = ID
LEFT JOIN
	(SELECT USER_ID,
			COUNT(*)
		FROM USER_ALBUMS
		WHERE USER_ID = '{user_id}'
        GROUP BY USER_ID) AS ALBUMS_COUNT ON USER_ID = ID
WHERE ID = '{user_id}'
    """
    user = db.run_select_query(query)[0]
    db.close_conn()
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
def get_saved_albums(
    user_id: str,
    background_task: BackgroundTasks,
):
    background_task.add_task(fetch_albums_data, user_id)
    return {"details": "albums are fetching", "user_id": user_id}


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


@app.get("/random_album")
def get_random_album(
    user_id: str,
    styles: str = None,
    curator: str = None,
    label: str = None,
    current_album_id: int = 999999,
):
    album_condition = f"""
    WHERE ALBUMS.ID in
            (SELECT ALBUM_ID
                FROM FOLLOWING_USERS_ALBUMS)
    AND ALBUMS.ID <> {current_album_id}
    AND ALBUMS.PRIMARY_COLOR IS NOT NULL
    AND STYLE IS NOT NULL 
    """
    if not user_id:
        user_id = -1
    if label:
        album_condition += f"""
        AND ALBUMS.label = '{label}'
        """
    if curator:
        curators_list = curator.split(",")
        curators = ", ".join(f"'{curator}'" for curator in curators_list)
        album_condition += f"""
        AND USERS.DISPLAY_NAME in ({curators})
        """
    if styles:
        styles_list = styles.split(",")
        styles = ", ".join(f"'{style}'" for style in styles_list)
        styles_count = len(styles_list)
        album_condition += f"""
        AND STYLE IN ({styles})
        """
    else:
        styles_count = 0
    random_album_query = f"""
    WITH FOLLOWING_USERS AS
        (SELECT FOLLOWING_ID
            FROM FOLLOWS
            WHERE FOLLOWER_ID = '{user_id}'
                AND IS_FOLLOWING IS TRUE),
        FOLLOWING_USERS_ALBUMS AS
        (SELECT ALBUM_ID
            FROM USER_ALBUMS
            WHERE USER_ID in
                    (SELECT FOLLOWING_ID
                        FROM FOLLOWING_USERS)
            OR USER_ID = '1138415959'),
        ALBUMS_ALL as (
    SELECT ALBUMS.*,
        ARTISTS.NAME ARTIST_NAME,
        STYLES.STYLE
    FROM ALBUMS
    LEFT JOIN ARTISTS ON ARTISTS.ID = ALBUMS.ARTIST_ID
    LEFT JOIN ALBUM_STYLES ON ALBUMS.ID = ALBUM_STYLES.ALBUM_ID
    LEFT JOIN STYLES ON STYLES.ID = ALBUM_STYLES.STYLE_ID
    LEFT JOIN USER_ALBUMS on USER_ALBUMS.ALBUM_ID = ALBUMS.ID
    LEFT JOIN USERS on USER_ALBUMS.USER_ID = USERS.ID
    {album_condition}),
    COUNT_STYLES AS
    (SELECT ID,
        SPOTIFY_ID,
        NAME,
        IMAGE_URL,
        LABEL,
        PRIMARY_COLOR,
        SECONDARY_COLOR,
        ARTIST_NAME,
        COUNT(STYLE)
    FROM ALBUMS_ALL
    GROUP BY 1,2,
        3,4,
        5,6,
        7,8)
        SELECT *
    FROM COUNT_STYLES
    WHERE COUNT >= {styles_count}
    
    order by random()
    limit 1
    """
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    if not db.run_select_query(random_album_query):
        db.close_conn()
        return False
    random_album = db.run_select_query(random_album_query)[0]
    db.close_conn()
    return random_album


@app.get("/users")
def get_users():
    query = """
    SELECT id, display_name, image_url from users"""
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    users = db.run_select_query(query)
    db.close_conn()
    return users


@app.get("/album_style_genre")
def get_album_style_genre(album_id):
    album_style_query = f"""
    SELECT style 
    FROM album_styles
    left join styles on album_styles.style_id = styles.id
    where album_id = {album_id} 
    """
    album_genre_query = f"""
    SELECT genre 
    FROM album_genres
    left join genres on album_genres.genre_id = genres.id
    where album_id = {album_id} 
    """
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    album_style = db.run_select_query(album_style_query)
    album_genre = db.run_select_query(album_genre_query)
    album_style_genre = {"style": album_style, "genre": album_genre}
    db.close_conn()
    return album_style_genre


@app.get("/album_curators")
def get_album_curators(album_id):
    album_curators_query = f"""
    SELECT display_name
    FROM user_albums
    LEFT JOIN users on users.id = user_albums.user_id
    where album_id = {album_id}
    """
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    album_curators = db.run_select_query(album_curators_query)
    db.close_conn()
    return album_curators


@app.post("/description")
def set_description(user_id: str, description: str):
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    db.update_description(user_id, description)
    db.close_conn()
    return description


@app.post("/follow")
def set_user_follows(follower_id: str, following_id: str) -> Dict[str, Any]:
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    query = f"""SELECT * FROM follows
    WHERE follower_id = '{follower_id}'
    and following_id = '{following_id}'"""
    result = db.run_select_query(query)
    if not result:
        follow = {
            "follower_id": follower_id,
            "following_id": following_id,
            "is_following": True,
        }
        db.insert_follow(follow)
        db.close_conn()
        return follow
    if result[0]["is_following"]:
        follow = {
            "follower_id": follower_id,
            "following_id": following_id,
            "is_following": False,
        }
    else:
        follow = {
            "follower_id": follower_id,
            "following_id": following_id,
            "is_following": True,
        }
    db.update_follow(follow)
    db.close_conn()
    return follow


@app.get("/albums")
def get_albums(
    user_id: str, offset: int = 0, limit: int = 50, sort: str = "random"
):
    if sort == "random":
        sorting_condition = "ORDER BY random()"
    elif sort == "alphabetical":
        sorting_condition = "ORDER BY albums.name"
    elif sort == "added_to_collection":
        sorting_condition = "ORDER BY added_at DESC"
    elif sort == "release_date":
        sorting_condition = "ORDER BY release_date DESC"
    elif sort == "color":
        sorting_condition = "ORDER BY luminance DESC"

    query = f"""
    SELECT 
        albums.name, 
        albums.label,
        albums.spotify_id,
        albums.image_url,
        artists.name as artist_name,
        user_albums.added_at,
        albums.release_date,
        ('x'||substring(primary_color, 2, 2))::bit(8)::int AS red,
       ('x'||substring(primary_color, 4, 2))::bit(8)::int AS green,
       ('x'||substring(primary_color, 6, 2))::bit(8)::int AS blue,
       (0.299 * ('x'||substring(primary_color, 2, 2))::bit(8)::int +
        0.587 * ('x'||substring(primary_color, 4, 2))::bit(8)::int +
        0.114 * ('x'||substring(primary_color, 6, 2))::bit(8)::int) AS luminance
    FROM
        albums
    LEFT JOIN artists
        ON albums.artist_id = artists.id
    INNER JOIN user_albums 
        ON user_albums.album_id = albums.id
    WHERE user_albums.user_id = '{user_id}'
    {sorting_condition}
    LIMIT {limit} OFFSET {offset}
    
    """
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        result = db.run_select_query(query)
    return result


@app.get("/follow")
def get_follow(follower_id: str, following_id: str) -> bool:
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    query = f"""SELECT * FROM follows
    WHERE follower_id = '{follower_id}'
    and following_id = '{following_id}'"""
    result = db.run_select_query(query)
    if not result:
        db.close_conn()
        return False
    db.close_conn()
    return result[0]["is_following"]


@app.get("/followers")
def get_followers(user_id: str):
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    following_id = str(user_id)
    query = f"""
    SELECT users.display_name, users.image_url, users.id,
    case when 
        (select count(*) 
        from follows 
        where following_id = users.id and follower_id = '{following_id}' and is_following is True)
        >0 
        then True else False end as following
    FROM FOLLOWS
    LEFT JOIN USERS ON USERS.ID = FOLLOWS.FOLLOWER_ID
    WHERE FOLLOWING_ID = '{following_id}'
    and is_following is True
    """
    result = db.run_select_query(query)
    db.close_conn()
    return result


@app.get("/following")
def get_following(user_id: str):
    db = DigsterDB(db_url=str(os.environ.get("DATABASE_URL")))
    follower_id = str(user_id)
    query = f"""
    SELECT users.display_name, users.image_url, users.id
    FROM FOLLOWS
    LEFT JOIN USERS ON USERS.ID = FOLLOWS.FOLLOWING_ID
    WHERE FOLLOWER_ID = '{follower_id}'
    and is_following is True
    """
    result = db.run_select_query(query)
    db.close_conn()
    return result
