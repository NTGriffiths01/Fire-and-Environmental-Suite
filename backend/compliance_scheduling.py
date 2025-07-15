from sqlalchemy.orm import Session
from compliance_models import (
    ComplianceSchedule, ComplianceRecord, calculate_next_due_date
)
from compliance_service import ComplianceService
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

class ComplianceSchedulingService:
    def __init__(self, db: Session):
        self.db = db
        self.compliance_service = ComplianceService(db)
    
    def generate_upcoming_records(self, days_ahead: int = 90) -> Dict[str, Any]:
        """Generate compliance records for upcoming due dates"""
        logger.info(f"Generating upcoming records for next {days_ahead} days")
        
        # Get all active schedules
        schedules = self.db.query(ComplianceSchedule).filter(
            ComplianceSchedule.is_active == True
        ).all()
        
        records_generated = 0
        records_updated = 0
        future_date = date.today() + timedelta(days=days_ahead)
        
        for schedule in schedules:
            # Calculate due dates for this schedule
            due_dates = self._calculate_due_dates_for_schedule(schedule, future_date)
            
            for due_date in due_dates:
                # Check if record already exists
                existing_record = self.db.query(ComplianceRecord).filter(
                    ComplianceRecord.schedule_id == schedule.id,
                    ComplianceRecord.due_date == due_date
                ).first()
                
                if not existing_record:
                    # Create new record
                    record = ComplianceRecord(
                        id=str(uuid.uuid4()),
                        schedule_id=schedule.id,
                        due_date=due_date,
                        status="pending"
                    )
                    self.db.add(record)
                    records_generated += 1
                else:
                    # Update existing record status if needed
                    if existing_record.status == "pending" and due_date < date.today():
                        existing_record.status = "overdue"
                        records_updated += 1
        
        self.db.commit()
        
        result = {
            "records_generated": records_generated,
            "records_updated": records_updated,
            "total_schedules_processed": len(schedules)
        }
        
        logger.info(f"Record generation complete: {result}")
        return result
    
    def _calculate_due_dates_for_schedule(self, schedule: ComplianceSchedule, end_date: date) -> List[date]:
        """Calculate all due dates for a schedule up to end_date"""
        due_dates = []
        current_date = schedule.start_date or date.today()
        
        # Start from next due date if available
        if schedule.next_due_date and schedule.next_due_date >= date.today():
            current_date = schedule.next_due_date
        
        # Generate due dates based on frequency
        while current_date <= end_date:
            due_dates.append(current_date)
            current_date = calculate_next_due_date(current_date, schedule.frequency)
            
            # Safety check to prevent infinite loops
            if len(due_dates) > 100:
                logger.warning(f"Too many due dates generated for schedule {schedule.id}")
                break
        
        return due_dates
    
    def update_overdue_records(self) -> Dict[str, Any]:
        """Update status of overdue records"""
        logger.info("Updating overdue records")
        
        overdue_records = self.db.query(ComplianceRecord).filter(
            ComplianceRecord.due_date < date.today(),
            ComplianceRecord.status == "pending"
        ).all()
        
        updated_count = 0
        for record in overdue_records:
            record.status = "overdue"
            record.updated_at = datetime.utcnow()
            updated_count += 1
        
        self.db.commit()
        
        result = {
            "overdue_records_updated": updated_count
        }
        
        logger.info(f"Overdue update complete: {result}")
        return result
    
    def update_schedule_next_due_date(self, schedule_id: str) -> bool:
        """Update the next due date for a schedule"""
        schedule = self.db.query(ComplianceSchedule).filter(ComplianceSchedule.id == schedule_id).first()
        if not schedule:
            return False
        
        # Find the most recent completed record
        last_completed = self.db.query(ComplianceRecord).filter(
            ComplianceRecord.schedule_id == schedule_id,
            ComplianceRecord.status == "completed"
        ).order_by(ComplianceRecord.completed_date.desc()).first()
        
        if last_completed:
            # Calculate next due date from last completion
            schedule.next_due_date = calculate_next_due_date(last_completed.completed_date, schedule.frequency)
        else:
            # Calculate from start date
            schedule.next_due_date = calculate_next_due_date(schedule.start_date or date.today(), schedule.frequency)
        
        schedule.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Updated next due date for schedule {schedule_id}: {schedule.next_due_date}")
        return True
    
    def get_schedule_analytics(self, facility_id: str = None) -> Dict[str, Any]:
        """Get analytics for scheduling system"""
        base_query = self.db.query(ComplianceSchedule)
        
        if facility_id:
            base_query = base_query.filter(ComplianceSchedule.facility_id == facility_id)
        
        schedules = base_query.all()
        
        # Calculate analytics
        total_schedules = len(schedules)
        frequency_breakdown = {}
        upcoming_due_dates = []
        
        for schedule in schedules:
            # Count by frequency
            freq = schedule.frequency
            frequency_breakdown[freq] = frequency_breakdown.get(freq, 0) + 1
            
            # Collect upcoming due dates
            if schedule.next_due_date:
                days_until_due = (schedule.next_due_date - date.today()).days
                if days_until_due >= 0:
                    upcoming_due_dates.append({
                        "schedule_id": schedule.id,
                        "facility_id": schedule.facility_id,
                        "function_id": schedule.function_id,
                        "next_due_date": schedule.next_due_date,
                        "days_until_due": days_until_due
                    })
        
        # Sort upcoming due dates
        upcoming_due_dates.sort(key=lambda x: x["days_until_due"])
        
        return {
            "total_schedules": total_schedules,
            "frequency_breakdown": frequency_breakdown,
            "upcoming_due_dates": upcoming_due_dates[:20],  # Top 20 upcoming
            "generated_at": datetime.utcnow()
        }
    
    def bulk_update_schedules(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update multiple schedules"""
        updated_count = 0
        error_count = 0
        errors = []
        
        for update in updates:
            try:
                schedule_id = update.get("schedule_id")
                schedule = self.db.query(ComplianceSchedule).filter(ComplianceSchedule.id == schedule_id).first()
                
                if schedule:
                    # Update frequency if provided
                    if "frequency" in update:
                        schedule.frequency = update["frequency"]
                        schedule.next_due_date = calculate_next_due_date(
                            schedule.start_date or date.today(), 
                            schedule.frequency
                        )
                    
                    # Update assigned_to if provided
                    if "assigned_to" in update:
                        schedule.assigned_to = update["assigned_to"]
                    
                    # Update start_date if provided
                    if "start_date" in update:
                        schedule.start_date = update["start_date"]
                        schedule.next_due_date = calculate_next_due_date(
                            schedule.start_date, 
                            schedule.frequency
                        )
                    
                    schedule.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    errors.append(f"Schedule {schedule_id} not found")
                    error_count += 1
                    
            except Exception as e:
                errors.append(f"Error updating schedule {update.get('schedule_id', 'unknown')}: {str(e)}")
                error_count += 1
        
        self.db.commit()
        
        return {
            "updated_count": updated_count,
            "error_count": error_count,
            "errors": errors
        }