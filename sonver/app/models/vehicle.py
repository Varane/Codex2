from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base


class VehicleMake(Base):
    __tablename__ = "vehicle_make"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    models = relationship("VehicleModel", back_populates="make", cascade="all, delete-orphan")


class VehicleModel(Base):
    __tablename__ = "vehicle_model"

    id = Column(Integer, primary_key=True, index=True)
    make_id = Column(Integer, ForeignKey("vehicle_make.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)

    make = relationship("VehicleMake", back_populates="models")
    submodels = relationship("VehicleSubmodel", back_populates="model", cascade="all, delete-orphan")


class VehicleSubmodel(Base):
    __tablename__ = "vehicle_submodel"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("vehicle_model.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)

    model = relationship("VehicleModel", back_populates="submodels")
    engines = relationship("VehicleEngine", back_populates="submodel", cascade="all, delete-orphan")


class VehicleEngine(Base):
    __tablename__ = "vehicle_engine"

    id = Column(Integer, primary_key=True, index=True)
    submodel_id = Column(Integer, ForeignKey("vehicle_submodel.id", ondelete="CASCADE"), nullable=False)
    engine_name = Column(String, nullable=False)
    year_start = Column(Integer, nullable=False)
    year_end = Column(Integer, nullable=False)

    submodel = relationship("VehicleSubmodel", back_populates="engines")
