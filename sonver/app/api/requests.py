from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import PartRequest
from app.schemas.part_request import PartRequestCreate, PartRequestResponse
from app.services.vin_decoder import decode_vin

router = APIRouter(tags=["requests"])


@router.post("/part-request", response_model=PartRequestResponse)
def create_part_request(payload: PartRequestCreate, request: Request, db: Session = Depends(get_db)):
    user_ip = request.client.host if request.client else "unknown"
    stored_payload = payload.dict()

    decoded_data = None
    if payload.vin:
        decoded_data = decode_vin(payload.vin)
        stored_payload["vin_decoded"] = decoded_data

    part_request = PartRequest(
        make_id=payload.make_id,
        model_id=payload.model_id,
        submodel_id=payload.submodel_id,
        engine_id=payload.engine_id,
        year=payload.year,
        vin=payload.vin,
        oem=payload.oem,
        part_name=payload.part_name,
        phone=payload.phone,
        message_json=stored_payload,
        user_ip=user_ip,
    )

    db.add(part_request)
    db.commit()
    db.refresh(part_request)

    return PartRequestResponse(request_id=part_request.id)
