# 모델로부터 요청을 받고 서 처리하는 API
from fastapi import APIRouter
from schemas.recognition import CatRecognitionInput
from models.model import Cat
from core.database import engine

router = APIRouter()

@router.post("/recognition")
async def recognize_cat(data: CatRecognitionInput):
    new_cat = Cat(
        image_path=data.image_path,
        feature_vector=data.feature_vector,
        save_at=data.detected_at,
        source="system"
    )
    await engine.save(new_cat)

    return {
        "message": "New cat registered",
        "cat_id": str(new_cat.id)
    }
