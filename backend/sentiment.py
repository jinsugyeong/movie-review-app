import torch
from pathlib import Path
from typing import Tuple
from transformers import BertTokenizer, BertConfig

BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models" / "my_korean_movie_sentiment_model"
MODEL_WEIGHTS = MODEL_DIR / "pytorch_model_quantized.pt"

_device = torch.device("cpu")
_model = None
_tokenizer = None

def load_model():
    """필요할 때만 모델 로드 (메모리 절약)"""
    global _model, _tokenizer

    if _model is not None:
        return _model, _tokenizer

    print("모델 로드 중...")

    try:
        _tokenizer = BertTokenizer.from_pretrained(MODEL_DIR)
        config = BertConfig.from_pretrained(MODEL_DIR, num_labels=3)
        
        # 모델을 eval 모드로, 그래디언트 비활성화
        _model = torch.load(MODEL_WEIGHTS, weights_only=False, map_location=_device)
        _model.to(_device)
        _model.eval()
        
        # 중요: 그래디언트 비활성화 (메모리 절약)
        for param in _model.parameters():
            param.requires_grad = False

        print("✅ 모델 로드 성공")
        return _model, _tokenizer

    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return None, None

def analyze_sentiment(text: str) -> Tuple[str, float, float]:
    """감성 분석 (메모리 효율적)"""
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

        # no_grad 사용 (메모리 절약)
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)[0]

        neg, neu, pos = probs.tolist()

        # 감성 분류
        if pos >= neg and pos >= neu:
            label = "긍정"
            confidence = pos
            sentiment_score = 0.5 + pos * 0.5
        elif neg >= pos and neg >= neu:
            label = "부정"
            confidence = neg
            sentiment_score = (1.0 - neg) * 0.5
        else:
            label = "중립"
            confidence = neu
            sentiment_score = 0.5

        print(f"✓ 감성분석 | NEG={neg:.3f} NEU={neu:.3f} POS={pos:.3f} → {label}")

        return label, round(confidence, 3), round(sentiment_score, 3)

    except Exception as e:
        print(f"❌ 감성분석 오류: {e}")
        return "중립", 0.5, 2.5
    finally:
        # 메모리 정리
        if 'inputs' in locals():
            del inputs
        torch.cuda.empty_cache()