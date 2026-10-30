"""Courtroom, Counterfactual Patching, and Benchmark API Router."""
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.db.database import get_db_context, init_db
from app.db.repository import Repository
from app.engines.benchmark_runner import BenchmarkRunner
from app.engines.counterfactual import CounterfactualPatchEngine
from app.engines.courtroom import AdversarialCourtroomEngine

router = APIRouter(prefix="/api/v1", tags=["courtroom"])


class QueryRequest(BaseModel):
    query: str
    factual_context: Optional[str] = Field(default=None, description="User-supplied factual notes or role context")
    persona: Optional[str] = Field(default=None, description="Legal context persona (employee, founder, hr, business, individual)")
    task_id: Optional[str] = Field(default=None, description="Objective task identifier selected by the user")


@router.post("/workspaces/{workspace_id}/courtroom/ask")
async def ask_courtroom(workspace_id: str, payload: QueryRequest) -> Dict[str, Any]:
    """Execute 3-Agent Adversarial Courtroom evaluation and return complete CourtroomVerdict."""
    init_db()
    with get_db_context() as conn:
        repo = Repository(conn)
        ws = repo.get_workspace(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")

    courtroom = AdversarialCourtroomEngine()
    verdict = await courtroom.evaluate_query(
        workspace_id=workspace_id,
        query=payload.query,
        factual_context=payload.factual_context,
        persona=payload.persona,
        task_id=payload.task_id,
    )
    return verdict.model_dump()


@router.post("/workspaces/{workspace_id}/courtroom/stream")
async def stream_courtroom(workspace_id: str, payload: QueryRequest):
    """Stream real-time Server-Sent Events (SSE) of the Courtroom trial."""
    init_db()
    with get_db_context() as conn:
        repo = Repository(conn)
        ws = repo.get_workspace(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")

    courtroom = AdversarialCourtroomEngine()
    return StreamingResponse(
        courtroom.stream_courtroom_events(
            workspace_id=workspace_id,
            query=payload.query,
            factual_context=payload.factual_context,
            persona=payload.persona,
            task_id=payload.task_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/workspaces/{workspace_id}/conflicts/{conflict_id}/patch")
async def generate_patch(workspace_id: str, conflict_id: str) -> Dict[str, Any]:
    """Simulate bad-faith exploit and generate in-memory verified redline patch."""
    init_db()
    patch_engine = CounterfactualPatchEngine()
    try:
        patch_result = await patch_engine.simulate_and_patch(workspace_id, conflict_id)
        return patch_result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/workspaces/{workspace_id}/patches/{patch_id}/apply")
async def apply_patch(workspace_id: str, patch_id: str) -> Dict[str, Any]:
    """Apply verified redline patch to workspace document and resolve conflict."""
    init_db()
    patch_engine = CounterfactualPatchEngine()
    try:
        result = patch_engine.apply_patch(workspace_id, patch_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/benchmark/summary")
async def get_benchmark_summary() -> Dict[str, Any]:
    """Return pre-computed 60-case benchmark evaluation metrics."""
    init_db()
    runner = BenchmarkRunner()
    result = await runner.run(max_cases=5)
    return {
        "status": "success",
        "sample_evaluation": result,
    }


@router.post("/benchmark/run")
async def run_benchmark(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run full 60-case ground truth evaluation comparing Baseline RAG vs Courtroom Engine."""
    init_db()
    max_cases = payload.get("max_cases") if payload else None
    runner = BenchmarkRunner()
    results = await runner.run(max_cases=max_cases)
    return {
        "status": "success",
        "evaluation": results,
    }
