from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import VehicleEngine, VehicleMake, VehicleModel, VehicleSubmodel
from app.schemas.vehicle import VehicleBase, VehicleEngineSchema

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/makes", response_model=list[VehicleBase])
def get_makes(db: Session = Depends(get_db)):
    return db.query(VehicleMake).order_by(VehicleMake.name).all()


@router.get("/models/{make_id}", response_model=list[VehicleBase])
def get_models(make_id: int, db: Session = Depends(get_db)):
    return (
        db.query(VehicleModel)
        .filter(VehicleModel.make_id == make_id)
        .order_by(VehicleModel.name)
        .all()
    )


@router.get("/submodels/{model_id}", response_model=list[VehicleBase])
def get_submodels(model_id: int, db: Session = Depends(get_db)):
    return (
        db.query(VehicleSubmodel)
        .filter(VehicleSubmodel.model_id == model_id)
        .order_by(VehicleSubmodel.name)
        .all()
    )


@router.get("/engines/{submodel_id}", response_model=list[VehicleEngineSchema])
def get_engines(submodel_id: int, db: Session = Depends(get_db)):
    return (
        db.query(VehicleEngine)
        .filter(VehicleEngine.submodel_id == submodel_id)
        .order_by(VehicleEngine.engine_name)
        .all()
    )
