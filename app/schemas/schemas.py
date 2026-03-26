from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.user import DocumentType


# ── Auth ─────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Permissions ───────────────────────────────────────────────────────────────
class PermissionOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ── Roles ─────────────────────────────────────────────────────────────────────
class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[List[str]] = []


class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[PermissionOut] = []

    class Config:
        from_attributes = True


class AssignRole(BaseModel):
    user_id: int
    role_name: str


# ── Documents ─────────────────────────────────────────────────────────────────
class DocumentOut(BaseModel):
    id: int
    title: str
    company_name: Optional[str] = None
    document_type: DocumentType
    file_name: Optional[str] = None
    uploaded_by: Optional[int] = None
    created_at: datetime
    is_indexed: int

    class Config:
        from_attributes = True


# ── RAG ───────────────────────────────────────────────────────────────────────
class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class RAGSearchResult(BaseModel):
    document_id: int
    title: str
    company_name: Optional[str] = None
    chunk_text: str
    score: float
