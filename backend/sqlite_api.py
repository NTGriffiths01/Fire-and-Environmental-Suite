from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json
from database_service import DatabaseService
from models import get_db, User, Template, Inspection, CorrectiveAction
from sqlalchemy.orm import Session

# Pydantic models for API
class UserCreate(BaseModel):
    username: str
    role: str

class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    created_at: datetime

class TemplateCreate(BaseModel):
    name: str
    schema: Dict[str, Any]

class TemplateResponse(BaseModel):
    id: str
    name: str
    schema: Dict[str, Any]
    created_by: str
    created_at: datetime

class InspectionCreate(BaseModel):
    template_id: str
    facility: str
    payload: Dict[str, Any]

class InspectionResponse(BaseModel):
    id: str
    template_id: str
    facility: str
    payload: Dict[str, Any]
    status: str
    inspector_id: str
    deputy_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CorrectiveActionCreate(BaseModel):
    inspection_id: str
    violation_ref: str
    action_plan: str
    due_date: date

class CorrectiveActionResponse(BaseModel):
    id: str
    inspection_id: str
    violation_ref: str
    action_plan: str
    due_date: date
    completed: bool
    completed_at: Optional[datetime] = None

# Helper functions to convert SQLAlchemy objects to Pydantic models
def user_to_dict(user: User) -> Dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "created_at": user.created_at
    }

def template_to_dict(template: Template) -> Dict[str, Any]:
    return {
        "id": template.id,
        "name": template.name,
        "schema": template.schema,
        "created_by": template.created_by,
        "created_at": template.created_at
    }

def inspection_to_dict(inspection: Inspection) -> Dict[str, Any]:
    return {
        "id": inspection.id,
        "template_id": inspection.template_id,
        "facility": inspection.facility,
        "payload": inspection.payload,
        "status": inspection.status,
        "inspector_id": inspection.inspector_id,
        "deputy_id": inspection.deputy_id,
        "created_at": inspection.created_at,
        "updated_at": inspection.updated_at
    }

def corrective_action_to_dict(action: CorrectiveAction) -> Dict[str, Any]:
    return {
        "id": action.id,
        "inspection_id": action.inspection_id,
        "violation_ref": action.violation_ref,
        "action_plan": action.action_plan,
        "due_date": action.due_date,
        "completed": action.completed,
        "completed_at": action.completed_at
    }

# Create FastAPI router for SQLite endpoints
def create_sqlite_router():
    from fastapi import APIRouter
    router = APIRouter()
    
    # Users endpoints
    @router.post("/users", response_model=UserResponse)
    async def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
        service = DatabaseService(db)
        try:
            db_user = service.create_user(user.username, user.role)
            return user_to_dict(db_user)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.get("/users", response_model=List[UserResponse])
    async def get_users_endpoint(db: Session = Depends(get_db)):
        service = DatabaseService(db)
        users = service.get_all_users()
        return [user_to_dict(user) for user in users]
    
    @router.get("/users/{user_id}", response_model=UserResponse)
    async def get_user_endpoint(user_id: str, db: Session = Depends(get_db)):
        service = DatabaseService(db)
        user = service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user_to_dict(user)
    
    # Templates endpoints
    @router.post("/templates", response_model=TemplateResponse)
    async def create_template_endpoint(template: TemplateCreate, db: Session = Depends(get_db)):
        service = DatabaseService(db)
        # For demo, use the first admin user as creator
        admin_user = service.get_user_by_username("admin@madoc.gov")
        if not admin_user:
            raise HTTPException(status_code=400, detail="Admin user not found")
        
        try:
            db_template = service.create_template(template.name, template.schema, admin_user.id)
            return template_to_dict(db_template)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.get("/templates", response_model=List[TemplateResponse])
    async def get_templates_endpoint(db: Session = Depends(get_db)):
        service = DatabaseService(db)
        templates = service.get_all_templates()
        return [template_to_dict(template) for template in templates]
    
    @router.get("/templates/{template_id}", response_model=TemplateResponse)
    async def get_template_endpoint(template_id: str, db: Session = Depends(get_db)):
        service = DatabaseService(db)
        template = service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template_to_dict(template)
    
    # Inspections endpoints
    @router.post("/inspections", response_model=InspectionResponse)
    async def create_inspection_endpoint(inspection: InspectionCreate, db: Session = Depends(get_db)):
        service = DatabaseService(db)
        # For demo, use the first admin user as inspector
        admin_user = service.get_user_by_username("admin@madoc.gov")
        if not admin_user:
            raise HTTPException(status_code=400, detail="Admin user not found")
        
        try:
            db_inspection = service.create_inspection(
                inspection.template_id,
                inspection.facility,
                inspection.payload,
                admin_user.id
            )
            return inspection_to_dict(db_inspection)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.get("/inspections", response_model=List[InspectionResponse])
    async def get_inspections_endpoint(db: Session = Depends(get_db)):
        service = DatabaseService(db)
        inspections = service.get_all_inspections()
        return [inspection_to_dict(inspection) for inspection in inspections]
    
    @router.get("/inspections/{inspection_id}", response_model=InspectionResponse)
    async def get_inspection_endpoint(inspection_id: str, db: Session = Depends(get_db)):
        service = DatabaseService(db)
        inspection = service.get_inspection_by_id(inspection_id)
        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")
        return inspection_to_dict(inspection)
    
    @router.put("/inspections/{inspection_id}/status")
    async def update_inspection_status_endpoint(
        inspection_id: str, 
        status: str, 
        db: Session = Depends(get_db)
    ):
        service = DatabaseService(db)
        inspection = service.update_inspection_status(inspection_id, status)
        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")
        return inspection_to_dict(inspection)
    
    # Corrective Actions endpoints
    @router.post("/corrective-actions", response_model=CorrectiveActionResponse)
    async def create_corrective_action_endpoint(
        action: CorrectiveActionCreate, 
        db: Session = Depends(get_db)
    ):
        service = DatabaseService(db)
        try:
            db_action = service.create_corrective_action(
                action.inspection_id,
                action.violation_ref,
                action.action_plan,
                action.due_date
            )
            return corrective_action_to_dict(db_action)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.get("/corrective-actions/inspection/{inspection_id}", response_model=List[CorrectiveActionResponse])
    async def get_corrective_actions_endpoint(inspection_id: str, db: Session = Depends(get_db)):
        service = DatabaseService(db)
        actions = service.get_corrective_actions_by_inspection(inspection_id)
        return [corrective_action_to_dict(action) for action in actions]
    
    @router.put("/corrective-actions/{action_id}/complete")
    async def complete_corrective_action_endpoint(action_id: str, db: Session = Depends(get_db)):
        service = DatabaseService(db)
        action = service.complete_corrective_action(action_id)
        if not action:
            raise HTTPException(status_code=404, detail="Corrective action not found")
        return corrective_action_to_dict(action)
    
    # Statistics endpoints
    @router.get("/statistics/dashboard")
    async def get_dashboard_statistics(db: Session = Depends(get_db)):
        service = DatabaseService(db)
        return service.get_statistics()
    
    @router.get("/statistics/inspector/{inspector_id}")
    async def get_inspector_statistics(inspector_id: str, db: Session = Depends(get_db)):
        service = DatabaseService(db)
        return service.get_inspector_statistics(inspector_id)
    
    @router.get("/statistics/deputy")
    async def get_deputy_statistics(db: Session = Depends(get_db)):
        service = DatabaseService(db)
        return service.get_deputy_statistics()
    
    return router

# Export for use in main server
sqlite_router = create_sqlite_router()