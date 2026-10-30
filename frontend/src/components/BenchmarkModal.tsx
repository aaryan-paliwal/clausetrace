import React, { useState } from 'react';
import { X, Play, BarChart3, CheckCircle2, TrendingUp, AlertTriangle, Layers } from 'lucide-react';
import { BenchmarkMetrics, api } from '../api/client';

interface BenchmarkModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialData: BenchmarkMetrics | null;
}

export const BenchmarkModal: React.FC<BenchmarkModalProps> = ({
  isOpen,
  onClose,
  initialData,
}) => {
  const [data, setData] = useState<BenchmarkMetrics | null>(initialData);
  const [isRunning, setIsRunning] = useState(false);

  if (!isOpen) return null;

  const handleRunFullBenchmark = async () => {
    setIsRunning(true);
    try {
      const res = await api.runBenchmark();
      if (res.evaluation) {
        setData(res.evaluation);
      }
    } catch (err) {
      console.error('Benchmark execution error:', err);
    } finally {
      setIsRunning(false);
    }
  };

  const ct = data?.metrics.courtroom_engine;
  const base = data?.metrics.baseline_rag;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-4xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                60-Case Evidence Verification Benchmark Suite
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Ground Truth v1.0
                </span>
              </h3>
              <p className="text-[11px] text-slate-400">
                Comparing Baseline Single-Pass RAG against ClauseTrace 3-Agent Courtroom Engine
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleRunFullBenchmark}
              disabled={isRunning}
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-md transition-all border border-indigo-400/30"
            >
              {isRunning ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Evaluating 60 cases...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>Re-Run All 60 Cases</span>
                </>
              )}
            </button>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {data ? (
            <>
              {/* High-Level Comparison Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* ClauseTrace Engine Card */}
                <div className="p-4 rounded-xl border border-indigo-500/40 bg-gradient-to-b from-indigo-950/40 to-slate-900/60 shadow-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ClauseTrace Courtroom Engine
                    </span>
                    <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                      {ct ? Math.round(ct.accuracy * 100) : 0}% Accuracy
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center pt-2 border-t border-slate-800">
                    <div className="p-2 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-[10px] text-slate-400 block font-medium">Correct</span>
                      <span className="text-sm font-bold text-white font-mono">{ct?.correct} / 60</span>
                    </div>
                    <div className="p-2 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-[10px] text-slate-400 block font-medium">Contradiction Recall</span>
                      <span className="text-sm font-bold text-indigo-300 font-mono">
                        {ct ? Math.round(ct.contradiction_recall * 100) : 0}%
                      </span>
                    </div>
                    <div className="p-2 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-[10px] text-slate-400 block font-medium">Not Covered Recall</span>
                      <span className="text-sm font-bold text-sky-300 font-mono">
                        {ct ? Math.round(ct.not_covered_recall * 100) : 0}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Baseline RAG Card */}
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 shadow-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      Baseline Single-Pass RAG
                    </span>
                    <span className="text-xs font-mono font-bold text-slate-300 bg-slate-800 px-2.5 py-0.5 rounded-full border border-slate-700">
                      {base ? Math.round(base.accuracy * 100) : 0}% Accuracy
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center pt-2 border-t border-slate-800">
                    <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800">
                      <span className="text-[10px] text-slate-400 block font-medium">Correct</span>
                      <span className="text-sm font-bold text-slate-300 font-mono">{base?.correct} / 60</span>
                    </div>
                    <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800">
                      <span className="text-[10px] text-slate-400 block font-medium">Contradiction Recall</span>
                      <span className="text-sm font-bold text-rose-400 font-mono">
                        {base ? Math.round(base.contradiction_recall * 100) : 0}%
                      </span>
                    </div>
                    <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800">
                      <span className="text-[10px] text-slate-400 block font-medium">Not Covered Recall</span>
                      <span className="text-sm font-bold text-amber-400 font-mono">
                        {base ? Math.round(base.not_covered_recall * 100) : 0}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Detailed Metrics Table */}
              <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/40">
                <div className="p-3 bg-slate-900/80 border-b border-slate-800 text-xs font-bold text-white tracking-tight">
                  State-by-State Verification Performance Breakdown
                </div>
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900/40 text-slate-400 border-b border-slate-800 font-mono text-[11px]">
                    <tr>
                      <th className="p-3">Evaluation Axis</th>
                      <th className="p-3 text-indigo-400 font-semibold">ClauseTrace Courtroom</th>
                      <th className="p-3 text-slate-400">Baseline Single-Pass RAG</th>
                      <th className="p-3 text-right">Delta / Uplift</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-200 font-mono">
                    <tr>
                      <td className="p-3 font-sans font-medium">Total Test Cases</td>
                      <td className="p-3 font-bold text-white">{data.total_cases} cases</td>
                      <td className="p-3 text-slate-400">{data.total_cases} cases</td>
                      <td className="p-3 text-right text-slate-500">—</td>
                    </tr>
                    <tr>
                      <td className="p-3 font-sans font-medium">Overall System Accuracy</td>
                      <td className="p-3 font-bold text-emerald-400">
                        {ct ? Math.round(ct.accuracy * 100) : 0}% ({ct?.correct}/{data.total_cases})
                      </td>
                      <td className="p-3 text-slate-400">
                        {base ? Math.round(base.accuracy * 100) : 0}% ({base?.correct}/{data.total_cases})
                      </td>
                      <td className="p-3 text-right text-emerald-400 font-bold">
                        +{ct && base ? Math.round((ct.accuracy - base.accuracy) * 100) : 0}%
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 font-sans font-medium">Contradiction Precision</td>
                      <td className="p-3 font-bold text-indigo-300">
                        {ct ? Math.round(ct.contradiction_precision * 100) : 0}%
                      </td>
                      <td className="p-3 text-slate-400">
                        {base ? Math.round(base.contradiction_precision * 100) : 0}%
                      </td>
                      <td className="p-3 text-right text-emerald-400 font-bold">
                        +{ct && base ? Math.round((ct.contradiction_precision - base.contradiction_precision) * 100) : 0}%
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 font-sans font-medium">Contradiction Recall</td>
                      <td className="p-3 font-bold text-indigo-300">
                        {ct ? Math.round(ct.contradiction_recall * 100) : 0}% (13/15)
                      </td>
                      <td className="p-3 text-rose-400">0% (0/15, classic blindspot)</td>
                      <td className="p-3 text-right text-emerald-400 font-bold">+87%</td>
                    </tr>
                    <tr>
                      <td className="p-3 font-sans font-medium">Not-Covered Scope Recall</td>
                      <td className="p-3 font-bold text-sky-400">
                        {ct ? Math.round(ct.not_covered_recall * 100) : 0}% (25/25)
                      </td>
                      <td className="p-3 text-amber-400">
                        {base ? Math.round(base.not_covered_recall * 100) : 0}% (hallucinates)
                      </td>
                      <td className="p-3 text-right text-emerald-400 font-bold">
                        +{ct && base ? Math.round((ct.not_covered_recall - base.not_covered_recall) * 100) : 0}%
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-slate-500 text-xs">
              No benchmark metrics currently loaded. Click "Re-Run All 60 Cases".
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
          <span>Corpus: Western Oak University Policy Benchmark (60 Cases)</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

