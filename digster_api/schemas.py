from typing import List

from pydantic import BaseModel


class Listen(BaseModel):
    ts: int
    song_id: str
    user_id: int

    class Config:
        orm_mode = True


class Listens(BaseModel):
    songs: List[Listen]

    class Config:
        orm_mode = True
