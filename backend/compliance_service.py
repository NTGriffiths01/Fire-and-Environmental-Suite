from sqlalchemy.orm import Session
from compliance_models import (
    ComplianceFacility, ComplianceFunction, ComplianceSchedule, 
    ComplianceRecord, ComplianceDocument, calculate_next_due_date
)
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date, timedelta
import base64

class ComplianceService:
    def __init__(self, db: Session):
        self.db = db
    
    # Facility operations
    def create_facility(self, name: str, address: str = None, facility_type: str = None, capacity: int = None) -> ComplianceFacility:
        """Create a new facility"""
        facility = ComplianceFacility(
            id=str(uuid.uuid4()),
            name=name,
            address=address,
            facility_type=facility_type,
            capacity=capacity
        )
        self.db.add(facility)
        self.db.commit()
        self.db.refresh(facility)
        return facility
    
    def get_all_facilities(self) -> List[ComplianceFacility]:
        """Get all active facilities"""
        return self.db.query(ComplianceFacility).filter(ComplianceFacility.is_active == True).all()
    
    def get_facility_by_id(self, facility_id: str) -> Optional[ComplianceFacility]:
        """Get facility by ID"""
        return self.db.query(ComplianceFacility).filter(ComplianceFacility.id == facility_id).first()
    
    # Compliance function operations
    def create_compliance_function(self, name: str, description: str = None, category: str = None, 
                                 default_frequency: str = "M", citation_references: List[str] = None) -> ComplianceFunction:
        """Create a new compliance function"""
        function = ComplianceFunction(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            category=category,
            default_frequency=default_frequency,
            citation_references=citation_references or []
        )
        self.db.add(function)
        self.db.commit()
        self.db.refresh(function)
        return function
    
    def get_all_compliance_functions(self) -> List[ComplianceFunction]:
        """Get all active compliance functions"""
        return self.db.query(ComplianceFunction).filter(ComplianceFunction.is_active == True).all()
    
    def get_compliance_function_by_id(self, function_id: str) -> Optional[ComplianceFunction]:
        """Get compliance function by ID"""
        return self.db.query(ComplianceFunction).filter(ComplianceFunction.id == function_id).first()
    
    # Compliance schedule operations
    def create_compliance_schedule(self, facility_id: str, function_id: str, frequency: str, 
                                 start_date: date = None, assigned_to: str = None) -> ComplianceSchedule:
        """Create a new compliance schedule"""
        if start_date is None:
            start_date = date.today()
        
        next_due_date = calculate_next_due_date(start_date, frequency)
        
        schedule = ComplianceSchedule(
            id=str(uuid.uuid4()),
            facility_id=facility_id,
            function_id=function_id,
            frequency=frequency,
            start_date=start_date,
            next_due_date=next_due_date,
            assigned_to=assigned_to
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule
    
    def get_schedules_by_facility(self, facility_id: str) -> List[ComplianceSchedule]:
        """Get all schedules for a facility"""
        return self.db.query(ComplianceSchedule).filter(
            ComplianceSchedule.facility_id == facility_id,
            ComplianceSchedule.is_active == True
        ).all()
    
    def update_schedule_frequency(self, schedule_id: str, frequency: str) -> Optional[ComplianceSchedule]:
        """Update schedule frequency"""
        schedule = self.db.query(ComplianceSchedule).filter(ComplianceSchedule.id == schedule_id).first()
        if schedule:
            schedule.frequency = frequency
            schedule.next_due_date = calculate_next_due_date(schedule.start_date, frequency)
            schedule.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(schedule)
        return schedule
    
    # Compliance record operations
    def create_compliance_record(self, schedule_id: str, due_date: date) -> ComplianceRecord:
        """Create a new compliance record"""
        record = ComplianceRecord(
            id=str(uuid.uuid4()),
            schedule_id=schedule_id,
            due_date=due_date,
            status="pending"
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def complete_compliance_record(self, record_id: str, completed_by: str, notes: str = None) -> Optional[ComplianceRecord]:
        """Mark a compliance record as completed"""
        record = self.db.query(ComplianceRecord).filter(ComplianceRecord.id == record_id).first()
        if record:
            record.completed_date = date.today()
            record.status = "completed"
            record.completed_by = completed_by
            if notes:
                record.notes = notes
            record.updated_at = datetime.utcnow()
            
            # Update the schedule's next due date
            schedule = record.schedule
            if schedule:
                schedule.next_due_date = calculate_next_due_date(record.completed_date, schedule.frequency)
                schedule.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(record)
        return record
    
    def get_records_by_schedule(self, schedule_id: str) -> List[ComplianceRecord]:
        """Get all records for a schedule"""
        return self.db.query(ComplianceRecord).filter(ComplianceRecord.schedule_id == schedule_id).all()
    
    def get_overdue_records(self, facility_id: str = None) -> List[ComplianceRecord]:
        """Get overdue records"""
        query = self.db.query(ComplianceRecord).filter(
            ComplianceRecord.due_date < date.today(),
            ComplianceRecord.status == "pending"
        )
        
        if facility_id:
            query = query.join(ComplianceSchedule).filter(ComplianceSchedule.facility_id == facility_id)
        
        return query.all()
    
    def get_upcoming_records(self, days_ahead: int = 30, facility_id: str = None) -> List[ComplianceRecord]:
        """Get upcoming records within specified days"""
        future_date = date.today() + timedelta(days=days_ahead)
        
        query = self.db.query(ComplianceRecord).filter(
            ComplianceRecord.due_date <= future_date,
            ComplianceRecord.due_date >= date.today(),
            ComplianceRecord.status == "pending"
        )
        
        if facility_id:
            query = query.join(ComplianceSchedule).filter(ComplianceSchedule.facility_id == facility_id)
        
        return query.all()
    
    # Document operations
    def upload_document(self, record_id: str, filename: str, file_content: bytes, 
                       file_type: str, uploaded_by: str) -> ComplianceDocument:
        """Upload a document for a compliance record"""
        base64_content = base64.b64encode(file_content).decode('utf-8')
        
        document = ComplianceDocument(
            id=str(uuid.uuid4()),
            record_id=record_id,
            filename=filename,
            file_type=file_type,
            file_size=len(file_content),
            base64_content=base64_content,
            uploaded_by=uploaded_by
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def get_documents_by_record(self, record_id: str) -> List[ComplianceDocument]:
        """Get all documents for a record"""
        return self.db.query(ComplianceDocument).filter(ComplianceDocument.record_id == record_id).all()
    
    # Dashboard operations
    def get_facility_dashboard_data(self, facility_id: str, year: int = None) -> Dict[str, Any]:
        """Get dashboard data for a facility"""
        if year is None:
            year = date.today().year
        
        schedules = self.get_schedules_by_facility(facility_id)
        dashboard_data = []
        
        for schedule in schedules:
            # Get records for this year
            records = self.db.query(ComplianceRecord).filter(
                ComplianceRecord.schedule_id == schedule.id,
                ComplianceRecord.due_date.between(date(year, 1, 1), date(year, 12, 31))
            ).all()
            
            # Create monthly status array
            monthly_status = {}
            for month in range(1, 13):
                monthly_status[month] = {
                    "status": "pending",
                    "due_date": None,
                    "completed_date": None,
                    "has_documents": False
                }
            
            # Fill in actual data
            for record in records:
                month = record.due_date.month
                monthly_status[month] = {
                    "status": record.status,
                    "due_date": record.due_date,
                    "completed_date": record.completed_date,
                    "has_documents": len(record.documents) > 0
                }
            
            dashboard_data.append({
                "schedule": schedule,
                "function": schedule.function,
                "monthly_status": monthly_status
            })
        
        return {
            "facility_id": facility_id,
            "year": year,
            "schedules": dashboard_data
        }
    
    def get_compliance_statistics(self, facility_id: str = None) -> Dict[str, Any]:
        """Get compliance statistics"""
        base_query = self.db.query(ComplianceRecord)
        
        if facility_id:
            base_query = base_query.join(ComplianceSchedule).filter(ComplianceSchedule.facility_id == facility_id)
        
        total_records = base_query.count()
        completed_records = base_query.filter(ComplianceRecord.status == "completed").count()
        overdue_records = base_query.filter(
            ComplianceRecord.due_date < date.today(),
            ComplianceRecord.status == "pending"
        ).count()
        
        return {
            "total_records": total_records,
            "completed_records": completed_records,
            "completion_rate": (completed_records / total_records * 100) if total_records > 0 else 0,
            "overdue_records": overdue_records
        }