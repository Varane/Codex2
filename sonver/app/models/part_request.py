from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db import Base


class PartRequest(Base):
    __tablename__ = "part_requests"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    make_id = Column(Integer, ForeignKey("vehicle_make.id"), nullable=True)
    model_id = Column(Integer, ForeignKey("vehicle_model.id"), nullable=True)
    submodel_id = Column(Integer, ForeignKey("vehicle_submodel.id"), nullable=True)
    engine_id = Column(Integer, ForeignKey("vehicle_engine.id"), nullable=True)
    year = Column(Integer, nullable=True)
    vin = Column(String, nullable=True)
    oem = Column(String, nullable=True)
    part_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    message_json = Column(JSONB, nullable=False)
    user_ip = Column(String, nullable=False)

    make = relationship("VehicleMake")
    model = relationship("VehicleModel")
    submodel = relationship("VehicleSubmodel")
    engine = relationship("VehicleEngine")
