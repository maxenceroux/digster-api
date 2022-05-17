from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import create_engine, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from digster_api.models import Album, AlbumGenre, AlbumStyle, Artist, Genre, Listen, Style, Track, User, UserAlbum


class DigsterDB:
    def __init__(self, db_url: str) -> None:
        self.db = create_engine(db_url)
        self.session = sessionmaker(self.db)()

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

    def insert_user_album(self, user_album: Dict[str, Any]) -> None:
        stmt = insert(UserAlbum).values(user_album)
        self.session.execute(stmt)
        self.session.commit()
    
    def insert_genre(self, genre: str) -> None:
        genre_dict = {"created_at":datetime.now(), "genre":genre}
        stmt = insert(Genre).values(genre_dict)
        self.session.execute(stmt)
        self.session.commit()

    def insert_style(self, style: str) -> None:
        style_dict = {"created_at":datetime.now(), "style":style}
        stmt = insert(Style).values(style_dict)
        self.session.execute(stmt)
        self.session.commit()

    def insert_album_genre(self, album_genre: Dict[str,Any]) -> None:
        album_genre.update({"created_at": datetime.now()})
        stmt = insert(AlbumGenre).values(album_genre)
        self.session.execute(stmt)
        self.session.commit()

    def insert_album_style(self, album_style: Dict[str,Any]) -> None:
        album_style.update({"created_at": datetime.now()})
        stmt = insert(AlbumStyle).values(album_style)
        self.session.execute(stmt)
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

    def update_fetching_allowance(self, user_id:int, value):

        stmt = (
            update(User).
            where(User.id == user_id).
            values(has_allowed_fetching=value)
        )
        self.session.execute(stmt)
        self.session.commit()

    def update_color_album(self, album_id:int, colors):

        stmt = (
            update(Album).
            where(Album.id == album_id).
            values(primary_color=colors[0],secondary_color=colors[1])
        )
        self.session.execute(stmt)
        self.session.commit()
        
    def close_conn(self):
            self.db.dispose()