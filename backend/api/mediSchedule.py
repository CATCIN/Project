from fastapi import APIRouter, HTTPException, Form
from odmantic import ObjectId
from typing import List
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
    note: str = Form("")
):
    medicine = await engine.find_one(Medicine, Medicine.id == ObjectId(medicine_id))
    if medicine is None:
        raise HTTPException(status_code=404, detail="Medicine not found")

    schedule = MediSchedule(
        medicine=medicine,
        interval_days=interval_days,
        dose=dose,
        note=note,
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

@router.get("/mediSchedules/{cat_id}")
async def check_due(cat_id: str):
    """
    주어진 cat_id에 대해, 모든 Medicine을 순회하면서
    마지막으로 투약된 시점(MediLog)과 비교해 '다음 투약 예정일(next_due)'과
    '지금 투약 가능 여부(is_due)'를 반환합니다.
    - MediLog 모델에서 medicine_id: ObjectId이므로, 이를 기준으로 필터링합니다.
    """

    # 1) 먼저 cat_id가 유효한 ObjectId인지 확인
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cat_id")

    # 2) 해당 고양이(Cat) 존재 여부 확인
    cat = await engine.find_one(Cat, Cat.id == cat_oid)
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")

    # 3) DB에 저장된 모든 Medicine을 가져옴
    medicines: List[Medicine] = await engine.find(Medicine)
    results = []
    now = datetime.utcnow()

    for med in medicines:
        # 4) 이 고양이(cat_oid)와 이 약(med.id)에 해당하는 마지막 투약 로그를 검색
        last_log = await engine.find_one(
            MediLog,
            {
                # ODMantic 0.4 기준: Reference 필드 ID 비교
                "cat": cat_oid,
                "medicine_id": med.id
            },
            sort=[-MediLog.administered_at]  # 최신 투약 시점 기준으로 정렬
        )

        interval_days = med.interval  # 기존 모델에서 Medicine.interval 필드를 사용
        if last_log:
            # 5) 마지막 투약 시점 + interval_days 로 다음 투약 예정일 계산
            next_due_dt = last_log.administered_at + timedelta(days=interval_days)
            is_due = now >= next_due_dt
            # ISO 포맷 문자열로 변환
            next_due_iso = next_due_dt.isoformat()
            last_admin_iso = last_log.administered_at.isoformat()
        else:
            # 6) 아직 투약된 이력이 없으므로, 즉시 투약 가능
            next_due_iso = "즉시 가능"
            last_admin_iso = None
            is_due = True

        results.append({
            "medicine_id": str(med.id),
            "medicine_name": med.name,
            "last_administered": last_admin_iso,
            "next_due": next_due_iso,
            "is_due": is_due
        })

    return {
        "cat_id": str(cat.id),
        "medications": results
    }


@router.post("/mediLogs", response_model=MediLog)
async def create_mediLog(
    cat_id: str = Form(...),
    medicine_id: str = Form(...),
):
    # 1) cat_id 유효성 검증 및 Cat 조회
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cat_id")

    cat = await engine.find_one(Cat, Cat.id == cat_oid)
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")

    # 2) medicine_id 유효성 검증 (Document 존재 여부는 체크하지 않음)
    try:
        med_oid = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid medicine_id")

    # 4) MediLog 객체 생성 시, medicine_id 필드에 ObjectId만 넘겨준다
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
    # 1) cat_id를 ObjectId로 변환
    try:
        cat_oid = ObjectId(cat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cat_id")

    # 2) Cat 문서가 실제로 존재하는지 확인
    cat = await engine.find_one(Cat, Cat.id == cat_oid)
    if cat is None:
        raise HTTPException(status_code=404, detail="Cat not found")

    # 3) MediLog 조회: 참조 대신 ObjectId로 직접 matching
    #    - {"cat": cat_oid} 형태의 dict 필터링을 쓰면 aggregation이 발생하지 않습니다.
    raw_logs: List[MediLog] = await engine.find(
        MediLog,
        {"cat": cat_oid}
    )

    # 4) JSON 직렬화할 수 있는 형태로 가공
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
