import React, { useState } from 'react';
import { 
  ShieldCheck, 
  BarChart3, 
  Cpu, 
  Sparkles, 
  Scale, 
  AlertTriangle, 
  FileCheck2, 
  Database,
  ArrowRight,
  ChevronRight
} from 'lucide-react';
import { PersonaId, ProblemTask, PERSONAS, PERSONA_TASKS } from '../data/personas';
import { PersonaSelector } from './PersonaSelector';
import { TaskSelector } from './TaskSelector';
import { ProblemIntakeForm } from './ProblemIntakeForm';
import { Workspace } from '../api/client';

interface UnifiedEntryViewProps {
  workspaces: Workspace[];
  activeWorkspaceId: string;
  onSelectWorkspace: (id: string) => void;
  onUploadDocument: (file: File) => Promise<void>;
  onProceedToAnalysis: (query: string, customContext?: string) => void;
  onOpenBenchmark: () => void;
  onDirectToWorkspace: () => void;
}

export const UnifiedEntryView: React.FC<UnifiedEntryViewProps> = ({
  workspaces,
  activeWorkspaceId,
  onSelectWorkspace,
  onUploadDocument,
  onProceedToAnalysis,
  onOpenBenchmark,
  onDirectToWorkspace,
}) => {
  const [selectedPersona, setSelectedPersona] = useState<PersonaId>('employee');
  const availableTasks = PERSONA_TASKS[selectedPersona] || [];
  const [selectedTask, setSelectedTask] = useState<ProblemTask>(
    availableTasks[0] || PERSONA_TASKS.employee[0]
  );

  const handlePersonaChange = (newPersona: PersonaId) => {
    setSelectedPersona(newPersona);
    const newTasks = PERSONA_TASKS[newPersona] || [];
    const firstAvailable = newTasks.find(t => t.status === 'available') || newTasks[0];
    if (firstAvailable) {
      setSelectedTask(firstAvailable);
    }
    // Also auto-select suggested workspace if matching
    const cfg = PERSONAS[newPersona];
    if (cfg && cfg.defaultWorkspaceId && workspaces.some(w => w.id === cfg.defaultWorkspaceId)) {
      onSelectWorkspace(cfg.defaultWorkspaceId);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-950 px-6 py-6 space-y-8 max-w-7xl mx-auto w-full">
      {/* Hero Product Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 p-6 md:p-8 shadow-2xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              ClauseTrace Evidence Verification Platform
            </div>

            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
              Evidence-Grounded Legal Intelligence & Conflict Detection
            </h1>

            <p className="text-sm text-slate-300 leading-relaxed font-normal">
              Cross-examine agreements, expose conflicting obligations, and audit contract risk using our 
              <span className="text-white font-semibold"> 3-Agent Adversarial Courtroom</span> and 
              <span className="text-indigo-400 font-semibold"> In-Memory Redline Verifier</span>.
            </p>
          </div>

          {/* Quick Metrics & Direct IDE Jump */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
            <button
              onClick={onDirectToWorkspace}
              className="flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-800/90 hover:bg-slate-700 active:bg-slate-800 text-slate-200 text-xs font-bold rounded-xl border border-slate-700 transition-all shadow-md"
            >
              <span>Explore Raw Workspace IDE</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </button>

            <button
              onClick={onOpenBenchmark}
              className="flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-xs font-bold rounded-xl border border-indigo-400/30 transition-all shadow-lg shadow-indigo-600/20"
            >
              <BarChart3 className="w-4 h-4" />
              <span>60-Case Evaluation Suite</span>
            </button>
          </div>
        </div>

        {/* Decorative Grid Lines */}
        <div className="absolute inset-0 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px] opacity-5 pointer-events-none" />
      </div>

      {/* Step 1: Persona Context Selector */}
      <section className="space-y-4">
        <PersonaSelector
          selectedPersona={selectedPersona}
          onSelectPersona={handlePersonaChange}
        />
      </section>

      {/* Step 2: Problem-Oriented Task Selector */}
      <section className="space-y-4 pt-2">
        <TaskSelector
          personaId={selectedPersona}
          selectedTaskId={selectedTask.id}
          onSelectTask={setSelectedTask}
        />
      </section>

      {/* Step 3: Document & Legal Problem Intake Form */}
      <section className="space-y-4 pt-2 pb-8">
        <ProblemIntakeForm
          personaId={selectedPersona}
          task={selectedTask}
          workspaces={workspaces}
          activeWorkspaceId={activeWorkspaceId}
          onSelectWorkspace={onSelectWorkspace}
          onUploadDocument={onUploadDocument}
          onProceedToAnalysis={onProceedToAnalysis}
        />
      </section>
    </div>
  );
};
