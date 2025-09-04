# api/cat.py
from fastapi import APIRouter, HTTPException, Request
from odmantic import ObjectId
from models.model import Cat
from core.database import engine
import os, boto3

S3_BUCKET = os.getenv("S3_BUCKET", "catcin-bucket")
S3_REGION = os.getenv("AWS_REGION", "us-east-1")
s3_client = boto3.client("s3", region_name=S3_REGION)

def make_presigned_url(bucket: str, key: str, expires=600) -> str:
    return s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
    )

router = APIRouter()

# 고양이 등록
@router.post("/cats")
async def create_cat(cat: Cat):
    await engine.save(cat)
    return cat

# 전체 고양이 조회
@router.get("/cats")
async def all_cats():
    cats = await engine.find(Cat)
    result = []
    for c in cats:
        doc = c.dict()
        doc["id"] = str(c.id)  
        doc["image_url"] = make_presigned_url(S3_BUCKET, c.image_path, 600) if c.image_path else None
        result.append(doc)
    return result

# 특정 고양이 조회
@router.get("/cats/{cat_id}")
async def get_cat(cat_id: str):
    cat = await engine.find_one(Cat, Cat.id == ObjectId(cat_id))
    if cat is None:
        raise HTTPException(404, detail="Cat not found")
    doc = cat.dict()
    doc["id"] = str(cat.id)
    doc["image_url"] = make_presigned_url(S3_BUCKET, cat.image_path, 600) if cat.image_path else None
    return doc

# 고양이 삭제
@router.delete("/cats/{cat_id}", response_model=Cat)
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
