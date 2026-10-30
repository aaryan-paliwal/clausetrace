"""Workspaces and deontic graph API router."""
import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db.database import get_db_context, init_db
from app.db.repository import Repository
from app.db.seed import seed_workspace_pack
from app.engines.deontic_compiler import DeonticRuleGraphCompiler
from app.engines.parser import extract_text_from_upload, parse_document_into_clauses
from app.engines.retrieval import compute_embedding

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


async def _ensure_default_workspaces_seeded(repo: Repository) -> None:
    """Ensure startup legal and university packs exist if repository is empty."""
    workspaces = repo.list_workspaces()
    if not workspaces:
        # Seed startup founder legal
        seed_workspace_pack("ws_startup_legal", "startup_founder_legal")
        # Compile deontic graph for default workspace
        compiler = DeonticRuleGraphCompiler()
        await compiler.compile_workspace("ws_startup_legal")

        # Seed university policy
        seed_workspace_pack("ws_university_policy", "university_policy")


@router.get("", response_model=List[Dict[str, Any]])
async def list_workspaces() -> List[Dict[str, Any]]:
    """List all active workspaces, auto-seeding defaults if empty."""
    init_db()
    with get_db_context() as conn:
        repo = Repository(conn)
        await _ensure_default_workspaces_seeded(repo)
        return repo.list_workspaces()


@router.post("/seed/{pack_name}")
async def seed_pack(pack_name: str) -> Dict[str, Any]:
    """Seed and compile a domain pack into a designated workspace."""
    init_db()
    if pack_name not in ["startup_founder_legal", "university_policy"]:
        raise HTTPException(status_code=400, detail=f"Unknown domain pack: {pack_name}")

    workspace_id = f"ws_{pack_name}"
    seed_res = seed_workspace_pack(workspace_id, pack_name)

    compiler = DeonticRuleGraphCompiler()
    graph_res = await compiler.compile_workspace(workspace_id)

    return {
        "status": "success",
        "workspace_id": workspace_id,
        "pack_name": pack_name,
        "seeded_docs": seed_res["seeded_docs"],
        "seeded_clauses": seed_res["seeded_clauses"],
        "summary_metrics": graph_res["summary_metrics"],
    }


@router.post("/{workspace_id}/documents")
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Upload and parse a new document into clauses and trigger graph re-compilation."""
    init_db()
    with get_db_context() as conn:
        repo = Repository(conn)
        ws = repo.get_workspace(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")

        content_bytes = await file.read()
        raw_text = extract_text_from_upload(file.filename, content_bytes)
        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="Uploaded file contains no readable text")

        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        title = file.filename.rsplit(".", 1)[0].replace("_", " ").title()
        repo.create_document(
            doc_id=doc_id,
            workspace_id=workspace_id,
            title=title,
            filename=file.filename,
            raw_text=raw_text,
            doc_type="contract",
        )

        # Parse clauses
        clauses = parse_document_into_clauses(doc_id, workspace_id, raw_text)
        for c in clauses:
            repo.create_clause(
                clause_id=c["id"],
                doc_id=doc_id,
                workspace_id=workspace_id,
                section_number=c["section_number"],
                heading=c["heading"],
                text=c["text"],
                char_start=c["char_start"],
                char_end=c["char_end"],
                embedding=compute_embedding(c["text"]),
            )

    # Re-compile workspace deontic rule graph
    compiler = DeonticRuleGraphCompiler()
    graph_res = await compiler.compile_workspace(workspace_id)

    return {
        "status": "success",
        "doc_id": doc_id,
        "title": title,
        "clauses_created": len(clauses),
        "summary_metrics": graph_res["summary_metrics"],
    }


@router.get("/{workspace_id}/graph")
async def get_workspace_graph(workspace_id: str) -> Dict[str, Any]:
    """Return full deontic rule-graph state, nodes, edges, and active conflicts."""
    init_db()
    with get_db_context() as conn:
        repo = Repository(conn)
        ws = repo.get_workspace(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")

    compiler = DeonticRuleGraphCompiler()
    return compiler.get_graph(workspace_id)
