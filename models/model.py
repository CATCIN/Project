# backend/models.py
from odmantic import Model, Field, Reference
from typing import List, Optional
from typing_extensions import Literal
from datetime import datetime, timedelta
from bson import ObjectId
from enum import Enum

class Category(str, Enum):
    ANTIBIOTIC = "antibiotic"
    PAINKILLER = "painkiller"
    VITAMIN = "vitamin"
    NUTRITIONAL = "nutritional"
    ANTHELMINTIC = "anthelmintic"

class Cat(Model):
    cat_code: Optional[str] = None
    source: Literal["user", "system"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    stats_seen: int = 1
    note: str = ""
    image_path: List[str]
    feature_vector: List[float]

class Medicine(Model):
    name: str
    category: Category
    interval: int
    expires_date: datetime
    image_url: Optional[str] = None
    note: str = ""

class MediLog(Model):
    cat_id: ObjectId
    medicine_id: ObjectId
    administered_at: datetime = Field(default_factory=datetime.utcnow)

class MediSchedule(Model):
    medicine: Medicine = Reference()
    interval_days: int
    dose: int = Field(1)
    note: str = ""
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    cat_id: Optional[ObjectId] = Field(None)

    @property
    def next_due(self) -> datetime:
        base = self.created_at or datetime.utcnow()
        return base + timedelta(days=self.interval_days)
