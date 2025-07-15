from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Date, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fire_safety_suite.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Enums
import enum

class RoleEnum(str, enum.Enum):
    admin = "admin"
    inspector = "inspector"
    deputy_ops = "deputy_ops"

class StatusEnum(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    completed = "completed"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(120), nullable=False, unique=True)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    templates = relationship("Template", back_populates="creator")
    inspections = relationship("Inspection", foreign_keys="Inspection.inspector_id", back_populates="inspector")
    reviewed_inspections = relationship("Inspection", foreign_keys="Inspection.deputy_id", back_populates="deputy")

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    schema = Column(JSON, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="templates")
    inspections = relationship("Inspection", back_populates="template")

class Inspection(Base):
    __tablename__ = "inspections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(36), ForeignKey("templates.id"))
    facility = Column(String(120), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(50), default="draft")
    inspector_id = Column(String(36), ForeignKey("users.id"))
    deputy_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = relationship("Template", back_populates="inspections")
    inspector = relationship("User", foreign_keys=[inspector_id], back_populates="inspections")
    deputy = relationship("User", foreign_keys=[deputy_id], back_populates="reviewed_inspections")
    corrective_actions = relationship("CorrectiveAction", back_populates="inspection")

class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("inspections.id"))
    violation_ref = Column(String(255))
    action_plan = Column(Text)
    due_date = Column(Date)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    # Relationships
    inspection = relationship("Inspection", back_populates="corrective_actions")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(120))
    action = Column(String(255))
    ip_addr = Column(String(45))
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()