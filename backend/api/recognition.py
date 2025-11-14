# api/recognition.py
from fastapi import APIRouter, HTTPException
from typing import List, Tuple
import numpy as np

from schemas.recognition import CatRecognitionInput
from models.model import Cat
from core.database import engine
from models.embedding import CatEmbedding
from core.utils import l2_normalize, l2_normalize_list, cosine

router = APIRouter(prefix="/recognitions", tags=["recognitions"])

# ---- 공통 정책 ----
TAU = 0.68          # 코사인 유사도 임계값
GAMMA = 0.05        # margin
EMA_ALPHA = 0.20    # 프로토타입 업데이트 계수

# ---- 내부 유틸 ----
async def _fetch_all_cats() -> List[Cat]:  
    # DB에서 모든 고양이 로드
    return await engine.find(Cat)

def _topk_by_cosine(q_norm: np.ndarray, cats: List[Cat], k: int = 3) -> List[Tuple[Cat, float]]:
    # 들어온 고양이들 중 코사인 유사도 기준 상위 k개 반환 (Top-K 후보 추출)
    scored: List[Tuple[Cat, float]] = []            # 유사도 저장 리스트
    for c in cats:
        proto = getattr(c, "feature_vector", None)  # = DB벡터
        if not proto:
            continue
        s = cosine(q_norm, l2_normalize(np.asarray(proto, dtype=np.float32)))  # 코사인 유사도 계산
        scored.append((c, s))
    scored.sort(key=lambda x: -x[1])
    return scored[:k]     # 상위 k(3)개 반환

def _ema_update(old_vec: np.ndarray, new_vec_normed: np.ndarray, alpha: float) -> np.ndarray:
    # 기존 벡터와 새 벡터를 EMA 방식으로 업데이트
    return l2_normalize((1.0 - alpha) * old_vec + alpha * new_vec_normed)

def _pick_source(data: CatRecognitionInput) -> str:
    val = getattr(data, "source", None)
    return val if val in ("system", "user") else "system"

@router.post("/recognition")
async def recognize_cat(data: CatRecognitionInput):
    # 1) 임베딩 정규화
    q_raw = np.asarray(data.feature_vector, dtype=np.float32)
    if q_raw.ndim != 1 or q_raw.size == 0:
        raise HTTPException(status_code=400, detail="feature_vector must be 1-D non-empty")
    q = l2_normalize(q_raw)
    src = _pick_source(data)
    q_norm_list = q.tolist()   # CatEmbedding에 넣을 L2 리스트

    # 2) 후보 탐색
    cats = await _fetch_all_cats()
    top = _topk_by_cosine(q, cats, k=3)

    if not top:
        # 비어있음 → 신규 등록
        new_cat = Cat(
            image_path=data.image_path,
            feature_vector=q_norm_list,
            save_at=data.detected_at,
            source=src,
            stats_seen=1,
            last_seen=data.detected_at or new_cat.save_at,
            created_at=data.detected_at or new_cat.save_at,
            updated_at=data.detected_at or new_cat.save_at,
        )
        await engine.save(new_cat)

        # 임베딩 로그 저장 (unknown)
        await engine.save(CatEmbedding(
            cat_id=None,                      
            embedding=q_norm_list,         
            source=src,
            image_path=data.image_path
        ))

        return {
            "message": "First cat registered (empty gallery)",
            "result": "unknown",
            "cat_id": str(new_cat.id),
            "s1": None, "s2": None, "margin": None,
            "source": src,
            "policy": {"tau": TAU, "gamma": GAMMA, "alpha": EMA_ALPHA}
        }

    # 3) 단일 프레임 판정
    (best_cat, s1) = top[0]
    s2 = top[1][1] if len(top) > 1 else -1.0
    margin = s1 - s2

    if s1 >= TAU and margin >= GAMMA:
        # 등록자로 인정 → 프로토타입/메타 업데이트
        old = np.asarray(best_cat.feature_vector, dtype=np.float32) if best_cat.feature_vector else q
        best_cat.feature_vector = _ema_update(l2_normalize(old), q, EMA_ALPHA).tolist()
        best_cat.image_path = data.image_path
        best_cat.save_at = data.detected_at
        best_cat.source = src
        best_cat.stats_seen = (best_cat.stats_seen or 0) + 1
        best_cat.last_seen = data.detected_at or best_cat.last_seen
        best_cat.updated_at = data.detected_at or best_cat.updated_at
        await engine.save(best_cat)

        # 임베딩 로그 저장 (accepted → cat_id 지정)
        await engine.save(CatEmbedding(
            cat_id=best_cat.id,              
            embedding=q_norm_list,
            source=src,
            image_path=data.image_path
        ))

        return {
            "message": "Recognized existing cat",
            "result": "accepted",
            "cat_id": str(best_cat.id),
            "s1": s1, "s2": s2, "margin": margin,
            "source": src,
            "policy": {"tau": TAU, "gamma": GAMMA, "alpha": EMA_ALPHA}
        }

    # 기준 미달 → 신규 등록
    new_cat = Cat(
        image_path=data.image_path,
        feature_vector=q_norm_list,
        save_at=data.detected_at,
        source=src,
        stats_seen=1,
        last_seen=data.detected_at,
        created_at=data.detected_at or datetime.utcnow(),
        updated_at=data.detected_at or datetime.utcnow(),
    )
    await engine.save(new_cat)

    # 임베딩 로그 저장
    await engine.save(CatEmbedding(
        cat_id=None,
        embedding=q_norm_list,
        source=src,
        image_path=data.image_path
    ))

    return {
        "message": "New cat registered",
        "result": "unknown",
        "cat_id": str(new_cat.id),
        "s1": s1, "s2": s2, "margin": margin,
        "source": src,
        "policy": {"tau": TAU, "gamma": GAMMA, "alpha": EMA_ALPHA}
    }
