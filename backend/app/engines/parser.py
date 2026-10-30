"""Document clause parser and file text extractor."""
import io
import re
from typing import Any, Dict, List
from pypdf import PdfReader


def extract_text_from_upload(filename: str, content_bytes: bytes) -> str:
    """Extract plain text from uploaded markdown, text, or PDF files."""
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    else:
        # Standard UTF-8 decoding with fallback
        try:
            return content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return content_bytes.decode("latin-1", errors="replace")


def parse_document_into_clauses(doc_id: str, workspace_id: str, raw_text: str) -> List[Dict[str, Any]]:
    """
    Split Markdown, plain text, or legal text into clauses based on headings and section markers.
    Guarantee exact substring character offsets: raw_text[char_start:char_end] == clause['text'].
    """
    if not raw_text.strip():
        return []

    # Combined regex pattern for Markdown headings or legal section numbers
    pattern = re.compile(
        r"(?:^(?:#{1,4}\s+|(?:\b(?:Section|Article|§)\s+\d+(?:\.\d+)*\b)|(?:\b\d+\.\d+\b))\s*(.*?)$)",
        re.MULTILINE,
    )

    matches = list(pattern.finditer(raw_text))

    if not matches:
        return [{
            "id": f"{doc_id}::sec_000",
            "doc_id": doc_id,
            "workspace_id": workspace_id,
            "section_number": "1.0",
            "heading": "General Provisions",
            "text": raw_text,
            "char_start": 0,
            "char_end": len(raw_text),
        }]

    clauses: List[Dict[str, Any]] = []

    # If there is preamble before first section
    if matches[0].start() > 0:
        preamble = raw_text[:matches[0].start()]
        if preamble.strip():
            clauses.append({
                "id": f"{doc_id}::sec_000",
                "doc_id": doc_id,
                "workspace_id": workspace_id,
                "section_number": "0.0",
                "heading": "Preamble / Title",
                "text": preamble,
                "char_start": 0,
                "char_end": matches[0].start(),
            })

    for i, match in enumerate(matches):
        char_start = match.start()
        char_end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        clause_text = raw_text[char_start:char_end]

        heading_line = match.group(0).strip()
        raw_heading = match.group(1).strip() if match.group(1) else heading_line

        # Extract cleaner section number
        sec_num_match = re.search(r"(\b\d+(?:\.\d+)*\b)", heading_line)
        sec_num = sec_num_match.group(1) if sec_num_match else f"{len(clauses) + 1}.0"

        # Format heading
        clean_heading = re.sub(r"^#{1,4}\s*", "", heading_line).strip()
        clean_heading = re.sub(r"^(?:Section|Article|§)\s*\d+(?:\.\d+)*[:\.\s-]*", "", clean_heading, flags=re.IGNORECASE).strip()
        if not clean_heading:
            clean_heading = f"Section {sec_num}"

        clauses.append({
            "id": f"{doc_id}::sec_{len(clauses):03d}",
            "doc_id": doc_id,
            "workspace_id": workspace_id,
            "section_number": sec_num,
            "heading": clean_heading,
            "text": clause_text,
            "char_start": char_start,
            "char_end": char_end,
        })

    return clauses
