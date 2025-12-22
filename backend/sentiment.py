import torch
from pathlib import Path
from typing import Tuple
import gdown
import zipfile
from transformers import BertTokenizer, BertConfig


torch.backends.quantized.engine = "qnnpack"


# =========================
# 모델 경로
# =========================
BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models" / "my_korean_movie_sentiment_model"
MODEL_WEIGHTS = MODEL_DIR / "pytorch_model_quantized.pt"

_device = torch.device("cpu")
_model = None
_tokenizer = None


# =========================
# 모델 로드 (메모리 최적화)
# =========================
def load_model():
    global _model, _tokenizer

    if _model is not None:
        return _model, _tokenizer

    print("🔄 감성분석 모델 로드 중...")

    try:
        # tokenizer 로드
        _tokenizer = BertTokenizer.from_pretrained(MODEL_DIR)

        # config 로드
        config = BertConfig.from_pretrained(
            MODEL_DIR,
            num_labels=3
        )

        # 모델 로드
        _model = torch.load(
            MODEL_WEIGHTS,
            weights_only=False,
            map_location=_device
        )
        _model.to(_device)
        _model.eval()
        
        # 중요: 그래디언트 비활성화 (메모리 절약)
        for param in _model.parameters():
            param.requires_grad = False
        
        # 동적 양자화 (메모리 30% 감소)
        try:
            _model = torch.quantization.quantize_dynamic(
                _model,
                {torch.nn.Linear},
                dtype=torch.qint8
            )
            print("✅ 동적 양자화 적용됨")
        except:
            print("⚠️ 양자화 실패 (모델이 이미 양자화되었을 수 있음)")

        print("☑️ 감성분석 모델 로드 성공")
        return _model, _tokenizer

    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return None, None


# =========================
# 감성 점수 계산 (개선된 로직)
# =========================
def calculate_sentiment_score(neg: float, neu: float, pos: float) -> Tuple[str, float, float]:
    """
    더 섬세한 감성 분석 로직
    """
    
    sorted_probs = sorted([pos, neg, neu], reverse=True)
    confidence_gap = sorted_probs[0] - sorted_probs[1]
    
    # 1. 확률이 거의 비슷한 경우 → 중립
    if confidence_gap < 0.1:
        label = "중립"
        confidence = neu
        sentiment_score = 2.5
    
    # 2. 중립이 가장 높은 경우
    elif neu >= pos and neu >= neg:
        label = "중립"
        confidence = neu
        sentiment_score = 2.5
    
    # 3. 긍정이 명확한 경우
    elif pos >= neg and pos > neu and pos >= 0.4:
        label = "긍정"
        confidence = pos
        sentiment_score = 3.0 + (pos - 0.4) / 0.6 * 2.0
    
    # 4. 부정이 명확한 경우
    elif neg >= pos and neg > neu and neg >= 0.4:
        label = "부정"
        confidence = neg
        sentiment_score = 2.0 - (neg - 0.4) / 0.6 * 1.0
    
    # 5. 긍정이 약한 경우
    elif pos >= neg and pos > neu and pos >= 0.3:
        label = "약긍정"
        confidence = pos
        sentiment_score = 2.75 + (pos - 0.3) / 0.1 * 0.25
    
    # 6. 부정이 약한 경우
    elif neg >= pos and neg > neu and neg >= 0.3:
        label = "약부정"
        confidence = neg
        sentiment_score = 2.25 - (neg - 0.3) / 0.1 * 0.25
    
    # 7. 기타 경우
    else:
        label = "중립"
        confidence = max(pos, neg, neu)
        sentiment_score = 2.5
    
    return label, confidence, sentiment_score


# =========================
# 감성 분석 (메모리 최적화)
# =========================
def analyze_sentiment(text: str) -> Tuple[str, float, float]:
    """
    메모리 효율적인 감성분석
    - 텍스트 길이 제한
    - 배치 처리 최소화
    - 메모리 정리
    """
    model, tokenizer = load_model()

    if model is None:
        return "중립", 0.5, 2.5

    try:
        # 텍스트 길이 제한 (메모리 절약)
        text = text[:256]  # 256 토큰으로 제한
        
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=256,  # 512 → 256으로 감소
            padding=True
        ).to(_device)

        # no_grad로 메모리 절약
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
    
    finally:
        # 메모리 정리
        if 'inputs' in locals():
            del inputs
        torch.cuda.empty_cache()