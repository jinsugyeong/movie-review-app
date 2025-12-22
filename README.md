# 영화 리뷰 감성분석 웹 애플리케이션

## 프로젝트 소개
한국 영화의 리뷰를 수집하고 감성분석을 수행하는 웹 애플리케이션

## 배포 링크
- **프론트엔드**: https://movie-review-app.streamlit.app
- **백엔드 API**: https://movie-review-api.onrender.com

## 로컬 실행

### 백엔드
```bash
pip install -r requirements.txt
cd backend
uvicorn main:app --reload
```

### 프론트엔드
```bash
cd frontend
streamlit run app.py
```

## 기술 스택
- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Database**: SQLite
- **ML**: Transformers (KoBERT)