import os
from sqlalchemy import String, ForeignKey, Text, DateTime, Enum, Integer, SmallInteger, PickleType, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func
func: callable
from typing import Optional, List
from uuid import uuid4

from datetime import datetime

def validate_date(field_name,value):
    if type(value) == datetime:
        return value
    if type(value) == str:
        return datetime.fromisoformat(value)
    if type(value) == int:
        return datetime(value)
    if not value:
        return None
    raise TypeError(f"Unexpected value for {field_name}. Expected type: datetime, str, int")


ENVIRONMENT = os.environ.get("ENVIRONMENT")

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users_"+ENVIRONMENT

    user_id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid4()), unique=True)
    user_name: Mapped[str] = mapped_column(String(50), unique=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    password: Mapped[str] = mapped_column(String(250))
    devices: Mapped[List["DeviceOrm"]] = relationship(back_populates="owner")
    media: Mapped[List["MediaOrm"]] = relationship(back_populates="owner")

    @validates("date")
    def validate_date_field(self, key, value):
        return validate_date(key,value)

class DeviceOrm(Base):
    __tablename__ = "devices_"+ENVIRONMENT

    device_id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid4()), unique=True)
    device_name: Mapped[str] = mapped_column(String(50), unique=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    device_status: Mapped[str] = mapped_column(String(50), default="ACTIVE") # ENUM: ACTIVE, DEACTIVATED
    owner_id: Mapped[str] = mapped_column(ForeignKey("users_"+ENVIRONMENT+".user_id"))
    owner: Mapped["User"] = relationship(back_populates="devices")
    media: Mapped[List["MediaOrm"]] = relationship(back_populates="device")

    @validates("date")
    def validate_date_field(self, key, value):
        return validate_date(key,value)


class MediaOrm(Base):
    __tablename__ = "media_"+ENVIRONMENT

    media_id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid4()), unique=True)
    media_name: Mapped[str] = mapped_column(String(250))
    media_type: Mapped[str] = mapped_column(String(50))
    media_size_bytes: Mapped[int] = mapped_column(Integer)
    media_description: Mapped[Optional[str]] = mapped_column(Text)
    media_width: Mapped[Optional[int]] = mapped_column(SmallInteger)
    media_height: Mapped[Optional[int]] = mapped_column(SmallInteger)
    media_thumbnail: Mapped[Optional[str]] = mapped_column(Text)
    media_thumbnail_width: Mapped[Optional[int]] = mapped_column(SmallInteger)
    media_thumbnail_height: Mapped[Optional[int]] = mapped_column(SmallInteger)
    exif: Mapped[Optional[str]] = mapped_column(Text)
    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    device_id: Mapped[str] = mapped_column(ForeignKey("devices_"+ENVIRONMENT+".device_id"))
    device_media_uri: Mapped[str] = mapped_column(String(250))
    upload_status: Mapped[str] = mapped_column(String(50), default="PENDING") # ENUM: PENDING, UPLOADED
    media_status_on_device: Mapped[str] = mapped_column(String(50), default="EXISTS") # ENUM: EXISTS, DELETED
    owner_id: Mapped[str] = mapped_column(ForeignKey("users_"+ENVIRONMENT+".user_id"))
    storage_service_name: Mapped[Optional[str]] = mapped_column(String(50))
    storage_bucket_name: Mapped[Optional[str]] = mapped_column(String(50))
    storage_media_uri: Mapped[Optional[str]] = mapped_column(String(50))
    media_key: Mapped[Optional[str]] = mapped_column(String(2048))

    device: Mapped["DeviceOrm"] = relationship(back_populates="media")
    owner: Mapped["User"] = relationship(back_populates="media")
    insights: Mapped[List["InsightOrm"]] = relationship(back_populates="media")
    insight_jobs: Mapped[List["InsightJobOrm"]] = relationship(back_populates="media")

    @validates("created_on")
    def validate_created_date(self, key, value):
        return validate_date(key,value)

class InsightEngineOrm(Base):
    __tablename__ =  "insight_engine_"+ENVIRONMENT

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid4()), unique=True)
    name: Mapped[str] = mapped_column(String(250))
    description: Mapped[Optional[str]] = mapped_column(Text())
    input_source: Mapped[str] = mapped_column(String(250))
    input_queue_name: Mapped[str] = mapped_column(String(250))
    output_exchange_name: Mapped[str] = mapped_column(String(250))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE") #ENUM: ACTIVE, DEACTIVATED

    jobs: Mapped[List["InsightJobOrm"]] = relationship(back_populates="insight_engine")
    insights: Mapped[List["InsightOrm"]] = relationship(back_populates="insight_engine")

class InsightOrm(Base):
    __tablename__ = "insights_"+ENVIRONMENT

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid4()), unique=True)
    insight_engine_id: Mapped[str] = mapped_column(ForeignKey("insight_engine_"+ENVIRONMENT+".id"))
    media_id: Mapped[str] = mapped_column(ForeignKey("media_"+ENVIRONMENT+".media_id"))
    job_id: Mapped[str] = mapped_column(ForeignKey("insight_jobs_"+ENVIRONMENT+".id"))
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    bounding_box: Mapped[Optional[List[int]]] = mapped_column(PickleType())
    status: Mapped[str] = mapped_column(String(50), default="COMPUTED") # ENUM: COMPUTED, APPROVED, REJECTED
    prob: Mapped[Optional[float]] = mapped_column(Float())

    media: Mapped["MediaOrm"] = relationship(back_populates="insights")
    insight_engine: Mapped["InsightEngineOrm"] = relationship(back_populates="insights")
    job: Mapped["InsightJobOrm"] = relationship(back_populates="insights")

class InsightJobOrm(Base):
    __tablename__ = "insight_jobs_"+ENVIRONMENT

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=lambda: str(uuid4()), unique=True)
    insight_engine_id: Mapped[str] = mapped_column(ForeignKey("insight_engine_"+ENVIRONMENT+".id"))
    media_id: Mapped[str] = mapped_column(ForeignKey("media_"+ENVIRONMENT+".media_id"))
    status: Mapped[str] = mapped_column(String(50), default="PENDING") # ENUM: PENDING, FAILED, DONE, CANCELED
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    net_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    media: Mapped["MediaOrm"] = relationship(back_populates="insight_jobs")
    insight_engine: Mapped["InsightEngineOrm"] = relationship(back_populates="jobs")
    insights: Mapped[List["InsightOrm"]] = relationship(back_populates="job")

    @validates("start_time", "end_time", "net_time_seconds")
    def validate_date_field(self, key, value):
        return validate_date(key,value)