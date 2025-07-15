from sqlalchemy.orm import Session
from compliance_models import ComplianceDocument, ComplianceRecord
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import base64
import mimetypes
import os
import hashlib
import logging

logger = logging.getLogger(__name__)

class DocumentManagementService:
    def __init__(self, db: Session):
        self.db = db
    
    # Supported file types
    SUPPORTED_TYPES = {
        'pdf': ['application/pdf'],
        'doc': ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'excel': ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'image': ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff'],
        'text': ['text/plain', 'text/csv'],
        'archive': ['application/zip', 'application/x-rar-compressed']
    }
    
    # Maximum file size (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    def validate_file(self, filename: str, file_content: bytes, file_type: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        errors = []
        warnings = []
        
        # Check file size
        if len(file_content) > self.MAX_FILE_SIZE:
            errors.append(f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({self.MAX_FILE_SIZE} bytes)")
        
        # Check file type
        is_supported = False
        detected_category = None
        
        for category, mime_types in self.SUPPORTED_TYPES.items():
            if file_type in mime_types:
                is_supported = True
                detected_category = category
                break
        
        if not is_supported:
            errors.append(f"File type '{file_type}' is not supported")
        
        # Check filename
        if not filename or len(filename) > 255:
            errors.append("Invalid filename")
        
        # Check for potentially dangerous file extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js']
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension in dangerous_extensions:
            errors.append(f"File extension '{file_extension}' is not allowed for security reasons")
        
        # File content validation
        if len(file_content) == 0:
            errors.append("File is empty")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "detected_category": detected_category,
            "file_size": len(file_content),
            "file_extension": file_extension
        }
    
    def upload_document(self, record_id: str, filename: str, file_content: bytes, 
                       file_type: str, uploaded_by: str, description: str = None) -> Dict[str, Any]:
        """Upload a document with validation and metadata"""
        
        # Validate file
        validation = self.validate_file(filename, file_content, file_type)
        if not validation["is_valid"]:
            return {
                "success": False,
                "errors": validation["errors"],
                "document": None
            }
        
        # Check if record exists
        record = self.db.query(ComplianceRecord).filter(ComplianceRecord.id == record_id).first()
        if not record:
            return {
                "success": False,
                "errors": ["Compliance record not found"],
                "document": None
            }
        
        try:
            # Generate file hash for integrity verification
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Check for duplicate files
            existing_doc = self.db.query(ComplianceDocument).filter(
                ComplianceDocument.record_id == record_id,
                ComplianceDocument.filename == filename
            ).first()
            
            if existing_doc:
                # Create versioned filename
                base_name, extension = os.path.splitext(filename)
                version = 2
                while existing_doc:
                    versioned_filename = f"{base_name}_v{version}{extension}"
                    existing_doc = self.db.query(ComplianceDocument).filter(
                        ComplianceDocument.record_id == record_id,
                        ComplianceDocument.filename == versioned_filename
                    ).first()
                    version += 1
                filename = versioned_filename
            
            # Encode file content
            base64_content = base64.b64encode(file_content).decode('utf-8')
            
            # Create document record
            document = ComplianceDocument(
                id=str(uuid.uuid4()),
                record_id=record_id,
                filename=filename,
                file_type=file_type,
                file_size=len(file_content),
                base64_content=base64_content,
                uploaded_by=uploaded_by,
                uploaded_at=datetime.utcnow()
            )
            
            # Add metadata as JSON in a separate field (we'll need to add this to the model)
            metadata = {
                "description": description,
                "file_hash": file_hash,
                "detected_category": validation["detected_category"],
                "file_extension": validation["file_extension"],
                "upload_ip": "127.0.0.1",  # Would get from request in real app
                "validation_warnings": validation["warnings"]
            }
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Document uploaded successfully: {filename} for record {record_id}")
            
            return {
                "success": True,
                "errors": [],
                "document": {
                    "id": document.id,
                    "filename": document.filename,
                    "file_type": document.file_type,
                    "file_size": document.file_size,
                    "uploaded_by": document.uploaded_by,
                    "uploaded_at": document.uploaded_at,
                    "metadata": metadata
                }
            }
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return {
                "success": False,
                "errors": [f"Upload failed: {str(e)}"],
                "document": None
            }
    
    def get_document_by_id(self, document_id: str) -> Optional[ComplianceDocument]:
        """Get document by ID"""
        return self.db.query(ComplianceDocument).filter(ComplianceDocument.id == document_id).first()
    
    def get_documents_by_record(self, record_id: str) -> List[ComplianceDocument]:
        """Get all documents for a record"""
        return self.db.query(ComplianceDocument).filter(
            ComplianceDocument.record_id == record_id
        ).order_by(ComplianceDocument.uploaded_at.desc()).all()
    
    def get_document_content(self, document_id: str) -> Dict[str, Any]:
        """Get document content for download"""
        document = self.get_document_by_id(document_id)
        if not document:
            return {
                "success": False,
                "error": "Document not found"
            }
        
        try:
            # Decode base64 content
            file_content = base64.b64decode(document.base64_content)
            
            return {
                "success": True,
                "filename": document.filename,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "content": file_content
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error retrieving document content: {str(e)}"
            }
    
    def delete_document(self, document_id: str, deleted_by: str) -> Dict[str, Any]:
        """Delete a document"""
        document = self.get_document_by_id(document_id)
        if not document:
            return {
                "success": False,
                "error": "Document not found"
            }
        
        try:
            # Log deletion for audit trail
            logger.info(f"Document deleted: {document.filename} (ID: {document_id}) by {deleted_by}")
            
            # Delete from database
            self.db.delete(document)
            self.db.commit()
            
            return {
                "success": True,
                "message": "Document deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return {
                "success": False,
                "error": f"Delete failed: {str(e)}"
            }
    
    def get_documents_by_facility(self, facility_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a facility"""
        from compliance_models import ComplianceSchedule
        
        documents = self.db.query(ComplianceDocument).join(
            ComplianceRecord, ComplianceDocument.record_id == ComplianceRecord.id
        ).join(
            ComplianceSchedule, ComplianceRecord.schedule_id == ComplianceSchedule.id
        ).filter(
            ComplianceSchedule.facility_id == facility_id
        ).order_by(ComplianceDocument.uploaded_at.desc()).all()
        
        return [self._document_to_dict(doc) for doc in documents]
    
    def get_document_statistics(self, facility_id: str = None) -> Dict[str, Any]:
        """Get document statistics"""
        base_query = self.db.query(ComplianceDocument)
        
        if facility_id:
            from compliance_models import ComplianceSchedule
            base_query = base_query.join(
                ComplianceRecord, ComplianceDocument.record_id == ComplianceRecord.id
            ).join(
                ComplianceSchedule, ComplianceRecord.schedule_id == ComplianceSchedule.id
            ).filter(ComplianceSchedule.facility_id == facility_id)
        
        documents = base_query.all()
        
        # Calculate statistics
        total_documents = len(documents)
        total_size = sum(doc.file_size for doc in documents)
        
        # Group by file type
        type_breakdown = {}
        for doc in documents:
            file_type = doc.file_type
            if file_type not in type_breakdown:
                type_breakdown[file_type] = {"count": 0, "size": 0}
            type_breakdown[file_type]["count"] += 1
            type_breakdown[file_type]["size"] += doc.file_size
        
        # Group by category
        category_breakdown = {}
        for doc in documents:
            category = self._get_file_category(doc.file_type)
            if category not in category_breakdown:
                category_breakdown[category] = {"count": 0, "size": 0}
            category_breakdown[category]["count"] += 1
            category_breakdown[category]["size"] += doc.file_size
        
        return {
            "total_documents": total_documents,
            "total_size": total_size,
            "average_size": total_size / total_documents if total_documents > 0 else 0,
            "type_breakdown": type_breakdown,
            "category_breakdown": category_breakdown
        }
    
    def _get_file_category(self, file_type: str) -> str:
        """Get file category from MIME type"""
        for category, mime_types in self.SUPPORTED_TYPES.items():
            if file_type in mime_types:
                return category
        return "unknown"
    
    def _document_to_dict(self, document: ComplianceDocument) -> Dict[str, Any]:
        """Convert document to dictionary"""
        return {
            "id": document.id,
            "record_id": document.record_id,
            "filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "uploaded_by": document.uploaded_by,
            "uploaded_at": document.uploaded_at,
            "category": self._get_file_category(document.file_type)
        }
    
    def bulk_upload_documents(self, uploads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk upload multiple documents"""
        results = []
        success_count = 0
        error_count = 0
        
        for upload in uploads:
            try:
                result = self.upload_document(
                    record_id=upload["record_id"],
                    filename=upload["filename"],
                    file_content=upload["file_content"],
                    file_type=upload["file_type"],
                    uploaded_by=upload["uploaded_by"],
                    description=upload.get("description")
                )
                
                results.append({
                    "filename": upload["filename"],
                    "success": result["success"],
                    "errors": result["errors"],
                    "document_id": result["document"]["id"] if result["success"] else None
                })
                
                if result["success"]:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                results.append({
                    "filename": upload.get("filename", "unknown"),
                    "success": False,
                    "errors": [str(e)],
                    "document_id": None
                })
                error_count += 1
        
        return {
            "total_uploads": len(uploads),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }