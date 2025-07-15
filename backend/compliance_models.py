from sqlalchemy import Column, String, DateTime, Boolean, Text, Date, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, date, timedelta
import uuid
from models import Base

class ComplianceFacility(Base):
    __tablename__ = "facilities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    address = Column(String(500))
    facility_type = Column(String(100))
    capacity = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    schedules = relationship("ComplianceSchedule", back_populates="facility")

class ComplianceFunction(Base):
    __tablename__ = "compliance_functions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    default_frequency = Column(String(10))
    citation_references = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    schedules = relationship("ComplianceSchedule", back_populates="function")

class ComplianceSchedule(Base):
    __tablename__ = "compliance_schedules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id"))
    function_id = Column(String(36), ForeignKey("compliance_functions.id"))
    frequency = Column(String(10), nullable=False)
    start_date = Column(Date)
    next_due_date = Column(Date)
    assigned_to = Column(String(36), ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    facility = relationship("ComplianceFacility", back_populates="schedules")
    function = relationship("ComplianceFunction", back_populates="schedules")
    records = relationship("ComplianceRecord", back_populates="schedule")

class ComplianceRecord(Base):
    __tablename__ = "compliance_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schedule_id = Column(String(36), ForeignKey("compliance_schedules.id"))
    due_date = Column(Date, nullable=False)
    completed_date = Column(Date)
    status = Column(String(20), default="pending")
    completed_by = Column(String(36), ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    schedule = relationship("ComplianceSchedule", back_populates="records")
    documents = relationship("ComplianceDocument", back_populates="record")

class ComplianceDocument(Base):
    __tablename__ = "compliance_documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    record_id = Column(String(36), ForeignKey("compliance_records.id"))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    file_path = Column(String(500))
    base64_content = Column(Text)
    uploaded_by = Column(String(36), ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    record = relationship("ComplianceRecord", back_populates="documents")

# Utility functions for frequency calculations
def calculate_next_due_date(current_date: date, frequency: str) -> date:
    """Calculate next due date based on frequency"""
    if frequency == "W":  # Weekly
        return current_date + timedelta(weeks=1)
    elif frequency == "M":  # Monthly
        return current_date + timedelta(days=30)
    elif frequency == "Q":  # Quarterly
        return current_date + timedelta(days=90)
    elif frequency == "SA":  # Semi-Annually
        return current_date + timedelta(days=180)
    elif frequency == "A":  # Annually
        return current_date + timedelta(days=365)
    elif frequency == "2y":  # Every 2 years
        return current_date + timedelta(days=730)
    elif frequency == "3y":  # Every 3 years
        return current_date + timedelta(days=1095)
    elif frequency == "5y":  # Every 5 years
        return current_date + timedelta(days=1825)
    else:
        return current_date + timedelta(days=30)  # Default to monthly

def get_frequency_display(frequency: str) -> str:
    """Get display name for frequency"""
    frequency_map = {
        "W": "Weekly",
        "M": "Monthly", 
        "Q": "Quarterly",
        "SA": "Semi-Annually",
        "A": "Annually",
        "2y": "Every 2 Years",
        "3y": "Every 3 Years",
        "5y": "Every 5 Years"
    }
    return frequency_map.get(frequency, frequency)