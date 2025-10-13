# api/medicine.py
import os
from datetime import datetime, timezone, date
import boto3
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from odmantic import ObjectId
from models.model import Medicine, Category, MediSchedule
from core.database import engine

router = APIRouter()

S3_BUCKET = os.getenv("S3_BUCKET", "catcin-bucket")
S3_PREFIX_MEDICINE = os.getenv("S3_PREFIX_MEDICINE", "medicine")  
s3_client = boto3.client("s3")

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}

def _build_medicine_s3_key(original_filename: str) -> str:
    """
    최종 S3 Key 형태:
      medicine/YYYY-MM-DD/YYYYMMDD_HHMMSS.jpg
    """
    _, ext = os.path.splitext((original_filename or "").lower())
    if ext not in ALLOWED_IMAGE_EXTS:
        ext = ".jpg"
    now = datetime.now(timezone.utc)
    folder = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y%m%d_%H%M%S")
    return f"{S3_PREFIX_MEDICINE}/{folder}/{stamp}{ext}"

def make_presigned_url(bucket: str, key: str, expires=600) -> str:
    return s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
    )

# 전체 약 조회
@router.get("/medicines")
async def all_medicines():
    medicines = await engine.find(Medicine)
    
    response_data = []
    for med in medicines:
        doc = med.model_dump()
        
        doc["id"] = str(med.id)
        
        if med.image_url:
            doc["image_url"] = make_presigned_url(S3_BUCKET, med.image_url)
        else:
            doc["image_url"] = None
            
        response_data.append(doc)
        
    return response_data

# 특정 약 조회
@router.get("/medicines/{medicine_id}", response_model=Medicine)
async def get_medicine(medicine_id: str):
    medicine = await engine.find_one(Medicine, Medicine.id == ObjectId(medicine_id))
    if medicine is None:
        raise HTTPException(404, detail="Medicine not found")
    return medicine

@router.post("/medicines", response_model=Medicine)
async def create_medicine(
    name: str = Form(...),
    category: Category = Form(...),
    interval: int = Form(...),
    expires_date: date = Form(...),
    note: str = Form(""),
    image: UploadFile = File(None),
):
    try:
        s3_key = None
        if image:
            _, ext = os.path.splitext((image.filename or "").lower())
            if ext not in ALLOWED_IMAGE_EXTS:
                raise HTTPException(status_code=400, detail="허용되지 않는 이미지 형식입니다.")

            s3_key = _build_medicine_s3_key(image.filename)
            content_type = image.content_type or "image/jpeg"

            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=await image.read(),
                ContentType=content_type,
            )

        new_medicine = Medicine(
            name=name,
            category=category,
            interval=interval,
            expires_date=expires_date,
            note=note,
            image_url=s3_key,  
        )

        await engine.save(new_medicine)
        return new_medicine

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"약 등록 중 오류 발생: {e}")

@router.delete("/medicines/{medicine_id}", status_code=204)
async def delete_medicine(medicine_id: str):
    """
    1) medicine_id가 유효한 ObjectId 형태인지 검사
    2) 해당 ID의 Medicine 문서를 찾는다. 없으면 404
    3) MediSchedule 컬렉션에서, 'medicine == med_oid' 로 “이 약을 참조하는 모든 스케줄”을 조회 후 전부 삭제
    4) Medicine 문서를 삭제
    """
    try:
        med_oid = ObjectId(medicine_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid medicine_id")

    med = await engine.find_one(Medicine, Medicine.id == med_oid)
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")

    schedules_to_delete = await engine.find(
        MediSchedule,
        MediSchedule.medicine == med_oid
    )
    for sched in schedules_to_delete:
        await engine.delete(sched)

    await engine.delete(med)

    return
