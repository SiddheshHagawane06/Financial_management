from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import Document
from app.schemas.schemas import RAGSearchRequest, RAGSearchResult
from app.core.security import get_current_user, require_permission
from app.services import rag_service

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/index-document")
def index_document(
    document_id: int = Query(..., description="ID of the document to index"),
    db: Session = Depends(get_db),
    _=Depends(require_permission("upload_document")),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    metadata = {
        "title": doc.title,
        "company_name": doc.company_name or "",
        "document_type": doc.document_type.value,
    }
    count = rag_service.index_document(doc.id, doc.file_path, metadata)
    doc.is_indexed = 1
    db.commit()
    return {"message": f"Indexed {count} chunks for '{doc.title}'"}


@router.delete("/remove-document/{document_id}")
def remove_document_embeddings(
    document_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("delete_document")),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    rag_service.remove_document(document_id)
    doc.is_indexed = 0
    db.commit()
    return {"message": f"Embeddings removed for document {document_id}"}


@router.post("/search", response_model=List[RAGSearchResult])
def semantic_search(
    payload: RAGSearchRequest,
    _=Depends(get_current_user),
):
    return rag_service.semantic_search(payload.query, top_k=payload.top_k)


@router.get("/context/{document_id}")
def get_document_context(
    document_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.is_indexed:
        raise HTTPException(status_code=400, detail="Document not indexed yet. Call /rag/index-document first.")
    chunks = rag_service.get_document_context(document_id)
    return {"document_id": document_id, "title": doc.title, "chunks": chunks}
