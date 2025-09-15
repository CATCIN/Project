# models/embedding.py
import io, numpy as np, boto3, os
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from .model import extractor

S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
_s3 = boto3.client("s3", region_name=AWS_REGION)

def _img_from_s3(key: str):
    obj = _s3.get_object(Bucket=S3_BUCKET, Key=key)
    return Image.open(io.BytesIO(obj["Body"].read())).convert("RGB")

def avg_vec(keys: list[str]) -> np.ndarray:
    vecs = [extractor.image_to_vec(_img_from_s3(k)) for k in keys]
    return np.mean(np.stack(vecs, axis=0), axis=0)

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(cosine_similarity(a.reshape(1,-1), b.reshape(1,-1))[0,0])
