from fastapi import APIRouter, HTTPException, Form
from odmantic import ObjectId
from typing import List, Optional
from models.model import MediSchedule, Medicine, MediLog, Cat
from core.database import engine
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/mediSchedules", summary="모든 투약 스케줄 목록 조회")
async def get_all_schedules() -> List[dict]:
    """
    DB에 저장된 모든 투약 스케줄 목록을 반환
    각 스케줄에 연결된 약과 고양이의 상세 정보를 포함
    """
    schedules = await engine.find(MediSchedule)
    
    response_data = []
    for schedule in schedules:
        medicine_doc = await engine.find_one(Medicine, Medicine.id == schedule.medicine.id)
        
        cat_doc = None
        if schedule.cat_id:
            cat_doc = await engine.find_one(Cat, Cat.id == schedule.cat_id)

        if medicine_doc:
            response_data.append({
                "id": str(schedule.id),
                "medicine_name": medicine_doc.name,
                "interval_days": schedule.interval_days,
                "dose": schedule.dose,
                "note": schedule.note,
                # 고양이가 지정된 경우 고양이 코드를, 아니면 '모든 고양이'로 표시
                "cat_code": cat_doc.cat_code if cat_doc else "모든 고양이",
                "created_at": schedule.created_at
            })
            
    return response_data
    
@router.get("/mediSchedules/{schedule_id}", response_model=MediSchedule)
async def get_schedule(schedule_id: str):
    schedule = await engine.find_one(MediSchedule, MediSchedule.id == ObjectId(schedule_id))
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

@router.post("/mediSchedules", summary="단일 투약 스케줄 생성")
async def create_schedule_single(
    medicine_id: str = Form(...),
    interval_days: int = Form(...),
    dose: int = Form(1),
    note: str = Form(""),
    cat_id: Optional[str] = Form(None) 
):
    medicine = await engine.find_one(Medicine, Medicine.id == ObjectId(medicine_id))
    if medicine is None:
        raise HTTPException(status_code=404, detail="Medicine not found")

    cat_oid_to_save = None 
    if cat_id:
        try:
            cat_oid = ObjectId(cat_id)
            cat_exists = await engine.find_one(Cat, Cat.id == cat_oid)
            if cat_exists is None:
                raise HTTPException(status_code=404, detail="Cat not found")
            cat_oid_to_save = cat_oid 
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cat_id format")

    schedule = MediSchedule(
        medicine=medicine,
        interval_days=interval_days,
        dose=dose,
        note=note,
        cat_id=cat_oid_to_save 
    )
    await engine.save(schedule)
    return schedule

@router.get("/schedules/stats/category", summary="약물 카테고리별 스케줄 통계 조회")
async def get_schedule_stats_by_category():
    """
    전체 스케줄을 약물 카테고리별로 그룹화하여 각 카테고리의 스케줄 개수를 반환
    """
    pipeline = [
        {
            "$lookup": {
                "from": "Medicine",
                "localField": "medicine",
                "foreignField": "_id",
                "as": "medicine_details"
            }
        },
        {"$unwind": "$medicine_details"},
        {
            "$group": {
                "_id": "$medicine_details.category",
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "label": "$_id",
                "value": "$count"
            }
        }
    ]

    schedule_collection = engine.get_collection(MediSchedule)
    stats_cursor = schedule_collection.aggregate(pipeline)
    
    stats = await stats_cursor.to_list(length=None)
    return stats

@router.delete("/mediSchedules/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: str):
    schedule = await engine.find_one(MediSchedule, MediSchedule.id == ObjectId(schedule_id))
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await engine.delete(schedule)
    return

@router.post("/medi-logs", summary="투약 기록 생성")
async def create_medication_log(
    cat_id: str = Form(...),
    medicine_id: str = Form(...)
):
    """
    투약 완료 후, 어떤 고양이에게 어떤 약을 투약했는지 로그를 남김.
    """
    try:
        cat_oid = ObjectId(cat_id)
        med_oid = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format.")

    cat_exists = await engine.find_one(Cat, Cat.id == cat_oid)
    med_exists = await engine.find_one(Medicine, Medicine.id == med_oid)
    if not cat_exists or not med_exists:
        raise HTTPException(status_code=404, detail="Cat or Medicine not found.")

    new_log = MediLog(cat_id=cat_oid, medicine_id=med_oid)
    await engine.save(new_log)
    
    return {"message": "Medication log created successfully", "log": new_log}

@router.get("/mediLogs/{cat_id}", summary="특정 고양이의 투약 기록 조회")
async def get_mediLogs_for_cat(cat_id: str):
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cat_id")

    raw_logs = await engine.find(MediLog, {"cat_id": cat_oid})

    response_logs = []
    for log in raw_logs:
        medicine_doc = await engine.find_one(Medicine, Medicine.id == log.medicine_id)
        response_logs.append({
            "id": str(log.id),
            "cat_id": str(log.cat_id),
            "medicine_id": str(log.medicine_id),
            "medicine_name": medicine_doc.name if medicine_doc else "알 수 없는 약",
            "medicine_category": medicine_doc.category if medicine_doc else "알 수 없는 카테고리",
            "administered_at": log.administered_at.isoformat()
        })

    return {"logs": response_logs}