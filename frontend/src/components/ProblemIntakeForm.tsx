import React, { useRef, useState } from 'react';
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  ArrowRight, 
  ShieldCheck, 
  Sparkles, 
  HelpCircle,
  AlertCircle,
  FileSearch,
  Database,
  Loader2
} from 'lucide-react';
import { PersonaId, ProblemTask, PERSONAS } from '../data/personas';
import { Workspace } from '../api/client';

interface ProblemIntakeFormProps {
  personaId: PersonaId;
  task: ProblemTask;
  workspaces: Workspace[];
  activeWorkspaceId: string;
  onSelectWorkspace: (id: string) => void;
  onUploadDocument: (file: File) => Promise<void>;
  onProceedToAnalysis: (query: string, customContext?: string) => void;
}

export const ProblemIntakeForm: React.FC<ProblemIntakeFormProps> = ({
  personaId,
  task,
  workspaces,
  activeWorkspaceId,
  onSelectWorkspace,
  onUploadDocument,
  onProceedToAnalysis,
}) => {
  const persona = PERSONAS[personaId];
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [query, setQuery] = useState(task.suggestedPromptTemplate || '');
  const [contextNotes, setContextNotes] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Sync template if task changes
  React.useEffect(() => {
    if (task.suggestedPromptTemplate) {
      setQuery(task.suggestedPromptTemplate);
    }
  }, [task.id]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setUploadError(null);
    setIsUploading(true);

    try {
      await onUploadDocument(file);
      setUploadSuccess(true);
    } catch (err) {
      console.error('Document intake upload failed:', err);
      setUploadError(err instanceof Error ? err.message : String(err));
      setSelectedFile(null);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onProceedToAnalysis(query.trim(), contextNotes.trim());
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-mono font-bold">3</span>
            Document & Legal Problem Intake
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Attach your agreement or select a pre-indexed corpus, specify your legal question, and enter context. No personal identifying information is stored.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl">
        {/* Left Column (Col 1-5): Document Source & Workspace */}
        <div className="lg:col-span-5 space-y-4 pr-0 lg:pr-4 border-b lg:border-b-0 lg:border-r border-slate-800/80 pb-4 lg:pb-0">
          <div>
            <label className="text-xs font-bold text-slate-200 block mb-1.5 flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              Target Legal Workspace Corpus
            </label>
            <select
              value={activeWorkspaceId}
              onChange={(e) => onSelectWorkspace(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
            >
              {workspaces.map((ws) => (
                <option key={ws.id} value={ws.id}>
                  {ws.name} ({ws.pack_name})
                </option>
              ))}
            </select>
            <p className="text-[10px] text-slate-400 mt-1">
              Corpus includes pre-indexed clauses, deontic rules, and conflict matrices.
            </p>
          </div>

          {/* Document Upload Box */}
          <div>
            <label className="text-xs font-bold text-slate-200 block mb-1.5 flex items-center gap-1.5">
              <Upload className="w-3.5 h-3.5 text-indigo-400" />
              Upload Agreement / Document (Optional)
            </label>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".md,.txt,.pdf"
              className="hidden"
            />

            <div
              onClick={() => !isUploading && fileInputRef.current?.click()}
              className={`p-4 rounded-xl border border-dashed transition-all cursor-pointer text-center flex flex-col items-center justify-center ${
                uploadSuccess
                  ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                  : uploadError
                  ? 'bg-rose-950/20 border-rose-500/40 text-rose-300'
                  : 'bg-slate-950/60 border-slate-700/80 hover:bg-slate-950 hover:border-indigo-500/50 text-slate-400'
              }`}
            >
              {isUploading ? (
                <div className="py-2 flex flex-col items-center gap-2">
                  <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
                  <span className="text-xs font-semibold text-slate-200">
                    Parsing clauses & compiling deontic graph...
                  </span>
                </div>
              ) : uploadSuccess ? (
                <div className="py-1 flex flex-col items-center gap-1.5">
                  <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  <span className="text-xs font-bold text-slate-200">
                    {selectedFile?.name || 'Document parsed successfully'}
                  </span>
                  <span className="text-[10px] text-emerald-400">
                    Integrated into active workspace deontic graph.
                  </span>
                </div>
              ) : (
                <div className="py-1 flex flex-col items-center gap-1.5">
                  <FileText className="w-6 h-6 text-slate-500 group-hover:text-indigo-400" />
                  <span className="text-xs font-bold text-slate-300">
                    Attach .md, .txt, or .pdf
                  </span>
                  <span className="text-[10px] text-slate-400 max-w-xs">
                    Exact character offsets are computed with zero external data sharing.
                  </span>
                </div>
              )}
            </div>

            {uploadError && (
              <p className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {uploadError}
              </p>
            )}
          </div>

          {/* Privacy & Grounding Guardrail Badge */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-[11px] text-slate-400 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-slate-300 text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Evidence-Grounded Legal Engine
            </div>
            <p className="leading-relaxed">
              Every finding must cite exact clause spans. The engine never hallucinates rights outside the governing corpus.
            </p>
          </div>
        </div>

        {/* Right Column (Col 6-12): Legal Question & Submission Form */}
        <div className="lg:col-span-7 flex flex-col justify-between space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4 flex-1 flex flex-col justify-between">
            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-slate-200 block mb-1.5 flex items-center justify-between">
                  <span>Describe the Legal Premise or Conflict to Examine</span>
                  <span className="text-[10px] font-normal text-slate-400">Required</span>
                </label>
                <textarea
                  rows={3}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g. Can the company immediately terminate employment without notice or cure upon a missed milestone?"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 leading-relaxed font-sans"
                  required
                />
              </div>

              {/* Preset Query Chips */}
              {task.recommendedQueries.length > 0 && (
                <div>
                  <span className="text-[11px] text-slate-400 block mb-1.5">
                    Recommended queries for this task:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {task.recommendedQueries.map((rq, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setQuery(rq)}
                        className={`text-left text-[11px] px-2.5 py-1 rounded-lg border transition-all ${
                          query === rq
                            ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-300 font-medium'
                            : 'bg-slate-950/80 hover:bg-slate-800 border-slate-800 text-slate-300'
                        }`}
                      >
                        {rq}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Context Notes (Optional) */}
              <div>
                <label className="text-xs font-bold text-slate-200 block mb-1 flex items-center justify-between">
                  <span>Specific Factual Context / Role Details (Optional)</span>
                  <span className="text-[10px] font-normal text-slate-400">Contextualizes agent arguments</span>
                </label>
                <input
                  type="text"
                  value={contextNotes}
                  onChange={(e) => setContextNotes(e.target.value)}
                  placeholder="e.g. Executive employee under 2024 offer schedule with claimed pre-existing open source repo"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-sans"
                />
              </div>
            </div>

            {/* Launch Action */}
            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
              <span className="text-[11px] text-slate-400 font-medium">
                Launches into 3-Pane Adversarial Courtroom
              </span>

              <button
                type="submit"
                disabled={!query.trim()}
                className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 active:from-indigo-700 active:to-indigo-600 disabled:from-slate-800 disabled:to-slate-800 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-600/20 transition-all border border-indigo-400/30 cursor-pointer disabled:cursor-not-allowed"
              >
                <span>Launch Courtroom Examination</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
