import onnxruntime as ort
import numpy as np
from pathlib import Path
from typing import Tuple
from transformers import BertTokenizer
from huggingface_hub import snapshot_download

# =========================
# 모델 경로
# =========================
HF_REPO_ID = "jinsugyeong/korean_movie_onnx"
CACHE_DIR = Path("/tmp/onnx_model")  # Render에서 안전

_session = None
_tokenizer = None


# =========================
# 모델 로드 (한 번만 실행)
# =========================
def load_model():
    global _session, _tokenizer

    if _session is not None:
        return _session, _tokenizer
    
    print("🔄 감성분석 ONNX 모델 로드 시작")

    # 모델 파일 존재 여부 체크
    if not (CACHE_DIR / "model.onnx").exists():
        print("📥 모델 캐시 없음 → 다운로드")
        snapshot_download(
            repo_id=HF_REPO_ID,
            local_dir=CACHE_DIR,
            local_dir_use_symlinks=False
        )
    else:
        print("♻️ 캐시된 모델 사용")

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # 1️⃣ 레포 전체 다운로드 (model.onnx + model.onnx.data + tokenizer)
        local_repo_path = snapshot_download(
            repo_id=HF_REPO_ID,
            cache_dir=CACHE_DIR,
            local_dir_use_symlinks=False,  # ⚠ Render에서 필수
        )

        # 2️⃣ tokenizer 로드
        _tokenizer = BertTokenizer.from_pretrained(local_repo_path)

        # 3️⃣ ONNX Runtime 세션
        onnx_path = Path(local_repo_path) / "model.onnx"

        _session = ort.InferenceSession(
            str(onnx_path),
            providers=["CPUExecutionProvider"]
        )

        print("✅ 감성분석 ONNX 모델 로드 성공")
        return _session, _tokenizer

    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return None, None



# =========================
# 감성 점수 계산
# =========================
def calculate_sentiment_score(neg: float, neu: float, pos: float) -> Tuple[str, float, float]:
    """
    감성 분석 로직 (긍정/중립/부정)
    - 긍정과 부정이 모두 높으면 중립으로 판단
    """
    
    sorted_probs = sorted([pos, neg, neu], reverse=True)
    confidence_gap = sorted_probs[0] - sorted_probs[1]
    
    # 1. 긍정과 부정이 모두 높은 경우 (혼합 감정) → 중립
    # 예: "영상미는 좋지만 스토리가 아쉽다"
    if pos > 0.25 and neg > 0.25:
        label = "중립"
        confidence = neu
        sentiment_score = 3.0
    
    # 2. 확률이 거의 비슷한 경우 → 중립
    elif confidence_gap < 0.1:
        label = "중립"
        confidence = neu
        sentiment_score = 2.5
    
    # 3. 중립이 가장 높은 경우
    elif neu >= pos and neu >= neg:
        label = "중립"
        confidence = neu
        sentiment_score = 3.0
    
    # 4. 긍정이 명확한 경우
    elif pos > neu and pos > neg:
        label = "긍정"
        confidence = pos
        # 긍정 확률에 따라 3.0 ~ 5.0 범위로 스케일링
        sentiment_score = 3.0 + (pos * 2.0)
    
    # 5. 부정이 명확한 경우
    elif neg > neu and neg > pos:
        label = "부정"
        confidence = neg
        # 부정 확률에 따라 1.0 ~ 2.0 범위로 스케일링
        sentiment_score = 2.5 - (neg * 1.0)
    
    # 6. 기타 경우
    else:
        label = "중립"
        confidence = max(pos, neg, neu)
        sentiment_score = 2.5
    
    return label, confidence, sentiment_score


