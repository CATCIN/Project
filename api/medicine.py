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

# 약 생성
@router.post("/medicines", response_model=Medicine)
async def create_medicine(
    name: str = Form(...),                    
    category: Category = Form(...),          
    interval: int = Form(...),                
    expires_date: date = Form(...),     
    note: str = Form(""),                    
    image: UploadFile = File(None),            
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

    # 3) MongoDB에 저장
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

    # 2) DB에서 Medicine 문서를 찾음
    med = await engine.find_one(Medicine, Medicine.id == med_oid)
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")

    # 3) MediSchedule에서 이 medicine을 참조하는 문서들을 모두 삭제
    schedules_to_delete = await engine.find(
        MediSchedule,
        MediSchedule.medicine == med_oid
    )
    for sched in schedules_to_delete:
        await engine.delete(sched)

    # 4) Medicine 본문 삭제
    await engine.delete(med)

    return
