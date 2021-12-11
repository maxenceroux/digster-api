from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(
        String,
    )
    last_name = Column(String)
    age = Column(Integer)


class User2(Base):
    __tablename__ = "users_2"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(
        String,
    )
    last_name = Column(String)
    age = Column(Integer)


class User3(Base):
    __tablename__ = "users_3"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(
        String,
    )
    last_name = Column(String)
    age = Column(Integer)
