import React, { useEffect, useState } from 'react';
import {
  api,
  Workspace,
  WorkspaceGraph,
  RuleConflict,
  Clause,
  CourtroomVerdict,
  AgentBrief,
  CounterfactualPatchResult,
  BenchmarkMetrics,
} from './api/client';
import { Navbar } from './components/Navbar';
import { ConflictGraphMatrix } from './components/ConflictGraphMatrix';
import { CourtroomStream } from './components/CourtroomStream';
import { DualClauseViewer } from './components/DualClauseViewer';
import { PatchSandboxModal } from './components/PatchSandboxModal';
import { BenchmarkModal } from './components/BenchmarkModal';

export const App: React.FC = () => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string>('ws_startup_legal');
  const [graph, setGraph] = useState<WorkspaceGraph | null>(null);
  const [isLoadingGraph, setIsLoadingGraph] = useState<boolean>(true);

  // Selected conflict & dual clause viewer states
  const [selectedConflict, setSelectedConflict] = useState<RuleConflict | null>(null);
  const [clauseA, setClauseA] = useState<Clause | null>(null);
  const [clauseB, setClauseB] = useState<Clause | null>(null);
  const [highlightClauseId, setHighlightClauseId] = useState<string | null>(null);

  // Courtroom stream state
  const [isAdjudicating, setIsAdjudicating] = useState<boolean>(false);
  const [verdict, setVerdict] = useState<CourtroomVerdict | null>(null);
  const [advocateBrief, setAdvocateBrief] = useState<AgentBrief | null>(null);
  const [skepticBrief, setSkepticBrief] = useState<AgentBrief | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Patch sandbox modal state
  const [isPatchModalOpen, setIsPatchModalOpen] = useState<boolean>(false);
  const [patchConflict, setPatchConflict] = useState<RuleConflict | null>(null);
  const [patchResult, setPatchResult] = useState<CounterfactualPatchResult | null>(null);
  const [isLoadingPatch, setIsLoadingPatch] = useState<boolean>(false);

  // Benchmark modal state
  const [isBenchmarkModalOpen, setIsBenchmarkModalOpen] = useState<boolean>(false);
  const [benchmarkMetrics, setBenchmarkMetrics] = useState<BenchmarkMetrics | null>(null);

  // Load initial workspaces & benchmark summary
  useEffect(() => {
    const init = async () => {
      try {
        const wsList = await api.listWorkspaces();
        if (wsList && wsList.length > 0) {
          setWorkspaces(wsList);
          setActiveWorkspaceId(wsList[0].id);
        }

        // Fetch pre-computed benchmark summary
        const benchSummary = await api.getBenchmarkSummary();
        if (benchSummary && benchSummary.sample_evaluation) {
          setBenchmarkMetrics(benchSummary.sample_evaluation);
        }
      } catch (err) {
        console.error('Initialization error:', err);
      }
    };
    init();
  }, []);

  // Fetch graph on active workspace change
  useEffect(() => {
    if (!activeWorkspaceId) return;

    const loadGraph = async () => {
      setIsLoadingGraph(true);
      try {
        const g = await api.getWorkspaceGraph(activeWorkspaceId);
        setGraph(g);

        // Pre-select first conflict if available
        if (g.conflicts && g.conflicts.length > 0) {
          const first = g.conflicts[0];
          setSelectedConflict(first);
          const cA = g.clauses.find((c) => c.id === first.clause_a_id) || null;
          const cB = g.clauses.find((c) => c.id === first.clause_b_id) || null;
          setClauseA(cA);
          setClauseB(cB);
        } else if (g.clauses && g.clauses.length >= 2) {
          setClauseA(g.clauses[0]);
          setClauseB(g.clauses[1]);
        }
      } catch (err) {
        console.error('Error loading graph:', err);
      } finally {
        setIsLoadingGraph(false);
      }
    };

    loadGraph();
  }, [activeWorkspaceId]);

  // Handler for selecting conflict from matrix
  const handleSelectConflict = (conflict: RuleConflict) => {
    setSelectedConflict(conflict);
    if (!graph) return;
    const cA = graph.clauses.find((c) => c.id === conflict.clause_a_id) || null;
    const cB = graph.clauses.find((c) => c.id === conflict.clause_b_id) || null;
    setClauseA(cA);
    setClauseB(cB);
    setHighlightClauseId(null);
  };

  // Handler for triggering patch sandbox modal
  const handleTriggerPatchSandbox = async (conflict: RuleConflict) => {
    setPatchConflict(conflict);
    setIsPatchModalOpen(true);
    setIsLoadingPatch(true);
    setPatchResult(null);

    try {
      const res = await api.simulatePatch(activeWorkspaceId, conflict.id);
      setPatchResult(res);
    } catch (err) {
      console.error('Patch simulation error:', err);
    } finally {
      setIsLoadingPatch(false);
    }
  };

  // Handler for applying verified redline patch
  const handleApplyPatch = async () => {
    if (!patchConflict || !patchResult) return;
    try {
      // Find created patch ID from repository or re-query graph
      const g = await api.getWorkspaceGraph(activeWorkspaceId);
      // Fallback apply directly
      await api.applyPatch(activeWorkspaceId, `patch_${patchConflict.id}`);
      // Refresh graph to show RESOLVED state
      const updatedGraph = await api.getWorkspaceGraph(activeWorkspaceId);
      setGraph(updatedGraph);
    } catch (err) {
      console.error('Apply patch error:', err);
      // Re-fetch graph anyway to synchronize state
      const updatedGraph = await api.getWorkspaceGraph(activeWorkspaceId);
      setGraph(updatedGraph);
    }
  };

  // Handler for asking courtroom via SSE stream
  const handleAskCourtroom = (query: string) => {
    setIsAdjudicating(true);
    setVerdict(null);
    setAdvocateBrief(null);
    setSkepticBrief(null);
    setStatusMessage('Initiating adversarial cross-examination...');

    api.streamCourtroom(
      activeWorkspaceId,
      query,
      (event, data) => {
        if (event === 'status') {
          setStatusMessage(data.message);
        } else if (event === 'retrieval') {
          setStatusMessage(`Retrieved ${data.clauses_count} relevant deontic clauses.`);
          if (data.clauses && data.clauses.length > 0 && graph) {
            const firstId = data.clauses[0].id;
            const found = graph.clauses.find((c) => c.id === firstId);
            if (found) setClauseA(found);
            if (data.clauses.length > 1) {
              const secondFound = graph.clauses.find((c) => c.id === data.clauses[1].id);
              if (secondFound) setClauseB(secondFound);
            }
          }
        } else if (event === 'advocate_brief') {
          setAdvocateBrief(data);
        } else if (event === 'skeptic_brief') {
          setSkepticBrief(data);
        } else if (event === 'verdict') {
          setVerdict(data);
          setStatusMessage(null);
          setIsAdjudicating(false);
        }
      },
      (err) => {
        console.error('Courtroom streaming error:', err);
        setStatusMessage('Error during stream adjudication.');
        setIsAdjudicating(false);
      }
    );
  };

  // Handler for clicking a verified citation span
  const handleCitationClick = (clauseId: string) => {
    setHighlightClauseId(clauseId);
    if (!graph) return;
    const clause = graph.clauses.find((c) => c.id === clauseId);
    if (clause) {
      setClauseA(clause);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 font-sans text-slate-100">
      {/* Top Navbar */}
      <Navbar
        workspaces={workspaces}
        activeWorkspaceId={activeWorkspaceId}
        onSelectWorkspace={setActiveWorkspaceId}
        onOpenBenchmark={() => setIsBenchmarkModalOpen(true)}
        metrics={graph?.summary_metrics}
      />

      {/* 3-Pane Responsive Layout */}
      <main className="flex-1 grid grid-cols-12 overflow-hidden">
        {/* Left Pane (Col 1-3): Proactive Conflict Matrix */}
        <div className="col-span-12 md:col-span-4 lg:col-span-3 h-full overflow-hidden">
          <ConflictGraphMatrix
            conflicts={graph?.conflicts || []}
            clauses={graph?.clauses || []}
            selectedConflictId={selectedConflict?.id || null}
            onSelectConflict={handleSelectConflict}
            onTriggerPatchSandbox={handleTriggerPatchSandbox}
            isLoading={isLoadingGraph}
          />
        </div>

        {/* Center Pane (Col 4-8): 3-Agent Adversarial Courtroom Console */}
        <div className="col-span-12 md:col-span-8 lg:col-span-5 h-full overflow-hidden border-r border-slate-800">
          <CourtroomStream
            onAsk={handleAskCourtroom}
            isLoading={isAdjudicating}
            verdict={verdict}
            advocateBrief={advocateBrief}
            skepticBrief={skepticBrief}
            statusMessage={statusMessage}
            onCitationClick={handleCitationClick}
          />
        </div>

        {/* Right Pane (Col 9-12): Synchronized Dual Clause Viewer */}
        <div className="hidden lg:block lg:col-span-4 h-full overflow-hidden">
          <DualClauseViewer
            documents={graph?.documents || []}
            clauseA={clauseA}
            clauseB={clauseB}
            highlightClauseId={highlightClauseId}
          />
        </div>
      </main>

      {/* Modals */}
      <PatchSandboxModal
        isOpen={isPatchModalOpen}
        onClose={() => setIsPatchModalOpen(false)}
        conflict={patchConflict}
        patchResult={patchResult}
        isLoading={isLoadingPatch}
        onApplyPatch={handleApplyPatch}
      />

      <BenchmarkModal
        isOpen={isBenchmarkModalOpen}
        onClose={() => setIsBenchmarkModalOpen(false)}
        initialData={benchmarkMetrics}
      />
    </div>
  );
};

export default App;
