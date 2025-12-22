from sqlalchemy.orm import Session
from models import Movie, Review
from sentiment import analyze_sentiment
from datetime import datetime


# Movie CRUD
def create_movie(db: Session, data):
    movie = Movie(**data)
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


def get_movies(db: Session):
    return db.query(Movie).all()


def get_movie(db: Session, movie_id: int):
    return db.query(Movie).get(movie_id)


def delete_movie(db: Session, movie_id: int):
    movie = db.query(Movie).get(movie_id)
    if movie:
        db.delete(movie)
        db.commit()


# Review CRUD
def create_review(db: Session, data):
    label, confidence, sentiment_score = analyze_sentiment(data["content"])
    review = Review(
        movie_id=data["movie_id"],
        author=data["author"],
        content=data["content"],
        sentiment_label=label,
        sentiment_confidence=confidence,  # 신뢰도 점수
        sentiment_score=sentiment_score,  # 감성점수 (별점용)
        created_at=datetime.utcnow()
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_recent_reviews(db: Session, limit=10):
    return db.query(Review).order_by(Review.created_at.desc()).limit(limit).all()

from sqlalchemy import asc
def get_reviews_by_movie(db: Session, movie_id: int, order_asc=False):
    q = db.query(Review).filter(Review.movie_id == movie_id)
    if order_asc:
        q = q.order_by(asc(Review.created_at))
    else:
        q = q.order_by(Review.created_at.desc())
    return q.all()



def delete_review(db: Session, review_id: int):
    """
    리뷰 삭제
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    
    if not review:
        return None
    
    db.delete(review)
    db.commit()
    return {"message": "리뷰가 삭제되었습니다."}