# =========================
# 감성 분석 (ONNX 추론)
# =========================
def analyze_sentiment(text: str) -> Tuple[str, float, float]:
    """
    ONNX 모델을 사용한 감성분석 + 키워드 기반 보정
    """
    session, tokenizer = load_model()

    if session is None:
        return "중립", 0.5, 3.0

    try:
        # 텍스트 길이 제한 (메모리 절약)
        text = text[:256]
        
        # 토크나이징
        inputs = tokenizer(
            text,
            return_tensors="np",  # NumPy array로 반환
            truncation=True,
            max_length=256,
            padding="max_length"
        )

        # ONNX 추론
        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64),
            "token_type_ids": inputs["token_type_ids"].astype(np.int64)
        }
        
        ort_outputs = session.run(None, ort_inputs)
        logits = ort_outputs[0][0]  # (batch_size, num_labels) → (num_labels,)
        
        # Softmax 계산
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / exp_logits.sum()
        
        neg, neu, pos = probs.tolist()
        
        # ===== 키워드 기반 혼합 감정 보정 =====
        
        # 1. 역접 접속사
        contrast_keywords = [
            "하지만", "그러나", "다만", "그런데", "근데", "BUT", "but",
            "오히려", "반면", "대신", "비록", "반대로", "아니라"
        ]
        
        # 2. 긍정 키워드
        positive_keywords = [
            "좋", "최고", "훌륭", "멋지", "완벽", "감동", "재밌", "재미",
            "화려", "압도", "대단", "멋", "환상", "끝내주", "굿", "좋아",
            "즐", "만족", "추천", "볼만", "괜찮", "훌륭", "대박", "재미있",
            "감명", "인상", "몰입", "수작", "명작", "일품", "예술", "탄탄", "짱"
        ]
        
        # 3. 강한 부정 키워드 (이것들이 많으면 무조건 부정)
        strong_negative_keywords = [
            "조잡", "졸작", "최악", "형편없", "쓰레기", "망작", "실패",
            "지루", "하품", "산만", "거슬리"
        ]
        
        # 4. 일반 부정 키워드
        negative_keywords = [
            "아쉽", "아쉬움", "단점", "별로", "실망", "비슷", "뻔", 
            "안", "못", "없", "나쁘", "평범", "무난", "그저", "그냥", "그럭저럭"
        ]
        
        # 5. 조건/양보 표현
        conditional_keywords = [
            "~만", "조금", "약간", "다소", "어느정도", "나름"
        ]
        
        # 키워드 개수 카운트 (문맥 고려)
        strong_negative_count = sum(1 for keyword in strong_negative_keywords if keyword in text)
        positive_count = sum(1 for keyword in positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        has_contrast = any(keyword in text for keyword in contrast_keywords)
        has_conditional = any(keyword in text for keyword in conditional_keywords)
        
        # ===== 우선순위 판단 =====
        
        # 1. 강한 부정 키워드가 2개 이상이면 무조건 부정으로 처리 (보정 안함)
        if strong_negative_count >= 2:
            # 모델 판단 그대로 사용 (보정하지 않음)
            pass
        
        # 2. 혼합 감정 패턴 감지
        else:
            is_mixed = False
            
            # 패턴 1: 역접 접속사 존재
            if has_contrast:
                is_mixed = True
            
            # 패턴 2: 긍정 + 부정 키워드 동시 존재 (개수로 판단)
            if positive_count >= 1 and negative_count >= 1:
                # 단, 부정이 압도적이면 혼합으로 보지 않음
                if negative_count + strong_negative_count > positive_count * 2:
                    is_mixed = False
                else:
                    is_mixed = True
            
            # 패턴 3: 조건부 표현 + (긍정 또는 부정)
            if has_conditional and (positive_count >= 1 or negative_count >= 1):
                is_mixed = True
            
            # 혼합 감정이 감지되면 확률 재조정
            if is_mixed:
                if pos > 0.6 or neg > 0.6:  # 한쪽이 60% 이상이면 보정
                    neu = 0.5
                    pos = 0.3
                    neg = 0.2

        # 감성 점수 계산
        label, confidence, sentiment_score = calculate_sentiment_score(neg, neu, pos)

        print(
            f"{text}\n"
            f"✓ 감성분석 | "
            f"NEG={neg:.3f} NEU={neu:.3f} POS={pos:.3f} → {label} (별점: {sentiment_score:.2f})"
        )

        return label, round(confidence, 3), round(sentiment_score, 2)

    except Exception as e:
        print(f"❌ 감성분석 오류: {e}")
        return "중립", 0.5, 3.0