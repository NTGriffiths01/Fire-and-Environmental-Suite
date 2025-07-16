from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import json
import base64
import hashlib
from enum import Enum
import jwt
from passlib.context import CryptContext
from weasyprint import HTML, CSS
from io import BytesIO
import tempfile

# Import SQLite API components
from sqlite_api import sqlite_router
from compliance_api import compliance_router
from monthly_inspection_api import monthly_inspection_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
ALGORITHM = "HS256"

# Create the main app
app = FastAPI(title="Fire and Environmental Safety Suite", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    INSPECTOR = "inspector"
    DEPUTY_OF_OPERATIONS = "deputy_of_operations"

class InspectionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class CitationCode(str, Enum):
    ICC_FIRE_CODE = "ICC-FC"
    ACA_STANDARD = "ACA-STD"
    CMR_451 = "105-CMR-451"

class CitationSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: UserRole
    facility_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    facility_id: Optional[str] = None
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Facility(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    facility_type: str
    capacity: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

class InspectionTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    template_data: Dict[str, Any]
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class InspectionForm(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_id: str
    facility_id: str
    inspector_id: str
    inspection_date: datetime
    form_data: Dict[str, Any]
    attachments: List[str] = []
    citations: List[Dict[str, Any]] = []
    status: InspectionStatus = InspectionStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    comments: List[Dict[str, Any]] = []

class Citation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    title: str
    description: str
    category: CitationCode
    severity: CitationSeverity
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    ip_address: str
    user_agent: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = {}

class FileUpload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    content_type: str
    size: int
    base64_content: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

# Utility functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_inspector_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.INSPECTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_deputy_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.DEPUTY_OF_OPERATIONS, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def log_audit_event(user_id: str, action: str, resource_type: str, resource_id: str, request: Request, details: Dict[str, Any] = {}):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details=details
    )
    await db.audit_logs.insert_one(audit_log.dict())

def generate_inspection_pdf(inspection_data: dict, template_data: dict) -> bytes:
    """Generate PDF report from inspection data"""
    
    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Fire Safety Inspection Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #1e3a8a;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .logo {{
                width: 80px;
                height: 80px;
                margin: 0 auto 20px;
                background: #1e3a8a;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
            }}
            .title {{
                font-size: 24px;
                font-weight: bold;
                color: #1e3a8a;
                margin: 0;
            }}
            .subtitle {{
                font-size: 16px;
                color: #666;
                margin: 10px 0;
            }}
            .section {{
                margin: 30px 0;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 8px;
            }}
            .section-title {{
                font-size: 18px;
                font-weight: bold;
                color: #1e3a8a;
                margin-bottom: 15px;
                border-bottom: 2px solid #f59e0b;
                padding-bottom: 5px;
            }}
            .field {{
                margin: 10px 0;
                padding: 8px;
                background: #f9f9f9;
                border-radius: 4px;
            }}
            .field-label {{
                font-weight: bold;
                color: #333;
            }}
            .field-value {{
                margin-left: 10px;
                color: #666;
            }}
            .citations {{
                background: #fef2f2;
                border: 1px solid #f87171;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
            }}
            .citation {{
                margin: 10px 0;
                padding: 10px;
                background: white;
                border-radius: 4px;
                border-left: 4px solid #dc2626;
            }}
            .citation-code {{
                font-weight: bold;
                color: #dc2626;
                font-size: 14px;
            }}
            .citation-title {{
                font-weight: bold;
                color: #b91c1c;
                margin: 5px 0;
            }}
            .citation-description {{
                color: #7f1d1d;
                font-size: 12px;
            }}
            .footer {{
                margin-top: 50px;
                text-align: center;
                border-top: 1px solid #ddd;
                padding-top: 20px;
                color: #666;
            }}
            .status {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 12px;
            }}
            .status-submitted {{
                background: #dbeafe;
                color: #1e40af;
            }}
            .status-approved {{
                background: #d1fae5;
                color: #065f46;
            }}
            .status-rejected {{
                background: #fee2e2;
                color: #991b1b;
            }}
            .signature-section {{
                margin: 30px 0;
                padding: 20px;
                border: 2px solid #1e3a8a;
                border-radius: 8px;
            }}
            .signature-box {{
                border: 1px solid #ccc;
                height: 80px;
                margin: 10px 0;
                padding: 10px;
                background: #f9f9f9;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">DOC</div>
            <h1 class="title">Massachusetts Department of Correction</h1>
            <p class="subtitle">Fire and Environmental Safety Inspection Report</p>
        </div>
        
        <div class="section">
            <div class="section-title">Inspection Details</div>
            <div class="field">
                <span class="field-label">Inspection ID:</span>
                <span class="field-value">{inspection_data.get('id', 'N/A')}</span>
            </div>
            <div class="field">
                <span class="field-label">Date:</span>
                <span class="field-value">{datetime.fromisoformat(inspection_data.get('inspection_date', '')).strftime('%B %d, %Y') if inspection_data.get('inspection_date') else 'N/A'}</span>
            </div>
            <div class="field">
                <span class="field-label">Status:</span>
                <span class="status status-{inspection_data.get('status', 'draft')}">{inspection_data.get('status', 'draft')}</span>
            </div>
            <div class="field">
                <span class="field-label">Template:</span>
                <span class="field-value">{template_data.get('name', 'N/A')}</span>
            </div>
        </div>
    """
    
    # Add form data sections
    form_data = inspection_data.get('form_data', {})
    if form_data:
        html_content += '<div class="section"><div class="section-title">Inspection Results</div>'
        for key, value in form_data.items():
            formatted_key = key.replace('_', ' ').title()
            formatted_value = 'Yes' if value is True else 'No' if value is False else str(value)
            html_content += f"""
            <div class="field">
                <span class="field-label">{formatted_key}:</span>
                <span class="field-value">{formatted_value}</span>
            </div>
            """
        html_content += '</div>'
    
    # Add citations if any
    citations = inspection_data.get('citations', [])
    if citations:
        html_content += '<div class="citations"><div class="section-title">Citations and Violations</div>'
        for citation in citations:
            html_content += f"""
            <div class="citation">
                <div class="citation-code">{citation.get('code', 'N/A')}</div>
                <div class="citation-title">{citation.get('title', 'N/A')}</div>
                <div class="citation-description">{citation.get('description', 'N/A')}</div>
            </div>
            """
        html_content += '</div>'
    
    # Add signature section
    html_content += """
        <div class="signature-section">
            <div class="section-title">Signatures</div>
            <div class="field">
                <span class="field-label">Inspector Signature:</span>
                <div class="signature-box">Digital signature applied</div>
            </div>
            <div class="field">
                <span class="field-label">Deputy Review:</span>
                <div class="signature-box">
    """
    
    # Add review comments if any
    comments = inspection_data.get('comments', [])
    if comments:
        latest_comment = comments[-1]
        html_content += f"Reviewed by: {latest_comment.get('user_name', 'N/A')}<br>"
        html_content += f"Comments: {latest_comment.get('comment', 'N/A')}<br>"
        html_content += f"Date: {datetime.fromisoformat(latest_comment.get('timestamp', '')).strftime('%B %d, %Y') if latest_comment.get('timestamp') else 'N/A'}"
    else:
        html_content += "Pending review"
    
    html_content += """
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>This report was generated electronically by the Fire and Environmental Safety Suite</p>
            <p>Massachusetts Department of Correction - Fire Safety Division</p>
            <p>Generated on: """ + datetime.now().strftime('%B %d, %Y at %I:%M %p') + """</p>
        </div>
    </body>
    </html>
    """
    
    # Generate PDF
    pdf_buffer = BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer.getvalue()

# Auth routes
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate, request: Request):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        facility_id=user_data.facility_id
    )
    
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Log the registration
    await log_audit_event(
        user.id, "USER_REGISTERED", "user", user.id, request,
        {"email": user.email, "role": user.role}
    )
    
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin, request: Request):
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    # Log the login
    await log_audit_event(
        user["id"], "USER_LOGIN", "user", user["id"], request,
        {"email": user["email"]}
    )
    
    user_obj = User(**user)
    return Token(access_token=access_token, token_type="bearer", user=user_obj)

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Facility routes
@api_router.get("/facilities", response_model=List[Facility])
async def get_facilities(current_user: User = Depends(get_current_user)):
    facilities = await db.facilities.find().to_list(1000)
    return [Facility(**facility) for facility in facilities]

@api_router.post("/facilities", response_model=Facility)
async def create_facility(facility_data: Facility, current_user: User = Depends(get_admin_user), request: Request = None):
    facility = Facility(**facility_data.dict())
    await db.facilities.insert_one(facility.dict())
    
    # Log the creation
    await log_audit_event(
        current_user.id, "FACILITY_CREATED", "facility", facility.id, request,
        {"name": facility.name}
    )
    
    return facility

# Template routes
@api_router.get("/templates", response_model=List[InspectionTemplate])
async def get_templates(current_user: User = Depends(get_current_user)):
    templates = await db.inspection_templates.find({"is_active": True}).to_list(1000)
    return [InspectionTemplate(**template) for template in templates]

@api_router.post("/templates", response_model=InspectionTemplate)
async def create_template(template_data: InspectionTemplate, current_user: User = Depends(get_admin_user), request: Request = None):
    template = InspectionTemplate(**template_data.dict())
    template.created_by = current_user.id
    await db.inspection_templates.insert_one(template.dict())
    
    # Log the creation
    await log_audit_event(
        current_user.id, "TEMPLATE_CREATED", "template", template.id, request,
        {"name": template.name}
    )
    
    return template

@api_router.get("/templates/{template_id}", response_model=InspectionTemplate)
async def get_template(template_id: str, current_user: User = Depends(get_current_user)):
    template = await db.inspection_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return InspectionTemplate(**template)

# Inspection routes
@api_router.get("/inspections", response_model=List[InspectionForm])
async def get_inspections(current_user: User = Depends(get_current_user)):
    query = {}
    if current_user.role == UserRole.INSPECTOR:
        query["inspector_id"] = current_user.id
    elif current_user.role == UserRole.DEPUTY_OF_OPERATIONS:
        query["status"] = {"$in": [InspectionStatus.SUBMITTED, InspectionStatus.UNDER_REVIEW]}
    
    inspections = await db.inspections.find(query).sort("created_at", -1).to_list(1000)
    return [InspectionForm(**inspection) for inspection in inspections]

@api_router.post("/inspections", response_model=InspectionForm)
async def create_inspection(inspection_data: InspectionForm, current_user: User = Depends(get_inspector_user), request: Request = None):
    inspection = InspectionForm(**inspection_data.dict())
    inspection.inspector_id = current_user.id
    
    # Set facility_id if not provided
    if not inspection.facility_id:
        facility = await db.facilities.find_one({})
        if facility:
            inspection.facility_id = facility["id"]
    
    await db.inspections.insert_one(inspection.dict())
    
    # Log the creation
    await log_audit_event(
        current_user.id, "INSPECTION_CREATED", "inspection", inspection.id, request,
        {"status": inspection.status}
    )
    
    return inspection

@api_router.get("/inspections/{inspection_id}", response_model=InspectionForm)
async def get_inspection(inspection_id: str, current_user: User = Depends(get_current_user)):
    inspection = await db.inspections.find_one({"id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return InspectionForm(**inspection)

@api_router.put("/inspections/{inspection_id}", response_model=InspectionForm)
async def update_inspection(inspection_id: str, inspection_data: InspectionForm, current_user: User = Depends(get_current_user), request: Request = None):
    inspection = await db.inspections.find_one({"id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    # Check permissions
    if current_user.role == UserRole.INSPECTOR and inspection["inspector_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this inspection")
    
    update_data = inspection_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.inspections.update_one(
        {"id": inspection_id},
        {"$set": update_data}
    )
    
    # Log the update
    await log_audit_event(
        current_user.id, "INSPECTION_UPDATED", "inspection", inspection_id, request,
        {"status": inspection_data.status}
    )
    
    updated_inspection = await db.inspections.find_one({"id": inspection_id})
    return InspectionForm(**updated_inspection)

@api_router.post("/inspections/{inspection_id}/submit")
async def submit_inspection(inspection_id: str, current_user: User = Depends(get_inspector_user), request: Request = None):
    inspection = await db.inspections.find_one({"id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    if inspection["inspector_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to submit this inspection")
    
    await db.inspections.update_one(
        {"id": inspection_id},
        {"$set": {
            "status": InspectionStatus.SUBMITTED,
            "submitted_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Log the submission
    await log_audit_event(
        current_user.id, "INSPECTION_SUBMITTED", "inspection", inspection_id, request
    )
    
    return {"message": "Inspection submitted successfully"}

@api_router.post("/inspections/{inspection_id}/review")
async def review_inspection(inspection_id: str, action: str, comments: str, current_user: User = Depends(get_deputy_user), request: Request = None):
    inspection = await db.inspections.find_one({"id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    new_status = InspectionStatus.APPROVED if action == "approve" else InspectionStatus.REJECTED
    
    comment = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "user_name": current_user.full_name,
        "comment": comments,
        "timestamp": datetime.utcnow().isoformat(),
        "action": action
    }
    
    await db.inspections.update_one(
        {"id": inspection_id},
        {"$set": {
            "status": new_status,
            "reviewed_by": current_user.id,
            "reviewed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }, "$push": {"comments": comment}}
    )
    
    # Log the review
    await log_audit_event(
        current_user.id, f"INSPECTION_{action.upper()}", "inspection", inspection_id, request,
        {"comments": comments}
    )
    
    return {"message": f"Inspection {action}d successfully"}

@api_router.get("/inspections/{inspection_id}/pdf")
async def get_inspection_pdf(inspection_id: str, current_user: User = Depends(get_current_user)):
    inspection = await db.inspections.find_one({"id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    # Get template data
    template = await db.inspection_templates.find_one({"id": inspection["template_id"]})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Generate PDF
    pdf_content = generate_inspection_pdf(inspection, template)
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=inspection_{inspection_id}.pdf"}
    )

# Citation routes
@api_router.get("/citations", response_model=List[Citation])
async def get_citations(current_user: User = Depends(get_current_user)):
    citations = await db.citations.find().to_list(1000)
    return [Citation(**citation) for citation in citations]

@api_router.post("/citations/suggest")
async def suggest_citations(finding: str, current_user: User = Depends(get_current_user)):
    keywords = finding.lower()
    suggestions = []
    
    # Advanced citation matching
    citation_patterns = {
        "fire": [
            {"code": "ICC-FC-907", "title": "Fire Alarm and Detection Systems", "description": "Requirements for fire alarm and detection systems", "category": "ICC-FC"},
            {"code": "105-CMR-451.100", "title": "Fire Safety in Correctional Facilities", "description": "Massachusetts fire safety regulations", "category": "105-CMR-451"}
        ],
        "smoke": [
            {"code": "ICC-FC-907", "title": "Fire Alarm and Detection Systems", "description": "Requirements for fire alarm and detection systems", "category": "ICC-FC"},
            {"code": "ICC-FC-908", "title": "Smoke Detection Systems", "description": "Requirements for smoke detection systems", "category": "ICC-FC"}
        ],
        "exit": [
            {"code": "ICC-FC-1030", "title": "Means of Egress", "description": "Requirements for means of egress systems", "category": "ICC-FC"},
            {"code": "ACA-STD-3A-17", "title": "Emergency Procedures", "description": "Standards for emergency procedures", "category": "ACA-STD"}
        ],
        "sprinkler": [
            {"code": "ICC-FC-903", "title": "Automatic Sprinkler Systems", "description": "Requirements for automatic sprinkler systems", "category": "ICC-FC"},
            {"code": "105-CMR-451.200", "title": "Fire Suppression Systems", "description": "Massachusetts fire suppression requirements", "category": "105-CMR-451"}
        ],
        "emergency": [
            {"code": "ACA-STD-3A-17", "title": "Safety and Emergency Procedures", "description": "Standards for safety and emergency procedures", "category": "ACA-STD"},
            {"code": "ICC-FC-404", "title": "Emergency Planning", "description": "Requirements for emergency planning", "category": "ICC-FC"}
        ],
        "electrical": [
            {"code": "ICC-FC-605", "title": "Electrical Systems", "description": "Requirements for electrical systems safety", "category": "ICC-FC"},
            {"code": "105-CMR-451.300", "title": "Electrical Safety", "description": "Massachusetts electrical safety regulations", "category": "105-CMR-451"}
        ],
        "hazardous": [
            {"code": "ICC-FC-5003", "title": "Hazardous Materials", "description": "Requirements for hazardous materials storage", "category": "ICC-FC"},
            {"code": "ACA-STD-3A-25", "title": "Hazardous Materials Management", "description": "Standards for hazardous materials", "category": "ACA-STD"}
        ]
    }
    
    for pattern, citations in citation_patterns.items():
        if pattern in keywords:
            suggestions.extend(citations)
    
    # Remove duplicates
    seen = set()
    unique_suggestions = []
    for suggestion in suggestions:
        if suggestion["code"] not in seen:
            seen.add(suggestion["code"])
            unique_suggestions.append(suggestion)
    
    return {"suggestions": unique_suggestions}

# Audit routes
@api_router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(current_user: User = Depends(get_admin_user)):
    logs = await db.audit_logs.find().sort("timestamp", -1).to_list(1000)
    return [AuditLog(**log) for log in logs]

# Dashboard routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    stats = {}
    
    if current_user.role == UserRole.ADMIN:
        stats = {
            "total_users": await db.users.count_documents({}),
            "total_facilities": await db.facilities.count_documents({}),
            "total_inspections": await db.inspections.count_documents({}),
            "pending_reviews": await db.inspections.count_documents({"status": InspectionStatus.SUBMITTED})
        }
    elif current_user.role == UserRole.INSPECTOR:
        stats = {
            "my_inspections": await db.inspections.count_documents({"inspector_id": current_user.id}),
            "draft_inspections": await db.inspections.count_documents({"inspector_id": current_user.id, "status": InspectionStatus.DRAFT}),
            "submitted_inspections": await db.inspections.count_documents({"inspector_id": current_user.id, "status": InspectionStatus.SUBMITTED})
        }
    elif current_user.role == UserRole.DEPUTY_OF_OPERATIONS:
        stats = {
            "pending_reviews": await db.inspections.count_documents({"status": InspectionStatus.SUBMITTED}),
            "approved_inspections": await db.inspections.count_documents({"status": InspectionStatus.APPROVED}),
            "rejected_inspections": await db.inspections.count_documents({"status": InspectionStatus.REJECTED})
        }
    
    return stats

# File upload route
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user), request: Request = None):
    try:
        content = await file.read()
        base64_content = base64.b64encode(content).decode('utf-8')
        
        file_record = FileUpload(
            filename=file.filename,
            content_type=file.content_type,
            size=len(content),
            base64_content=base64_content,
            uploaded_by=current_user.id
        )
        
        await db.files.insert_one(file_record.dict())
        
        # Log the upload
        await log_audit_event(
            current_user.id, "FILE_UPLOADED", "file", file_record.id, request,
            {"filename": file.filename, "size": len(content)}
        )
        
        return {
            "file_id": file_record.id,
            "filename": file.filename,
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# Test route
@api_router.get("/")
async def root():
    return {"message": "Fire and Environmental Safety Suite API", "version": "1.0.0"}

# Include routers
app.include_router(api_router)
app.include_router(sqlite_router, prefix="/api/v2", tags=["SQLite Database"])
app.include_router(compliance_router, prefix="/api/compliance", tags=["Compliance Tracking"])

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # Create default admin user if none exists
    admin_exists = await db.users.find_one({"role": UserRole.ADMIN})
    if not admin_exists:
        admin_user = User(
            email="admin@madoc.gov",
            full_name="System Administrator",
            role=UserRole.ADMIN
        )
        admin_dict = admin_user.dict()
        admin_dict["password"] = hash_password("admin123")
        await db.users.insert_one(admin_dict)
        logger.info("Default admin user created")
    
    # Create default facilities if none exist
    facility_count = await db.facilities.count_documents({})
    if facility_count == 0:
        default_facilities = [
            Facility(
                name="MCI-Cedar Junction",
                address="1 Administration Rd, Norfolk, MA 02056",
                facility_type="Maximum Security",
                capacity=1200
            ),
            Facility(
                name="MCI-Framingham",
                address="1 Holbrook St, Framingham, MA 01702",
                facility_type="Medium Security",
                capacity=550
            ),
            Facility(
                name="MCI-Norfolk",
                address="2 Clark St, Norfolk, MA 02056",
                facility_type="Medium Security",
                capacity=1450
            ),
            Facility(
                name="Souza-Baranowski Correctional Center",
                address="1 Administration Rd, Lancaster, MA 01523",
                facility_type="Maximum Security",
                capacity=1200
            ),
            Facility(
                name="Old Colony Correctional Center",
                address="1 Administration Rd, Bridgewater, MA 02324",
                facility_type="Medium Security",
                capacity=1000
            ),
            Facility(
                name="North Central Correctional Institution",
                address="500 Colony Rd, Gardner, MA 01440",
                facility_type="Medium Security",
                capacity=1200
            )
        ]
        
        for facility in default_facilities:
            await db.facilities.insert_one(facility.dict())
        logger.info("Default facilities created")
    
    # Create default inspection templates if none exist
    template_count = await db.inspection_templates.count_documents({})
    if template_count == 0:
        default_templates = [
            InspectionTemplate(
                name="Monthly Fire Safety Inspection",
                description="Comprehensive monthly fire safety inspection checklist",
                template_data={
                    "sections": [
                        {
                            "title": "Fire Detection and Alarm Systems",
                            "fields": [
                                {"name": "fire_alarm_tested", "type": "checkbox", "label": "Fire alarm system tested and functional"},
                                {"name": "smoke_detectors_functional", "type": "checkbox", "label": "All smoke detectors functional"},
                                {"name": "manual_pull_stations", "type": "checkbox", "label": "Manual pull stations accessible and functional"},
                                {"name": "fire_alarm_notes", "type": "textarea", "label": "Fire alarm system notes"}
                            ]
                        },
                        {
                            "title": "Fire Suppression Systems",
                            "fields": [
                                {"name": "sprinkler_system_functional", "type": "checkbox", "label": "Sprinkler system functional"},
                                {"name": "fire_extinguishers_present", "type": "checkbox", "label": "Fire extinguishers present and properly charged"},
                                {"name": "suppression_system_notes", "type": "textarea", "label": "Suppression system notes"}
                            ]
                        },
                        {
                            "title": "Emergency Exits and Egress",
                            "fields": [
                                {"name": "exits_clear", "type": "checkbox", "label": "All exits clear and properly marked"},
                                {"name": "exit_signs_functional", "type": "checkbox", "label": "Exit signs illuminated and functional"},
                                {"name": "emergency_lighting", "type": "checkbox", "label": "Emergency lighting operational"},
                                {"name": "egress_notes", "type": "textarea", "label": "Egress system notes"}
                            ]
                        },
                        {
                            "title": "Electrical Safety",
                            "fields": [
                                {"name": "electrical_panels_accessible", "type": "checkbox", "label": "Electrical panels accessible and properly labeled"},
                                {"name": "no_exposed_wiring", "type": "checkbox", "label": "No exposed or damaged wiring"},
                                {"name": "electrical_notes", "type": "textarea", "label": "Electrical system notes"}
                            ]
                        },
                        {
                            "title": "Hazardous Materials",
                            "fields": [
                                {"name": "hazmat_properly_stored", "type": "checkbox", "label": "Hazardous materials properly stored"},
                                {"name": "msds_sheets_available", "type": "checkbox", "label": "MSDS sheets available and current"},
                                {"name": "hazmat_notes", "type": "textarea", "label": "Hazardous materials notes"}
                            ]
                        }
                    ]
                },
                created_by="system",
                is_active=True
            ),
            InspectionTemplate(
                name="Weekly Environmental Safety Check",
                description="Weekly environmental safety inspection checklist",
                template_data={
                    "sections": [
                        {
                            "title": "Air Quality and Ventilation",
                            "fields": [
                                {"name": "ventilation_adequate", "type": "checkbox", "label": "Ventilation system adequate"},
                                {"name": "air_quality_concerns", "type": "checkbox", "label": "Any air quality concerns"},
                                {"name": "ventilation_notes", "type": "textarea", "label": "Ventilation notes"}
                            ]
                        },
                        {
                            "title": "Water and Sanitation",
                            "fields": [
                                {"name": "water_quality_acceptable", "type": "checkbox", "label": "Water quality acceptable"},
                                {"name": "sanitation_adequate", "type": "checkbox", "label": "Sanitation facilities adequate"},
                                {"name": "water_notes", "type": "textarea", "label": "Water and sanitation notes"}
                            ]
                        },
                        {
                            "title": "Waste Management",
                            "fields": [
                                {"name": "waste_disposal_proper", "type": "checkbox", "label": "Waste disposal procedures followed"},
                                {"name": "recycling_program", "type": "checkbox", "label": "Recycling program functional"},
                                {"name": "waste_notes", "type": "textarea", "label": "Waste management notes"}
                            ]
                        }
                    ]
                },
                created_by="system",
                is_active=True
            )
        ]
        
        for template in default_templates:
            await db.inspection_templates.insert_one(template.dict())
        logger.info("Default inspection templates created")
    
    # Create default citations if none exist
    citation_count = await db.citations.count_documents({})
    if citation_count == 0:
        default_citations = [
            Citation(
                code="ICC-FC-907",
                title="Fire Alarm and Detection Systems",
                description="Requirements for fire alarm and detection systems in correctional facilities",
                category=CitationCode.ICC_FIRE_CODE,
                severity=CitationSeverity.HIGH
            ),
            Citation(
                code="ICC-FC-903",
                title="Automatic Sprinkler Systems",
                description="Requirements for automatic sprinkler systems installation and maintenance",
                category=CitationCode.ICC_FIRE_CODE,
                severity=CitationSeverity.HIGH
            ),
            Citation(
                code="ICC-FC-1030",
                title="Means of Egress",
                description="Requirements for means of egress systems and emergency exits",
                category=CitationCode.ICC_FIRE_CODE,
                severity=CitationSeverity.HIGH
            ),
            Citation(
                code="ICC-FC-605",
                title="Electrical Systems",
                description="Requirements for electrical systems safety and maintenance",
                category=CitationCode.ICC_FIRE_CODE,
                severity=CitationSeverity.MEDIUM
            ),
            Citation(
                code="ACA-STD-3A-17",
                title="Safety and Emergency Procedures",
                description="Standards for safety and emergency procedures in correctional facilities",
                category=CitationCode.ACA_STANDARD,
                severity=CitationSeverity.MEDIUM
            ),
            Citation(
                code="ACA-STD-3A-25",
                title="Hazardous Materials Management",
                description="Standards for hazardous materials storage and handling",
                category=CitationCode.ACA_STANDARD,
                severity=CitationSeverity.MEDIUM
            ),
            Citation(
                code="105-CMR-451.100",
                title="Fire Safety in Correctional Facilities",
                description="Massachusetts fire safety regulations for correctional facilities",
                category=CitationCode.CMR_451,
                severity=CitationSeverity.HIGH
            ),
            Citation(
                code="105-CMR-451.200",
                title="Fire Suppression Systems",
                description="Massachusetts requirements for fire suppression systems",
                category=CitationCode.CMR_451,
                severity=CitationSeverity.HIGH
            ),
            Citation(
                code="105-CMR-451.300",
                title="Electrical Safety",
                description="Massachusetts electrical safety regulations for correctional facilities",
                category=CitationCode.CMR_451,
                severity=CitationSeverity.MEDIUM
            )
        ]
        
        for citation in default_citations:
            await db.citations.insert_one(citation.dict())
        logger.info("Default citations created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()