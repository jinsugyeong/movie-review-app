from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
import crud


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Movie Review Sentiment API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/movies")
def list_movies(db: Session = Depends(get_db)):
    return crud.get_movies(db)


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    return crud.get_movie(db, movie_id)


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    crud.delete_movie(db, movie_id)
    return {"status": "deleted"}


@app.post("/movies")
def add_movie(movie: dict, db: Session = Depends(get_db)):
    return crud.create_movie(db, movie)


@app.post("/reviews")
def add_review(review: dict, db: Session = Depends(get_db)):
    return crud.create_review(db, review)


@app.get("/reviews")
def recent_reviews(db: Session = Depends(get_db)):
    return crud.get_recent_reviews(db)


@app.get("/movies/{movie_id}/reviews")
def movie_reviews(movie_id: int, db: Session = Depends(get_db)):
    return crud.get_reviews_by_movie(db, movie_id)


@app.delete("/reviews/{review_id}")
def delete_review_endpoint(review_id: int, db: Session = Depends(get_db)):
    """
    특정 리뷰 삭제
    """
    result = crud.delete_review(db, review_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")
    
    return result