from fastapi import APIRouter, HTTPException, Query
import os, boto3

router = APIRouter(prefix="/s3", tags=["s3-view"])

S3_BUCKET = os.getenv("S3_BUCKET", "catcin-bucket")
S3_REGION = os.getenv("AWS_REGION", "us-east-1")
s3_client = boto3.client("s3", region_name=S3_REGION)

def make_presigned_url(bucket: str, key: str, expires=600) -> str:
    return s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
    )

@router.get("/url")
async def get_presigned_url(key: str = Query(..., description="Cat.image_path (S3 key)")):
    if not key:
        raise HTTPException(400, "key required")
    return {"image_key": key, "image_url": make_presigned_url(S3_BUCKET, key, 600)}
