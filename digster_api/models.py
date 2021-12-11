from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import DateTime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(
        String,
    )
    email = Column(String)
    country = Column(String)
    image_url = Column(String)
    created_at = Column(DateTime)


class Listen(Base):
    __tablename__ = "listens"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime,
    )
    track_id = Column(String)
    user_id = Column(Integer)
