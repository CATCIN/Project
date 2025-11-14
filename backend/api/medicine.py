# api/medicine.py
import os
from datetime import date

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from odmantic import ObjectId

from models.model import Medicine, Category, MediSchedule
from core.database import engine
from core.utils import save_image

router = APIRouter()

# 전체 약 조회
@router.get("/medicines")
async def all_medicines():
    return await engine.find(Medicine)

# 특정 약 조회
@router.get("/medicines/{medicine_id}", response_model=Medicine)
async def get_medicine(medicine_id: str):
    medicine = await engine.find_one(Medicine, Medicine.id == ObjectId(medicine_id))
    if medicine is None:
        raise HTTPException(404, detail="Medicine not found")
    return medicine

@router.post("/medicines", response_model=Medicine)
async def create_medicine(
    name: str = Form(...),                     # 반드시 Form-data 에 "name" 키가 있어야 함
    category: Category = Form(...),             # Form-data 의 "category"
    interval: int = Form(...),                  # Form-data 의 "interval" (정수)
    expires_date: date = Form(...),             # Form-data 의 "expires_date" ("YYYY-MM-DD" 문자열)
    note: str = Form(""),                       # Form-data 의 "note" (선택사항)
    image: UploadFile = File(None),             # multipart/form-data 의 "image" (파일 업로드)
):
    # 1) Medicine 모델 생성
    medicine = Medicine(
        name=name,
        category=category,
        interval=interval,
        expires_date=expires_date,
        note=note,
        image_url=None,
    )

    # 2) 이미지가 업로드됐다면 저장하고 URL을 넣어준다
    if image:
        allowed_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        _, ext = os.path.splitext(image.filename.lower())
        if ext not in allowed_exts:
            raise HTTPException(status_code=400, detail="허용되지 않는 이미지 형식입니다.")
        image_path = await save_image(image)
        medicine.image_url = image_path

    # 3) MongoDB(ODMantic)를 통해 저장
    await engine.save(medicine)
    return medicine

@router.delete("/medicines/{medicine_id}", status_code=204)
async def delete_medicine(medicine_id: str):
    """
    1) medicine_id가 유효한 ObjectId 형태인지 검사
    2) 해당 ID의 Medicine 문서를 찾는다. 없으면 404
    3) MediSchedule 컬렉션에서, 'medicine == med_oid' 로 “이 약을 참조하는 모든 스케줄”을 조회 후 전부 삭제
    4) Medicine 문서를 삭제
    """
    # 1) medicine_id가 올바른 ObjectId인지 검증
    try:
        med_oid = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid medicine_id")

    # 2) DB에서 Medicine 문서를 찾아본다
    med = await engine.find_one(Medicine, Medicine.id == med_oid)
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")

    # 3) MediSchedule에서 이 medicine을 참조하는 문서들을 모두 삭제
    #    → MediSchedule.medicine 필드 자체에 ObjectId를 비교
    schedules_to_delete = await engine.find(
        MediSchedule,
        MediSchedule.medicine == med_oid
    )
    for sched in schedules_to_delete:
        await engine.delete(sched)
    #  ODMantic 1.10+ 버전이면, 아래 한 줄로 일괄 삭제할 수도 있습니다:
    #    await engine.delete_many(MediSchedule, MediSchedule.medicine == med_oid)

    # 4) Medicine 본문 삭제
    await engine.delete(med)

    # status_code=204이므로, 빈 바디(응답 본문 없음)으로 종료
    return
