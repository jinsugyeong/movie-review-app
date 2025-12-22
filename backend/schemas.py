from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
import datetime as dt


class MovieCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    release_date: Optional[dt.date] = None
    director: Optional[str] = None
    genre: Optional[str] = None
    poster_url: Optional[str] = None  # url 검증 빡세게 안 걸어도 됨


class MovieOut(BaseModel):
    id: int
    title: str
    release_date: Optional[dt.date]
    director: Optional[str]
    genre: Optional[str]
    poster_url: Optional[str]
    created_at: dt.datetime
    avg_sentiment: Optional[float] = None  # 리뷰 평균(심화)

    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    movie_id: int
    author: str = Field(..., min_length=1, max_length=80)
    content: str = Field(..., min_length=1, max_length=5000)


class ReviewOut(BaseModel):
    id: int
    movie_id: int
    author: str
    content: str
    sentiment_label: str
    sentiment_score: float
    created_at: dt.datetime

    class Config:
        from_attributes = True


class PaginatedReviews(BaseModel):
    items: List[ReviewOut]
    total: int
