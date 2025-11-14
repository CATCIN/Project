# api/cat.py
from fastapi import APIRouter, HTTPException, Request
from odmantic import ObjectId
from models.model import Cat
from core.database import engine

router = APIRouter()

# 고양이 등록
@router.post("/cats")   
async def create_cat(cat: Cat):
    await engine.save(cat)
    return cat

# 전체 고양이 조회
@router.get("/cats")
async def all_cats():
    return await engine.find(Cat)

# 특정 고양이 조회(아직은 등록한 내용 그대로만)
@router.get("/cats/{cat_id}", response_model=Cat)
async def get_cat(cat_id: str):
    cat = await engine.find_one(Cat, Cat.id == ObjectId(cat_id))
    if cat is None:
            raise HTTPException(404, detail="Cat not found")
    return cat

# 고양이 삭제
@router.delete("/cats/{cat_id}", response_model = Cat)
async def delete_cat(cat_id: str):
    cat = await engine.find_one(Cat, Cat.id == ObjectId(cat_id))
    if cat is None:
        raise HTTPException(404, detail="Cat not found")
    await engine.delete(cat)
    return cat

# 고양이 수정
@router.patch("/cats/{cat_id}", response_model=Cat)
async def update_cat(cat_id: str, request: Request):
    cat = await engine.find_one(Cat, Cat.id == ObjectId(cat_id))
    if cat is None:
        raise HTTPException(status_code=404, detail="Cat not found")

    update_data = await request.json()

    for field, value in update_data.items():
        if hasattr(cat, field):
            setattr(cat, field, value)

    await engine.save(cat)
    return cat
