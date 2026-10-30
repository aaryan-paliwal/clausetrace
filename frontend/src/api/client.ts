export interface Workspace {
  id: string;
  name: string;
  pack_name: string;
  description: string;
  created_at: string;
}

export interface Document {
  id: string;
  workspace_id: string;
  title: string;
  filename: string;
  doc_type: string;
  raw_text: string;
  authority_rank: number;
}

export interface Clause {
  id: string;
  doc_id: string;
  workspace_id: string;
  section_number: string;
  heading: string;
  text: string;
  char_start: number;
  char_end: number;
}

export interface DeonticRule {
  id: string;
  clause_id: string;
  doc_id: string;
  workspace_id: string;
  subject: string;
  modality: 'MUST' | 'MAY' | 'MUST_NOT' | 'CONDITIONAL';
  action_category: string;
  action_summary: string;
  conditions: string[];
  exceptions: string[];
  is_override: boolean;
  temporal_scope?: string;
  numeric_constraint?: string;
  exact_quote: string;
  char_start: number;
  char_end: number;
}

export interface RuleConflict {
  id: string;
  workspace_id: string;
  rule_a_id: string;
  rule_b_id: string;
  clause_a_id: string;
  clause_b_id: string;
  conflict_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  collision_axis: string;
  explanation: string;
  winning_rule_id?: string;
  status: 'ACTIVE' | 'RESOLVED';
  created_at: string;
}

export interface WorkspaceGraph {
  workspace_id: string;
  summary_metrics: {
    total_documents: number;
    total_clauses: number;
    total_rules: number;
    active_conflicts: number;
    critical_count: number;
    total_patches: number;
  };
  documents: Document[];
  clauses: Clause[];
  deontic_rules: DeonticRule[];
  conflicts: RuleConflict[];
  patches?: any[];
  nodes: any[];
  edges: any[];
}

export interface CitationSpan {
  clause_id: string;
  doc_id: string;
  doc_title: string;
  section_number: string;
  verbatim_quote: string;
  char_start: number;
  char_end: number;
}

export interface AgentBrief {
  agent_role: string;
  thesis: string;
  arguments: string[];
  cited_clause_ids: string[];
  flagged_gaps_or_undefined_terms: string[];
}

export interface CourtroomVerdict {
  verdict_state: 'ANSWERABLE' | 'CONTRADICTION' | 'EXPLOITABLE_LOOPHOLE' | 'NOT_COVERED';
  benchmark_compat_state: 'ANSWERABLE' | 'CONTRADICTION' | 'NOT_COVERED';
  confidence_score: number;
  executive_ruling: string;
  advocate_brief?: AgentBrief;
  skeptic_brief?: AgentBrief;
  missing_prerequisites: string[];
  verified_citations: CitationSpan[];
}

export interface CounterfactualPatchResult {
  conflict_id: string;
  target_clause_id: string;
  exploit_actor: string;
  exploit_scenario: string;
  financial_or_legal_impact: string;
  original_text: string;
  patched_text: string;
  rationale: string;
  verification_passed: boolean;
  initial_conflicts: number;
  remaining_conflicts: number;
  patch_id?: string;
}

export interface BenchmarkMetrics {
  total_cases: number;
  metrics: {
    courtroom_engine: {
      accuracy: number;
      correct: number;
      contradiction_precision: number;
      contradiction_recall: number;
      not_covered_recall: number;
    };
    baseline_rag: {
      accuracy: number;
      correct: number;
      contradiction_precision: number;
      contradiction_recall: number;
      not_covered_recall: number;
    };
  };
  category_breakdown: Record<string, { total: number; courtroom_correct: number; baseline_correct: number }>;
  sample_results: any[];
}

const API_BASE = '/api/v1';

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  async listWorkspaces(): Promise<Workspace[]> {
    const res = await fetch(`${API_BASE}/workspaces`);
    return res.json();
  },

  async seedWorkspace(workspaceId: string, packName: string): Promise<Workspace> {
    const res = await fetch(`${API_BASE}/workspaces/seed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: workspaceId, pack_name: packName }),
    });
    return res.json();
  },

  async uploadDocument(workspaceId: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/documents`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to upload document' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async getWorkspaceGraph(workspaceId: string): Promise<WorkspaceGraph> {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/graph`);
    return res.json();
  },

  async askCourtroom(workspaceId: string, query: string): Promise<CourtroomVerdict> {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/courtroom/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    return res.json();
  },

  streamCourtroom(
    workspaceId: string,
    query: string,
    onEvent: (event: string, data: any) => void,
    onError: (err: any) => void
  ) {
    const controller = new AbortController();
    fetch(`${API_BASE}/workspaces/${workspaceId}/courtroom/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.body) return;
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          let currentEvent = 'message';
          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('event:')) {
              currentEvent = trimmed.replace('event:', '').trim();
            } else if (trimmed.startsWith('data:')) {
              const dataStr = trimmed.replace('data:', '').trim();
              try {
                const parsed = JSON.parse(dataStr);
                onEvent(currentEvent, parsed);
              } catch {
                onEvent(currentEvent, dataStr);
              }
            }
          }
        }
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          onError(err);
        }
      });

    return () => controller.abort();
  },

  async simulatePatch(workspaceId: string, conflictId: string): Promise<CounterfactualPatchResult> {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/conflicts/${conflictId}/patch`, {
      method: 'POST',
    });
    return res.json();
  },

  async applyPatch(workspaceId: string, patchId: string) {
    const res = await fetch(`${API_BASE}/workspaces/${workspaceId}/patches/${patchId}/apply`, {
      method: 'POST',
    });
    return res.json();
  },

  async getBenchmarkSummary(): Promise<{ status: string; sample_evaluation: BenchmarkMetrics }> {
    const res = await fetch(`${API_BASE}/benchmark/summary`);
    return res.json();
  },

  async runBenchmark(maxCases?: number): Promise<{ status: string; evaluation: BenchmarkMetrics }> {
    const res = await fetch(`${API_BASE}/benchmark/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ max_cases: maxCases }),
    });
    return res.json();
  },
};
