from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PartRequestCreate(BaseModel):
    make_id: Optional[int] = None
    model_id: Optional[int] = None
    submodel_id: Optional[int] = None
    engine_id: Optional[int] = None
    year: Optional[int] = None
    vin: Optional[str] = None
    oem: Optional[str] = None
    part_name: Optional[str] = None
    phone: Optional[str]
    notes: Optional[str] = None


class PartRequestResponse(BaseModel):
    status: str = Field(default="ok")
    request_id: int
