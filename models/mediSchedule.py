from fastapi import APIRouter, HTTPException, Form
from odmantic import ObjectId
from typing import List, Optional
from models.model import MediSchedule, Medicine, MediLog, Cat
from core.database import engine
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/mediSchedules", response_model=List[MediSchedule])
async def get_all_schedules():
    schedules = await engine.find(MediSchedule)
    return schedules

@router.get("/mediSchedules/{schedule_id}", response_model=MediSchedule)
async def get_schedule(schedule_id: str):
    schedule = await engine.find_one(MediSchedule, MediSchedule.id == ObjectId(schedule_id))
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

@router.post("/mediSchedules", response_model=MediSchedule)
async def create_schedule_single(
    medicine_id: str = Form(...),
    interval_days: int = Form(...),
    dose: int = Form(1),
    note: str = Form(""),
    cat_id: str = Form(None)
):
    medicine = await engine.find_one(Medicine, Medicine.id == ObjectId(medicine_id))
    if medicine is None:
        raise HTTPException(status_code=404, detail="Medicine not found")

    referenced_cat = None
    if cat_id:
        try:
            cat_oid = ObjectId(cat_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cat_id")
        # 고양이 객체를 찾아서 Reference로 사용
        referenced_cat = await engine.find_one(Cat, Cat.id == cat_oid)
        if referenced_cat is None:
            raise HTTPException(status_code=404, detail="Cat not found")

    schedule = MediSchedule(
        medicine=medicine,
        interval_days=interval_days,
        dose=dose,
        note=note,
        cat=referenced_cat  # Cat 객체 전체를 Reference로 전달
    )
    await engine.save(schedule)
    return schedule

@router.delete("/mediSchedules/{schedule_id}", status_code=204)
async def delete_schedule(schedule_id: str):
    schedule = await engine.find_one(MediSchedule, MediSchedule.id == ObjectId(schedule_id))
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await engine.delete(schedule)
    return


# /mediSchedules/{cat_id}: 카메라에 찍힌 고양이의 투약 필요 약 조회
@router.get("/mediSchedules/{cat_id}")
async def get_due_medicines_for_cat(cat_id: str):
    """
    카메라에 찍힌 고양이(cat_id)가 DB에 없으면 전체 약을 즉시 투약 가능으로,
    이미 등록된 고양이라면 각 약별로 마지막 투약일+주기 기준으로 투약 필요 여부를 반환.
    """
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cat_id")

    cat = await engine.find_one(Cat, Cat.id == cat_oid)
    now = datetime.utcnow()
    results = []

    # 전체 약 목록 조회
    medicines: List[Medicine] = await engine.find(Medicine)

    if not cat:
        # 새로운 고양이: 전체 약을 즉시 투약 가능으로 반환 (투약량 포함)
        for med in medicines:
            sched = await engine.find_one(MediSchedule, {"medicine": med.id, "cat": None})
            dose = sched.dose if sched else 1
            results.append({
                "medicine_id": str(med.id),
                "medicine_name": med.name,
                "dose": dose,
                "last_administered": None,
                "next_due": "즉시 가능",
                "is_due": True
            })
        return {
            "cat_id": cat_id,
            "is_new_cat": True,
            "due_medicines": results
        }

    # 기존 고양이: 각 약별로 마지막 투약일+주기 기준으로 투약 필요 여부 판단
    for med in medicines:
        # 마지막 투약 로그 조회
        last_log = await engine.find_one(
            MediLog,
            {
                "cat": cat_oid,
                "medicine_id": med.id
            },
            sort=[-MediLog.administered_at]
        )
        # 해당 고양이-약 조합의 스케줄(투약량 등) 우선, 없으면 전체 스케줄, 없으면 1
        sched = await engine.find_one(MediSchedule, {"medicine": med.id, "$or": [{"cat": cat_oid}, {"cat": None}]})
        dose = sched.dose if sched else 1
        interval_days = getattr(med, "interval", None)
        if interval_days is None:
            continue
        if last_log:
            next_due_dt = last_log.administered_at + timedelta(days=interval_days)
            is_due = now >= next_due_dt
            next_due_iso = next_due_dt.isoformat()
            last_admin_iso = last_log.administered_at.isoformat()
        else:
            next_due_iso = "즉시 가능"
            last_admin_iso = None
            is_due = True

        results.append({
            "medicine_id": str(med.id),
            "medicine_name": med.name,
            "dose": dose,
            "last_administered": last_admin_iso,
            "next_due": next_due_iso,
            "is_due": is_due
        })

    # 실제로 지금 줘야 하는 약만 필터링
    due_meds = [r for r in results if r["is_due"]]

    # 투약 로그 자동 생성 (cat이 DB에 있는 경우만)
    for med in due_meds:
        # 이미 로그가 오늘 날짜로 있으면 중복 생성 방지
        today = now.date()
        existing_log = await engine.find_one(
            MediLog,
            {
                "cat": cat_oid,
                "medicine_id": ObjectId(med["medicine_id"]),
            },
            sort=[-MediLog.administered_at]
        )
        if not existing_log or existing_log.administered_at.date() < today:
            med_log = MediLog(
                cat=cat,
                medicine_id=ObjectId(med["medicine_id"]),
            )
            await engine.save(med_log)

    return {
        "cat_id": cat_id,
        "is_new_cat": False,
        "due_medicines": due_meds
    }


@router.post("/mediLogs", response_model=MediLog)
async def create_mediLog(
    cat_id: str = Form(...),
    medicine_id: str = Form(...),
):
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cat_id")

    cat = await engine.find_one(Cat, Cat.id == cat_oid)
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")

    try:
        med_oid = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid medicine_id")

    med_log = MediLog(
        cat=cat,
        medicine_id=med_oid,
    )
    await engine.save(med_log)
    return med_log

@router.get("/mediLogs/{cat_id}")
async def get_mediLog(cat_id: str):
    """
    고양이(cat_id)별 투약 로그를 반환합니다.
    - aggregation 없이, cat 필드를 ObjectId로 직접 비교하여 조회합니다.
    """
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cat_id")

    cat = await engine.find_one(Cat, Cat.id == cat_oid)
    if cat is None:
        raise HTTPException(status_code=404, detail="Cat not found")

    raw_logs: List[MediLog] = await engine.find(
        MediLog,
        {"cat": cat_oid}
    )

    response_logs = []
    for log in raw_logs:
        response_logs.append({
            "id": str(log.id),
            "cat_id": str(log.cat.id),
            "medicine_id": str(log.medicine_id) if log.medicine_id else None,
            "administered_at": log.administered_at.isoformat()
        })

    return {
        "cat_id": cat_id,
        "logs": response_logs
    }
