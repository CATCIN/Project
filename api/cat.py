# api/cat.py
from fastapi import APIRouter, HTTPException, Form, Request
from odmantic import ObjectId
from models.model import MediSchedule, Medicine, MediLog, Cat
from core.database import engine
from datetime import datetime, timedelta
import os, boto3
from typing import List
from odmantic.query import desc

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
    """DB에 저장된 모든 고양이의 목록을 반환"""
    cats = await engine.find(Cat)
    
    response_data = []
    for c in cats:
        doc = c.model_dump() 
        doc["id"] = str(c.id) 
        if c.image_path:
            doc["image_url"] = make_presigned_url(S3_BUCKET, c.image_path[0])
        else:
            doc["image_url"] = None
        
        response_data.append(doc)
        
    return response_data

@router.get("/cats/recent", summary="[메인페이지용] 최근 인식된 고양이 6마리 조회")
async def get_recent_cats():
    """
    가장 최근에 업데이트된 고양이 6마리의 목록을 반환
    """
    recent_cats = await engine.find(
        Cat, 
        sort=desc(Cat.updated_at), 
        limit=6
    )
    
    response_data = []
    for c in recent_cats:
        doc = c.model_dump()
        doc["id"] = str(c.id)
        if c.image_path:
            doc["image_url"] = make_presigned_url(S3_BUCKET, c.image_path[0])
        else:
            doc["image_url"] = None
        response_data.append(doc)
            
    return response_data

@router.get("/cats/{cat_id}", summary="[모듈] 특정 고양이 정보 조회")
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

@router.get("/cats/{cat_id}/schedules", summary="[모듈] 특정 고양이의 투약 스케줄 조회")
async def get_cat_schedules(cat_id: str) -> dict:
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 cat_id 형식입니다.")

    cat_exists = await engine.find_one(Cat, Cat.id == cat_oid)
    if not cat_exists:
        raise HTTPException(status_code=404, detail="해당 ID의 고양이를 찾을 수 없습니다.")

    schedules = await engine.find(MediSchedule, {"$or": [{"cat_id": cat_oid}, {"cat_id": None}]})

    response_schedules = []
    for schedule in schedules:
        medicine_doc = await engine.find_one(Medicine, Medicine.id == schedule.medicine.id)
        if medicine_doc:
            response_schedules.append({
                "schedule_id": str(schedule.id),
                "medicine_name": medicine_doc.name,
                "medicine_category": medicine_doc.category,
                "interval_days": schedule.interval_days,
                "dose": schedule.dose,
            })
    
    return {"medications_status": response_schedules}

@router.get("/cats/{cat_id}/due-medicines", summary="[모듈] 특정 고양이의 투약 필요 약 조회")
async def get_due_medicines_for_cat(cat_id: str):
    """
    고양이 ID를 받아, 현재 투약이 필요한 약 목록을 반환함.
    """
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cat_id format.")

    # 1. 고양이 정보 조회
    cat = await engine.find_one(Cat, Cat.id == cat_oid)
    if not cat:
        raise HTTPException(status_code=404, detail="Cat with this ID not found.")

    now = datetime.utcnow()
    all_medicines = await engine.find(Medicine)
    due_medicines = []

    # 2. 모든 약에 대해 투약 필요 여부 계산
    for med in all_medicines:
        # 해당 고양이의 개인 스케줄 또는 전체 스케줄을 찾음
        schedule = await engine.find_one(MediSchedule, {"medicine": med.id, "cat_id": cat_oid})
        if not schedule:
            schedule = await engine.find_one(MediSchedule, {"medicine": med.id, "cat_id": None})
        
        # 스케줄이 없으면 이 약은 대상이 아님
        if not schedule:
            continue

        # 해당 약에 대한 마지막 투약 기록을 찾음
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

    return {"due_medicines": due_medicines}