from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Movie(Base):
    __tablename__ = "movies"


    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    release_date = Column(String)
    director = Column(String)
    genre = Column(String)
    poster_url = Column(String)


    reviews = relationship("Review", back_populates="movie", cascade="all, delete")


class Review(Base):
    __tablename__ = "reviews"


    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    author = Column(String)
    content = Column(String)
    sentiment_label = Column(String)
    sentiment_confidence = Column(Float)  # 신뢰도 점수
    sentiment_score = Column(Float)  # 감성점수 (별점용)
    created_at = Column(DateTime, default=datetime.utcnow)


    movie = relationship("Movie", back_populates="reviews")


class MovieCreate(BaseModel):
    title: str
    release_date: str
    director: str
    genre: str
    poster_url: str


class ReviewCreate(BaseModel):
    movie_id: int
    author: str
    content: str