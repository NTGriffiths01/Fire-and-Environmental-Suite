from sqlalchemy.orm import Session
from monthly_inspection_models import ViolationCode, ViolationPDF
from typing import List, Dict, Any, Optional
import uuid
import base64
import logging

logger = logging.getLogger(__name__)

class ViolationCodesService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_violation_code(self, code_data: Dict[str, Any]) -> ViolationCode:
        """Create a new violation code"""
        try:
            violation_code = ViolationCode(
                id=str(uuid.uuid4()),
                code_type=code_data.get("code_type"),
                code_number=code_data.get("code_number"),
                section=code_data.get("section"),
                title=code_data.get("title"),
                description=code_data.get("description"),
                severity_level=code_data.get("severity_level", "medium"),
                area_category=code_data.get("area_category"),
                pdf_document_id=code_data.get("pdf_document_id"),
                is_active=code_data.get("is_active", True)
            )
            
            self.db.add(violation_code)
            self.db.commit()
            self.db.refresh(violation_code)
            
            logger.info(f"Created violation code: {violation_code.code_type} {violation_code.code_number}")
            return violation_code
            
        except Exception as e:
            logger.error(f"Error creating violation code: {str(e)}")
            self.db.rollback()
            raise
    
    def get_violation_codes(self, code_type: str = None, area_category: str = None, is_active: bool = True) -> List[ViolationCode]:
        """Get violation codes with optional filters"""
        query = self.db.query(ViolationCode)
        
        if code_type:
            query = query.filter(ViolationCode.code_type == code_type)
        
        if area_category:
            query = query.filter(ViolationCode.area_category == area_category)
        
        if is_active is not None:
            query = query.filter(ViolationCode.is_active == is_active)
        
        return query.order_by(ViolationCode.code_type, ViolationCode.code_number).all()
    
    def get_violation_code_by_id(self, code_id: str) -> Optional[ViolationCode]:
        """Get violation code by ID"""
        return self.db.query(ViolationCode).filter(ViolationCode.id == code_id).first()
    
    def search_violation_codes(self, search_term: str) -> List[ViolationCode]:
        """Search violation codes by title or description"""
        return self.db.query(ViolationCode).filter(
            ViolationCode.is_active == True,
            (ViolationCode.title.ilike(f"%{search_term}%") | 
             ViolationCode.description.ilike(f"%{search_term}%") |
             ViolationCode.code_number.ilike(f"%{search_term}%"))
        ).order_by(ViolationCode.code_type, ViolationCode.code_number).all()
    
    def update_violation_code(self, code_id: str, update_data: Dict[str, Any]) -> ViolationCode:
        """Update a violation code"""
        violation_code = self.get_violation_code_by_id(code_id)
        if not violation_code:
            raise ValueError("Violation code not found")
        
        # Update allowed fields
        updateable_fields = [
            'title', 'description', 'severity_level', 'area_category', 
            'pdf_document_id', 'is_active'
        ]
        
        for field in updateable_fields:
            if field in update_data:
                setattr(violation_code, field, update_data[field])
        
        self.db.commit()
        self.db.refresh(violation_code)
        
        return violation_code
    
    def delete_violation_code(self, code_id: str) -> bool:
        """Soft delete a violation code"""
        violation_code = self.get_violation_code_by_id(code_id)
        if not violation_code:
            raise ValueError("Violation code not found")
        
        violation_code.is_active = False
        self.db.commit()
        
        return True
    
    def upload_violation_pdf(self, file_data: Dict[str, Any]) -> ViolationPDF:
        """Upload a violation code PDF document"""
        try:
            violation_pdf = ViolationPDF(
                id=str(uuid.uuid4()),
                filename=file_data.get("filename"),
                file_type=file_data.get("file_type"),
                file_size=file_data.get("file_size"),
                base64_content=file_data.get("base64_content"),
                code_type=file_data.get("code_type"),
                uploaded_by=file_data.get("uploaded_by"),
                description=file_data.get("description"),
                is_active=file_data.get("is_active", True)
            )
            
            self.db.add(violation_pdf)
            self.db.commit()
            self.db.refresh(violation_pdf)
            
            logger.info(f"Uploaded violation PDF: {violation_pdf.filename}")
            return violation_pdf
            
        except Exception as e:
            logger.error(f"Error uploading violation PDF: {str(e)}")
            self.db.rollback()
            raise
    
    def get_violation_pdfs(self, code_type: str = None) -> List[ViolationPDF]:
        """Get violation PDFs with optional filtering"""
        query = self.db.query(ViolationPDF).filter(ViolationPDF.is_active == True)
        
        if code_type:
            query = query.filter(ViolationPDF.code_type == code_type)
        
        return query.order_by(ViolationPDF.uploaded_at.desc()).all()
    
    def get_violation_pdf_by_id(self, pdf_id: str) -> Optional[ViolationPDF]:
        """Get violation PDF by ID"""
        return self.db.query(ViolationPDF).filter(ViolationPDF.id == pdf_id).first()
    
    def delete_violation_pdf(self, pdf_id: str) -> bool:
        """Soft delete a violation PDF"""
        violation_pdf = self.get_violation_pdf_by_id(pdf_id)
        if not violation_pdf:
            raise ValueError("Violation PDF not found")
        
        violation_pdf.is_active = False
        self.db.commit()
        
        return True
    
    def seed_default_violation_codes(self) -> Dict[str, Any]:
        """Seed the database with default violation codes"""
        try:
            # ICC Fire Safety Codes
            icc_codes = [
                {
                    "code_type": "ICC",
                    "code_number": "503.1",
                    "section": "Fire apparatus access roads",
                    "title": "Fire apparatus access roads shall be provided",
                    "description": "Fire apparatus access roads shall be provided to serve all portions of a building or structure",
                    "severity_level": "high",
                    "area_category": "fire_safety"
                },
                {
                    "code_type": "ICC",
                    "code_number": "901.1",
                    "section": "Fire protection systems",
                    "title": "Fire protection systems shall be maintained",
                    "description": "Fire protection systems shall be maintained in accordance with the International Fire Code",
                    "severity_level": "high",
                    "area_category": "fire_safety"
                },
                {
                    "code_type": "ICC",
                    "code_number": "1031.1",
                    "section": "Emergency egress",
                    "title": "Emergency egress shall be maintained",
                    "description": "Emergency egress shall be maintained in accordance with the International Fire Code",
                    "severity_level": "critical",
                    "area_category": "fire_safety"
                }
            ]
            
            # 780 CMR Codes
            cmr_780_codes = [
                {
                    "code_type": "780_CMR",
                    "code_number": "1009.1",
                    "section": "Exits and emergency egress",
                    "title": "Exits shall be clearly marked and unobstructed",
                    "description": "All exits shall be clearly marked and kept free from obstruction",
                    "severity_level": "high",
                    "area_category": "fire_safety"
                },
                {
                    "code_type": "780_CMR",
                    "code_number": "901.6",
                    "section": "Fire extinguishers",
                    "title": "Fire extinguishers shall be properly maintained",
                    "description": "Fire extinguishers shall be inspected and maintained in accordance with NFPA standards",
                    "severity_level": "medium",
                    "area_category": "fire_safety"
                }
            ]
            
            # 527 CMR Codes
            cmr_527_codes = [
                {
                    "code_type": "527_CMR",
                    "code_number": "1.0",
                    "section": "General requirements",
                    "title": "General fire safety requirements",
                    "description": "General fire safety requirements for correctional facilities",
                    "severity_level": "medium",
                    "area_category": "fire_safety"
                }
            ]
            
            # 105 CMR 451 Environmental Health Codes
            cmr_451_codes = [
                {
                    "code_type": "105_CMR_451",
                    "code_number": "451.110",
                    "section": "Food service sanitation",
                    "title": "Food service areas shall be maintained in sanitary condition",
                    "description": "All food service areas shall be maintained in a clean and sanitary condition",
                    "severity_level": "high",
                    "area_category": "environmental_health"
                },
                {
                    "code_type": "105_CMR_451",
                    "code_number": "451.120",
                    "section": "Water supply",
                    "title": "Potable water supply shall be maintained",
                    "description": "A safe and adequate supply of potable water shall be maintained",
                    "severity_level": "critical",
                    "area_category": "environmental_health"
                },
                {
                    "code_type": "105_CMR_451",
                    "code_number": "451.130",
                    "section": "Waste management",
                    "title": "Waste shall be properly managed and disposed",
                    "description": "All waste shall be properly collected, stored, and disposed of in accordance with regulations",
                    "severity_level": "medium",
                    "area_category": "environmental_health"
                },
                {
                    "code_type": "105_CMR_451",
                    "code_number": "451.140",
                    "section": "Pest control",
                    "title": "Pest control program shall be maintained",
                    "description": "An effective pest control program shall be maintained to prevent infestations",
                    "severity_level": "medium",
                    "area_category": "environmental_health"
                }
            ]
            
            # Combine all codes
            all_codes = icc_codes + cmr_780_codes + cmr_527_codes + cmr_451_codes
            
            created_count = 0
            for code_data in all_codes:
                try:
                    existing = self.db.query(ViolationCode).filter(
                        ViolationCode.code_type == code_data["code_type"],
                        ViolationCode.code_number == code_data["code_number"],
                        ViolationCode.section == code_data["section"]
                    ).first()
                    
                    if not existing:
                        self.create_violation_code(code_data)
                        created_count += 1
                        
                except Exception as e:
                    logger.error(f"Error creating violation code {code_data['code_number']}: {str(e)}")
                    continue
            
            result = {
                "created_count": created_count,
                "total_codes": len(all_codes),
                "seeded_at": datetime.utcnow()
            }
            
            logger.info(f"Seeded {created_count} violation codes")
            return result
            
        except Exception as e:
            logger.error(f"Error seeding violation codes: {str(e)}")
            raise
    
    def get_violation_codes_by_area(self) -> Dict[str, List[ViolationCode]]:
        """Get violation codes grouped by area category"""
        codes = self.get_violation_codes(is_active=True)
        
        grouped = {
            "fire_safety": [],
            "environmental_health": []
        }
        
        for code in codes:
            if code.area_category in grouped:
                grouped[code.area_category].append(code)
        
        return grouped
    
    def validate_file_upload(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_data) > max_size:
            raise ValueError("File size exceeds maximum limit of 10MB")
        
        # Check file type
        allowed_types = ['.pdf', '.doc', '.docx']
        file_extension = filename.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_types:
            raise ValueError("File type not supported. Please upload PDF, DOC, or DOCX files.")
        
        # Convert to base64
        base64_content = base64.b64encode(file_data).decode('utf-8')
        
        return {
            "filename": filename,
            "file_type": file_extension,
            "file_size": len(file_data),
            "base64_content": base64_content,
            "is_valid": True
        }