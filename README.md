# ClauseTrace

ClauseTrace is a production-grade, evidence-grounded contract and policy verification engine powered by the **Meta Model API (Llama 3.3 70B & Llama 3.1 8B)**.

It compiles unstructured regulatory policies, enterprise contracts, and institutional handbooks into formal deontic rule graphs, subjects proposed queries to an adversarial 3-agent verification pipeline, and computes deterministic conflict states with counterfactual redline patches.

---

## Key Capabilities

- **Autonomous Deontic Rule-Graph Compiler**: Parses complex contractual language into structured modal logic representations (Obligations, Permissions, Prohibitions, Conditions, Exceptions).
- **3-Agent Adversarial Courtroom Pipeline**:
  - *Prosecutor Agent* (Llama-3.3-70B): Challenges contractual compliance and extracts latent edge-case conflicts.
  - *Defense Agent* (Llama-3.3-70B): Validates safe harbors, affirmative defenses, and explicit waiver clauses.
  - *Judge Agent* (Llama-3.3-70B): Delivers deterministic three-state rulings (`ANSWERABLE`, `CONTRADICTION`, `NOT_COVERED`) strictly grounded in citation indices.
- **Counterfactual Redline Patch Verifier**: Synthesizes minimal-edit contract amendment patches with before/after simulation to resolve detected deontic contradictions.
- **Strict Evidence Grounding**: Hallucination-resistant retrieval gate that returns `NOT_COVERED` on missing or out-of-distribution scope rather than conjecturing answers.

---

## Architecture Overview

```text
               +---------------------------------------+
               |         Client (React / Vite)         |
               +---------------------------------------+
                                   |
                                   v  [REST / JSON]
               +---------------------------------------+
               |        FastAPI Core Service           |
               +---------------------------------------+
                                   |
        +--------------------------+--------------------------+
        |                                                     |
        v                                                     v
+-----------------------------+               +-----------------------------+
|    Deontic Graph Ingestion  |               |  Adversarial Reasoning Core |
|  - Semantic / Lexical Gate  |               |  - Prosecutor Agent         |
|  - Rule Compiler            |               |  - Defense Agent            |
|  - SQLite Citation Store    |               |  - Presiding Judge (States) |
+-----------------------------+               +-----------------------------+
                                                              |
                                                              v
                                              +-----------------------------+
                                              |  Meta Model API Integration |
                                              |  - Llama-3.3-70B-Instruct   |
                                              |  - Llama-3.1-8B-Instruct    |
                                              +-----------------------------+
```

---

## Repository Structure

```text
clausetrace/
├── backend/
│   ├── app/
│   │   ├── config.py             # Typed settings loaded from environment
│   │   └── main.py               # FastAPI application entrypoint & middleware
│   ├── tests/
│   │   └── test_health.py        # System health and API verification tests
│   ├── pytest.ini                # Test runner configuration
│   └── requirements.txt          # Python dependencies
├── .env.example                  # Environment configuration template
├── .gitignore                    # Monorepo git ignore rules
└── README.md                     # Engineering documentation
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Meta Model API key

### Backend Setup

1. Navigate to the backend directory and set up a virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy the environment configuration:
   ```bash
   cp ../.env.example .env
   # Edit .env with your META_API_KEY
   ```

4. Run the test suite:
   ```bash
   pytest
   ```

5. Launch the backend API server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The health check will be accessible at `http://localhost:8000/api/v1/health`.
