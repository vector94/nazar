from sqlalchemy import Column, String, Float, BigInteger, DateTime, Integer, Text
from sqlalchemy.sql import func

from .database import Base


class Metric(Base):
    __tablename__ = "metrics"

    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    host = Column(String(255), primary_key=True, nullable=False)
    cpu_percent = Column(Float)
    cpu_min = Column(Float)
    cpu_max = Column(Float)
    memory_percent = Column(Float)
    memory_min = Column(Float)
    memory_max = Column(Float)
    disk_percent = Column(Float)
    disk_min = Column(Float)
    disk_max = Column(Float)
    network_in = Column(BigInteger)
    network_out = Column(BigInteger)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    host = Column(String(255), nullable=False)
    metric_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text)
    status = Column(String(20), nullable=False, default="pending")
