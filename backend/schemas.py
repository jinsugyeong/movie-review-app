from pydantic import BaseModel, Field
from typing import Optional, List
import datetime as dt


from pydantic import BaseModel, Field
from typing import Optional, List
import datetime as dt


# ---------- Movie ----------
class MovieCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    release_date: Optional[dt.date] = None
    director: Optional[str] = None
    genre: Optional[str] = None
    poster_url: Optional[str] = None


class MovieOut(BaseModel):
    id: int
    title: str
    release_date: Optional[dt.date]
    director: Optional[str]
    genre: Optional[str]
    poster_url: Optional[str]
    created_at: Optional[dt.datetime] = None

    class Config:
        from_attributes = True


# ---------- Review ----------
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
    sentiment_confidence: float
    created_at: dt.datetime

    class Config:
        from_attributes = True


class PaginatedReviews(BaseModel):
    items: List[ReviewOut]
    total: int

