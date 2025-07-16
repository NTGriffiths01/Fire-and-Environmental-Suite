from sqlalchemy.orm import Session
from monthly_inspection_models import (
    MonthlyInspection, InspectionSignature, InspectionDeficiency, 
    ViolationCode, FormConfiguration, ViolationPDF
)
from compliance_models import ComplianceFacility
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import uuid
import json
import hashlib
import base64
import logging

logger = logging.getLogger(__name__)

class MonthlyInspectionService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_monthly_inspection(self, facility_id: str, year: int, month: int, created_by: str) -> MonthlyInspection:
        """Create a new monthly inspection"""
        try:
            # Check if inspection already exists
            existing = self.db.query(MonthlyInspection).filter(
                MonthlyInspection.facility_id == facility_id,
                MonthlyInspection.year == year,
                MonthlyInspection.month == month
            ).first()
            
            if existing:
                return existing
            
            # Get carryover deficiencies from previous month
            carryover_deficiencies = self._get_carryover_deficiencies(facility_id, year, month)
            
            # Create new inspection
            inspection = MonthlyInspection(
                id=str(uuid.uuid4()),
                facility_id=facility_id,
                year=year,
                month=month,
                created_by=created_by,
                carryover_deficiencies=carryover_deficiencies,
                form_data={}
            )
            
            self.db.add(inspection)
            self.db.commit()
            self.db.refresh(inspection)
            
            logger.info(f"Created monthly inspection for facility {facility_id}, {year}-{month}")
            return inspection
            
        except Exception as e:
            logger.error(f"Error creating monthly inspection: {str(e)}")
            self.db.rollback()
            raise
    
    def get_monthly_inspection(self, inspection_id: str) -> Optional[MonthlyInspection]:
        """Get monthly inspection by ID"""
        return self.db.query(MonthlyInspection).filter(MonthlyInspection.id == inspection_id).first()
    
    def get_monthly_inspections_by_facility(self, facility_id: str, year: int = None) -> List[MonthlyInspection]:
        """Get all monthly inspections for a facility"""
        query = self.db.query(MonthlyInspection).filter(MonthlyInspection.facility_id == facility_id)
        
        if year:
            query = query.filter(MonthlyInspection.year == year)
        
        return query.order_by(MonthlyInspection.year.desc(), MonthlyInspection.month.desc()).all()
    
    def update_inspection_form_data(self, inspection_id: str, form_data: Dict[str, Any]) -> MonthlyInspection:
        """Update inspection form data"""
        inspection = self.get_monthly_inspection(inspection_id)
        if not inspection:
            raise ValueError("Inspection not found")
        
        inspection.form_data = form_data
        inspection.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(inspection)
        
        return inspection
    
    def add_inspection_signature(self, inspection_id: str, signature_type: str, signed_by: str, 
                               signature_data: str, ip_address: str = None, user_agent: str = None) -> InspectionSignature:
        """Add a signature to an inspection"""
        try:
            inspection = self.get_monthly_inspection(inspection_id)
            if not inspection:
                raise ValueError("Inspection not found")
            
            # Check if signature already exists
            existing_signature = self.db.query(InspectionSignature).filter(
                InspectionSignature.inspection_id == inspection_id,
                InspectionSignature.signature_type == signature_type
            ).first()
            
            if existing_signature:
                raise ValueError(f"{signature_type} signature already exists")
            
            # Create verification hash
            verification_hash = hashlib.sha256(
                f"{inspection_id}{signature_type}{signed_by}{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()
            
            # Create signature record
            signature = InspectionSignature(
                id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                signature_type=signature_type,
                signed_by=signed_by,
                signed_at=datetime.utcnow(),
                signature_data=signature_data,
                ip_address=ip_address,
                user_agent=user_agent,
                verification_hash=verification_hash
            )
            
            self.db.add(signature)
            
            # Update inspection status
            if signature_type == "inspector":
                inspection.status = "inspector_signed"
            elif signature_type == "deputy" and inspection.status == "inspector_signed":
                inspection.status = "deputy_signed"
                # Auto-populate to compliance tracking
                self._populate_to_compliance_tracking(inspection)
            
            inspection.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(signature)
            
            logger.info(f"Added {signature_type} signature to inspection {inspection_id}")
            return signature
            
        except Exception as e:
            logger.error(f"Error adding signature: {str(e)}")
            self.db.rollback()
            raise
    
    def add_inspection_deficiency(self, inspection_id: str, deficiency_data: Dict[str, Any]) -> InspectionDeficiency:
        """Add a deficiency to an inspection"""
        try:
            inspection = self.get_monthly_inspection(inspection_id)
            if not inspection:
                raise ValueError("Inspection not found")
            
            deficiency = InspectionDeficiency(
                id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                area_type=deficiency_data.get("area_type"),
                location=deficiency_data.get("location"),
                description=deficiency_data.get("description"),
                citation_code=deficiency_data.get("citation_code"),
                citation_section=deficiency_data.get("citation_section"),
                severity=deficiency_data.get("severity", "medium"),
                corrective_action=deficiency_data.get("corrective_action"),
                target_completion_date=deficiency_data.get("target_completion_date"),
                carryover_from_month=deficiency_data.get("carryover_from_month"),
                violation_code_id=deficiency_data.get("violation_code_id")
            )
            
            self.db.add(deficiency)
            self.db.commit()
            self.db.refresh(deficiency)
            
            logger.info(f"Added deficiency to inspection {inspection_id}")
            return deficiency
            
        except Exception as e:
            logger.error(f"Error adding deficiency: {str(e)}")
            self.db.rollback()
            raise
    
    def get_inspection_deficiencies(self, inspection_id: str) -> List[InspectionDeficiency]:
        """Get all deficiencies for an inspection"""
        return self.db.query(InspectionDeficiency).filter(
            InspectionDeficiency.inspection_id == inspection_id
        ).all()
    
    def update_deficiency_status(self, deficiency_id: str, status: str, completed_by: str = None) -> InspectionDeficiency:
        """Update deficiency status"""
        deficiency = self.db.query(InspectionDeficiency).filter(
            InspectionDeficiency.id == deficiency_id
        ).first()
        
        if not deficiency:
            raise ValueError("Deficiency not found")
        
        deficiency.status = status
        deficiency.updated_at = datetime.utcnow()
        
        if status == "resolved":
            deficiency.actual_completion_date = date.today()
            deficiency.completed_by = completed_by
        
        self.db.commit()
        self.db.refresh(deficiency)
        
        return deficiency
    
    def auto_generate_monthly_inspections(self, target_date: date = None) -> Dict[str, Any]:
        """Auto-generate monthly inspections for all facilities"""
        if not target_date:
            target_date = date.today()
        
        # Get all active facilities
        facilities = self.db.query(ComplianceFacility).filter(
            ComplianceFacility.is_active == True
        ).all()
        
        created_count = 0
        errors = []
        
        for facility in facilities:
            try:
                inspection = self.create_monthly_inspection(
                    facility_id=facility.id,
                    year=target_date.year,
                    month=target_date.month,
                    created_by="system"
                )
                created_count += 1
                
            except Exception as e:
                errors.append(f"Error creating inspection for facility {facility.name}: {str(e)}")
        
        result = {
            "created_count": created_count,
            "total_facilities": len(facilities),
            "errors": errors,
            "generated_at": datetime.utcnow()
        }
        
        logger.info(f"Auto-generated {created_count} monthly inspections for {target_date.year}-{target_date.month}")
        return result
    
    def _get_carryover_deficiencies(self, facility_id: str, year: int, month: int) -> List[Dict[str, Any]]:
        """Get carryover deficiencies from previous month"""
        try:
            # Calculate previous month
            if month == 1:
                prev_year = year - 1
                prev_month = 12
            else:
                prev_year = year
                prev_month = month - 1
            
            # Get previous month's inspection
            prev_inspection = self.db.query(MonthlyInspection).filter(
                MonthlyInspection.facility_id == facility_id,
                MonthlyInspection.year == prev_year,
                MonthlyInspection.month == prev_month
            ).first()
            
            if not prev_inspection:
                return []
            
            # Get open deficiencies from previous month
            open_deficiencies = self.db.query(InspectionDeficiency).filter(
                InspectionDeficiency.inspection_id == prev_inspection.id,
                InspectionDeficiency.status.in_(["open", "in_progress"])
            ).all()
            
            carryover_data = []
            for deficiency in open_deficiencies:
                carryover_data.append({
                    "original_id": deficiency.id,
                    "area_type": deficiency.area_type,
                    "location": deficiency.location,
                    "description": deficiency.description,
                    "citation_code": deficiency.citation_code,
                    "citation_section": deficiency.citation_section,
                    "severity": deficiency.severity,
                    "corrective_action": deficiency.corrective_action,
                    "target_completion_date": deficiency.target_completion_date.isoformat() if deficiency.target_completion_date else None,
                    "carryover_from_month": prev_month,
                    "violation_code_id": deficiency.violation_code_id
                })
            
            return carryover_data
            
        except Exception as e:
            logger.error(f"Error getting carryover deficiencies: {str(e)}")
            return []
    
    def _populate_to_compliance_tracking(self, inspection: MonthlyInspection):
        """Populate completed inspection to compliance tracking system"""
        try:
            # This would integrate with the existing compliance tracking system
            # For now, we'll just log it
            logger.info(f"Populating inspection {inspection.id} to compliance tracking system")
            
            # TODO: Implement actual integration with compliance tracking
            # This would create or update a compliance record in the existing system
            
        except Exception as e:
            logger.error(f"Error populating to compliance tracking: {str(e)}")
    
    def get_inspection_statistics(self, facility_id: str = None, year: int = None) -> Dict[str, Any]:
        """Get inspection statistics"""
        query = self.db.query(MonthlyInspection)
        
        if facility_id:
            query = query.filter(MonthlyInspection.facility_id == facility_id)
        
        if year:
            query = query.filter(MonthlyInspection.year == year)
        
        inspections = query.all()
        
        # Calculate statistics
        total_inspections = len(inspections)
        completed_inspections = len([i for i in inspections if i.status == "deputy_signed"])
        pending_inspector = len([i for i in inspections if i.status == "draft"])
        pending_deputy = len([i for i in inspections if i.status == "inspector_signed"])
        
        # Get deficiency statistics
        total_deficiencies = 0
        open_deficiencies = 0
        resolved_deficiencies = 0
        
        for inspection in inspections:
            deficiencies = self.get_inspection_deficiencies(inspection.id)
            total_deficiencies += len(deficiencies)
            open_deficiencies += len([d for d in deficiencies if d.status in ["open", "in_progress"]])
            resolved_deficiencies += len([d for d in deficiencies if d.status == "resolved"])
        
        return {
            "total_inspections": total_inspections,
            "completed_inspections": completed_inspections,
            "pending_inspector": pending_inspector,
            "pending_deputy": pending_deputy,
            "completion_rate": (completed_inspections / total_inspections * 100) if total_inspections > 0 else 0,
            "total_deficiencies": total_deficiencies,
            "open_deficiencies": open_deficiencies,
            "resolved_deficiencies": resolved_deficiencies,
            "deficiency_resolution_rate": (resolved_deficiencies / total_deficiencies * 100) if total_deficiencies > 0 else 0
        }