from sqlalchemy.orm import Session
from models import User, Template, Inspection, CorrectiveAction, AuditLog, get_db, RoleEnum, StatusEnum
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db
    
    # User operations
    def create_user(self, username: str, role: str, password: str = None) -> User:
        """Create a new user"""
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            role=role
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        return self.db.query(User).all()
    
    # Template operations
    def create_template(self, name: str, schema: Dict[str, Any], created_by: str) -> Template:
        """Create a new template"""
        template = Template(
            id=str(uuid.uuid4()),
            name=name,
            schema=schema,
            created_by=created_by
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def get_template_by_id(self, template_id: str) -> Optional[Template]:
        """Get template by ID"""
        return self.db.query(Template).filter(Template.id == template_id).first()
    
    def get_all_templates(self) -> List[Template]:
        """Get all templates"""
        return self.db.query(Template).all()
    
    # Inspection operations
    def create_inspection(self, template_id: str, facility: str, payload: Dict[str, Any], inspector_id: str) -> Inspection:
        """Create a new inspection"""
        inspection = Inspection(
            id=str(uuid.uuid4()),
            template_id=template_id,
            facility=facility,
            payload=payload,
            inspector_id=inspector_id,
            status="draft"
        )
        self.db.add(inspection)
        self.db.commit()
        self.db.refresh(inspection)
        return inspection
    
    def get_inspection_by_id(self, inspection_id: str) -> Optional[Inspection]:
        """Get inspection by ID"""
        return self.db.query(Inspection).filter(Inspection.id == inspection_id).first()
    
    def get_inspections_by_inspector(self, inspector_id: str) -> List[Inspection]:
        """Get all inspections by inspector"""
        return self.db.query(Inspection).filter(Inspection.inspector_id == inspector_id).all()
    
    def get_all_inspections(self) -> List[Inspection]:
        """Get all inspections"""
        return self.db.query(Inspection).all()
    
    def update_inspection_status(self, inspection_id: str, status: str, deputy_id: str = None) -> Optional[Inspection]:
        """Update inspection status"""
        inspection = self.db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if inspection:
            inspection.status = status
            if deputy_id:
                inspection.deputy_id = deputy_id
            inspection.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(inspection)
        return inspection
    
    def update_inspection_payload(self, inspection_id: str, payload: Dict[str, Any]) -> Optional[Inspection]:
        """Update inspection payload"""
        inspection = self.db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if inspection:
            inspection.payload = payload
            inspection.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(inspection)
        return inspection
    
    # Corrective Action operations
    def create_corrective_action(self, inspection_id: str, violation_ref: str, action_plan: str, due_date: date) -> CorrectiveAction:
        """Create a corrective action"""
        action = CorrectiveAction(
            id=str(uuid.uuid4()),
            inspection_id=inspection_id,
            violation_ref=violation_ref,
            action_plan=action_plan,
            due_date=due_date
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action
    
    def get_corrective_actions_by_inspection(self, inspection_id: str) -> List[CorrectiveAction]:
        """Get corrective actions for an inspection"""
        return self.db.query(CorrectiveAction).filter(CorrectiveAction.inspection_id == inspection_id).all()
    
    def complete_corrective_action(self, action_id: str) -> Optional[CorrectiveAction]:
        """Mark corrective action as completed"""
        action = self.db.query(CorrectiveAction).filter(CorrectiveAction.id == action_id).first()
        if action:
            action.completed = True
            action.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(action)
        return action
    
    # Audit Log operations
    def create_audit_log(self, username: str, action: str, ip_addr: str) -> AuditLog:
        """Create an audit log entry"""
        log = AuditLog(
            username=username,
            action=action,
            ip_addr=ip_addr
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        """Get audit logs"""
        return self.db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    # Statistics operations
    def get_statistics(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        total_users = self.db.query(User).count()
        total_templates = self.db.query(Template).count()
        total_inspections = self.db.query(Inspection).count()
        pending_reviews = self.db.query(Inspection).filter(Inspection.status == "submitted").count()
        
        return {
            "total_users": total_users,
            "total_templates": total_templates,
            "total_inspections": total_inspections,
            "pending_reviews": pending_reviews
        }
    
    def get_inspector_statistics(self, inspector_id: str) -> Dict[str, Any]:
        """Get inspector-specific statistics"""
        inspections = self.db.query(Inspection).filter(Inspection.inspector_id == inspector_id)
        
        return {
            "my_inspections": inspections.count(),
            "draft_inspections": inspections.filter(Inspection.status == "draft").count(),
            "submitted_inspections": inspections.filter(Inspection.status == "submitted").count(),
            "completed_inspections": inspections.filter(Inspection.status == "completed").count()
        }
    
    def get_deputy_statistics(self) -> Dict[str, Any]:
        """Get deputy-specific statistics"""
        inspections = self.db.query(Inspection)
        
        return {
            "pending_reviews": inspections.filter(Inspection.status == "submitted").count(),
            "completed_inspections": inspections.filter(Inspection.status == "completed").count(),
            "total_inspections": inspections.count()
        }