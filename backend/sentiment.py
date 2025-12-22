import torch
from pathlib import Path
from typing import Tuple

from transformers import (
    BertTokenizer,
    BertConfig
)


torch.backends.quantized.engine = "qnnpack"



# =========================
# 모델 경로
# =========================
BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models" / "korean_movie_sentiment_model"
MODEL_WEIGHTS = MODEL_DIR / "pytorch_model_quantized.pt"

_device = torch.device("cpu")

_model = None
_tokenizer = None


# =========================
# 모델 로드 (1회)
# =========================
def load_model():
    global _model, _tokenizer

    if _model is not None:
        return _model, _tokenizer

    print(":arrows_counterclockwise: 감성분석 모델 로드 중...")

    try:
        # :one: tokenizer 로드
        _tokenizer = BertTokenizer.from_pretrained(MODEL_DIR)

        # :two: config 직접 생성 (중요)
        config = BertConfig.from_pretrained(
            MODEL_DIR,
            num_labels=3
        )

        # :three: 모델 구조 생성 (from_pretrained :x:)
        _model = torch.load(
            MODEL_WEIGHTS,
            weights_only = False,
            map_location=_device
        )
        _model.to(_device)
        _model.eval()

        print(":white_check_mark: 감성분석 모델 로드 성공")
        return _model, _tokenizer

    except Exception as e:
        print(f":x: 모델 로드 실패: {e}")
        return None, None


# =========================
# 감성 점수 계산 (개선된 로직)
# =========================
def calculate_sentiment_score(neg: float, neu: float, pos: float) -> Tuple[str, float, float]:
    """
    더 섬세한 감성 분석 로직
    - 확률의 차이도 고려
    - 중립 판정의 명확한 기준
    - 0~5점 스케일 변환
    """
    
    # 감정별 차이 계산
    pos_margin = pos - max(neg, neu)  # 긍정이 다른 감정들보다 얼마나 우월한지
    neg_margin = neg - max(pos, neu)  # 부정이 다른 감정들보다 얼마나 우월한지
    
    # 가장 높은 확률과 두 번째 확률의 차이
    sorted_probs = sorted([pos, neg, neu], reverse=True)
    confidence_gap = sorted_probs[0] - sorted_probs[1]
    
    # 1. 확률이 거의 비슷한 경우 → 중립
    if confidence_gap < 0.1:  # 10% 이내 차이
        label = "중립"
        confidence = neu
        sentiment_score = 2.5  # 0~5점 중 정중앙
    
    # 2. 중립이 가장 높은 경우
    elif neu >= pos and neu >= neg:
        label = "중립"
        confidence = neu
        sentiment_score = 2.5
    
    # 3. 긍정이 명확한 경우 (pos >= 0.4)
    elif pos >= neg and pos > neu and pos >= 0.4:
        label = "긍정"
        confidence = pos
        # 0.4~1.0 범위를 3~5점으로 매핑
        sentiment_score = 3.0 + (pos - 0.4) / 0.6 * 2.0
    
    # 4. 부정이 명확한 경우 (neg >= 0.4)
    elif neg >= pos and neg > neu and neg >= 0.4:
        label = "부정"
        confidence = neg
        # 0.4~1.0 범위를 1~1점으로 매핑
        sentiment_score = 2.0 - (neg - 0.4) / 0.6 * 1.0
    
    # 5. 긍정이 약한 경우 (0.3~0.4)
    elif pos >= neg and pos > neu and pos >= 0.3:
        label = "약긍정"
        confidence = pos
        sentiment_score = 2.75 + (pos - 0.3) / 0.1 * 0.25
    
    # 6. 부정이 약한 경우 (0.3~0.4)
    elif neg >= pos and neg > neu and neg >= 0.3:
        label = "약부정"
        confidence = neg
        sentiment_score = 2.25 - (neg - 0.3) / 0.1 * 0.25
    
    # 7. 기타 경우 (매우 약한 신호)
    else:
        label = "중립"
        confidence = max(pos, neg, neu)
        sentiment_score = 2.5
    
    return label, confidence, sentiment_score


# =========================
# 감성 분석
# =========================
def analyze_sentiment(text: str) -> Tuple[str, float, float]:
    model, tokenizer = load_model()

    if model is None:
        return "중립", 0.5, 2.5

    try:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(_device)

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)[0]

        neg, neu, pos = probs.tolist()

        # 개선된 로직 사용
        label, confidence, sentiment_score = calculate_sentiment_score(neg, neu, pos)

        print(
            f"✓ 감성분석 | "
            f"NEG={neg:.3f} NEU={neu:.3f} POS={pos:.3f} → {label} (별점: {sentiment_score:.2f}/5.0)"
        )

        return label, round(confidence, 3), round(sentiment_score, 2)

    except Exception as e:
        print(f":x: 감성분석 오류: {e}")
        return "중립", 0.5, 2.5