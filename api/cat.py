# api/cat.py
from fastapi import APIRouter, HTTPException, Form, Request, Query
from bson import ObjectId
from models.model import MediSchedule, Medicine, MediLog, Cat
from core.database import engine
from datetime import datetime, timedelta, timezone
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

@router.get("/cats/due-today", summary="[메인] UTC 기준 오늘 또는 연체된 투약 대상 고양이 N마리")
async def get_cats_due_today(limit: int = Query(3, ge=1, le=50)):
    today_utc = datetime.utcnow().date()
    cats = await engine.find(Cat)
    medi_log_col = engine.get_collection(MediLog)
    results = []

    for cat in cats:
        schedules = await engine.find(
            MediSchedule, {"$or": [{"cat_id": cat.id}, {"cat_id": None}]}
        )

        chosen = {}
        for sch in schedules:
            mid = str(sch.medicine.id)
            if mid not in chosen or (chosen[mid].cat_id is None and sch.cat_id == cat.id):
                chosen[mid] = sch

        best_overdue_days = -1
        best_next_due_utc = None

        for sch in chosen.values():
            med = await engine.find_one(Medicine, Medicine.id == sch.medicine.id)
            if not med:
                continue

            last_log = await medi_log_col.find_one(
                {"cat_id": cat.id, "medicine_id": med.id},
                sort=[("administered_at", -1)]
            )

            base_utc = last_log["administered_at"] if last_log else (sch.created_at or datetime.utcnow())
            next_due_utc = base_utc + timedelta(days=sch.interval_days)
            next_due_date = next_due_utc.date()

            if next_due_date <= today_utc:
                overdue_days = (today_utc - next_due_date).days
                if (
                    overdue_days > best_overdue_days
                    or (overdue_days == best_overdue_days and (best_next_due_utc is None or next_due_utc < best_next_due_utc))
                ):
                    best_overdue_days = overdue_days
                    best_next_due_utc = next_due_utc

        if best_overdue_days >= 0:
            last_any = await medi_log_col.find_one({"cat_id": cat.id}, sort=[("administered_at", -1)])
            last_admin_date = (
                last_any["administered_at"].date().strftime("%Y.%m.%d") if last_any else "정보 없음"
            )

            results.append({
                "id": str(cat.id),
                "cat_code": cat.cat_code,
                "image_url": make_presigned_url(S3_BUCKET, cat.image_path[0]) if cat.image_path else None,
                "last_administered_date": last_admin_date,
                "next_due_date": best_next_due_utc.isoformat() if best_next_due_utc else None,
                "overdue_days": int(best_overdue_days)
            })

    results.sort(key=lambda r: (-(r.get("overdue_days", 0)), r.get("next_due_date") or "9999-12-31T00:00:00"))
    return {"due_today": results[:limit]}
    
@router.post("/cats")
async def create_cat(cat: Cat):
    await engine.save(cat)
    return cat

@router.get("/cats", summary="모든 고양이 목록 조회")
async def all_cats():
    cats = await engine.find(Cat)
    response_data = []
    for c in cats:
        doc = c.model_dump()
        doc["id"] = str(c.id)
        doc["image_url"] = make_presigned_url(S3_BUCKET, c.image_path[0]) if c.image_path else None
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
    try:
        obj_id = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 cat_id 형식입니다.")
    cat = await engine.find_one(Cat, Cat.id == obj_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="해당 ID의 고양이를 찾을 수 없습니다.")
    doc = cat.model_dump()
    doc["id"] = str(cat.id)
    doc["image_url"] = make_presigned_url(S3_BUCKET, cat.image_path[0]) if cat.image_path else None
    return doc

@router.delete("/cats/{cat_id}", response_model=Cat)
async def delete_cat(cat_id: str):
    cat = await engine.find_one(Cat, Cat.id == ObjectId(cat_id))
    if cat is None:
        raise HTTPException(404, detail="Cat not found")
    await engine.delete(cat)
    return cat

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

@router.get("/cats/{cat_id}/schedules", summary="[모듈] 특정 고양이의 스케줄 및 다음 투약일")
async def get_cat_schedules_with_next_due(cat_id: str):
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cat_id format.")

    cat = await engine.find_one(Cat, Cat.id == cat_oid)
    if not cat:
        raise HTTPException(status_code=404, detail="Cat with this ID not found.")

    schedules = await engine.find(
        MediSchedule,
        {"$or": [{"cat_id": cat_oid}, {"cat_id": None}]}
    )

    selected = {}
    for sch in schedules:
        mid = str(sch.medicine.id)
        if mid not in selected or (selected[mid].cat_id is None and sch.cat_id == cat_oid):
            selected[mid] = sch

    medi_log_col = engine.get_collection(MediLog)
    results = []

    for sch in selected.values():
        med = await engine.find_one(Medicine, Medicine.id == sch.medicine.id)
        if not med:
            continue

        last_log = await medi_log_col.find_one(
            {"cat_id": cat_oid, "medicine_id": med.id},
            sort=[("administered_at", -1)]
        )

        if last_log:
            next_due_date = last_log["administered_at"] + timedelta(days=sch.interval_days)
        else:
            # 투약 이력이 없으면 스케줄 생성일 자체를 다음 투약일로 사용
            next_due_date = sch.created_at or datetime.utcnow()

        results.append({
            "schedule_id": str(sch.id),
            "medicine_id": str(med.id),
            "medicine_name": med.name,
            "medicine_category": med.category.value if hasattr(med.category, "value") else str(med.category),
            "interval_days": sch.interval_days,
            "dose": sch.dose,
            "next_due_date": next_due_date.isoformat()
        })

    results.sort(key=lambda r: r["next_due_date"])
    return {"medications_status": results}


@router.get("/cats/{cat_id}/due-medicines", summary="[모듈] 특정 고양이의 투약 필요 약 조회")
async def get_due_medicines_for_cat(cat_id: str):
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cat_id format.")
    cat = await engine.find_one(Cat, Cat.id == cat_oid)
    if not cat:
        raise HTTPException(status_code=404, detail="Cat with this ID not found.")
    now = datetime.utcnow()
    all_medicines = await engine.find(Medicine)
    due_medicines = []
    medi_log_col = engine.get_collection(MediLog)
    for med in all_medicines:
        schedule = await engine.find_one(MediSchedule, {"medicine": med.id, "cat_id": cat_oid})
        if not schedule:
            schedule = await engine.find_one(MediSchedule, {"medicine": med.id, "cat_id": None})
        if not schedule:
            continue
        last_log = await medi_log_col.find_one(
            {"cat_id": cat_oid, "medicine_id": med.id},
            sort=[("administered_at", -1)]
        )
        if last_log:
            next_due_date = last_log["administered_at"] + timedelta(days=schedule.interval_days)
            is_due = now >= next_due_date
            reason = f"마지막 투약({last_log['administered_at'].strftime('%Y-%m-%d')}) 후 {schedule.interval_days}일이 경과함" if is_due else ""
        else:
            base = schedule.created_at or now
            next_due_date = base + timedelta(days=schedule.interval_days)
            is_due = now >= next_due_date
            reason = "투약 기록이 없어 즉시 투약 가능" if is_due else ""
        if is_due:
            due_medicines.append({
                "medicine_id": str(med.id),
                "medicine_name": med.name,
                "dose": schedule.dose,
                "is_due": True,
                "reason": reason,
                "next_due_date": next_due_date.isoformat()
            })
    return {"due_medicines": due_medicines}