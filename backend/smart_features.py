from sqlalchemy.orm import Session
from compliance_models import ComplianceRecord, ComplianceSchedule, ComplianceFacility, ComplianceFunction
from typing import List, Dict, Any, Optional
import uuid
import json
from datetime import datetime, date, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

class SmartFeaturesService:
    def __init__(self, db: Session):
        self.db = db
    
    def assign_task(self, record_id: str, assigned_to: str, assigned_by: str, notes: str = None) -> Dict[str, Any]:
        """Assign a compliance task to a user"""
        try:
            # Get the record
            record = self.db.query(ComplianceRecord).filter(ComplianceRecord.id == record_id).first()
            if not record:
                return {"success": False, "error": "Record not found"}
            
            # Update the schedule with assignment
            schedule = record.schedule
            if schedule:
                schedule.assigned_to = assigned_to
                schedule.updated_at = datetime.utcnow()
            
            # Log the assignment
            self._log_activity(
                record_id=record_id,
                action="task_assigned",
                user=assigned_by,
                details={
                    "assigned_to": assigned_to,
                    "notes": notes
                }
            )
            
            self.db.commit()
            
            # Send notification email
            self._send_assignment_notification(record, assigned_to, assigned_by, notes)
            
            return {
                "success": True,
                "message": "Task assigned successfully",
                "assigned_to": assigned_to
            }
            
        except Exception as e:
            logger.error(f"Error assigning task: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def add_comment(self, record_id: str, comment: str, user: str, comment_type: str = "general") -> Dict[str, Any]:
        """Add a comment to a compliance record"""
        try:
            # Verify record exists
            record = self.db.query(ComplianceRecord).filter(ComplianceRecord.id == record_id).first()
            if not record:
                return {"success": False, "error": "Record not found"}
            
            # Create comment entry
            comment_data = {
                "id": str(uuid.uuid4()),
                "comment": comment,
                "user": user,
                "timestamp": datetime.utcnow().isoformat(),
                "type": comment_type
            }
            
            # Update record notes with comment thread
            if record.notes:
                try:
                    notes_data = json.loads(record.notes)
                    if not isinstance(notes_data, dict):
                        notes_data = {"comments": []}
                except:
                    notes_data = {"comments": []}
            else:
                notes_data = {"comments": []}
            
            if "comments" not in notes_data:
                notes_data["comments"] = []
            
            notes_data["comments"].append(comment_data)
            
            # Keep only last 50 comments
            if len(notes_data["comments"]) > 50:
                notes_data["comments"] = notes_data["comments"][-50:]
            
            record.notes = json.dumps(notes_data)
            record.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return {
                "success": True,
                "message": "Comment added successfully",
                "comment_id": comment_data["id"]
            }
            
        except Exception as e:
            logger.error(f"Error adding comment: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_comments(self, record_id: str) -> List[Dict[str, Any]]:
        """Get all comments for a record"""
        try:
            record = self.db.query(ComplianceRecord).filter(ComplianceRecord.id == record_id).first()
            if not record or not record.notes:
                return []
            
            notes_data = json.loads(record.notes)
            return notes_data.get("comments", [])
            
        except Exception as e:
            logger.error(f"Error getting comments: {str(e)}")
            return []
    
    def get_overdue_notifications(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get tasks that will be overdue soon or are already overdue"""
        try:
            # Get overdue records
            overdue_date = date.today()
            upcoming_date = date.today() + timedelta(days=days_ahead)
            
            records = self.db.query(ComplianceRecord).filter(
                ComplianceRecord.due_date <= upcoming_date,
                ComplianceRecord.status == "pending"
            ).all()
            
            notifications = []
            for record in records:
                schedule = record.schedule
                facility = schedule.facility if schedule else None
                function = schedule.function if schedule else None
                
                # Calculate urgency
                days_until_due = (record.due_date - date.today()).days
                urgency = "overdue" if days_until_due < 0 else "urgent" if days_until_due <= 3 else "upcoming"
                
                notifications.append({
                    "record_id": record.id,
                    "due_date": record.due_date,
                    "days_until_due": days_until_due,
                    "urgency": urgency,
                    "facility_name": facility.name if facility else "Unknown",
                    "function_name": function.name if function else "Unknown",
                    "assigned_to": schedule.assigned_to if schedule else None,
                    "status": record.status
                })
            
            # Sort by urgency and due date
            notifications.sort(key=lambda x: (x["days_until_due"], x["urgency"]))
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting overdue notifications: {str(e)}")
            return []
    
    def send_reminder_emails(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Send reminder emails for upcoming and overdue tasks"""
        try:
            notifications = self.get_overdue_notifications(days_ahead)
            
            # Group notifications by assigned user
            user_notifications = {}
            for notification in notifications:
                assigned_to = notification["assigned_to"]
                if assigned_to:
                    if assigned_to not in user_notifications:
                        user_notifications[assigned_to] = []
                    user_notifications[assigned_to].append(notification)
            
            sent_count = 0
            error_count = 0
            
            for user, user_tasks in user_notifications.items():
                try:
                    self._send_reminder_email(user, user_tasks)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending email to {user}: {str(e)}")
                    error_count += 1
            
            return {
                "notifications_found": len(notifications),
                "emails_sent": sent_count,
                "errors": error_count
            }
            
        except Exception as e:
            logger.error(f"Error sending reminder emails: {str(e)}")
            return {"error": str(e)}
    
    def export_compliance_data(self, facility_id: str = None, format: str = "json") -> Dict[str, Any]:
        """Export compliance data in various formats"""
        try:
            # Get compliance data
            query = self.db.query(ComplianceRecord)
            if facility_id:
                query = query.join(ComplianceSchedule).filter(ComplianceSchedule.facility_id == facility_id)
            
            records = query.all()
            
            # Format data for export
            export_data = []
            for record in records:
                schedule = record.schedule
                facility = schedule.facility if schedule else None
                function = schedule.function if schedule else None
                
                export_data.append({
                    "record_id": record.id,
                    "facility_name": facility.name if facility else "",
                    "function_name": function.name if function else "",
                    "function_category": function.category if function else "",
                    "frequency": schedule.frequency if schedule else "",
                    "due_date": record.due_date.isoformat() if record.due_date else "",
                    "completed_date": record.completed_date.isoformat() if record.completed_date else "",
                    "status": record.status,
                    "assigned_to": schedule.assigned_to if schedule else "",
                    "notes": record.notes or "",
                    "has_documents": len(record.documents) > 0
                })
            
            if format == "csv":
                return self._export_to_csv(export_data)
            elif format == "excel":
                return self._export_to_excel(export_data)
            else:  # json
                return {
                    "success": True,
                    "format": "json",
                    "data": export_data,
                    "total_records": len(export_data)
                }
                
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _log_activity(self, record_id: str, action: str, user: str, details: Dict[str, Any] = None):
        """Log activity for audit trail"""
        try:
            # This would typically go to a separate audit log table
            # For now, we'll just log it
            logger.info(f"Activity: {action} by {user} on record {record_id} - {details}")
        except Exception as e:
            logger.error(f"Error logging activity: {str(e)}")
    
    def _send_assignment_notification(self, record: ComplianceRecord, assigned_to: str, assigned_by: str, notes: str = None):
        """Send email notification for task assignment"""
        try:
            # This would use the email service from the main app
            # For now, we'll just log it
            logger.info(f"Assignment notification: Task {record.id} assigned to {assigned_to} by {assigned_by}")
        except Exception as e:
            logger.error(f"Error sending assignment notification: {str(e)}")
    
    def _send_reminder_email(self, user: str, tasks: List[Dict[str, Any]]):
        """Send reminder email to user"""
        try:
            # This would use the email service from the main app
            # For now, we'll just log it
            logger.info(f"Reminder email to {user} for {len(tasks)} tasks")
        except Exception as e:
            logger.error(f"Error sending reminder email: {str(e)}")
    
    def _export_to_csv(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export data to CSV format"""
        try:
            import csv
            import io
            
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            return {
                "success": True,
                "format": "csv",
                "content": output.getvalue(),
                "total_records": len(data)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _export_to_excel(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export data to Excel format"""
        try:
            # This would require openpyxl or similar library
            # For now, return CSV format
            return self._export_to_csv(data)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_task_assignments(self, facility_id: str = None, assigned_to: str = None) -> List[Dict[str, Any]]:
        """Get task assignments with filtering"""
        try:
            query = self.db.query(ComplianceSchedule).filter(ComplianceSchedule.assigned_to.isnot(None))
            
            if facility_id:
                query = query.filter(ComplianceSchedule.facility_id == facility_id)
            if assigned_to:
                query = query.filter(ComplianceSchedule.assigned_to == assigned_to)
            
            schedules = query.all()
            
            assignments = []
            for schedule in schedules:
                # Get current pending record
                current_record = self.db.query(ComplianceRecord).filter(
                    ComplianceRecord.schedule_id == schedule.id,
                    ComplianceRecord.status == "pending"
                ).first()
                
                if current_record:
                    assignments.append({
                        "schedule_id": schedule.id,
                        "record_id": current_record.id,
                        "facility_name": schedule.facility.name,
                        "function_name": schedule.function.name,
                        "assigned_to": schedule.assigned_to,
                        "due_date": current_record.due_date,
                        "status": current_record.status,
                        "frequency": schedule.frequency,
                        "next_due_date": schedule.next_due_date
                    })
            
            return assignments
            
        except Exception as e:
            logger.error(f"Error getting task assignments: {str(e)}")
            return []
    
    def get_activity_feed(self, facility_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity feed"""
        try:
            # Get recent records with activity
            query = self.db.query(ComplianceRecord).order_by(ComplianceRecord.updated_at.desc()).limit(limit)
            
            if facility_id:
                query = query.join(ComplianceSchedule).filter(ComplianceSchedule.facility_id == facility_id)
            
            records = query.all()
            
            activity_feed = []
            for record in records:
                schedule = record.schedule
                facility = schedule.facility if schedule else None
                function = schedule.function if schedule else None
                
                activity_feed.append({
                    "record_id": record.id,
                    "facility_name": facility.name if facility else "",
                    "function_name": function.name if function else "",
                    "status": record.status,
                    "completed_by": record.completed_by,
                    "updated_at": record.updated_at,
                    "activity_type": "completed" if record.status == "completed" else "updated"
                })
            
            return activity_feed
            
        except Exception as e:
            logger.error(f"Error getting activity feed: {str(e)}")
            return []