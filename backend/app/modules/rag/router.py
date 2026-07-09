from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.modules.rag import service

router = APIRouter(prefix="/rag", tags=["rag"])

MISSING = 'local RAG requires the optional extra: pip install -e ".[rag]"'


class IndexRequest(BaseModel):
    doc_id: str
    text: str
    metadata: dict = {}


class QueryRequest(BaseModel):
    text: str
    n_results: int = 5
    where: dict = {}


@router.get("/status")
def status() -> dict:
    return {"available": service.rag_available()}


@router.post("/index")
def index(payload: IndexRequest) -> dict:
    if not service.rag_available():
        raise HTTPException(501, MISSING)
    service.index(payload.doc_id, payload.text, payload.metadata)
    return {"indexed": payload.doc_id}


@router.post("/query")
def query(payload: QueryRequest) -> list[dict]:
    if not service.rag_available():
        raise HTTPException(501, MISSING)
    return service.query(payload.text, payload.n_results, payload.where)
