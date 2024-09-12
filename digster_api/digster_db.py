from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import create_engine, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

try:
    from models import (
        Album,
        AlbumGenre,
        AlbumStyle,
        Artist,
        Follow,
        Genre,
        Listen,
        Style,
        Track,
        User,
        UserAlbum,
    )
except:
    from digster_api.models import (
        Album,
        AlbumGenre,
        AlbumStyle,
        Artist,
        Follow,
        Genre,
        Listen,
        Style,
        Track,
        User,
        UserAlbum,
    )


class DigsterDB:
    def __init__(self, db_url: str) -> None:
        self.db = create_engine(db_url)
        self.session = sessionmaker(self.db)()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get_user_spotify_tokens(self, user_id):
        token = (
            self.session.query(
                User.spotify_access_token, User.spotify_refresh_token
            )
            .filter(User.id == user_id)
            .first()
        )
        if token:
            return {"access_token": token[0], "refresh_token": token[1]}
        return None

    def get_user_info(self, user_id: str):
        return self.session.query(User).filter(User.id == user_id).first()

    def insert_user(self, user, access_token, refresh_token):
        db_user = (
            self.session.query(User).filter(User.id == user.get("id")).first()
        )

        if db_user:
            db_user.spotify_access_token = access_token
            db_user.spotify_refresh_token = refresh_token
        else:
            new_user = User(
                id=user.get("id"),
                created_at=datetime.now(),
                display_name=user.get("display_name"),
                email=user.get("email"),
                country=user.get("country"),
                description=user.get("description"),
                image_url=user.get("image_url"),
                spotify_access_token=access_token,
                spotify_refresh_token=refresh_token,
            )
            self.session.add(new_user)
        self.session.commit()

    def upsert_user(self, user: Dict[str, Any]) -> None:
        user["created_at"] = datetime.now()
        stmt = insert(User).values(user)
        stmt = stmt.on_conflict_do_update(
            constraint="users_pkey",
            set_={
                "display_name": stmt.excluded.display_name,
                "email": stmt.excluded.email,
                "country": stmt.excluded.country,
                "image_url": stmt.excluded.image_url,
            },
        )
        self.session.execute(stmt)
        self.session.commit()

    def insert_genre(self, genre: str) -> None:
        db_genre = (
            self.session.query(Genre).filter(Genre.genre == genre).first()
        )
        if not db_genre:
            new_genre = Genre(genre=genre, created_at=datetime.now())
            self.session.add(new_genre)
            self.session.commit()
            return new_genre.id
        else:
            return db_genre.id

    def insert_style(self, style: str) -> None:
        db_style = (
            self.session.query(Style).filter(Style.style == style).first()
        )
        if not db_style:
            new_style = Style(style=style, created_at=datetime.now())
            self.session.add(new_style)
            self.session.commit()
            return new_style.id
        else:
            return db_style.id

    def insert_artist(self, spotify_id: str, name: str) -> None:
        artist = (
            self.session.query(Artist)
            .filter(Artist.spotify_id == spotify_id)
            .first()
        )
        db_artist = Artist(
            spotify_id=spotify_id,
            name=name,
            created_at=datetime.now(),
        )
        if not artist:
            self.session.add(db_artist)
            self.session.commit()
            return db_artist.id
        else:
            return artist.id

    def insert_album(
        self,
        spotify_id: str,
        artist_id: int,
        type: str,
        upc_id: str,
        label: str,
        name: str,
        release_date: str,
        image_url: str,
        genres: str,
        total_tracks: int,
        popularity: int,
    ):
        album = (
            self.session.query(Album)
            .filter(Album.spotify_id == spotify_id)
            .first()
        )
        db_album = Album(
            spotify_id=spotify_id,
            artist_id=artist_id,
            type=type,
            upc_id=upc_id,
            label=label,
            name=name,
            release_date=release_date,
            image_url=image_url,
            genres=genres,
            total_tracks=total_tracks,
            popularity=popularity,
            created_at=datetime.now(),
        )
        if not album:
            self.session.add(db_album)
            self.session.commit()
            return db_album.id
        else:
            return album.id

    def insert_user_album(
        self, user_id: int, album_id: int, added_at: datetime.date
    ):
        user_album = (
            self.session.query(UserAlbum)
            .filter(UserAlbum.user_id == user_id)
            .filter(UserAlbum.album_id == album_id)
            .first()
        )
        db_user_album = UserAlbum(
            user_id=user_id,
            album_id=album_id,
            added_at=added_at,
            created_at=datetime.now(),
        )
        if not user_album:
            self.session.add(db_user_album)
            self.session.commit()

    def insert_album_genre(self, album_genre: Dict[str, Any]) -> None:
        album_genre.update({"created_at": datetime.now()})
        stmt = insert(AlbumGenre).values(album_genre)
        self.session.execute(stmt)
        self.session.commit()

    def insert_album_style(self, album_style: Dict[str, Any]) -> None:
        album_style.update({"created_at": datetime.now()})
        stmt = insert(AlbumStyle).values(album_style)
        self.session.execute(stmt)
        self.session.commit()

    def update_fetched_genres_date(self, album_id: int):
        album = self.session.query(Album).filter(Album.id == album_id).first()
        album.fetched_genres_date = datetime.now()
        self.session.commit()

    def update_fetched_colors_date(self, album_id: int):
        album = self.session.query(Album).filter(Album.id == album_id).first()
        album.fetched_colors_date = datetime.now()
        self.session.commit()

    def insert_listens(self, listens: List[Listen]) -> None:
        self.session.bulk_save_objects(listens)
        self.session.commit()

    def insert_tracks(self, tracks: List[Track]) -> None:
        self.session.bulk_save_objects(tracks)
        self.session.commit()

    def insert_albums(self, albums: List[Album]) -> None:
        self.session.bulk_save_objects(albums)
        self.session.commit()

    def insert_artists(self, artists: List[Artist]) -> None:
        self.session.bulk_save_objects(artists)
        self.session.commit()

    def run_select_query(self, query: str):
        results_list = self.session.execute(query).fetchall()
        return results_list

    def update_fetching_allowance(self, user_id: int, value):

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(has_allowed_fetching=value)
        )
        self.session.execute(stmt)
        self.session.commit()

    def update_color_album(self, album_id: int, colors):

        stmt = (
            update(Album)
            .where(Album.id == album_id)
            .values(primary_color=colors[0], secondary_color=colors[1])
        )
        self.session.execute(stmt)
        self.session.commit()

    def update_description(self, user_id: int, description: str):
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(description=description)
        )
        self.session.execute(stmt)
        self.session.commit()

    def insert_follow(self, follow: Dict[str, Any]) -> None:
        follow.update(
            {"created_at": datetime.now(), "updated_at": datetime.now()}
        )
        stmt = insert(Follow).values(follow)
        self.session.execute(stmt)
        self.session.commit()

    def follows(self, follower_id: str, following_id: str):
        follow = (
            self.session.query(Follow)
            .filter(Follow.follower_id == follower_id)
            .filter(Follow.following_id == following_id)
            .first()
        )
        if follow:
            return True
        return False

    def update_follow(self, follow: Dict[str, Any]):
        stmt = (
            update(Follow)
            .where(Follow.following_id == follow["following_id"])
            .where(Follow.follower_id == follow["follower_id"])
            .values(
                updated_at=datetime.now(), is_following=follow["is_following"]
            )
        )
        self.session.execute(stmt)
        self.session.commit()

    def close_conn(self):
        self.db.dispose()
