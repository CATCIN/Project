# api/recognition.py

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from odmantic.query import desc
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from models.model import Cat, Medicine, MediSchedule, MediLog
import numpy as np
import requests
import boto3
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
SAGEMAKER_NOTEBOOK_URL = "https://supermediocre-unbrined-rebecka.ngrok-free.dev/extract-features"
SIMILARITY_THRESHOLD = 0.60

def make_presigned_url(bucket: str, key: str, expires=600) -> str:
    return s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
    )

async def get_next_cat_code() -> str:
    count = await engine.count(Cat)
    return f"CAT_{count + 1:03d}"

async def get_vectors_from_sagemaker(s3_keys: List[str]) -> np.ndarray:
    """S3 키 리스트를 SageMaker로 보내 특징 벡터 '리스트'를 추출합니다."""
    presigned_urls = [make_presigned_url(S3_BUCKET, key) for key in s3_keys]
    try:
        payload = {"presigned_urls": presigned_urls}
        response = requests.post(SAGEMAKER_NOTEBOOK_URL, json=payload, verify=False, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        vectors = result.get("feature_vector")
        
        if not vectors or not isinstance(vectors, list) or len(vectors) == 0:
            raise HTTPException(status_code=400, detail="SageMaker에서 유효한 특징 벡터 리스트를 받지 못했습니다.")
            
        return np.array(vectors)
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"SageMaker Notebook 서버 연결 오류: {e}")


# ==============================================================================
# API 엔드포인트
# ==============================================================================
@router.post("/recognize-and-get-dues", tags=["Camera Workflow"], summary="[카메라용 통합] 식별 및 투약 필요 약 조회")
async def recognize_and_get_dues(files: List[UploadFile] = File(...)):
    """
    카메라에서 촬영된 이미지를 받아 고양이를 식별하고,
    즉시 투약이 필요한 약 목록까지 한 번에 반환하는 통합 API.
    """
    if not files:
        raise HTTPException(status_code=400, detail="하나 이상의 이미지 파일이 필요합니다.")
    
    # 1. 이미지 S3 업로드 (recognize_from_shots 로직)
    uploaded_s3_keys = []
    dt = datetime.now(timezone.utc)
    date_prefix = dt.strftime("%Y-%m-%d")
    timestamp = dt.strftime("%Y%m%d_%H%M%S")

    for i, file in enumerate(files):
        s3_key = f"{date_prefix}/{timestamp}_{i}.jpg"
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET, Key=s3_key, Body=await file.read(),
                ContentType=file.content_type or "image/jpeg"
            )
            uploaded_s3_keys.append(s3_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류: {e}")

    # 2. 고양이 식별 로직 호출 (_identify_cat_logic)
    recognition_result = await _identify_cat_logic(uploaded_s3_keys)
    
    # 3. 식별 결과에서 cat_id 추출
    cat_id = recognition_result.get("cat_id") or recognition_result.get("new_cat_id")
    if not cat_id:
        raise HTTPException(status_code=500, detail="식별 과정에서 cat_id를 얻지 못했습니다.")

    # 4. 추출한 cat_id로 투약 필요 약 조회 로직 실행 (get_due_medicines_for_cat 로직)
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="반환된 cat_id가 유효하지 않습니다.")

    cat = await engine.find_one(Cat, Cat.id == cat_oid)
    if not cat:
        raise HTTPException(status_code=404, detail="식별된 고양이 ID를 DB에서 찾을 수 없습니다.")

    now = datetime.utcnow()
    all_medicines = await engine.find(Medicine)
    due_medicines = []

    for med in all_medicines:
        schedule = await engine.find_one(MediSchedule, {"medicine": med.id, "cat_id": cat_oid})
        if not schedule:
            schedule = await engine.find_one(MediSchedule, {"medicine": med.id, "cat_id": None})
        if not schedule:
            continue

        last_log = await engine.find_one(
            MediLog,
            {"cat_id": cat_oid, "medicine_id": med.id},
            sort=desc(MediLog.administered_at)
        )

        is_due = False
        reason = ""
        if not last_log:
            is_due = True
            reason = "투약 기록이 없어 즉시 투약 가능"
        else:
            next_due_date = last_log.administered_at + timedelta(days=schedule.interval_days)
            if now >= next_due_date:
                is_due = True
                reason = f"마지막 투약({last_log.administered_at.strftime('%Y-%m-%d')}) 후 {schedule.interval_days}일이 경과함"

        if is_due:
            due_medicines.append({
                "medicine_id": str(med.id),
                "medicine_name": med.name,
                "dose": schedule.dose,
                "is_due": True,
                "reason": reason
            })

    final_response = {
        "recognition": recognition_result,
        "medication": {"due_medicines": due_medicines}
    }
    
    return final_response

