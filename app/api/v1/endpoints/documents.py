import os
import shutil
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import Document, DocumentType
from app.schemas.schemas import DocumentOut
from app.core.security import get_current_user, require_permission
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_EXT = {".pdf", ".docx", ".doc", ".txt"}


def save_upload(file: UploadFile) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(settings.UPLOAD_DIR, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return dest


@router.post("/upload", response_model=DocumentOut, status_code=201)
def upload_document(
    title: str = Form(...),
    company_name: str = Form(""),
    document_type: DocumentType = Form(DocumentType.other),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("upload_document")),
):
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not supported")

    file_path = save_upload(file)
    doc = Document(
        title=title,
        company_name=company_name or None,
        document_type=document_type,
        file_path=file_path,
        file_name=file.filename,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("", response_model=List[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return db.query(Document).all()


# NOTE: /search MUST be declared before /{document_id} to avoid FastAPI
# treating the literal string "search" as a document_id integer.
@router.get("/search", response_model=List[DocumentOut])
def search_documents(
    title: Optional[str] = Query(None),
    company_name: Optional[str] = Query(None),
    document_type: Optional[DocumentType] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(Document)
    if title:
        q = q.filter(Document.title.ilike(f"%{title}%"))
    if company_name:
        q = q.filter(Document.company_name.ilike(f"%{company_name}%"))
    if document_type:
        q = q.filter(Document.document_type == document_type)
    return q.all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("delete_document")),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
