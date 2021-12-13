from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from digster_api.models import Listen, Track, User


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

    def insert_listens(self, listens: List[Listen]) -> None:
        self.session.bulk_save_objects(listens)
        self.session.commit()

    def insert_tracks(self, tracks: List[Track]) -> None:
        self.session.bulk_save_objects(tracks)
        self.session.commit()

    def run_select_query(self, query: str):
        results_list = self.session.execute(query).fetchall()
        return results_list
