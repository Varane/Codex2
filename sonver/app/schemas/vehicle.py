from pydantic import BaseModel


class VehicleBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class VehicleEngineSchema(BaseModel):
    id: int
    engine_name: str
    year_start: int
    year_end: int

    class Config:
        orm_mode = True
