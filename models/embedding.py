# models/embedding.py 
from odmantic import Model
from typing import List, Optional, Literal
from datetime import datetime
from bson import ObjectId

class CatEmbedding(Model):
    cat_id: Optional[ObjectId] = None         
    embedding: List[float]                     # L2 정규화된 벡터
    source: Literal["system","user"] = "system"
    image_path: Optional[str] = None
    created_at: datetime = datetime.utcnow()
