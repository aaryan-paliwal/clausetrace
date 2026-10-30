import React from 'react';
import { ShieldCheck, BarChart3, Database, Cpu, Sparkles } from 'lucide-react';
import { Workspace } from '../api/client';

interface NavbarProps {
  workspaces: Workspace[];
  activeWorkspaceId: string;
  onSelectWorkspace: (id: string) => void;
  onOpenBenchmark: () => void;
  metrics?: {
    active_conflicts: number;
    critical_count: number;
    total_rules: number;
  };
}

export const Navbar: React.FC<NavbarProps> = ({
  workspaces,
  activeWorkspaceId,
  onSelectWorkspace,
  onOpenBenchmark,
  metrics,
}) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-sky-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              ClauseTrace
              <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
                v1.0 Pro
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 font-medium">
              Evidence-Grounded Policy & Contract Verification
            </p>
          </div>
        </div>

        {/* Workspace Selector */}
        <div className="flex items-center space-x-2 pl-4 border-l border-slate-800">
          <Database className="w-4 h-4 text-slate-400" />
          <select
            value={activeWorkspaceId}
            onChange={(e) => onSelectWorkspace(e.target.value)}
            className="bg-slate-900 border border-slate-700/80 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer font-medium hover:border-slate-600 transition-colors"
          >
            {workspaces.map((ws) => (
              <option key={ws.id} value={ws.id}>
                {ws.name} ({ws.pack_name})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Proactive Conflict Badges */}
        {metrics && (
          <div className="hidden lg:flex items-center space-x-2 bg-slate-900/60 border border-slate-800 rounded-lg px-3 py-1">
            <span className="text-xs text-slate-400 font-medium">Active Graph:</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
              {metrics.active_conflicts} Conflicts
            </span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              {metrics.total_rules} Rules
            </span>
          </div>
        )}

        {/* Active Meta Llama Model Badge */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5">
          <Cpu className="w-4 h-4 text-indigo-400 animate-pulse" />
          <div className="flex flex-col text-left">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Engine Engine</span>
            <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
              Llama 3.3 70B
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 ring-2 ring-emerald-500/20"></span>
            </span>
          </div>
        </div>

        {/* Benchmark Trigger Button */}
        <button
          onClick={onOpenBenchmark}
          className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all border border-indigo-400/30"
        >
          <BarChart3 className="w-4 h-4" />
          <span>60-Case Benchmark</span>
        </button>
      </div>
    </header>
  );
};
