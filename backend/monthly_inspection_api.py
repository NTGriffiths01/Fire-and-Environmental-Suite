from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
from models import get_db
from monthly_inspection_service import MonthlyInspectionService
from violation_codes_service import ViolationCodesService
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import json
import logging

logger = logging.getLogger(__name__)

def create_monthly_inspection_router():
    router = APIRouter()

    # Pydantic models for API responses
    class MonthlyInspectionResponse(BaseModel):
        id: str
        facility_id: str
        year: int
        month: int
        inspection_date: Optional[date]
        status: str
        created_by: str
        created_at: datetime
        updated_at: datetime
        form_data: Dict[str, Any]
        notes: Optional[str]
        carryover_deficiencies: List[Dict[str, Any]]

    class InspectionSignatureResponse(BaseModel):
        id: str
        inspection_id: str
        signature_type: str
        signed_by: str
        signed_at: datetime
        verification_hash: str

    class InspectionDeficiencyResponse(BaseModel):
        id: str
        inspection_id: str
        area_type: str
        location: Optional[str]
        description: str
        citation_code: Optional[str]
        citation_section: Optional[str]
        severity: str
        status: str
        corrective_action: Optional[str]
        target_completion_date: Optional[date]
        actual_completion_date: Optional[date]
        completed_by: Optional[str]
        carryover_from_month: Optional[int]
        created_at: datetime
        updated_at: datetime

    class ViolationCodeResponse(BaseModel):
        id: str
        code_type: str
        code_number: str
        section: Optional[str]
        title: str
        description: Optional[str]
        severity_level: str
        area_category: str
        is_active: bool

    class InspectionStatisticsResponse(BaseModel):
        total_inspections: int
        completed_inspections: int
        pending_inspector: int
        pending_deputy: int
        completion_rate: float
        total_deficiencies: int
        open_deficiencies: int
        resolved_deficiencies: int
        deficiency_resolution_rate: float

    def inspection_to_dict(inspection) -> Dict[str, Any]:
        """Convert inspection model to dictionary"""
        return {
            "id": inspection.id,
            "facility_id": inspection.facility_id,
            "year": inspection.year,
            "month": inspection.month,
            "inspection_date": inspection.inspection_date,
            "status": inspection.status,
            "created_by": inspection.created_by,
            "created_at": inspection.created_at,
            "updated_at": inspection.updated_at,
            "form_data": inspection.form_data or {},
            "notes": inspection.notes,
            "carryover_deficiencies": inspection.carryover_deficiencies or []
        }

    def signature_to_dict(signature) -> Dict[str, Any]:
        """Convert signature model to dictionary"""
        return {
            "id": signature.id,
            "inspection_id": signature.inspection_id,
            "signature_type": signature.signature_type,
            "signed_by": signature.signed_by,
            "signed_at": signature.signed_at,
            "verification_hash": signature.verification_hash
        }

    def deficiency_to_dict(deficiency) -> Dict[str, Any]:
        """Convert deficiency model to dictionary"""
        return {
            "id": deficiency.id,
            "inspection_id": deficiency.inspection_id,
            "area_type": deficiency.area_type,
            "location": deficiency.location,
            "description": deficiency.description,
            "citation_code": deficiency.citation_code,
            "citation_section": deficiency.citation_section,
            "severity": deficiency.severity,
            "status": deficiency.status,
            "corrective_action": deficiency.corrective_action,
            "target_completion_date": deficiency.target_completion_date,
            "actual_completion_date": deficiency.actual_completion_date,
            "completed_by": deficiency.completed_by,
            "carryover_from_month": deficiency.carryover_from_month,
            "created_at": deficiency.created_at,
            "updated_at": deficiency.updated_at
        }

    def violation_code_to_dict(code) -> Dict[str, Any]:
        """Convert violation code model to dictionary"""
        return {
            "id": code.id,
            "code_type": code.code_type,
            "code_number": code.code_number,
            "section": code.section,
            "title": code.title,
            "description": code.description,
            "severity_level": code.severity_level,
            "area_category": code.area_category,
            "is_active": code.is_active
        }

    # **Monthly Inspection Endpoints**

    @router.post("/create")
    async def create_monthly_inspection(
        facility_id: str = Form(...),
        year: int = Form(...),
        month: int = Form(...),
        created_by: str = Form(...),
        db: Session = Depends(get_db)
    ):
        """Create a new monthly inspection"""
        try:
            service = MonthlyInspectionService(db)
            inspection = service.create_monthly_inspection(facility_id, year, month, created_by)
            return {
                "success": True,
                "message": "Monthly inspection created successfully",
                "inspection": inspection_to_dict(inspection)
            }
        except Exception as e:
            logger.error(f"Error creating monthly inspection: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{inspection_id}")
    async def get_monthly_inspection(inspection_id: str, db: Session = Depends(get_db)):
        """Get monthly inspection by ID"""
        try:
            service = MonthlyInspectionService(db)
            inspection = service.get_monthly_inspection(inspection_id)
            if not inspection:
                raise HTTPException(status_code=404, detail="Monthly inspection not found")
            return inspection_to_dict(inspection)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting monthly inspection: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/facility/{facility_id}")
    async def get_monthly_inspections_by_facility(
        facility_id: str, 
        year: int = None, 
        db: Session = Depends(get_db)
    ):
        """Get all monthly inspections for a facility"""
        try:
            service = MonthlyInspectionService(db)
            inspections = service.get_monthly_inspections_by_facility(facility_id, year)
            return [inspection_to_dict(inspection) for inspection in inspections]
        except Exception as e:
            logger.error(f"Error getting monthly inspections: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.put("/{inspection_id}/form-data")
    async def update_inspection_form_data(
        inspection_id: str,
        form_data: str = Form(...),
        db: Session = Depends(get_db)
    ):
        """Update inspection form data"""
        try:
            service = MonthlyInspectionService(db)
            parsed_form_data = json.loads(form_data)
            inspection = service.update_inspection_form_data(inspection_id, parsed_form_data)
            return {
                "success": True,
                "message": "Form data updated successfully",
                "inspection": inspection_to_dict(inspection)
            }
        except Exception as e:
            logger.error(f"Error updating form data: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/{inspection_id}/signature")
    async def add_inspection_signature(
        inspection_id: str,
        signature_type: str = Form(...),
        signed_by: str = Form(...),
        signature_data: str = Form(...),
        ip_address: str = Form(None),
        user_agent: str = Form(None),
        db: Session = Depends(get_db)
    ):
        """Add a signature to an inspection"""
        try:
            service = MonthlyInspectionService(db)
            signature = service.add_inspection_signature(
                inspection_id, signature_type, signed_by, signature_data, ip_address, user_agent
            )
            return {
                "success": True,
                "message": f"{signature_type} signature added successfully",
                "signature": signature_to_dict(signature)
            }
        except Exception as e:
            logger.error(f"Error adding signature: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{inspection_id}/signatures")
    async def get_inspection_signatures(inspection_id: str, db: Session = Depends(get_db)):
        """Get all signatures for an inspection"""
        try:
            service = MonthlyInspectionService(db)
            inspection = service.get_monthly_inspection(inspection_id)
            if not inspection:
                raise HTTPException(status_code=404, detail="Monthly inspection not found")
            return [signature_to_dict(sig) for sig in inspection.signatures]
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting signatures: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # **Deficiency Management Endpoints**

    @router.post("/{inspection_id}/deficiencies")
    async def add_inspection_deficiency(
        inspection_id: str,
        area_type: str = Form(...),
        description: str = Form(...),
        location: str = Form(None),
        citation_code: str = Form(None),
        citation_section: str = Form(None),
        severity: str = Form("medium"),
        corrective_action: str = Form(None),
        target_completion_date: str = Form(None),
        violation_code_id: str = Form(None),
        carryover_from_month: int = Form(None),
        db: Session = Depends(get_db)
    ):
        """Add a deficiency to an inspection"""
        try:
            service = MonthlyInspectionService(db)
            deficiency_data = {
                "area_type": area_type,
                "description": description,
                "location": location,
                "citation_code": citation_code,
                "citation_section": citation_section,
                "severity": severity,
                "corrective_action": corrective_action,
                "target_completion_date": target_completion_date,
                "violation_code_id": violation_code_id,
                "carryover_from_month": carryover_from_month
            }
            
            deficiency = service.add_inspection_deficiency(inspection_id, deficiency_data)
            return {
                "success": True,
                "message": "Deficiency added successfully",
                "deficiency": deficiency_to_dict(deficiency)
            }
        except Exception as e:
            logger.error(f"Error adding deficiency: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{inspection_id}/deficiencies")
    async def get_inspection_deficiencies(inspection_id: str, db: Session = Depends(get_db)):
        """Get all deficiencies for an inspection"""
        try:
            service = MonthlyInspectionService(db)
            deficiencies = service.get_inspection_deficiencies(inspection_id)
            return [deficiency_to_dict(deficiency) for deficiency in deficiencies]
        except Exception as e:
            logger.error(f"Error getting deficiencies: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.put("/deficiencies/{deficiency_id}/status")
    async def update_deficiency_status(
        deficiency_id: str,
        status: str = Form(...),
        completed_by: str = Form(None),
        db: Session = Depends(get_db)
    ):
        """Update deficiency status"""
        try:
            service = MonthlyInspectionService(db)
            deficiency = service.update_deficiency_status(deficiency_id, status, completed_by)
            return {
                "success": True,
                "message": "Deficiency status updated successfully",
                "deficiency": deficiency_to_dict(deficiency)
            }
        except Exception as e:
            logger.error(f"Error updating deficiency status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # **Violation Codes Endpoints**

    @router.get("/violation-codes")
    async def get_violation_codes(
        code_type: str = None,
        area_category: str = None,
        search: str = None,
        db: Session = Depends(get_db)
    ):
        """Get violation codes with optional filters"""
        try:
            service = ViolationCodesService(db)
            
            if search:
                codes = service.search_violation_codes(search)
            else:
                codes = service.get_violation_codes(code_type, area_category)
            
            return [violation_code_to_dict(code) for code in codes]
        except Exception as e:
            logger.error(f"Error getting violation codes: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/violation-codes/by-area")
    async def get_violation_codes_by_area(db: Session = Depends(get_db)):
        """Get violation codes grouped by area category"""
        try:
            service = ViolationCodesService(db)
            grouped_codes = service.get_violation_codes_by_area()
            
            result = {}
            for area, codes in grouped_codes.items():
                result[area] = [violation_code_to_dict(code) for code in codes]
            
            return result
        except Exception as e:
            logger.error(f"Error getting violation codes by area: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/violation-codes")
    async def create_violation_code(
        code_type: str = Form(...),
        code_number: str = Form(...),
        title: str = Form(...),
        section: str = Form(None),
        description: str = Form(None),
        severity_level: str = Form("medium"),
        area_category: str = Form(...),
        db: Session = Depends(get_db)
    ):
        """Create a new violation code"""
        try:
            service = ViolationCodesService(db)
            code_data = {
                "code_type": code_type,
                "code_number": code_number,
                "title": title,
                "section": section,
                "description": description,
                "severity_level": severity_level,
                "area_category": area_category
            }
            
            violation_code = service.create_violation_code(code_data)
            return {
                "success": True,
                "message": "Violation code created successfully",
                "violation_code": violation_code_to_dict(violation_code)
            }
        except Exception as e:
            logger.error(f"Error creating violation code: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/violation-codes/upload-pdf")
    async def upload_violation_pdf(
        file: UploadFile = File(...),
        code_type: str = Form(...),
        uploaded_by: str = Form(...),
        description: str = Form(None),
        db: Session = Depends(get_db)
    ):
        """Upload a violation code PDF document"""
        try:
            service = ViolationCodesService(db)
            
            # Read and validate file
            file_content = await file.read()
            validated_file = service.validate_file_upload(file_content, file.filename)
            
            file_data = {
                "filename": validated_file["filename"],
                "file_type": validated_file["file_type"],
                "file_size": validated_file["file_size"],
                "base64_content": validated_file["base64_content"],
                "code_type": code_type,
                "uploaded_by": uploaded_by,
                "description": description
            }
            
            violation_pdf = service.upload_violation_pdf(file_data)
            return {
                "success": True,
                "message": "PDF uploaded successfully",
                "pdf_id": violation_pdf.id
            }
        except Exception as e:
            logger.error(f"Error uploading PDF: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # **System Management Endpoints**

    @router.post("/monthly-inspections/auto-generate")
    async def auto_generate_monthly_inspections(
        target_year: int = Form(None),
        target_month: int = Form(None),
        db: Session = Depends(get_db)
    ):
        """Auto-generate monthly inspections for all facilities"""
        try:
            service = MonthlyInspectionService(db)
            
            if target_year and target_month:
                target_date = date(target_year, target_month, 1)
            else:
                target_date = date.today()
            
            result = service.auto_generate_monthly_inspections(target_date)
            return {
                "success": True,
                "message": f"Generated {result['created_count']} monthly inspections",
                "result": result
            }
        except Exception as e:
            logger.error(f"Error auto-generating inspections: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/monthly-inspections/statistics")
    async def get_inspection_statistics(
        facility_id: str = None,
        year: int = None,
        db: Session = Depends(get_db)
    ):
        """Get inspection statistics"""
        try:
            service = MonthlyInspectionService(db)
            stats = service.get_inspection_statistics(facility_id, year)
            return InspectionStatisticsResponse(**stats)
        except Exception as e:
            logger.error(f"Error getting inspection statistics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/violation-codes/seed")
    async def seed_violation_codes(db: Session = Depends(get_db)):
        """Seed the database with default violation codes"""
        try:
            service = ViolationCodesService(db)
            result = service.seed_default_violation_codes()
            return {
                "success": True,
                "message": f"Seeded {result['created_count']} violation codes",
                "result": result
            }
        except Exception as e:
            logger.error(f"Error seeding violation codes: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router

# Create the router instance
monthly_inspection_router = create_monthly_inspection_router()