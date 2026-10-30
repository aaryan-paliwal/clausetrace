import React, { useState } from 'react';
import {
  Send,
  Mic,
  Scale,
  Shield,
  AlertTriangle,
  CheckCircle,
  FileSearch,
  Sparkles,
  Info,
  Clock,
  Layers
} from 'lucide-react';
import { AgentBrief, CourtroomVerdict } from '../api/client';

interface CourtroomStreamProps {
  onAsk: (query: string) => void;
  isLoading: boolean;
  verdict: CourtroomVerdict | null;
  advocateBrief: AgentBrief | null;
  skepticBrief: AgentBrief | null;
  statusMessage: string | null;
  onCitationClick?: (clauseId: string) => void;
}

export const CourtroomStream: React.FC<CourtroomStreamProps> = ({
  onAsk,
  isLoading,
  verdict,
  advocateBrief,
  skepticBrief,
  statusMessage,
  onCitationClick,
}) => {
  const [query, setQuery] = useState('');

  const sampleQueries = [
    'Can the company immediately terminate employment without notice or cure?',
    'What defines a Critical Deliverable Breach that triggers termination?',
    'What is the base salary of the Executive?',
    'What is the maximum number of credits an undergraduate student can register for in a regular semester?',
    'Can employees bring dogs and pets into the office cafeteria?',
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onAsk(query.trim());
    }
  };

  const handleSimulateVoice = () => {
    const randomQuery = sampleQueries[Math.floor(Math.random() * sampleQueries.length)];
    setQuery(randomQuery);
  };

  const getVerdictBanner = (v: CourtroomVerdict) => {
    switch (v.verdict_state) {
      case 'CONTRADICTION':
        return {
          bg: 'from-rose-950/80 to-slate-950 border-rose-500/40',
          text: 'text-rose-400',
          icon: <AlertTriangle className="w-5 h-5 text-rose-400" />,
          title: 'Direct Cross-Document Contradiction Detected',
          badge: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
        };
      case 'EXPLOITABLE_LOOPHOLE':
        return {
          bg: 'from-amber-950/80 to-slate-950 border-amber-500/40',
          text: 'text-amber-400',
          icon: <AlertTriangle className="w-5 h-5 text-amber-400" />,
          title: 'Exploitable Ambiguity / Loophole Exception',
          badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
        };
      case 'NOT_COVERED':
        return {
          bg: 'from-slate-900 to-slate-950 border-slate-700',
          text: 'text-slate-400',
          icon: <Info className="w-5 h-5 text-slate-400" />,
          title: 'Subject Matter Not Covered In Governing Corpus',
          badge: 'bg-slate-800 text-slate-300 border-slate-700',
        };
      case 'ANSWERABLE':
      default:
        return {
          bg: 'from-emerald-950/80 to-slate-950 border-emerald-500/40',
          text: 'text-emerald-400',
          icon: <CheckCircle className="w-5 h-5 text-emerald-400" />,
          title: 'Affirmative Deontic Authority Verified',
          badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
        };
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950">
      {/* Query Bar */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/40">
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a premise, legal inquiry, or cross-clause conflict check..."
              disabled={isLoading}
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all pr-10"
            />
            <button
              type="button"
              onClick={handleSimulateVoice}
              title="Sample random legal premise"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-indigo-400 transition-colors"
            >
              <Mic className="w-4 h-4" />
            </button>
          </div>

          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-600/20 transition-all border border-indigo-400/30"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Adjudicating...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Examine</span>
              </>
            )}
          </button>
        </form>

        {/* Query Presets Chips */}
        <div className="flex items-center gap-1.5 mt-2.5 overflow-x-auto pb-1 text-[11px] text-slate-400">
          <span className="shrink-0 text-slate-500">Presets:</span>
          {sampleQueries.slice(0, 3).map((sq, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(sq);
                onAsk(sq);
              }}
              className="shrink-0 bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 px-2.5 py-1 rounded-lg text-slate-300 transition-all truncate max-w-xs"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Main Examination Canvas */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Real-time Status Notification */}
        {statusMessage && (
          <div className="p-3 bg-indigo-950/40 border border-indigo-500/30 rounded-xl text-xs text-indigo-300 flex items-center gap-2 animate-pulse">
            <Clock className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>{statusMessage}</span>
          </div>
        )}

        {/* Empty state */}
        {!verdict && !advocateBrief && !skepticBrief && !isLoading && (
          <div className="flex flex-col items-center justify-center h-80 text-center text-slate-400 p-6">
            <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-4">
              <Scale className="w-8 h-8 text-indigo-400" />
            </div>
            <h3 className="text-base font-bold text-slate-200 mb-1">
              3-Agent Adversarial Courtroom Console
            </h3>
            <p className="text-xs text-slate-400 max-w-md leading-relaxed mb-4">
              Enter any inquiry or premise above. The engine retrieves deontic rules, deploys The Advocate to construct the affirmative case, The Skeptic to cross-examine conflicts and loopholes, and The Adjudicator to issue an authoritative ruling.
            </p>
          </div>
        )}

        {/* 1. Presiding Adjudicator Verdict Banner */}
        {verdict && (
          <div
            className={`p-4 rounded-xl border bg-gradient-to-b ${getVerdictBanner(verdict).bg} shadow-xl`}
          >
            <div className="flex items-start justify-between gap-4 mb-2">
              <div className="flex items-center gap-2">
                {getVerdictBanner(verdict).icon}
                <h3 className="text-sm font-bold text-white tracking-tight">
                  {getVerdictBanner(verdict).title}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border uppercase tracking-wider ${getVerdictBanner(verdict).badge}`}
                >
                  {verdict.verdict_state}
                </span>
                <span className="text-xs font-mono font-semibold text-slate-300 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-700">
                  {Math.round(verdict.confidence_score * 100)}% Conf
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-200 leading-relaxed font-sans mb-3 pl-7">
              {verdict.executive_ruling}
            </p>

            {/* Verified Citations Pills */}
            {verdict.verified_citations.length > 0 && (
              <div className="pl-7 pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                  <FileSearch className="w-3.5 h-3.5 text-indigo-400" />
                  Verified Citations:
                </span>
                {verdict.verified_citations.map((cite, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onCitationClick && onCitationClick(cite.clause_id)}
                    className="text-[11px] font-mono bg-slate-900 hover:bg-indigo-950/60 text-slate-300 hover:text-indigo-300 border border-slate-700 hover:border-indigo-500/50 px-2 py-0.5 rounded transition-all"
                  >
                    §{cite.section_number} ({cite.doc_title.slice(0, 16)}...)
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 2. Adversarial Dual Briefs (Advocate vs Skeptic) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* The Advocate Card */}
          {(advocateBrief || isLoading) && (
            <div className="p-4 rounded-xl border border-sky-500/30 bg-sky-950/20 backdrop-blur-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-sky-400" />
                    <h4 className="text-xs font-bold text-sky-300 uppercase tracking-wider">
                      The Advocate (Affirmative)
                    </h4>
                  </div>
                  <span className="text-[10px] font-mono text-sky-400/80 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                    Pro-Permit
                  </span>
                </div>

                {advocateBrief ? (
                  <>
                    <p className="text-xs font-medium text-slate-200 mb-2 leading-relaxed">
                      "{advocateBrief.thesis}"
                    </p>
                    <ul className="space-y-1.5 text-[11px] text-slate-300 list-disc list-inside">
                      {advocateBrief.arguments.map((arg, idx) => (
                        <li key={idx} className="leading-relaxed">
                          {arg}
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <div className="space-y-2 py-4 animate-pulse">
                    <div className="h-3 bg-sky-500/20 rounded w-3/4"></div>
                    <div className="h-3 bg-sky-500/20 rounded w-5/6"></div>
                    <div className="h-3 bg-sky-500/20 rounded w-1/2"></div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* The Skeptic Card */}
          {(skepticBrief || isLoading) && (
            <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-950/20 backdrop-blur-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Scale className="w-4 h-4 text-amber-400" />
                    <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider">
                      The Skeptic (Adversarial)
                    </h4>
                  </div>
                  <span className="text-[10px] font-mono text-amber-400/80 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                    Cross-Exam
                  </span>
                </div>

                {skepticBrief ? (
                  <>
                    <p className="text-xs font-medium text-slate-200 mb-2 leading-relaxed">
                      "{skepticBrief.thesis}"
                    </p>
                    <ul className="space-y-1.5 text-[11px] text-slate-300 list-disc list-inside mb-2">
                      {skepticBrief.arguments.map((arg, idx) => (
                        <li key={idx} className="leading-relaxed">
                          {arg}
                        </li>
                      ))}
                    </ul>
                    {skepticBrief.flagged_gaps_or_undefined_terms.length > 0 && (
                      <div className="text-[10px] text-amber-300/90 bg-amber-500/10 border border-amber-500/20 rounded p-2">
                        <span className="font-semibold">Flagged Exceptions / Loopholes:</span>{' '}
                        {skepticBrief.flagged_gaps_or_undefined_terms.join(', ')}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="space-y-2 py-4 animate-pulse">
                    <div className="h-3 bg-amber-500/20 rounded w-3/4"></div>
                    <div className="h-3 bg-amber-500/20 rounded w-5/6"></div>
                    <div className="h-3 bg-amber-500/20 rounded w-1/2"></div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