async def _identify_cat_logic(s3_paths: list[str]):
    """S3 경로 리스트를 받아 고양이를 식별하는 핵심 로직 (중복 등록 방지 추가)"""
    new_cat_vectors = await get_vectors_from_sagemaker(s3_paths)
    average_vector = np.mean(new_cat_vectors, axis=0).reshape(1, -1)
    
    known_cats = await engine.find(Cat)
    
    # 1. DB에 고양이가 한 마리도 없는 초기 상태
    if not known_cats:
        new_cat = Cat(
            image_path=s3_paths, 
            feature_vector=average_vector.flatten().tolist(), 
            source="system", cat_code=await get_next_cat_code()
        )
        await engine.save(new_cat)
        return {"result": "new_cat_registered", "cat_id": str(new_cat.id)}

    # 2. 유사도 계산
    similarities = {
        str(cat.id): float(cosine_similarity(average_vector, np.array(cat.feature_vector).reshape(1, -1))[0][0])
        for cat in known_cats
    }
    
    most_similar_cat_id_str = max(similarities, key=similarities.get)
    max_similarity = similarities[most_similar_cat_id_str]
    
    # 3. 임계값 이상이면 기존 고양이로 식별
    if max_similarity >= SIMILARITY_THRESHOLD:
        identified_cat = await engine.find_one(Cat, Cat.id == ObjectId(most_similar_cat_id_str))
        if identified_cat:
            identified_cat.stats_seen += 1
            identified_cat.updated_at = datetime.utcnow() 
            await engine.save(identified_cat)
        return {"result": "identified", "cat_id": most_similar_cat_id_str, "similarity": max_similarity}
    
    else:
        very_similar_cat = await engine.find_one(
            Cat, 
            {"feature_vector": {"$all": average_vector.flatten().tolist()}}
        )
        if very_similar_cat:
             return {
                "result": "already_registered_by_another_request", 
                "cat_id": str(very_similar_cat.id),
                "message": "거의 동시에 발생한 다른 요청에 의해 이미 등록되었습니다."
             }
        new_cat = Cat(
            image_path=s3_paths, 
            feature_vector=average_vector.flatten().tolist(), 
            source="system", cat_code=await get_next_cat_code()
        )
        await engine.save(new_cat)
        return {
            "result": "new_cat_registered", "new_cat_id": str(new_cat.id), 
            "most_similar_to": most_similar_cat_id_str, "similarity": max_similarity
        }

@router.post("/register-manual", tags=["Recognition"], summary="[사용자용] 사진 1장으로 등록")
async def register_from_site(file: UploadFile = File(...), note: str = Form("")):
    try:
        s3_key = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}/{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.user.jpg"
        s3_client.put_object(
            Bucket=S3_BUCKET, Key=s3_key, Body=await file.read(),
            ContentType=file.content_type or "image/jpeg",
        )
        
        feature_vector = (await get_vectors_from_sagemaker([s3_key])).flatten().tolist()
        new_cat = Cat(
            image_path=[s3_key], feature_vector=feature_vector,
            source="user", note=note, cat_code=await get_next_cat_code()
        )
        await engine.save(new_cat)
        return new_cat
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"수동 등록 중 오류 발생: {e}")

@router.post("/generate-vector/{cat_id}", tags=["Recognition"], summary="[관리용] 기존 고양이 벡터 재계산")
async def regenerate_vector_for_cat(cat_id: str):
    try:
        obj_id = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 cat_id 형식입니다.")

    cat = await engine.find_one(Cat, Cat.id == obj_id)
    if not cat:
        raise HTTPException(status_code=404, detail="해당 ID의 고양이를 찾을 수 없습니다.")
    if not cat.image_path:
        raise HTTPException(status_code=400, detail="벡터를 생성할 이미지가 없습니다.")

    # 여러 이미지의 벡터를 평균내어 업데이트
    feature_vectors = await get_vectors_from_sagemaker(cat.image_path)
    average_vector = np.mean(feature_vectors, axis=0).flatten().tolist()
    
    cat.feature_vector = average_vector
    cat.updated_at = datetime.utcnow()
    await engine.save(cat)
    
    return {"message": f"고양이(ID: {cat_id})의 특징 벡터가 성공적으로 업데이트되었습니다."}
