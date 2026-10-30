"""Tests for the autonomous deontic rule compiler and conflict sweeper."""
import os
import tempfile
import pytest
from app.db.database import init_db
from app.db.seed import seed_workspace_pack
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
async def test_compile_startup_founder_legal_end_to_end(temp_db):
    # Seed documents and clauses into the test database
    seed_workspace_pack("ws_startup", "startup_founder_legal", db_path=temp_db)

    compiler = DeonticRuleGraphCompiler(db_path=temp_db)
    graph = await compiler.compile_workspace("ws_startup")

    # 1. Assert summary metrics
    metrics = graph["summary_metrics"]
    assert metrics["total_documents"] == 3
    assert metrics["total_clauses"] > 0
    assert metrics["total_rules"] > 0
    assert metrics["active_conflicts"] > 0

    # 2. Assert deontic rules extracted with valid offsets
    rules = graph["deontic_rules"]
    for r in rules:
        assert r["subject"]
        assert r["modality"] in ["MUST", "MAY", "MUST_NOT", "CONDITIONAL"]
        assert r["action_category"]
        assert r["char_start"] is not None
        assert r["char_end"] is not None
        assert r["char_end"] >= r["char_start"]

    # 3. Assert proactive conflict sweeper caught the planted contradictions
    conflicts = graph["conflicts"]
    conflict_axes = [c["collision_axis"] for c in conflicts]
    conflict_types = [c["conflict_type"] for c in conflicts]

    # Check for Termination notice clash (30 days vs immediate)
    assert any("termination_notice_period" in axis or "notice" in axis for axis in conflict_axes)

    # Check for IP ownership supremacy clash (Section 2.1 vs Section 6.4)
    assert any("ip_ownership_carveout" in axis or "UNRESOLVED_OVERRIDE_COLLISION" in conflict_types for axis in conflict_axes)

    # Check for Confidentiality survival mismatch (5 years vs 2 years)
    assert any("confidentiality" in axis for axis in conflict_axes)

    # 4. Assert graph node and edge connectivity
    nodes = graph["nodes"]
    edges = graph["edges"]
    assert len(nodes) == metrics["total_documents"] + metrics["total_clauses"] + metrics["total_rules"]
    assert len(edges) >= len(conflicts)
