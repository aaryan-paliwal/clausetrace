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
  CourtroomQueryParams,
  DocumentUploadResponse,
} from './api/client';
import { Navbar } from './components/Navbar';
import { UnifiedEntryView } from './components/UnifiedEntryView';
import { ConflictGraphMatrix } from './components/ConflictGraphMatrix';
import { CourtroomStream } from './components/CourtroomStream';
import { DualClauseViewer } from './components/DualClauseViewer';
import { PatchSandboxModal } from './components/PatchSandboxModal';
import { BenchmarkModal } from './components/BenchmarkModal';

export const App: React.FC = () => {
  // Navigation mode: 'entry' (Product Landing & Intake) vs 'workspace' (3-Pane Analysis Engine)
  const [currentView, setCurrentView] = useState<'entry' | 'workspace'>('entry');

  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string>('ws_startup_legal');
  const [graph, setGraph] = useState<WorkspaceGraph | null>(null);
  const [isLoadingGraph, setIsLoadingGraph] = useState<boolean>(true);

  // Track if user has uploaded custom documents to protect active workspace selection
  const [hasUserUploadedDocument, setHasUserUploadedDocument] = useState<boolean>(false);

  // Selected conflict & dual clause viewer states
  const [selectedConflict, setSelectedConflict] = useState<RuleConflict | null>(null);
  const [clauseA, setClauseA] = useState<Clause | null>(null);
  const [clauseB, setClauseB] = useState<Clause | null>(null);
  const [highlightClauseId, setHighlightClauseId] = useState<string | null>(null);

  // Courtroom stream state & context preservation
  const [isAdjudicating, setIsAdjudicating] = useState<boolean>(false);
  const [verdict, setVerdict] = useState<CourtroomVerdict | null>(null);
  const [advocateBrief, setAdvocateBrief] = useState<AgentBrief | null>(null);
  const [skepticBrief, setSkepticBrief] = useState<AgentBrief | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [activeQuery, setActiveQuery] = useState<string>('');
  const [activePersona, setActivePersona] = useState<string>('employee');
  const [activeTaskId, setActiveTaskId] = useState<string>('emp_review_contract');
  const [activeFactualContext, setActiveFactualContext] = useState<string>('');

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

  // Handler for uploading document
  const handleUploadDocument = async (file: File): Promise<DocumentUploadResponse> => {
    const res = await api.uploadDocument(activeWorkspaceId, file);
    setHasUserUploadedDocument(true);
    // Refresh graph to incorporate new clauses
    const updatedGraph = await api.getWorkspaceGraph(activeWorkspaceId);
    setGraph(updatedGraph);
    return res;
  };

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
      let patchId = patchResult.patch_id;
      if (!patchId) {
        // Fallback: search graph for matching patch
        const currentGraph = await api.getWorkspaceGraph(activeWorkspaceId);
        const match = currentGraph.patches?.find((p: any) => p.conflict_id === patchConflict.id);
        patchId = match ? match.id : `patch_${patchConflict.id}`;
      }
      if (patchId) {
        await api.applyPatch(activeWorkspaceId, patchId);
      }
      // Refresh graph to show RESOLVED state
      const updatedGraph = await api.getWorkspaceGraph(activeWorkspaceId);
      setGraph(updatedGraph);
    } catch (err) {
      console.error('Apply patch error:', err);
      const updatedGraph = await api.getWorkspaceGraph(activeWorkspaceId);
      setGraph(updatedGraph);
    }
  };

  // Handler for asking courtroom via SSE stream with full structured context
  const handleAskCourtroom = (params: CourtroomQueryParams) => {
    setActiveQuery(params.query);
    if (params.persona) setActivePersona(params.persona);
    if (params.task_id) setActiveTaskId(params.task_id);
    if (params.factual_context !== undefined) setActiveFactualContext(params.factual_context);

    setIsAdjudicating(true);
    setVerdict(null);
    setAdvocateBrief(null);
    setSkepticBrief(null);
    setStatusMessage('Initiating adversarial cross-examination...');

    api.streamCourtroom(
      activeWorkspaceId,
      params,
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

  // Handler for proceeding from Product Entry to Courtroom Workspace
  const handleProceedToAnalysis = (
    query: string, 
    customContext?: string, 
    persona?: string, 
    taskId?: string
  ) => {
    setCurrentView('workspace');
    setActiveQuery(query);
    if (persona) setActivePersona(persona);
    if (taskId) setActiveTaskId(taskId);
    if (customContext) setActiveFactualContext(customContext);

    // Forward structured context into courtroom API call
    handleAskCourtroom({
      query,
      factual_context: customContext?.trim() || undefined,
      persona: persona || activePersona,
      task_id: taskId || activeTaskId,
    });
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 font-sans text-slate-100">
      {/* Top Navbar */}
      <Navbar
        workspaces={workspaces}
        activeWorkspaceId={activeWorkspaceId}
        onSelectWorkspace={setActiveWorkspaceId}
        onOpenBenchmark={() => setIsBenchmarkModalOpen(true)}
        onUploadDocument={handleUploadDocument}
        currentView={currentView}
        onToggleView={setCurrentView}
        metrics={graph?.summary_metrics}
      />

      {/* Main View Area */}
      {currentView === 'entry' ? (
        <UnifiedEntryView
          workspaces={workspaces}
          activeWorkspaceId={activeWorkspaceId}
          hasUserUploadedDocument={hasUserUploadedDocument}
          onSelectWorkspace={setActiveWorkspaceId}
          onUploadDocument={handleUploadDocument}
          onProceedToAnalysis={handleProceedToAnalysis}
          onOpenBenchmark={() => setIsBenchmarkModalOpen(true)}
          onDirectToWorkspace={() => setCurrentView('workspace')}
        />
      ) : (
        /* 3-Pane Responsive Layout */
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
              initialQuery={activeQuery}
              activePersona={activePersona}
              activeTaskId={activeTaskId}
              activeFactualContext={activeFactualContext}
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
      )}

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
