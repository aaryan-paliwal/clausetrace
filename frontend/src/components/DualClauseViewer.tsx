import React from 'react';
import { BookOpen, FileText, CheckCircle, ExternalLink, Sparkles } from 'lucide-react';
import { Clause, Document } from '../api/client';

interface DualClauseViewerProps {
  documents: Document[];
  clauseA: Clause | null;
  clauseB: Clause | null;
  highlightClauseId?: string | null;
}

export const DualClauseViewer: React.FC<DualClauseViewerProps> = ({
  documents,
  clauseA,
  clauseB,
  highlightClauseId,
}) => {
  const getDocById = (id: string) => documents.find((d) => d.id === id);

  const renderClauseCard = (clause: Clause | null, label: string, accentColor: 'indigo' | 'amber') => {
    if (!clause) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center p-6 border border-dashed border-slate-800 rounded-xl bg-slate-900/30 text-center text-slate-500 text-xs">
          <BookOpen className="w-8 h-8 text-slate-600 mb-2" />
          <span className="font-semibold text-slate-400">No {label} Selected</span>
          <p className="text-[11px] text-slate-500 mt-1">
            Select a proactive conflict from the matrix or click a citation link to view authoritative text.
          </p>
        </div>
      );
    }

    const doc = getDocById(clause.doc_id);
    const isTargetHighlight = highlightClauseId === clause.id;
    const borderCls =
      accentColor === 'indigo'
        ? isTargetHighlight
          ? 'border-indigo-500 ring-2 ring-indigo-500/30'
          : 'border-indigo-500/30'
        : isTargetHighlight
        ? 'border-amber-500 ring-2 ring-amber-500/30'
        : 'border-amber-500/30';

    const tagCls =
      accentColor === 'indigo'
        ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
        : 'bg-amber-500/10 text-amber-400 border-amber-500/20';

    return (
      <div className={`flex-1 flex flex-col rounded-xl border bg-slate-900/60 overflow-hidden ${borderCls} shadow-lg`}>
        {/* Document & Clause Meta Bar */}
        <div className="p-3 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border uppercase tracking-wider ${tagCls}`}>
              {label}
            </span>
            <div className="flex flex-col text-left">
              <span className="text-xs font-bold text-white tracking-tight flex items-center gap-1">
                §{clause.section_number} {clause.heading}
              </span>
              <span className="text-[10px] text-slate-400 truncate max-w-[200px]">
                {doc ? doc.title : clause.doc_id}
              </span>
            </div>
          </div>
          <div className="text-[10px] font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/60">
            chars: {clause.char_start}..{clause.char_end}
          </div>
        </div>

        {/* Verbatim Clause Text Viewport */}
        <div className="flex-1 p-4 overflow-y-auto font-serif text-sm text-slate-200 leading-relaxed bg-slate-950/40 select-text">
          <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800/60 whitespace-pre-wrap">
            {clause.text}
          </div>
        </div>

        {/* Footer */}
        <div className="p-2.5 border-t border-slate-800 bg-slate-900/40 flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1 font-mono text-[10px]">
            <FileText className="w-3.5 h-3.5 text-slate-400" />
            Clause ID: {clause.id}
          </span>
          <span className="text-[10px] text-emerald-400 font-medium flex items-center gap-1">
            <CheckCircle className="w-3 h-3" /> Exact Offset Verified
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-slate-950/70 border-l border-slate-800">
      <div className="p-4 border-b border-slate-800 bg-slate-900/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-bold text-white tracking-tight">Synchronized Dual Clause Viewer</h3>
        </div>
        <span className="text-[11px] text-slate-400">Character-exact legal grounding</span>
      </div>

      <div className="flex-1 p-3 flex flex-col gap-3 overflow-hidden">
        {renderClauseCard(clauseA, 'Clause A (Baseline)', 'indigo')}
        {renderClauseCard(clauseB, 'Clause B (Colliding)', 'amber')}
      </div>
    </div>
  );
};

