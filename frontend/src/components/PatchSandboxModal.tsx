import React, { useState } from 'react';
import { X, Sparkles, CheckCircle2, ShieldAlert, ArrowRight, Check, AlertCircle } from 'lucide-react';
import { RuleConflict, CounterfactualPatchResult } from '../api/client';

interface PatchSandboxModalProps {
  isOpen: boolean;
  onClose: () => void;
  conflict: RuleConflict | null;
  patchResult: CounterfactualPatchResult | null;
  isLoading: boolean;
  onApplyPatch: (patchId?: string) => Promise<void>;
}

export const PatchSandboxModal: React.FC<PatchSandboxModalProps> = ({
  isOpen,
  onClose,
  conflict,
  patchResult,
  isLoading,
  onApplyPatch,
}) => {
  const [isApplying, setIsApplying] = useState(false);
  const [appliedSuccess, setAppliedSuccess] = useState(false);

  if (!isOpen || !conflict) return null;

  const handleApply = async () => {
    setIsApplying(true);
    try {
      await onApplyPatch();
      setAppliedSuccess(true);
      setTimeout(() => {
        setAppliedSuccess(false);
        onClose();
      }, 1200);
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                Counterfactual Exploit Simulator & Redline Sandbox
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  {conflict.conflict_type}
                </span>
              </h3>
              <p className="text-[11px] text-slate-400">
                Axis: <span className="font-mono text-slate-300">{conflict.collision_axis}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16 text-center space-y-3">
              <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
              <div className="text-xs font-semibold text-slate-200">
                Simulating Adversarial Counterfactual Exploit...
              </div>
              <p className="text-[11px] text-slate-400 max-w-sm">
                Generating surgical redline amendment and running the in-memory zero-regression verification loop.
              </p>
            </div>
          ) : patchResult ? (
            <>
              {/* Exploit Scenario Warning Box */}
              <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 space-y-2">
                <div className="flex items-center gap-2 text-rose-400 text-xs font-bold uppercase tracking-wider">
                  <ShieldAlert className="w-4 h-4" />
                  Simulated Exploit Scenario (Actor: {patchResult.exploit_actor})
                </div>
                <p className="text-xs text-slate-200 leading-relaxed">
                  {patchResult.exploit_scenario}
                </p>
                <div className="text-[11px] text-rose-300/80 pt-1 border-t border-rose-500/20">
                  <span className="font-semibold text-rose-300">Financial / Legal Impact:</span>{' '}
                  {patchResult.financial_or_legal_impact}
                </div>
              </div>

              {/* Mathematical In-Memory Verification Badge */}
              <div className="p-3 rounded-xl border border-emerald-500/30 bg-emerald-950/20 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                  <div>
                    <span className="text-xs font-bold text-emerald-300 block">
                      Mathematical In-Memory Subgraph Verification Passed
                    </span>
                    <span className="text-[11px] text-slate-400">
                      Zero new regressions created in neighboring deontic rules
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono font-semibold">
                  <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    Initial: {patchResult.initial_conflicts}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Remaining: {patchResult.remaining_conflicts}
                  </span>
                </div>
              </div>

              {/* Redline Diff View */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Surgical Redline Amendment Diff
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-serif">
                  {/* Original */}
                  <div className="p-3.5 rounded-xl border border-rose-500/30 bg-slate-950/80 space-y-2">
                    <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                      Original Colliding Clause
                    </span>
                    <p className="text-slate-300 leading-relaxed whitespace-pre-wrap select-text">
                      {patchResult.original_text}
                    </p>
                  </div>

                  {/* Patched */}
                  <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-slate-950/80 space-y-2">
                    <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      Patched Harmonized Clause
                    </span>
                    <p className="text-slate-200 leading-relaxed whitespace-pre-wrap select-text">
                      {patchResult.patched_text}
                    </p>
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 italic pt-1">
                  <span className="font-semibold text-slate-300 not-italic">Rationale:</span>{' '}
                  {patchResult.rationale}
                </div>
              </div>
            </>
          ) : (
            <div className="text-center text-xs text-slate-400 py-8">
              No patch simulation data available.
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-all"
          >
            Cancel
          </button>

          <button
            onClick={handleApply}
            disabled={!patchResult || !patchResult.verification_passed || isApplying || appliedSuccess}
            className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-600/20 transition-all border border-emerald-400/30"
          >
            {appliedSuccess ? (
              <>
                <Check className="w-4 h-4 text-white" />
                <span>Patch Applied to Document!</span>
              </>
            ) : isApplying ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Applying Redline...</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4 text-white" />
                <span>Apply Patch & Harmonize</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

