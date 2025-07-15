from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
    template_data: Dict[str, Any]  # JSON structure for dynamic form
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
    attachments: List[str] = []  # Base64 encoded files
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
    severity: str
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
        expire = datetime.utcnow() + timedelta(minutes=15)
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

async def log_audit_event(user_id: str, action: str, resource_type: str, resource_id: str, ip_address: str, user_agent: str, details: Dict[str, Any] = {}):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )
    await db.audit_logs.insert_one(audit_log.dict())

# Auth routes
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with hashed password
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
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Update last login
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
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
async def create_facility(facility_data: Facility, current_user: User = Depends(get_admin_user)):
    facility = Facility(**facility_data.dict())
    await db.facilities.insert_one(facility.dict())
    return facility

# Template routes
@api_router.get("/templates", response_model=List[InspectionTemplate])
async def get_templates(current_user: User = Depends(get_current_user)):
    templates = await db.inspection_templates.find({"is_active": True}).to_list(1000)
    return [InspectionTemplate(**template) for template in templates]

@api_router.post("/templates", response_model=InspectionTemplate)
async def create_template(template_data: InspectionTemplate, current_user: User = Depends(get_admin_user)):
    template = InspectionTemplate(**template_data.dict())
    template.created_by = current_user.id
    await db.inspection_templates.insert_one(template.dict())
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
    
    inspections = await db.inspections.find(query).to_list(1000)
    return [InspectionForm(**inspection) for inspection in inspections]

@api_router.post("/inspections", response_model=InspectionForm)
async def create_inspection(inspection_data: InspectionForm, current_user: User = Depends(get_inspector_user)):
    inspection = InspectionForm(**inspection_data.dict())
    inspection.inspector_id = current_user.id
    await db.inspections.insert_one(inspection.dict())
    return inspection

@api_router.get("/inspections/{inspection_id}", response_model=InspectionForm)
async def get_inspection(inspection_id: str, current_user: User = Depends(get_current_user)):
    inspection = await db.inspections.find_one({"id": inspection_id})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return InspectionForm(**inspection)

@api_router.put("/inspections/{inspection_id}", response_model=InspectionForm)
async def update_inspection(inspection_id: str, inspection_data: InspectionForm, current_user: User = Depends(get_current_user)):
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
    
    updated_inspection = await db.inspections.find_one({"id": inspection_id})
    return InspectionForm(**updated_inspection)

@api_router.post("/inspections/{inspection_id}/submit")
async def submit_inspection(inspection_id: str, current_user: User = Depends(get_inspector_user)):
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
    
    return {"message": "Inspection submitted successfully"}

@api_router.post("/inspections/{inspection_id}/review")
async def review_inspection(inspection_id: str, action: str, comments: str, current_user: User = Depends(get_deputy_user)):
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
        "timestamp": datetime.utcnow(),
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
    
    return {"message": f"Inspection {action}d successfully"}

# Citation routes
@api_router.get("/citations", response_model=List[Citation])
async def get_citations(current_user: User = Depends(get_current_user)):
    citations = await db.citations.find().to_list(1000)
    return [Citation(**citation) for citation in citations]

