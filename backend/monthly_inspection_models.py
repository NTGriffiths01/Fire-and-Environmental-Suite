from sqlalchemy import Column, String, DateTime, Boolean, Text, Date, Integer, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid
from models import Base

class MonthlyInspection(Base):
    __tablename__ = "monthly_inspections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    inspection_date = Column(Date)
    status = Column(String(20), default="draft")  # draft, inspector_signed, deputy_signed, completed
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    form_data = Column(JSON)  # Store the complete form data
    notes = Column(Text)
    carryover_deficiencies = Column(JSON)  # Previous month's deficiencies
    
    # Relationships
    signatures = relationship("InspectionSignature", back_populates="inspection")
    deficiencies = relationship("InspectionDeficiency", back_populates="inspection")
    
    # Composite unique constraint
    __table_args__ = (UniqueConstraint('facility_id', 'year', 'month', name='uq_monthly_inspection_facility_year_month'),)

class InspectionSignature(Base):
    __tablename__ = "inspection_signatures"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("monthly_inspections.id"), nullable=False)
    signature_type = Column(String(20), nullable=False)  # inspector, deputy
    signed_by = Column(String(100), nullable=False)
    signed_at = Column(DateTime, nullable=False)
    signature_data = Column(Text)  # Base64 encoded signature image
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    verification_hash = Column(String(256))  # For signature verification
    
    # Relationships
    inspection = relationship("MonthlyInspection", back_populates="signatures")

class InspectionDeficiency(Base):
    __tablename__ = "inspection_deficiencies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String(36), ForeignKey("monthly_inspections.id"), nullable=False)
    violation_code_id = Column(String(36), ForeignKey("violation_codes.id"))
    area_type = Column(String(50), nullable=False)  # fire_safety, environmental_health, etc.
    location = Column(String(200))
    description = Column(Text, nullable=False)
    citation_code = Column(String(50))
    citation_section = Column(String(100))
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(String(20), default="open")  # open, in_progress, resolved, carried_over
    corrective_action = Column(Text)
    target_completion_date = Column(Date)
    actual_completion_date = Column(Date)
    completed_by = Column(String(100))
    carryover_from_month = Column(Integer)  # If carried over from previous month
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inspection = relationship("MonthlyInspection", back_populates="deficiencies")
    violation_code = relationship("ViolationCode", back_populates="deficiencies")

class ViolationCode(Base):
    __tablename__ = "violation_codes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code_type = Column(String(50), nullable=False)  # ICC, 780_CMR, 527_CMR, 105_CMR_451
    code_number = Column(String(50), nullable=False)
    section = Column(String(100))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    severity_level = Column(String(20), default="medium")
    area_category = Column(String(50))  # fire_safety, environmental_health, etc.
    pdf_document_id = Column(String(36))  # Reference to uploaded PDF
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    deficiencies = relationship("InspectionDeficiency", back_populates="violation_code")
    
    # Composite unique constraint
    __table_args__ = (UniqueConstraint('code_type', 'code_number', 'section', name='uq_violation_code'),)

class FormConfiguration(Base):
    __tablename__ = "form_configurations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_type = Column(String(50), nullable=False)  # monthly_inspection
    section_name = Column(String(100), nullable=False)
    field_name = Column(String(100), nullable=False)
    field_type = Column(String(50), nullable=False)  # checkbox, text, textarea, select
    field_label = Column(String(200), nullable=False)
    is_enabled = Column(Boolean, default=True)
    is_required = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    field_options = Column(JSON)  # For select fields, etc.
    validation_rules = Column(JSON)
    role_visibility = Column(JSON)  # Which roles can see this field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint
    __table_args__ = (UniqueConstraint('form_type', 'section_name', 'field_name', name='uq_form_field'),)

class ViolationPDF(Base):
    __tablename__ = "violation_pdfs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    base64_content = Column(Text, nullable=False)
    code_type = Column(String(50), nullable=False)
    uploaded_by = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

# Utility functions
def get_inspection_status_display(status):
    """Get display name for inspection status"""
    status_map = {
        "draft": "Draft",
        "inspector_signed": "Inspector Signed",
        "deputy_signed": "Deputy Signed", 
        "completed": "Completed"
    }
    return status_map.get(status, status)

def get_deficiency_severity_display(severity):
    """Get display name for deficiency severity"""
    severity_map = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Critical"
    }
    return severity_map.get(severity, severity)

def get_deficiency_status_display(status):
    """Get display name for deficiency status"""
    status_map = {
        "open": "Open",
        "in_progress": "In Progress",
        "resolved": "Resolved",
        "carried_over": "Carried Over"
    }
    return status_map.get(status, status)