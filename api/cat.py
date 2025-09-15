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


@router.post("/cats")
async def create_cat(cat: Cat):
    await engine.save(cat)
    return cat

@router.get("/cats", summary="모든 고양이 목록 조회")
async def all_cats():
    """DB에 저장된 모든 고양이의 목록을 반환합니다."""
    cats = await engine.find(Cat)
    
    response_data = []
    for c in cats:
        doc = c.model_dump() 
        doc["id"] = str(c.id) 

        # image_path가 비어있지 않다면, 그 리스트의 '첫 번째' 항목으로 URL을 생성합니다.
        if c.image_path:
            doc["image_url"] = make_presigned_url(S3_BUCKET, c.image_path[0])
        else:
            doc["image_url"] = None
        
        response_data.append(doc)
        
    return response_data

@router.get("/cats/{cat_id}", summary="특정 고양이 정보 조회")
async def get_cat(cat_id: str):
    """ID를 사용하여 특정 고양이의 상세 정보를 조회합니다."""
    try:
        obj_id = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 cat_id 형식입니다.")
        
    cat = await engine.find_one(Cat, Cat.id == obj_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="해당 ID의 고양이를 찾을 수 없습니다.")
    
    doc = cat.model_dump() 
    doc["id"] = str(cat.id)
    
    if cat.image_path:
        doc["image_url"] = make_presigned_url(S3_BUCKET, cat.image_path[0])
    else:
        doc["image_url"] = None
        
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
