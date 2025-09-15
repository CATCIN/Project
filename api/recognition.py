from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests
import boto3
import json
from datetime import datetime, timezone
import os

# --- 프로젝트 모듈 임포트 ---
from models.model import Cat
from core.database import engine
from odmantic import ObjectId

# --- 라우터 및 클라이언트 설정 ---
router = APIRouter()
s3_client = boto3.client("s3")

# --- 환경 변수 및 상수 ---
S3_BUCKET = os.getenv("S3_BUCKET", "catcin-bucket")
SAGEMAKER_NOTEBOOK_URL = "https://b69657225980.ngrok-free.app/extract-features"

# ==============================================================================
#  Helper 함수
# ==============================================================================
def make_presigned_url(bucket: str, key: str, expires=600) -> str:
    """S3 객체에 대한 임시 접근 URL을 생성"""
    return s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
    )

async def get_next_cat_code() -> str:
    """새로운 고양이 코드를 생성 (예: CAT_001)."""
    count = await engine.count(Cat)
    next_id = count + 1
    return f"CAT_{next_id:03d}"

async def get_vector_from_sagemaker(s3_keys: List[str]) -> np.ndarray:
    presigned_urls = [make_presigned_url(S3_BUCKET, key) for key in s3_keys]
    try:
        payload = {"presigned_urls": presigned_urls}
        response = requests.post(SAGEMAKER_NOTEBOOK_URL, json=payload, verify=False, timeout=60)
        response.raise_for_status()
        result = response.json()
        vector_list = result.get("feature_vector")
        if not vector_list:
            raise HTTPException(status_code=400, detail="SageMaker에서 특징 벡터를 추출하지 못했습니다.")
        return np.array(vector_list).reshape(1, -1)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"SageMaker Notebook 서버 연결 오류: {e}")

async def identify_cat_from_paths(s3_paths: list[str]):
    """S3 경로 리스트를 받아 고양이를 식별하는 핵심 로직"""
    new_cat_avg_vector = await get_vector_from_sagemaker(s3_paths)
    known_cats = await engine.find(Cat, project={Cat.id: 1, Cat.feature_vector: 1})
    
    if not known_cats:
        new_cat = Cat(
            image_path=s3_paths, 
            feature_vector=new_cat_avg_vector.flatten().tolist(), 
            source="system",
            cat_code=await get_next_cat_code()
        )
        await engine.save(new_cat)
        return {"result": "new_cat_registered", "cat_id": new_cat.id}

    similarities = {cat.id: cosine_similarity(new_cat_avg_vector, np.array(cat.feature_vector).reshape(1, -1))[0][0] for cat in known_cats}
    most_similar_cat_id = max(similarities, key=similarities.get)
    max_similarity = similarities[most_similar_cat_id]
    
    if max_similarity >= 0.85:
        identified_cat = await engine.find_one(Cat, Cat.id == most_similar_cat_id)
        if identified_cat:
            identified_cat.stats_seen += 1
            identified_cat.updated_at = datetime.utcnow() 
            await engine.save(identified_cat)
        return {"result": "identified", "cat_id": most_similar_cat_id, "similarity": float(max_similarity)}
    else:
        new_cat = Cat(
            image_path=s3_paths, 
            feature_vector=new_cat_avg_vector.flatten().tolist(), 
            source="system",
            cat_code=await get_next_cat_code()
        )
        await engine.save(new_cat)
        return {"result": "new_cat", "new_cat_id": new_cat.id, "most_similar_to": most_similar_cat_id, "similarity": float(max_similarity)}

# ==============================================================================
#  API 엔드포인트
# ==============================================================================
@router.post("/recognize-from-shots", tags=["Recognition"], summary="[카메라용] 촬영된 3장 이미지로 식별")
async def recognize_from_shots(files: List[UploadFile] = File(...)):
    if len(files) != 3:
        raise HTTPException(status_code=400, detail="반드시 3개의 이미지 파일이 필요합니다.")
        
    uploaded_s3_keys = []
    dt = datetime.now(timezone.utc)
    date_prefix = dt.strftime("%Y-%m-%d")
    timestamp = dt.strftime("%Y%m%d_%H%M%S")

    for i, file in enumerate(files):
        try:
            content = await file.read()
            ext = (file.filename.rsplit(".", 1)[-1] or "jpg")
            s3_key = f"{date_prefix}/{timestamp}_{i}.{ext}"
            
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=content,
                ContentType=file.content_type or "image/jpeg",
            )
            uploaded_s3_keys.append(s3_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{i+1}번째 파일 업로드 중 오류 발생: {e}")

    if len(uploaded_s3_keys) == 3:
        result = await identify_cat_from_paths(uploaded_s3_keys)
        return result
    else:
        raise HTTPException(status_code=500, detail="모든 파일이 정상적으로 업로드되지 않았습니다.")

@router.post("/register-manual", tags=["Recognition"], summary="[사용자용] 사진 1장으로 등록 및 벡터 생성")
async def register_from_site_and_generate_vector(
    file: UploadFile = File(...),
    note: str = Form(""),
):
    try:
        content = await file.read()
        s3_key = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}/{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.user.jpg"

        s3_client.put_object(
            Bucket=S3_BUCKET, Key=s3_key, Body=content,
            ContentType=file.content_type or "image/jpeg",
        )

        feature_vector_array = await get_vector_from_sagemaker([s3_key])
        feature_vector = feature_vector_array.flatten().tolist()

        cat = Cat(
            image_path=[s3_key],
            feature_vector=feature_vector,
            source="user",
            note=note,
            cat_code=await get_next_cat_code()
        )
        await engine.save(cat)

        return {
            "cat_id": str(cat.id),
            "image_key": s3_key,
            "image_url": make_presigned_url(S3_BUCKET, s3_key),
            "message": "고양이 등록 및 특징 벡터 생성이 완료되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수동 등록 중 오류 발생: {e}")

@router.post("/generate-vector/{cat_id}", tags=["Recognition"], summary="[관리용] 기존 고양이 벡터 재계산")
async def generate_vector_for_cat(cat_id: str):
    """DB에 저장된 고양이의 이미지 경로를 이용해 특징 벡터를 재계산하고 업데이트"""
    try:
        obj_id = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 cat_id 형식입니다.")

    cat = await engine.find_one(Cat, Cat.id == obj_id)
    if not cat:
        raise HTTPException(status_code=404, detail="해당 ID의 고양이를 찾을 수 없습니다.")
    
    if not cat.image_path:
        raise HTTPException(status_code=400, detail="벡터를 생성할 이미지가 등록되어 있지 않습니다.")

    feature_vector_array = await get_vector_from_sagemaker(cat.image_path)
    
    cat.feature_vector = feature_vector_array.flatten().tolist()
    cat.updated_at = datetime.utcnow()
    await engine.save(cat)
    
    return {"message": f"고양이(ID: {cat_id})의 특징 벡터가 성공적으로 업데이트되었습니다."}