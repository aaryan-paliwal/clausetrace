"""Courtroom, Counterfactual Patching, and Benchmark API Router."""
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.db.database import get_db_context, init_db
from app.db.repository import Repository
from app.engines.benchmark_runner import BenchmarkRunner
from app.engines.counterfactual import CounterfactualPatchEngine
from app.engines.courtroom import AdversarialCourtroomEngine

router = APIRouter(prefix="/api/v1", tags=["courtroom"])


class QueryRequest(BaseModel):
    query: str


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
    verdict = await courtroom.evaluate_query(workspace_id, payload.query)
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
        courtroom.stream_courtroom_events(workspace_id, payload.query),
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
    """Return benchmark metadata and cached evaluation results."""
    runner = BenchmarkRunner()
    results = await runner.run(max_cases=10)
    return {
        "status": "success",
        "benchmark_name": "ClauseTrace 60-Case University Policy Ground Truth",
        "sample_evaluation": results,
    }


@router.post("/benchmark/run")
async def run_full_benchmark() -> Dict[str, Any]:
    """Execute complete 60-case benchmark evaluation comparing Baseline RAG vs ClauseTrace Courtroom."""
    runner = BenchmarkRunner()
    results = await runner.run()
    return {
        "status": "success",
        "benchmark_name": "ClauseTrace 60-Case Evaluation Suite",
        "results": results,
    }
