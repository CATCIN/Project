from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests
import boto3
import json
from datetime import datetime, timezone

# --- 프로젝트 모듈 임포트 ---
from models.model import Cat
from core.database import engine

# --- 라우터 및 클라이언트 설정 ---
router = APIRouter()
s3_client = boto3.client("s3")

# --- 환경 변수 및 상수 ---
S3_BUCKET = "catcin-bucket" # 실제 버킷 이름으로 설정
SAGEMAKER_NOTEBOOK_URL = "https://catcin-notebook.notebook.us-east-1.sagemaker.aws:8080/extract-features"

# --- Helper 함수 ---
def make_presigned_url(bucket: str, key: str, expires=600) -> str:
    """ S3 객체에 대한 임시 접근 URL을 생성 """
    return s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
    )

# =======================================================================
#  S3 경로를 받아 고양이를 식별하는 함수
#  - 이제 API 엔드포인트가 아닌, 내부 호출용 함수로 사용될 수 있습니다.
# ========================================================================
async def identify_cat_from_paths(s3_paths: list[str]):
    # --- 1. S3 경로를 Presigned URL로 변환 ---
    presigned_urls = []
    for s3_path in s3_paths:
        try:
            url = make_presigned_url(S3_BUCKET, s3_path)
            presigned_urls.append(url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"S3 Presigned URL 생성 오류: {s3_path}, error: {e}")

    # --- 2. SageMaker Notebook에 Presigned URL로 계산 요청 ---
    try:
        payload = {"presigned_urls": presigned_urls}
        response = requests.post(SAGEMAKER_NOTEBOOK_URL, json=payload, verify=False, timeout=60)
        response.raise_for_status()
        result = response.json()
        new_cat_vector_list = result.get("feature_vector")
        if not new_cat_vector_list:
            raise HTTPException(status_code=400, detail="SageMaker에서 특징 벡터를 추출하지 못했습니다.")
        new_cat_avg_vector = np.array(new_cat_vector_list).reshape(1, -1)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"SageMaker Notebook 서버 연결 오류: {e}")

    # --- 3. DB 비교 및 판별 ---
    known_cats = await engine.find(Cat, project={Cat.id: 1, Cat.feature_vector: 1})
    
    if not known_cats:
        new_cat = Cat(image_path=s3_paths, feature_vector=new_cat_avg_vector.flatten().tolist(), source="system")
        await engine.save(new_cat)
        return {"result": "new_cat_registered", "cat_id": new_cat.id}

    similarities = {}
    for cat in known_cats:
        known_vector = np.array(cat.feature_vector).reshape(1, -1)
        similarity = cosine_similarity(new_cat_avg_vector, known_vector)[0][0]
        similarities[cat.id] = similarity

    most_similar_cat_id = max(similarities, key=similarities.get)
    max_similarity = similarities[most_similar_cat_id]
    
    threshold = 0.85
    if max_similarity >= threshold:
        identified_cat = await engine.find_one(Cat, Cat.id == most_similar_cat_id)
        if identified_cat:
            identified_cat.stats_seen += 1
            identified_cat.last_seen = datetime.utcnow()
            await engine.save(identified_cat)
        return {"result": "identified", "cat_id": most_similar_cat_id, "similarity": float(max_similarity)}
    else:
        new_cat = Cat(image_path=s3_paths, feature_vector=new_cat_avg_vector.flatten().tolist(), source="system")
        await engine.save(new_cat)
        return {"result": "new_cat", "new_cat_id": new_cat.id, "most_similar_to": most_similar_cat_id, "similarity": float(max_similarity)}

# ==============================================
#  카메라가 직접 호출할 메인 API 엔드포인트
# ==============================================
@router.post("/recognize-from-shots", tags=["Recognition"], summary="촬영된 이미지 3장으로 고양이 식별")
async def recognize_from_shots(files: List[UploadFile] = File(...)):
    """
    카메라에서 촬영된 연속 3장의 이미지를 받아 S3에 업로드하고,
    업로드된 경로를 이용해 고양이 식별 로직을 호출하는 메인 API
    """
    if len(files) != 3:
        raise HTTPException(status_code=400, detail="반드시 3개의 이미지 파일이 필요합니다.")
        
    uploaded_s3_keys = []
    dt = datetime.now(timezone.utc)
    date_prefix = dt.strftime("%Y-%m-%d")
    timestamp = dt.strftime("%Y%m%d_%H%M%S")

    # 1. 전달받은 파일 3개를 S3에 업로드
    for i, file in enumerate(files):
        try:
            content = await file.read()
            ext = (file.filename.rsplit(".", 1)[-1] or "jpg")
            # 파일명을 타임스탬프와 인덱스로 생성 (예: 2025-09-15/20250915_133000_0.jpg)
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

    # 2. 업로드된 S3 경로들을 이용해 식별 함수 호출
    if len(uploaded_s3_keys) == 3:
        result = await identify_cat_from_paths(uploaded_s3_keys)
        return result
    else:
        raise HTTPException(status_code=500, detail="모든 파일이 정상적으로 업로드되지 않았습니다.")

# =================================================
#  사용자가 등록한 사진의 특징 벡터를 추출하는 API
# =================================================
@router.post("/generate-vector/{cat_id}", tags=["Recognition"], summary="지정된 고양이의 특징 벡터 생성/업데이트")
async def generate_vector_for_cat(cat_id: str):
    try:
        obj_id = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 cat_id 형식입니다.")

    cat = await engine.find_one(Cat, Cat.id == obj_id)
    if not cat:
        raise HTTPException(status_code=404, detail="해당 ID의 고양이를 찾을 수 없습니다.")
    
    if not cat.image_path:
        raise HTTPException(status_code=400, detail="벡터를 생성할 이미지가 등록되어 있지 않습니다.")

    # 헬퍼 함수를 호출하여 벡터를 받아옵니다.
    feature_vector_array = await get_vector_from_sagemaker(cat.image_path)
    
    # 받아온 벡터(numpy array)를 리스트로 변환하여 DB에 업데이트
    cat.feature_vector = feature_vector_array.flatten().tolist()
    cat.updated_at = datetime.utcnow() # 업데이트 시간 기록
    await engine.save(cat)
    
    return {"message": f"고양이(ID: {cat_id})의 특징 벡터가 성공적으로 업데이트되었습니다."}