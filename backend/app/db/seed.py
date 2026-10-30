"""Corpus pack seeding and benchmark loading utilities."""
import json
import os
import re
from typing import Any, Dict, List, Optional
from app.db.database import get_db_context
from app.db.repository import Repository

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
PACKS_DIR = os.path.join(DATA_DIR, "packs")
BENCHMARKS_DIR = os.path.join(DATA_DIR, "benchmarks")


def load_benchmark_60() -> Dict[str, Any]:
    """Load the 60-case ground truth evaluation benchmark."""
    benchmark_path = os.path.join(BENCHMARKS_DIR, "ground_truth_60.json")
    if not os.path.exists(benchmark_path):
        raise FileNotFoundError(f"Benchmark file not found at {benchmark_path}")
    with open(benchmark_path, "r", encoding="utf-8") as f:
        return json.load(f)


def chunk_markdown_sections(text: str) -> List[Dict[str, Any]]:
    """Parse Markdown text into section clauses with exact character offsets."""
    pattern = re.compile(r"(^#{1,3}\s+(.+)$)", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        return [{
            "section_number": "1.0",
            "heading": "General",
            "text": text.strip(),
            "char_start": 0,
            "char_end": len(text),
        }]

    sections = []
    for i, match in enumerate(matches):
        heading = match.group(2).strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk_text = text[start:end].strip()

        # extract section number if formatted like "2.1 Base Salary"
        sec_num_match = re.match(r"^(\d+(?:\.\d+)*)\b", heading)
        sec_num = sec_num_match.group(1) if sec_num_match else f"{i + 1}.0"

        sections.append({
            "section_number": sec_num,
            "heading": heading,
            "text": chunk_text,
            "char_start": start,
            "char_end": end,
        })
    return sections


def seed_workspace_pack(workspace_id: str, pack_name: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Seed documents and clauses from a designated domain pack into SQLite."""
    pack_dir = os.path.join(PACKS_DIR, pack_name)
    if not os.path.isdir(pack_dir):
        raise ValueError(f"Domain pack directory does not exist: {pack_dir}")

    with get_db_context(db_path) as conn:
        repo = Repository(conn)

        # Check or create workspace
        existing_ws = repo.get_workspace(workspace_id)
        if not existing_ws:
            repo.create_workspace(
                workspace_id=workspace_id,
                name=f"Workspace: {pack_name.replace('_', ' ').title()}",
                description=f"Auto-seeded domain workspace for {pack_name}",
                domain_pack=pack_name,
            )

        seeded_docs = 0
        seeded_clauses = 0

        for fname in sorted(os.listdir(pack_dir)):
            if not (fname.endswith(".md") or fname.endswith(".txt")):
                continue

            file_path = os.path.join(pack_dir, fname)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            doc_id = f"{workspace_id}::{os.path.splitext(fname)[0]}"
            title = os.path.splitext(fname)[0].replace("_", " ").title()

            existing_doc = repo.get_document(doc_id)
            if not existing_doc:
                repo.create_document(
                    doc_id=doc_id,
                    workspace_id=workspace_id,
                    title=title,
                    filename=fname,
                    raw_text=content,
                    doc_type="policy" if "policy" in pack_name else "contract",
                )
                seeded_docs += 1

                # Chunk clauses
                sections = chunk_markdown_sections(content)
                for s_idx, sec in enumerate(sections):
                    clause_id = f"{doc_id}::sec_{s_idx:03d}"
                    repo.create_clause(
                        clause_id=clause_id,
                        doc_id=doc_id,
                        workspace_id=workspace_id,
                        section_number=sec["section_number"],
                        heading=sec["heading"],
                        text=sec["text"],
                        char_start=sec["char_start"],
                        char_end=sec["char_end"],
                    )
                    seeded_clauses += 1

        return {
            "workspace_id": workspace_id,
            "pack_name": pack_name,
            "seeded_docs": seeded_docs,
            "seeded_clauses": seeded_clauses,
        }
