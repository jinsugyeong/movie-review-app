from sqlalchemy.orm import Session
from models import Movie, Review
from sentiment import analyze_sentiment
from datetime import datetime
from schemas import MovieCreate, ReviewCreate


# ---------- Movie ----------
def create_movie(db: Session, data: MovieCreate):
    movie = Movie(**data.model_dump())
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


def get_movies(db: Session):
    return db.query(Movie).order_by(Movie.id.desc()).all()


def get_movie(db: Session, movie_id: int):
    return db.query(Movie).filter(Movie.id == movie_id).first()


def delete_movie(db: Session, movie_id: int):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if movie:
        db.delete(movie)
        db.commit()


# ---------- Review ----------
def create_review(db: Session, data: ReviewCreate):
    label, confidence, score = analyze_sentiment(data.content)

    review = Review(
        movie_id=data.movie_id,
        author=data.author,
        content=data.content,
        sentiment_label=label,
        sentiment_confidence=confidence,
        sentiment_score=score,
        created_at=datetime.utcnow(),
    )

    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_recent_reviews(db: Session, limit: int = 10):
    return (
        db.query(Review)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .all()
    )


def get_reviews_by_movie(db: Session, movie_id: int):
    return (
        db.query(Review)
        .filter(Review.movie_id == movie_id)
        .order_by(Review.created_at.desc())
        .all()
    )


def delete_review(db: Session, review_id: int):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        return None

    db.delete(review)
    db.commit()
    return {"message": "리뷰가 삭제되었습니다."}
