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

from digster_api.spotify_controller import SpotifyController
from digster_api.bg_tasks import fetch_albums_data
from digster_api.mailjet_client import MailJetClient
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

import requests

origins = [
    "http://localhost:3000",
    "http://localhost:3003",
    "https://fck-algos.com",
    "http://192.168.0.10:3005",
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
REDIRECT_URI = "https://fck-algos.com/callback"
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
        if not db.follows(user["id"], "1138415959"):
            db.insert_follow(
                {
                    "follower_id": user["id"],
                    "following_id": "1138415959",
                    "is_following": True,
                }
            )
    return RedirectResponse(f"https://fck-algos.com?user_id={user.get('id')}")


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
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        query = (
            f"SELECT has_allowed_fetching FROM USERS WHERE id = '{user_id}'"
        )
        actual_fetching = db.run_select_query(query)[0]["has_allowed_fetching"]
        if actual_fetching:
            new_fetching = False
        else:
            new_fetching = True
        db.update_fetching_allowance(user_id, new_fetching)
    return new_fetching


@app.get("/user_info")
def get_spotify_user_info(user_id: str) -> Dict[str, Any]:

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
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        user = db.run_select_query(query)[0]
    return user


@app.get("/saved_albums")
def get_saved_albums(
    user_id: str,
    background_task: BackgroundTasks,
):
    background_task.add_task(fetch_albums_data, user_id)
    return {"details": "albums are fetching", "user_id": user_id}


@app.get("/random_album")
def get_random_album(
    user_id: str,
    styles: str = None,
    curator: str = None,
    label: str = None,
    year: str = None,
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
    if year:
        album_condition += f"""
        AND left(ALBUMS.release_date,4) = '{year}'
        """
    if curator:
        curators_list = curator.split(",")
        curators = ", ".join(f"'{curator}'" for curator in curators_list)
        curator_condition = f"""HAVING ARRAY_AGG(DISTINCT ALBUMS_ALL.DISPLAY_NAME 
        ORDER BY ALBUMS_ALL.DISPLAY_NAME)::text[] @> 
        ARRAY[{curators}]::text[]"""
    else:
        curator_condition = ""

    if styles:
        styles_list = styles.split(",")
        styles = ", ".join(f"'{style}'" for style in styles_list)
        styles_count = len(styles_list)
        # album_condition += f"""
        # AND STYLE IN ({styles})
        # """
        having_condition = f"""HAVING ARRAY_AGG(DISTINCT ALBUMS_ALL.STYLE 
        ORDER BY ALBUMS_ALL.STYLE)::text[] @> 
        ARRAY[{styles}]::text[]"""
    else:
        having_condition = ""
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
        STYLES.STYLE,
        USERS.DISPLAY_NAME

    FROM ALBUMS
    LEFT JOIN ARTISTS ON ARTISTS.ID = ALBUMS.ARTIST_ID
    LEFT JOIN ALBUM_STYLES ON ALBUMS.ID = ALBUM_STYLES.ALBUM_ID
    LEFT JOIN STYLES ON STYLES.ID = ALBUM_STYLES.STYLE_ID
    LEFT JOIN USER_ALBUMS on USER_ALBUMS.ALBUM_ID = ALBUMS.ID
    LEFT JOIN USERS on USER_ALBUMS.USER_ID = USERS.ID
    {album_condition})
    
    SELECT ID,
        SPOTIFY_ID,
        NAME,
        IMAGE_URL,
        LABEL,
        PRIMARY_COLOR,
        SECONDARY_COLOR,
        ARTIST_NAME,
        LEFT(RELEASE_DATE,4) AS RELEASE_DATE_YEAR,
        COUNT(STYLE)
    FROM ALBUMS_ALL
    GROUP BY 1,2,
        3,4,
        5,6,
        7,8,9
        
    {having_condition}
    {curator_condition}
    order by random()
    limit 1
    """
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        if not db.run_select_query(random_album_query):
            return False
        random_album = db.run_select_query(random_album_query)[0]
    return random_album


@app.get("/users")
def get_users():
    query = """
    SELECT USERS.ID,
	USERS.DISPLAY_NAME,
	USERS.IMAGE_URL,
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
		WHERE IS_FOLLOWING IS TRUE
		GROUP BY FOLLOWER_ID) AS FOLLOWING ON FOLLOWER_ID = ID
LEFT JOIN
	(SELECT FOLLOWING_ID,
			COUNT(*)
		FROM FOLLOWS
		WHERE IS_FOLLOWING IS TRUE
		GROUP BY FOLLOWING_ID) AS FOLLOWER ON FOLLOWING_ID = ID
LEFT JOIN
	(SELECT USER_ID,
			COUNT(*)
		FROM USER_ALBUMS
		GROUP BY USER_ID) AS ALBUMS_COUNT ON USER_ID = ID
ORDER BY FOLLOWER_COUNT DESC,
	ALBUMS_COUNT DESC"""
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        users = db.run_select_query(query)
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
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        album_style = db.run_select_query(album_style_query)
        album_genre = db.run_select_query(album_genre_query)
        album_style_genre = {"style": album_style, "genre": album_genre}
    return album_style_genre


@app.get("/album_curators")
def get_album_curators(album_id: str, user_id: str):
    album_curators_query = f"""
    SELECT DISPLAY_NAME,
       IMAGE_URL,
       USERS.ID,
       CASE
           WHEN USERS.ID = '1138415959' THEN TRUE
           ELSE COALESCE(IS_FOLLOWING, FALSE)
       END AS IS_FOLLOWING
FROM USER_ALBUMS
LEFT JOIN USERS ON USERS.ID = USER_ALBUMS.USER_ID
LEFT JOIN FOLLOWS ON FOLLOWER_ID = '{user_id}'
AND FOLLOWING_ID = USERS.ID
WHERE ALBUM_ID = {album_id}
AND (USERS.ID <> '{user_id}' OR '{user_id}' = '1138415959')

    """
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        album_curators = db.run_select_query(album_curators_query)
    return album_curators


@app.post("/description")
def set_description(user_id: str, description: str):
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        db.update_description(user_id, description)
    return description


@app.post("/follow")
def set_user_follows(follower_id: str, following_id: str) -> Dict[str, Any]:
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
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
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        query = f"""SELECT * FROM follows
        WHERE follower_id = '{follower_id}'
        and following_id = '{following_id}'"""
        result = db.run_select_query(query)
        if not result:
            return False
    return result[0]["is_following"]


@app.get("/followers")
def get_followers(user_id: str):
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:

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
    return result


@app.get("/following")
def get_following(user_id: str):
    with DigsterDB(db_url=str(os.environ.get("DATABASE_URL"))) as db:
        follower_id = str(user_id)
        query = f"""
        SELECT users.display_name, users.image_url, users.id
        FROM FOLLOWS
        LEFT JOIN USERS ON USERS.ID = FOLLOWS.FOLLOWING_ID
        WHERE FOLLOWER_ID = '{follower_id}'
        and is_following is True
        """
        result = db.run_select_query(query)
    return result
