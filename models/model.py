from odmantic import Model, Field, Reference
from typing import List, Optional
from typing_extensions import Literal
from datetime import datetime
from bson import ObjectId
from enum import Enum

class Category(str, Enum):
    ANTIBIOTIC = "항생제"
    PAINKILLER = "진통제"
    VITAMIN = "비타민"
    nutritional = "영양제"
    anthelmintic = "구충제"

class Cat(Model):
    image_path: str
    feature_vector: List[float]
    source: Literal["user", "system"]
    save_at: datetime = Field(default_factory=datetime.utcnow)
    note: str = ""

class Medicine(Model):
    name: str
    category: Category
    interval: int
    expires_date: datetime
    image_url: Optional[str] = Field(None)
    note: str = ""

class MediLog(Model):
    cat: Cat = Reference()
    medicine_id: Optional[ObjectId] = Field(None)
    administered_at: datetime = Field(default_factory=datetime.utcnow)

class MediSchedule(Model):
    """
    하나의 스케줄만 존재하며, 모든 고양이에게 동일하게 적용됩니다.
    """
    medicine: Medicine = Reference()
    interval_days: int
    dose: int = Field(1)
    note: str = ""
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @property
    def next_due(self) -> datetime:
        base = self.created_at or datetime.utcnow()
        return base + timedelta(days=self.interval_days)
