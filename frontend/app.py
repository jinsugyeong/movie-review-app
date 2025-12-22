import streamlit as st
import requests
import random
from datetime import datetime

API = "https://movie-review-app-wmnz.onrender.com"
#API = "http://localhost:8000"

st.set_page_config(page_title="Movie Review App", page_icon="🎬", layout="wide")

# 감성 점수를 별로 변환
def score_to_stars(score: float) -> str:
    """0.0 ~ 1.0 범위의 점수를 별로 변환"""
    if score < 2.0:
        return "⭐☆☆☆☆"
    elif score < 3.0:
        return "⭐⭐☆☆☆"
    elif score < 4.0:
        return "⭐⭐⭐☆☆"
    elif score < 4.8:
        return "⭐⭐⭐⭐☆"
    else:
        return "⭐⭐⭐⭐⭐"


# ---------------- CSS ----------------
st.markdown("""
<style>
div[data-testid="stSidebar"] button {
    border-radius: 10px;
    height: 48px;
}

div[data-testid="stSidebar"] button.active-menu {
    background-color: #ff4b4b !important;
    color: white !important;
    font-weight: 700 !important;
}

.movie-card {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.movie-poster-wrapper {
    width: 100%;
    height: 400px;
    overflow: hidden;
    border-radius: 8px;
    margin-bottom: 12px;
    background-color: #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.movie-poster-wrapper img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.movie-title-btn {
    width: 100%;
    height: 48px !important;
    padding: 8px !important;
    margin-bottom: 8px;
    overflow: hidden !important;
}

.movie-title-btn > div > p {
    margin: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    height: 32px !important;
    line-height: 32px !important;
}

.movie-title-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: bold;
    font-size: 0.95rem;
}

.movie-meta {
    text-align: left;
    font-size: 1rem;
    margin-bottom: 8px;
    min-height: 20px;
    padding-left: 4px;
}

.movie-delete-btn {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)


# ---------------- Session State ----------------
if "menu" not in st.session_state:
    st.session_state.menu = "movie_list"

if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

if "review_movie_id" not in st.session_state:
    st.session_state.review_movie_id = None

if "review_page" not in st.session_state:
    st.session_state.review_page = 0

# ---------------- Sidebar ----------------
def sidebar_btn(label, value):
    is_active = st.session_state.menu == value

    btn = st.sidebar.button(
        label,
        use_container_width=True,
        key=f"menu_{value}"
    )

    if btn:
        st.session_state.menu = value
        st.session_state.selected_movie = None
        st.rerun()

    if is_active:
        st.sidebar.markdown(
            f"""
            <script>
            setTimeout(() => {{
                const btns = window.parent.document.querySelectorAll(
                    'div[data-testid="stSidebar"] button'
                );
                btns.forEach(b => {{
                    b.classList.remove('active-menu');
                    if (b.innerText.includes("{label}")) {{
                        b.classList.add('active-menu');
                    }}
                }});
            }}, 100);
            </script>
            """,
            unsafe_allow_html=True
        )


st.sidebar.markdown("## Main Menu")
sidebar_btn("🏠 영화 목록", "movie_list")
sidebar_btn("🎬 영화 등록", "movie_add")
sidebar_btn("✍️ 리뷰 등록", "review_add")
st.sidebar.markdown("---")

# ---------------- Dummy Data ----------------
if st.sidebar.button("더미 데이터 생성", use_container_width=True):
    existing_titles = {m["title"] for m in requests.get(f"{API}/movies").json()}

    movies = [
        ("아바타: 불과 재", "2024-12-20", "제임스 카메론", "SF", "https://i.namu.wiki/i/UyN7wDQJ2QnXo-RivyWd573b1K-YZ9fAFUr0nyWMZLc_vd1NW45XQBBslwhUIfrHGyqSLIqryRYb9ItDci2hvc6C6TV1g822dsIAYcmw4VLWoPldfg-060N-9ua7vghptFaEAefg7sNzxvseXqsksg.webp"),
        ("탈주", "2024-07-03", "이종필", "액션", "https://i.namu.wiki/i/GOCVqsctfY_ei_5gC38-8UlHqQ4ypixYpkfgGn_LcDsYpgelrJDMAlgxzrkwWZo0n0vnCcdgPgA7-_mNfScR5OkZuZU9JaGdNUZZyikeeUB19MlwR3VUdxaTjA4XHaUvyKP2LaGad9A4nVAi4ymAkg.webp"),
        ("집으로 가는 길", "2013-12-11", "방은진", "드라마", "https://i.namu.wiki/i/O58yKrByuDlVcPA4TXIlytF98-4mBDnVGLloYTsQeqrkklOVqXkIR2rAySTDnLmWAb_Pe4VCSsVNEFDG4kWJOI4F9TrjcyL3DD26lpQBunOZaCl1z2DH5tjRABEyRXdMmcsUEYrryf--NoP9Ezd1lw.webp"),
        ("전지적 독자 시점", "2025-01-01", "김병우", "판타지", "https://i.namu.wiki/i/78fa4oC92J13_-Z7Pw-_v_6TsLDJ2kBkTZqrfLm-ll9f_jgXP41H7UtUTXXCZpvTOZcIAsMqP3tsi6IfFvA2GFr8Cnto-mKubovE-MzWQeqcPVnG9LayEW46wv7UDm1lwnyYPxuiakPxi_LGLZccjQ.webp"),
        ("극장판 짱구는 못말려: 초화려! 작열하는 떡잎마을 댄서즈", "2025-12-24", "하시모토 마사카즈", "애니메이션", "https://i.namu.wiki/i/yyOX12GcO3Z83hCYIxFvvjaUZnf9FshyOTeoT0s28URV1EhVWfDZ_349Mj6pyOQ3WuOK-oxRS9BHp_sP8hiZYq0aEGyMp8aNTlR6PwEGiZ4GNy_WtzkTC_i-PIha4yL5wusVyP5dsPhf3_aJ6zXWZg.webp"),
    ]

    for title, rd, d, g, p in movies:
        if title in existing_titles:
            continue
        res = requests.post(f"{API}/movies", json={
            "title": title,
            "release_date": rd,
            "director": d,
            "genre": g,
            "poster_url": p
        })
        mid = res.json()["id"]
        KOREAN_REVIEWS = [
            # 👍 매우 긍정
            "스토리도 탄탄하고 연출이 정말 뛰어났어요. 시간 가는 줄 모르고 봤습니다.",
            "배우들의 연기가 몰입감을 높여줘서 끝까지 재미있게 감상했어요.",
            "영상미와 음악이 잘 어우러져서 극장에서 볼 가치가 충분한 작품이었습니다.",
            "기대 이상으로 완성도가 높아서 다시 보고 싶은 영화예요.",

            # 🙂 긍정
            "전반적으로 재미있게 봤고, 몇몇 장면은 인상 깊었습니다.",
            "조금 늘어지는 부분은 있었지만 전체적으로 만족스러웠어요.",
            "가볍게 보기 좋은 영화라서 부담 없이 즐길 수 있었습니다.",

            # 😐 중립
            "무난한 영화였습니다. 나쁘지도 좋지도 않았어요.",
            "스토리는 평범했지만 연출은 괜찮은 편이었습니다.",
            "기대가 컸던 만큼 아쉬움도 조금 남는 작품이네요.",

            # 🙁 부정
            "스토리가 예상 가능해서 중간부터 흥미가 떨어졌습니다.",
            "연출이 다소 산만해서 몰입하기 어려웠어요.",
            "러닝타임에 비해 내용이 너무 얕게 느껴졌습니다.",

            # 😡 매우 부정
            "기대하고 봤는데 실망이 컸어요. 전개가 너무 엉성했습니다.",
            "캐릭터의 행동이 이해되지 않아서 보는 내내 답답했어요.",
            "끝까지 보기 힘들 정도로 지루했습니다."
        ]

        for i in range(10):
            requests.post(f"{API}/reviews", json={
                "movie_id": mid,
                "author": f"user{i}",
                "content": random.choice(KOREAN_REVIEWS)
            })

    st.sidebar.success("더미 데이터 생성 완료")

# ---------------- 영화 목록 ----------------
if st.session_state.menu == "movie_list":
    if st.session_state.selected_movie is None:
        st.title("🎞 영화 목록")
        res = requests.get(f"{API}/movies")

        if res.status_code != 200:
            st.error(f"/movies API 오류: {res.status_code}")
            st.code(res.text)   # 👈 여기서 진짜 원인 보임
            st.stop()

        movies = res.json()

        # ---------------- 목록 ----------------
        cols = st.columns(3)

        for idx, m in enumerate(movies):
            reviews = requests.get(f"{API}/movies/{m['id']}/reviews").json()
            if reviews:
                avg_score = round(
                    sum(r["sentiment_score"] for r in reviews) / len(reviews), 2
                )
                avg_text = f"{score_to_stars(avg_score)} ({avg_score})"
            else:
                avg_text = "📝 등록된 리뷰 없음"

            with cols[idx % 3]:
                st.markdown(f"""
                <div class="movie-card">
                """, unsafe_allow_html=True)
                
                # 포스터 이미지 - HTML로 직접 렌더링
                poster_html = ""
                if m.get("poster_url") and isinstance(m["poster_url"], str) and (m["poster_url"].startswith("http://") or m["poster_url"].startswith("https://")):
                    poster_url_escaped = m["poster_url"].replace('"', '&quot;')
                    poster_html = f"""
                    <div class="movie-poster-wrapper">
                        <img src="{poster_url_escaped}" alt="{m['title']}" onerror="this.parentElement.innerHTML='⚠️ 이미지 로드 실패';">
                    </div>
                    """
                else:
                    poster_html = """
                    <div class="movie-poster-wrapper" style="background-color: #e0e0e0;">
                        <span>⚠️ 이미지 없음</span>
                    </div>
                    """
                
                st.markdown(poster_html, unsafe_allow_html=True)
                
                # 제목 버튼 (한 줄, 줄임표)
                # 제목이 20글자 이상이면 잘라서 ...붙이기
                title_display = m['title']
                if len(title_display) > 20:
                    title_display = title_display[:17] + "..."
                
                title_escaped = title_display.replace('"', '&quot;')
                button_col = st.columns([1])[0]
                with button_col:
                    if st.button(title_escaped, key=f"title_{m['id']}", use_container_width=True):
                        st.session_state.selected_movie = m["id"]
                        st.rerun()
                
                # 메타 정보와 삭제 버튼을 한 줄로
                meta_col, del_col = st.columns([5, 1])
                with meta_col:
                    st.markdown(f"""
                    <div class="movie-meta">{avg_text}</div>
                    """, unsafe_allow_html=True)
                
                with del_col:
                    if st.button("🗑", key=f"del_{m['id']}", use_container_width=True):
                        requests.delete(f"{API}/movies/{m['id']}")
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        # ---------------- 상세 ----------------
        movie = requests.get(f"{API}/movies/{st.session_state.selected_movie}").json()
        reviews = requests.get(f"{API}/movies/{movie['id']}/reviews").json()

        st.title(movie["title"])
        
        left, right, tmp = st.columns([1.5, 2,2])
        with left:
            if movie.get("poster_url") and isinstance(movie["poster_url"], str) and (movie["poster_url"].startswith("http://") or movie["poster_url"].startswith("https://")):
                try:
                    st.image(movie["poster_url"], use_container_width=True)
                except Exception as e:
                    st.warning("⚠️ 포스터 이미지를 불러올 수 없습니다.")
            else:
                st.warning("⚠️ 유효한 포스터 URL이 없습니다.")

        if reviews:
            avg_score = round(
                sum(r["sentiment_score"] for r in reviews) / len(reviews), 2
            )
            avg_text = f"{score_to_stars(avg_score)} ({avg_score})"
        else:
            avg_text = "📝 등록된 리뷰 없음"

        with right:
            st.dataframe({
                "항목": ["개봉일", "감독", "장르", "평점"],
                "정보": [movie["release_date"], movie["director"], movie["genre"], avg_text ],
            })

        # 리뷰 섹션 제목과 버튼을 한 줄로
        col_title, col_btn = st.columns([0.85, 0.15])
        with col_title:
            st.markdown("### 📝 리뷰")
        with col_btn:
            st.markdown("")  # 상단 공간 맞추기
            if st.button("✍️ 리뷰 작성하기", use_container_width=True, key="review_write_btn"):
                st.session_state.review_movie_id = st.session_state.selected_movie
                st.session_state.menu = "review_add"
                st.session_state.selected_movie = None
                st.rerun()
        
        if reviews:
            # 페이지네이션 설정
            reviews_per_page = 10
            total_pages = (len(reviews) + reviews_per_page - 1) // reviews_per_page
            
            # 현재 페이지 리뷰 계산
            start_idx = st.session_state.review_page * reviews_per_page
            end_idx = start_idx + reviews_per_page
            page_reviews = reviews[start_idx:end_idx]

            cols = st.columns([1, 5, 1.5, 1, 1])
            
            with cols[0]:
                st.markdown("**작성자**")
            with cols[1]:
                st.markdown("**리뷰**")
            with cols[2]:
                st.markdown("**감성**")
            with cols[3]:
                st.markdown("**평점**")
            with cols[4]:
                st.markdown("**삭제**")
            
            st.divider()
            
            for r in page_reviews:
                cols = st.columns([1, 5, 1.5, 1, 1])
                
                with cols[0]:
                    st.markdown(r["author"])
                with cols[1]:
                    st.markdown(r["content"])
                with cols[2]:
                    score = round(r["sentiment_confidence"], 2) if "sentiment_confidence" in r else round(r["sentiment_score"], 2)
                    st.markdown(r["sentiment_label"] + " (" + str(score) + ")")
                with cols[3]:
                    st.markdown(str(r["sentiment_score"]))
                with cols[4]:
                    if st.button("🗑️", key=f"delete_review_{r['id']}", help="삭제"):
                        response = requests.delete(f"{API}/reviews/{r['id']}")
                        if response.status_code == 200:
                            st.success("✅ 리뷰가 삭제되었습니다.")
                            st.rerun()
                        else:
                            st.error("❌ 삭제 실패")

            # 페이지 네비게이션
            st.divider()
            page_col1, page_col2, page_col3, page_col4 = st.columns([1, 2, 1, 1])
            
            with page_col1:
                if st.session_state.review_page > 0:
                    if st.button("⬅️ 이전", use_container_width=True):
                        st.session_state.review_page -= 1
                        st.rerun()
                else:
                    st.write("")
            
            with page_col2:
                st.markdown(f"<div style='text-align: center; padding-top: 8px;'><b>페이지 {st.session_state.review_page + 1} / {total_pages}</b></div>", unsafe_allow_html=True)
            
            with page_col3:
                if st.session_state.review_page < total_pages - 1:
                    if st.button("다음 ➡️", use_container_width=True):
                        st.session_state.review_page += 1
                        st.rerun()
                else:
                    st.write("")
            
            with page_col4:
                st.write("")
        else:
            st.info("등록된 리뷰가 없습니다.")
        
        if st.button("← 목록으로"):
            st.session_state.selected_movie = None
            st.session_state.review_page = int(0)
            st.session_state.review_movie_id = None
            st.rerun()

# ---------------- 영화 등록 ----------------
elif st.session_state.menu == "movie_add":
    st.title("🎬 영화 등록")
    with st.form("movie_form"):
        title = st.text_input("제목")
        release = st.date_input("개봉일", value=datetime.now())
        director = st.text_input("감독")
        genre = st.text_input("장르")
        poster = st.text_input("포스터 URL")
        if st.form_submit_button("등록"):
            if isinstance(release, str):
                release_str = release
            else:
                release_str = release.strftime("%Y-%m-%d")
            requests.post(f"{API}/movies", json={
                "title": title,
                "release_date": release_str,
                "director": director,
                "genre": genre,
                "poster_url": poster
            })
            st.success("등록 완료")

# ---------------- 리뷰 등록 ----------------
elif st.session_state.menu == "review_add":
    st.title("✍️ 리뷰 등록")
    movies = requests.get(f"{API}/movies").json()

    # 영화가 없는 경우
    if not movies:
        st.warning("⚠️ 등록된 영화가 없습니다. 먼저 영화를 등록해주세요.")
    else:
        # 영화가 있는 경우 - 입력 폼 표시
        movie_map = {m["title"]: m["id"] for m in movies}
        # 선택된 영화가 있으면 자동 선택, 없으면 첫 번째 영화 선택
        if st.session_state.review_movie_id:
            selected_movie_title = next(
                (m["title"] for m in movies if m["id"] == st.session_state.review_movie_id),
                list(movie_map.keys())[0]
            )
        else:
            selected_movie_title = list(movie_map.keys())[0]
        
        movie_idx = list(movie_map.keys()).index(selected_movie_title)
        movie = st.selectbox("영화 선택", movie_map.keys(), index=movie_idx)

        author = st.text_input("작성자")
        content = st.text_area("리뷰")

        if st.button("등록"):
            if author and content:
                requests.post(f"{API}/reviews", json={
                    "movie_id": movie_map[movie],
                    "author": author,
                    "content": content
                })
                st.success("✅ 리뷰 등록 완료")
                st.rerun()
            else:
                st.error("❌ 작성자와 리뷰 내용을 모두 입력하세요.")

    # 최근 리뷰
    st.markdown("### 🕒 최근 리뷰")
    reviews = requests.get(f"{API}/reviews").json()
    
    if not reviews:
        st.info("등록된 리뷰가 없습니다.")
    else:
        st.dataframe([{
            "영화 ID": r["movie_id"],
            "리뷰": r["content"],
            "감성": r["sentiment_label"],
            "감성분석점수": round(r["sentiment_confidence"], 2) if "sentiment_confidence" in r else round(r["sentiment_score"], 2),
            "평점": r["sentiment_score"]
        } for r in reviews], use_container_width=True)