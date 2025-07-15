from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy.orm import Session
from models import get_db
from compliance_service import ComplianceService
from compliance_scheduling import ComplianceSchedulingService
from document_management import DocumentManagementService
from smart_features import SmartFeaturesService
from compliance_models import (
    ComplianceFacility, ComplianceFunction, ComplianceSchedule, 
    ComplianceRecord, ComplianceDocument, get_frequency_display
)
import io

# Additional Pydantic models for scheduling
class ScheduleUpdateRequest(BaseModel):
    schedule_id: str
    frequency: Optional[str] = None
    assigned_to: Optional[str] = None
    start_date: Optional[date] = None

class BulkScheduleUpdateRequest(BaseModel):
    updates: List[ScheduleUpdateRequest]

class ScheduleAnalyticsResponse(BaseModel):
    total_schedules: int
    frequency_breakdown: Dict[str, int]
    upcoming_due_dates: List[Dict[str, Any]]
    generated_at: datetime

class RecordGenerationResponse(BaseModel):
    records_generated: int
    records_updated: int
    total_schedules_processed: int

# Existing Pydantic models...
class FacilityResponse(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    facility_type: Optional[str] = None
    capacity: Optional[int] = None
    is_active: bool
    created_at: datetime

class ComplianceFunctionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    default_frequency: str
    citation_references: List[str]
    is_active: bool

class ComplianceScheduleResponse(BaseModel):
    id: str
    facility_id: str
    function_id: str
    frequency: str
    start_date: date
    next_due_date: date
    assigned_to: Optional[str] = None
    is_active: bool

class ComplianceRecordResponse(BaseModel):
    id: str
    schedule_id: str
    due_date: date
    completed_date: Optional[date] = None
    status: str
    completed_by: Optional[str] = None
    notes: Optional[str] = None
    has_documents: bool = False

class ComplianceDocumentResponse(BaseModel):
    id: str
    record_id: str
    filename: str
    file_type: str
    file_size: int
    uploaded_by: str
    uploaded_at: datetime

class DashboardCellResponse(BaseModel):
    status: str
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    has_documents: bool = False

class DashboardRowResponse(BaseModel):
    schedule_id: str
    function_name: str
    function_category: str
    frequency: str
    frequency_display: str
    citation_references: List[str]
    monthly_status: Dict[int, DashboardCellResponse]

class FacilityDashboardResponse(BaseModel):
    facility_id: str
    facility_name: str
    year: int
    schedules: List[DashboardRowResponse]

class ComplianceStatisticsResponse(BaseModel):
    total_records: int
    completed_records: int
    completion_rate: float
    overdue_records: int

# Phase 4: Document Management Models
class DocumentUploadResponse(BaseModel):
    success: bool
    errors: List[str]
    document: Optional[Dict[str, Any]] = None

class DocumentStatisticsResponse(BaseModel):
    total_documents: int
    total_size: int
    average_size: float
    type_breakdown: Dict[str, Dict[str, int]]
    category_breakdown: Dict[str, Dict[str, int]]

class BulkUploadResponse(BaseModel):
    total_uploads: int
    success_count: int
    error_count: int
    results: List[Dict[str, Any]]

# Phase 5: Smart Features Models
class TaskAssignmentRequest(BaseModel):
    record_id: str
    assigned_to: str
    notes: Optional[str] = None

class CommentRequest(BaseModel):
    record_id: str
    comment: str
    comment_type: str = "general"

class ReminderEmailResponse(BaseModel):
    notifications_found: int
    emails_sent: int
    errors: int

class ExportRequest(BaseModel):
    facility_id: Optional[str] = None
    format: str = "json"  # json, csv, excel

# Helper functions
def facility_to_dict(facility: ComplianceFacility) -> Dict[str, Any]:
    return {
        "id": facility.id,
        "name": facility.name,
        "address": facility.address,
        "facility_type": facility.facility_type,
        "capacity": facility.capacity,
        "is_active": facility.is_active,
        "created_at": facility.created_at
    }

def function_to_dict(function: ComplianceFunction) -> Dict[str, Any]:
    return {
        "id": function.id,
        "name": function.name,
        "description": function.description,
        "category": function.category,
        "default_frequency": function.default_frequency,
        "citation_references": function.citation_references or [],
        "is_active": function.is_active
    }

def schedule_to_dict(schedule: ComplianceSchedule) -> Dict[str, Any]:
    return {
        "id": schedule.id,
        "facility_id": schedule.facility_id,
        "function_id": schedule.function_id,
        "frequency": schedule.frequency,
        "start_date": schedule.start_date,
        "next_due_date": schedule.next_due_date,
        "assigned_to": schedule.assigned_to,
        "is_active": schedule.is_active
    }

def record_to_dict(record: ComplianceRecord) -> Dict[str, Any]:
    return {
        "id": record.id,
        "schedule_id": record.schedule_id,
        "due_date": record.due_date,
        "completed_date": record.completed_date,
        "status": record.status,
        "completed_by": record.completed_by,
        "notes": record.notes,
        "has_documents": len(record.documents) > 0
    }

def document_to_dict(document: ComplianceDocument) -> Dict[str, Any]:
    return {
        "id": document.id,
        "record_id": document.record_id,
        "filename": document.filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "uploaded_by": document.uploaded_by,
        "uploaded_at": document.uploaded_at
    }

# Create router
def create_compliance_router():
    router = APIRouter()
    
    # Facility endpoints
    @router.get("/facilities", response_model=List[FacilityResponse])
    async def get_facilities(db: Session = Depends(get_db)):
        service = ComplianceService(db)
        facilities = service.get_all_facilities()
        return [facility_to_dict(facility) for facility in facilities]
    
    @router.get("/facilities/{facility_id}", response_model=FacilityResponse)
    async def get_facility(facility_id: str, db: Session = Depends(get_db)):
        service = ComplianceService(db)
        facility = service.get_facility_by_id(facility_id)
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        return facility_to_dict(facility)
    
    # Compliance function endpoints
    @router.get("/functions", response_model=List[ComplianceFunctionResponse])
    async def get_compliance_functions(db: Session = Depends(get_db)):
        service = ComplianceService(db)
        functions = service.get_all_compliance_functions()
        return [function_to_dict(function) for function in functions]
    
    @router.get("/functions/{function_id}", response_model=ComplianceFunctionResponse)
    async def get_compliance_function(function_id: str, db: Session = Depends(get_db)):
        service = ComplianceService(db)
        function = service.get_compliance_function_by_id(function_id)
        if not function:
            raise HTTPException(status_code=404, detail="Compliance function not found")
        return function_to_dict(function)
    
    # Schedule endpoints
    @router.get("/facilities/{facility_id}/schedules", response_model=List[ComplianceScheduleResponse])
    async def get_facility_schedules(facility_id: str, db: Session = Depends(get_db)):
        service = ComplianceService(db)
        schedules = service.get_schedules_by_facility(facility_id)
        return [schedule_to_dict(schedule) for schedule in schedules]
    
    @router.put("/schedules/{schedule_id}/frequency")
    async def update_schedule_frequency(
        schedule_id: str, 
        frequency: str, 
        db: Session = Depends(get_db)
    ):
        service = ComplianceService(db)
        schedule = service.update_schedule_frequency(schedule_id, frequency)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return schedule_to_dict(schedule)
    
    # **NEW PHASE 3: Scheduling System Endpoints**
    @router.post("/scheduling/generate-records", response_model=RecordGenerationResponse)
    async def generate_upcoming_records(
        background_tasks: BackgroundTasks,
        days_ahead: int = 90,
        db: Session = Depends(get_db)
    ):
        """Generate compliance records for upcoming due dates"""
        scheduling_service = ComplianceSchedulingService(db)
        result = scheduling_service.generate_upcoming_records(days_ahead)
        return RecordGenerationResponse(**result)
    
    @router.post("/scheduling/update-overdue")
    async def update_overdue_records(db: Session = Depends(get_db)):
        """Update status of overdue records"""
        scheduling_service = ComplianceSchedulingService(db)
        result = scheduling_service.update_overdue_records()
        return result
    
    @router.get("/scheduling/analytics", response_model=ScheduleAnalyticsResponse)
    async def get_schedule_analytics(
        facility_id: str = None,
        db: Session = Depends(get_db)
    ):
        """Get analytics for scheduling system"""
        scheduling_service = ComplianceSchedulingService(db)
        analytics = scheduling_service.get_schedule_analytics(facility_id)
        return ScheduleAnalyticsResponse(**analytics)
    
    @router.post("/scheduling/bulk-update")
    async def bulk_update_schedules(
        request: BulkScheduleUpdateRequest,
        db: Session = Depends(get_db)
    ):
        """Bulk update multiple schedules"""
        scheduling_service = ComplianceSchedulingService(db)
        updates = [update.dict() for update in request.updates]
        result = scheduling_service.bulk_update_schedules(updates)
        return result
    
    @router.put("/schedules/{schedule_id}/next-due-date")
    async def update_schedule_next_due_date(
        schedule_id: str,
        db: Session = Depends(get_db)
    ):
        """Update the next due date for a schedule"""
        scheduling_service = ComplianceSchedulingService(db)
        success = scheduling_service.update_schedule_next_due_date(schedule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return {"message": "Next due date updated successfully"}
    
    # Record endpoints
    @router.post("/records/{record_id}/complete")
    async def complete_record(
        record_id: str,
        completed_by: str = Form(...),
        notes: str = Form(None),
        db: Session = Depends(get_db)
    ):
        service = ComplianceService(db)
        record = service.complete_compliance_record(record_id, completed_by, notes)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        # Update the schedule's next due date
        scheduling_service = ComplianceSchedulingService(db)
        scheduling_service.update_schedule_next_due_date(record.schedule_id)
        
        return record_to_dict(record)
    
    @router.get("/records/overdue")
    async def get_overdue_records(
        facility_id: str = None,
        db: Session = Depends(get_db)
    ):
        service = ComplianceService(db)
        records = service.get_overdue_records(facility_id)
        return [record_to_dict(record) for record in records]
    
    @router.get("/records/upcoming")
    async def get_upcoming_records(
        days_ahead: int = 30,
        facility_id: str = None,
        db: Session = Depends(get_db)
    ):
        service = ComplianceService(db)
        records = service.get_upcoming_records(days_ahead, facility_id)
        return [record_to_dict(record) for record in records]
    
    # Document endpoints
    @router.post("/records/{record_id}/documents")
    async def upload_document(
        record_id: str,
        file: UploadFile = File(...),
        uploaded_by: str = Form(...),
        description: str = Form(None),
        db: Session = Depends(get_db)
    ):
        doc_service = DocumentManagementService(db)
        
        # Read file content
        file_content = await file.read()
        
        # Upload document with enhanced validation
        result = doc_service.upload_document(
            record_id=record_id,
            filename=file.filename,
            file_content=file_content,
            file_type=file.content_type,
            uploaded_by=uploaded_by,
            description=description
        )
        
        return DocumentUploadResponse(**result)
    
    @router.get("/records/{record_id}/documents")
    async def get_record_documents(record_id: str, db: Session = Depends(get_db)):
        doc_service = DocumentManagementService(db)
        documents = doc_service.get_documents_by_record(record_id)
        return [doc_service._document_to_dict(document) for document in documents]
    
    # **NEW PHASE 4: Enhanced Document Management Endpoints**
    @router.get("/documents/{document_id}")
    async def get_document_details(document_id: str, db: Session = Depends(get_db)):
        """Get detailed information about a document"""
        doc_service = DocumentManagementService(db)
        document = doc_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc_service._document_to_dict(document)
    
    @router.get("/documents/{document_id}/download")
    async def download_document(document_id: str, db: Session = Depends(get_db)):
        """Download a document"""
        doc_service = DocumentManagementService(db)
        result = doc_service.get_document_content(document_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Create streaming response
        content = io.BytesIO(result["content"])
        return StreamingResponse(
            content,
            media_type=result["file_type"],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}",
                "Content-Length": str(result["file_size"])
            }
        )
    
    @router.delete("/documents/{document_id}")
    async def delete_document(
        document_id: str,
        deleted_by: str = Form(...),
        db: Session = Depends(get_db)
    ):
        """Delete a document"""
        doc_service = DocumentManagementService(db)
        result = doc_service.delete_document(document_id, deleted_by)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {"message": result["message"]}
    
    @router.get("/facilities/{facility_id}/documents")
    async def get_facility_documents(facility_id: str, db: Session = Depends(get_db)):
        """Get all documents for a facility"""
        doc_service = DocumentManagementService(db)
        documents = doc_service.get_documents_by_facility(facility_id)
        return documents
    
    @router.get("/documents/statistics")
    async def get_document_statistics(
        facility_id: str = None,
        db: Session = Depends(get_db)
    ):
        """Get document statistics"""
        doc_service = DocumentManagementService(db)
        stats = doc_service.get_document_statistics(facility_id)
        return DocumentStatisticsResponse(**stats)
    
    @router.post("/documents/bulk-upload")
    async def bulk_upload_documents(
        uploads: List[UploadFile] = File(...),
        record_ids: List[str] = Form(...),
        uploaded_by: str = Form(...),
        descriptions: List[str] = Form(None),
        db: Session = Depends(get_db)
    ):
        """Bulk upload multiple documents"""
        doc_service = DocumentManagementService(db)
        
        # Prepare upload data
        upload_data = []
        for i, file in enumerate(uploads):
            file_content = await file.read()
            upload_data.append({
                "record_id": record_ids[i] if i < len(record_ids) else record_ids[0],
                "filename": file.filename,
                "file_content": file_content,
                "file_type": file.content_type,
                "uploaded_by": uploaded_by,
                "description": descriptions[i] if descriptions and i < len(descriptions) else None
            })
        
        result = doc_service.bulk_upload_documents(upload_data)
        return BulkUploadResponse(**result)
    
    @router.post("/documents/validate")
    async def validate_document(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        """Validate a document before upload"""
        doc_service = DocumentManagementService(db)
        file_content = await file.read()
        
        validation = doc_service.validate_file(file.filename, file_content, file.content_type)
        return validation
    
    # Dashboard endpoints
    @router.get("/facilities/{facility_id}/dashboard", response_model=FacilityDashboardResponse)
    async def get_facility_dashboard(
        facility_id: str,
        year: int = None,
        db: Session = Depends(get_db)
    ):
        service = ComplianceService(db)
        
        # Get facility info
        facility = service.get_facility_by_id(facility_id)
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        
        # Get dashboard data
        dashboard_data = service.get_facility_dashboard_data(facility_id, year)
        
        # Format for response
        dashboard_rows = []
        for schedule_data in dashboard_data["schedules"]:
            schedule = schedule_data["schedule"]
            function = schedule_data["function"]
            monthly_status = schedule_data["monthly_status"]
            
            # Convert monthly status to response format
            monthly_status_response = {}
            for month, status_data in monthly_status.items():
                monthly_status_response[month] = DashboardCellResponse(
                    status=status_data["status"],
                    due_date=status_data["due_date"],
                    completed_date=status_data["completed_date"],
                    has_documents=status_data["has_documents"]
                )
            
            dashboard_rows.append(DashboardRowResponse(
                schedule_id=schedule.id,
                function_name=function.name,
                function_category=function.category,
                frequency=schedule.frequency,
                frequency_display=get_frequency_display(schedule.frequency),
                citation_references=function.citation_references or [],
                monthly_status=monthly_status_response
            ))
        
        return FacilityDashboardResponse(
            facility_id=facility_id,
            facility_name=facility.name,
            year=dashboard_data["year"],
            schedules=dashboard_rows
        )
    
    # Statistics endpoints
    @router.get("/statistics", response_model=ComplianceStatisticsResponse)
    async def get_compliance_statistics(
        facility_id: str = None,
        db: Session = Depends(get_db)
    ):
        service = ComplianceService(db)
        stats = service.get_compliance_statistics(facility_id)
        return ComplianceStatisticsResponse(**stats)
    
    # **NEW PHASE 5: Smart Features Endpoints**
    @router.post("/tasks/assign")
    async def assign_task(
        record_id: str = Form(...),
        assigned_to: str = Form(...),
        assigned_by: str = Form(...),
        notes: str = Form(None),
        db: Session = Depends(get_db)
    ):
        """Assign a compliance task to a user"""
        smart_service = SmartFeaturesService(db)
        result = smart_service.assign_task(
            record_id=record_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            notes=notes
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    
    @router.get("/tasks/assignments")
    async def get_task_assignments(
        facility_id: str = None,
        assigned_to: str = None,
        db: Session = Depends(get_db)
    ):
        """Get task assignments with filtering"""
        smart_service = SmartFeaturesService(db)
        assignments = smart_service.get_task_assignments(facility_id, assigned_to)
        return assignments
    
    @router.post("/comments")
    async def add_comment(
        record_id: str = Form(...),
        comment: str = Form(...),
        user: str = Form(...),
        comment_type: str = Form("general"),
        db: Session = Depends(get_db)
    ):
        """Add a comment to a compliance record"""
        smart_service = SmartFeaturesService(db)
        result = smart_service.add_comment(
            record_id=record_id,
            comment=comment,
            user=user,
            comment_type=comment_type
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    
    @router.get("/records/{record_id}/comments")
    async def get_comments(record_id: str, db: Session = Depends(get_db)):
        """Get all comments for a record"""
        smart_service = SmartFeaturesService(db)
        comments = smart_service.get_comments(record_id)
        return comments
    
    @router.get("/notifications/overdue")
    async def get_overdue_notifications(
        days_ahead: int = 7,
        db: Session = Depends(get_db)
    ):
        """Get overdue and upcoming task notifications"""
        smart_service = SmartFeaturesService(db)
        notifications = smart_service.get_overdue_notifications(days_ahead)
        return notifications
    
    @router.post("/notifications/send-reminders")
    async def send_reminder_emails(
        background_tasks: BackgroundTasks,
        days_ahead: int = 7,
        db: Session = Depends(get_db)
    ):
        """Send reminder emails for upcoming and overdue tasks"""
        smart_service = SmartFeaturesService(db)
        result = smart_service.send_reminder_emails(days_ahead)
        return ReminderEmailResponse(**result)
    
    @router.get("/activity-feed")
    async def get_activity_feed(
        facility_id: str = None,
        limit: int = 50,
        db: Session = Depends(get_db)
    ):
        """Get recent activity feed"""
        smart_service = SmartFeaturesService(db)
        feed = smart_service.get_activity_feed(facility_id, limit)
        return feed
    
    @router.post("/export")
    async def export_compliance_data(
        request: ExportRequest,
        db: Session = Depends(get_db)
    ):
        """Export compliance data in various formats"""
        smart_service = SmartFeaturesService(db)
        result = smart_service.export_compliance_data(request.facility_id, request.format)
        
        if not result.get("success", True):
            raise HTTPException(status_code=400, detail=result.get("error", "Export failed"))
        
        return result
    
    return router

# Export for use in main server
compliance_router = create_compliance_router()