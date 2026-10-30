import React from 'react';
import { AlertTriangle, ShieldAlert, Sparkles, ArrowRight, Layers, CheckCircle2 } from 'lucide-react';
import { RuleConflict, Clause } from '../api/client';

interface ConflictGraphMatrixProps {
  conflicts: RuleConflict[];
  clauses: Clause[];
  selectedConflictId: string | null;
  onSelectConflict: (conflict: RuleConflict) => void;
  onTriggerPatchSandbox: (conflict: RuleConflict) => void;
  isLoading?: boolean;
}

export const ConflictGraphMatrix: React.FC<ConflictGraphMatrixProps> = ({
  conflicts,
  clauses,
  selectedConflictId,
  onSelectConflict,
  onTriggerPatchSandbox,
  isLoading,
}) => {
  const getClauseById = (id: string) => clauses.find((c) => c.id === id);

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
      case 'HIGH':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 uppercase tracking-wider flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-rose-400" />
            {severity}
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
            {severity}
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/30 uppercase tracking-wider">
            {severity}
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950/70 border-r border-slate-800">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/40 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <h2 className="text-sm font-bold text-white tracking-tight">Proactive Conflict Matrix</h2>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Autonomously discovered cross-document collisions
          </p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
          {conflicts.length} detected
        </span>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-500 text-xs gap-2">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <span>Sweeping deontic conflict graph...</span>
          </div>
        ) : conflicts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-400 text-xs text-center p-4">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-2" />
            <span className="font-semibold text-slate-200">Zero Active Conflicts</span>
            <p className="text-slate-500 text-[11px] mt-1">
              All rules in this workspace are harmonized or patched.
            </p>
          </div>
        ) : (
          conflicts.map((conflict) => {
            const isSelected = selectedConflictId === conflict.id;
            const clauseA = getClauseById(conflict.clause_a_id);
            const clauseB = getClauseById(conflict.clause_b_id);

            return (
              <div
                key={conflict.id}
                onClick={() => onSelectConflict(conflict)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer relative group ${
                  isSelected
                    ? 'bg-slate-900 border-indigo-500/80 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/30'
                    : 'bg-slate-900/60 border-slate-800/80 hover:bg-slate-900 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {getSeverityBadge(conflict.severity)}
                    <span className="text-[10px] font-mono font-medium text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/50">
                      {conflict.conflict_type}
                    </span>
                  </div>
                  {conflict.status === 'RESOLVED' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">
                      RESOLVED
                    </span>
                  )}
                </div>

                <div className="text-xs font-semibold text-slate-200 line-clamp-1 mb-1 font-mono">
                  axis: {conflict.collision_axis}
                </div>

                <p className="text-[12px] text-slate-300 leading-relaxed mb-3 line-clamp-3">
                  {conflict.explanation}
                </p>

                {/* Colliding Clauses Preview */}
                <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 bg-slate-950/70 p-2 rounded-lg border border-slate-800/70 mb-3 font-mono">
                  <div className="truncate">
                    <span className="text-indigo-400 font-semibold">Clause A:</span>{' '}
                    {clauseA ? `§${clauseA.section_number}` : conflict.clause_a_id}
                  </div>
                  <div className="truncate">
                    <span className="text-amber-400 font-semibold">Clause B:</span>{' '}
                    {clauseB ? `§${clauseB.section_number}` : conflict.clause_b_id}
                  </div>
                </div>

                {/* Action Footer */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                  <span className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Layers className="w-3 h-3" />
                    Click to view pair
                  </span>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onTriggerPatchSandbox(conflict);
                    }}
                    className="flex items-center gap-1 text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 px-2.5 py-1 rounded-md border border-indigo-500/30 transition-all"
                  >
                    <Sparkles className="w-3 h-3" />
                    Simulate Patch
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

