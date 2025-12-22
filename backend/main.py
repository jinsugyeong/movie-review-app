from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import Base, engine, SessionLocal
import crud
from schemas import (
    MovieCreate,
    MovieOut,
    ReviewCreate,
    ReviewOut,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Movie Review Sentiment API")


# ---------- DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Movie ----------
@app.get("/movies", response_model=List[MovieOut])
def list_movies(db: Session = Depends(get_db)):
    return crud.get_movies(db)


@app.get("/movies/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = crud.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="영화를 찾을 수 없습니다.")
    return movie


@app.post("/movies", response_model=MovieOut)
def add_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    return crud.create_movie(db, movie)


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    crud.delete_movie(db, movie_id)
    return {"status": "deleted"}


# ---------- Review ----------
@app.post("/reviews", response_model=ReviewOut)
def add_review(review: ReviewCreate, db: Session = Depends(get_db)):
    return crud.create_review(db, review)


@app.get("/reviews", response_model=List[ReviewOut])
def recent_reviews(db: Session = Depends(get_db)):
    return crud.get_recent_reviews(db)


@app.get("/movies/{movie_id}/reviews", response_model=List[ReviewOut])
def movie_reviews(movie_id: int, db: Session = Depends(get_db)):
    return crud.get_reviews_by_movie(db, movie_id)


@app.delete("/reviews/{review_id}")
def delete_review_endpoint(review_id: int, db: Session = Depends(get_db)):
    result = crud.delete_review(db, review_id)
    if result is None:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")
    return result
