import React from 'react';
import { 
  FileSearch, 
  HelpCircle, 
  AlertTriangle, 
  ShieldCheck, 
  FileText, 
  CheckCircle2, 
  Clock, 
  Lock,
  ArrowRight,
  ExternalLink,
  Sparkles
} from 'lucide-react';
import { PersonaId, ProblemTask, PERSONA_TASKS, PERSONAS } from '../data/personas';

interface TaskSelectorProps {
  personaId: PersonaId;
  selectedTaskId: string;
  onSelectTask: (task: ProblemTask) => void;
}

const TASK_ICONS: Record<string, React.ReactNode> = {
  emp_review_contract: <FileSearch className="w-4 h-4 text-sky-400" />,
  emp_understand_clause: <HelpCircle className="w-4 h-4 text-sky-400" />,
  emp_find_unfair_terms: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  emp_check_compliance: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
  emp_statutory_violations: <Lock className="w-4 h-4 text-slate-500" />,
  emp_draft_representation: <FileText className="w-4 h-4 text-slate-500" />,

  fnd_review_contract: <FileSearch className="w-4 h-4 text-indigo-400" />,
  fnd_understand_clause: <HelpCircle className="w-4 h-4 text-indigo-400" />,
  fnd_find_unfair_terms: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  fnd_check_compliance: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
  fnd_remedies: <Lock className="w-4 h-4 text-slate-500" />,
  fnd_draft_representation: <FileText className="w-4 h-4 text-slate-500" />,

  hr_review_contract: <FileSearch className="w-4 h-4 text-violet-400" />,
  hr_understand_clause: <HelpCircle className="w-4 h-4 text-violet-400" />,
  hr_find_unfair_terms: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  hr_check_compliance: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
  hr_statutory_violations: <Lock className="w-4 h-4 text-slate-500" />,
  hr_draft_representation: <FileText className="w-4 h-4 text-slate-500" />,

  biz_review_contract: <FileSearch className="w-4 h-4 text-amber-400" />,
  biz_understand_clause: <HelpCircle className="w-4 h-4 text-amber-400" />,
  biz_find_unfair_terms: <AlertTriangle className="w-4 h-4 text-rose-400" />,
  biz_check_compliance: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
  biz_remedies: <Lock className="w-4 h-4 text-slate-500" />,
  biz_draft_representation: <FileText className="w-4 h-4 text-slate-500" />,

  ind_review_contract: <FileSearch className="w-4 h-4 text-emerald-400" />,
  ind_understand_clause: <HelpCircle className="w-4 h-4 text-emerald-400" />,
  ind_find_unfair_terms: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  ind_check_compliance: <ShieldCheck className="w-4 h-4 text-sky-400" />,
  ind_statutory_violations: <Lock className="w-4 h-4 text-slate-500" />,
  ind_draft_representation: <FileText className="w-4 h-4 text-slate-500" />,
};

export const TaskSelector: React.FC<TaskSelectorProps> = ({
  personaId,
  selectedTaskId,
  onSelectTask,
}) => {
  const tasks = PERSONA_TASKS[personaId] || [];
  const persona = PERSONAS[personaId];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-mono font-bold">2</span>
            Select Your Legal Objective ({persona.title})
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Choose what you need to solve. Only live, evidence-grounded capabilities are executable; forthcoming features are clearly transparent.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {tasks.map((task) => {
          const isSelected = selectedTaskId === task.id;
          const isAvailable = task.status === 'available';

          return (
            <button
              key={task.id}
              type="button"
              disabled={!isAvailable}
              onClick={() => isAvailable && onSelectTask(task)}
              className={`p-3.5 rounded-xl border text-left transition-all relative flex flex-col justify-between ${
                !isAvailable
                  ? 'bg-slate-950/40 border-slate-900 opacity-60 cursor-not-allowed'
                  : isSelected
                  ? 'bg-slate-900 border-2 border-indigo-500/80 shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/20'
                  : 'bg-slate-900/60 border-slate-800 hover:bg-slate-900/90 hover:border-slate-700 cursor-pointer'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="w-7 h-7 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-center">
                    {TASK_ICONS[task.id] || <FileSearch className="w-4 h-4 text-slate-400" />}
                  </div>

                  {isAvailable ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      Available Now
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-400/80 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
                      <Clock className="w-3 h-3 text-amber-400" />
                      Forthcoming
                    </span>
                  )}
                </div>

                <div className="text-xs font-bold text-white tracking-tight mb-1 flex items-center gap-1.5">
                  {task.title}
                  {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 shrink-0" />}
                </div>

                <p className="text-[11px] text-slate-400 leading-relaxed mb-2">
                  {task.description}
                </p>

                {!isAvailable && task.statusNote && (
                  <div className="text-[10px] text-amber-300/80 bg-amber-950/30 border border-amber-500/20 rounded p-2 mt-2 leading-relaxed">
                    {task.statusNote}
                  </div>
                )}
              </div>

              {isAvailable && (
                <div className="pt-2 mt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400">
                  <span className="text-indigo-400 font-medium flex items-center gap-1">
                    <Sparkles className="w-3 h-3" />
                    3-Agent Verified
                  </span>
                  <span className="font-mono text-slate-400">{task.recommendedQueries.length} presets</span>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
