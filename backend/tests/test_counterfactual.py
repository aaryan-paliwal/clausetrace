"""Tests for the Counterfactual Exploit Simulator and Patch Verifier."""
import os
import tempfile
import pytest
from app.db.database import get_db_context, init_db
from app.db.repository import Repository
from app.db.seed import seed_workspace_pack
from app.engines.counterfactual import CounterfactualPatchEngine
from app.engines.deontic_compiler import DeonticRuleGraphCompiler


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.mark.asyncio
async def test_simulate_patch_and_apply(temp_db):
    # 1. Seed startup founder legal and compile
    seed_workspace_pack("ws_startup", "startup_founder_legal", db_path=temp_db)
    compiler = DeonticRuleGraphCompiler(db_path=temp_db)
    graph = await compiler.compile_workspace("ws_startup")

    conflicts = graph["conflicts"]
    assert len(conflicts) > 0
    target_conflict = conflicts[0]

    patch_engine = CounterfactualPatchEngine(db_path=temp_db)

    # 2. Simulate exploit and generate verified patch
    patch_result = await patch_engine.simulate_and_patch(
        workspace_id="ws_startup",
        conflict_id=target_conflict["id"],
    )

    assert patch_result.conflict_id == target_conflict["id"]
    assert patch_result.exploit_actor
    assert patch_result.exploit_scenario
    assert patch_result.financial_or_legal_impact
    assert patch_result.patched_text
    assert patch_result.verification_passed is True
    assert patch_result.remaining_conflicts == 0

    # 3. Apply the verified patch
    with get_db_context(temp_db) as conn:
        repo = Repository(conn)
        patches = repo.list_patches(conflict_id=target_conflict["id"])
        assert len(patches) == 1
        patch_record = patches[0]

    apply_result = patch_engine.apply_patch("ws_startup", patch_record["id"])
    assert apply_result["status"] == "applied"

    # Verify conflict status marked RESOLVED in database
    with get_db_context(temp_db) as conn:
        repo = Repository(conn)
        updated_conf = repo.get_conflict(target_conflict["id"])
        assert updated_conf["status"] == "RESOLVED"