@api_router.post("/citations/suggest")
async def suggest_citations(finding: str, current_user: User = Depends(get_current_user)):
    # Simple citation suggestion based on keywords
    keywords = finding.lower()
    suggestions = []
    
    if "fire" in keywords or "smoke" in keywords or "alarm" in keywords:
        suggestions.append({
            "code": "ICC-FC-907",
            "title": "Fire Alarm and Detection Systems",
            "description": "Requirements for fire alarm and detection systems",
            "category": "ICC-FC"
        })
    
    if "exit" in keywords or "egress" in keywords or "door" in keywords:
        suggestions.append({
            "code": "ICC-FC-1030",
            "title": "Means of Egress",
            "description": "Requirements for means of egress systems",
            "category": "ICC-FC"
        })
    
    if "sprinkler" in keywords or "suppression" in keywords:
        suggestions.append({
            "code": "ICC-FC-903",
            "title": "Automatic Sprinkler Systems",
            "description": "Requirements for automatic sprinkler systems",
            "category": "ICC-FC"
        })
    
    return {"suggestions": suggestions}

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
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    try:
        # Read file content
        content = await file.read()
        
        # Convert to base64
        base64_content = base64.b64encode(content).decode('utf-8')
        
        # Create file record
        file_record = {
            "id": str(uuid.uuid4()),
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "base64_content": base64_content,
            "uploaded_by": current_user.id,
            "uploaded_at": datetime.utcnow()
        }
        
        await db.files.insert_one(file_record)
        
        return {
            "file_id": file_record["id"],
            "filename": file.filename,
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# Test route
@api_router.get("/")
async def root():
    return {"message": "Fire and Environmental Safety Suite API"}

# Include router
app.include_router(api_router)

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
    
    # Create default facility if none exists
    facility_exists = await db.facilities.find_one({})
    if not facility_exists:
        facility = Facility(
            name="MCI-Cedar Junction",
            address="1 Administration Rd, Norfolk, MA 02056",
            facility_type="Maximum Security",
            capacity=1200
        )
        await db.facilities.insert_one(facility.dict())
        logger.info("Default facility created")
    
    # Create default inspection template if none exists
    template_exists = await db.inspection_templates.find_one({})
    if not template_exists:
        template = InspectionTemplate(
            name="Monthly Fire Safety Inspection",
            description="Standard monthly fire safety inspection form",
            template_data={
                "sections": [
                    {
                        "title": "Fire Alarm Systems",
                        "fields": [
                            {"name": "alarm_functional", "type": "checkbox", "label": "Fire alarm system functional"},
                            {"name": "alarm_notes", "type": "textarea", "label": "Notes"}
                        ]
                    },
                    {
                        "title": "Sprinkler Systems",
                        "fields": [
                            {"name": "sprinkler_functional", "type": "checkbox", "label": "Sprinkler system functional"},
                            {"name": "sprinkler_notes", "type": "textarea", "label": "Notes"}
                        ]
                    },
                    {
                        "title": "Emergency Exits",
                        "fields": [
                            {"name": "exits_clear", "type": "checkbox", "label": "All exits clear and marked"},
                            {"name": "exit_notes", "type": "textarea", "label": "Notes"}
                        ]
                    }
                ]
            },
            created_by="system",
            is_active=True
        )
        await db.inspection_templates.insert_one(template.dict())
        logger.info("Default inspection template created")
    
    # Create default citations if none exist
    citation_exists = await db.citations.find_one({})
    if not citation_exists:
        default_citations = [
            Citation(
                code="ICC-FC-907",
                title="Fire Alarm and Detection Systems",
                description="Requirements for fire alarm and detection systems",
                category=CitationCode.ICC_FIRE_CODE,
                severity="high"
            ),
            Citation(
                code="ICC-FC-903",
                title="Automatic Sprinkler Systems",
                description="Requirements for automatic sprinkler systems",
                category=CitationCode.ICC_FIRE_CODE,
                severity="high"
            ),
            Citation(
                code="ICC-FC-1030",
                title="Means of Egress",
                description="Requirements for means of egress systems",
                category=CitationCode.ICC_FIRE_CODE,
                severity="medium"
            ),
            Citation(
                code="ACA-STD-3A-17",
                title="Safety and Emergency Procedures",
                description="Standards for safety and emergency procedures",
                category=CitationCode.ACA_STANDARD,
                severity="medium"
            ),
            Citation(
                code="105-CMR-451.100",
                title="Fire Safety in Correctional Facilities",
                description="Massachusetts fire safety regulations for correctional facilities",
                category=CitationCode.CMR_451,
                severity="high"
            )
        ]
        
        for citation in default_citations:
            await db.citations.insert_one(citation.dict())
        logger.info("Default citations created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()