import React, { useRef, useState } from 'react';
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  ArrowRight, 
  ShieldCheck, 
  Sparkles, 
  AlertCircle, 
  Database, 
  Loader2,
  FileCheck2,
  Info
} from 'lucide-react';
import { PersonaId, ProblemTask, PERSONAS } from '../data/personas';
import { Workspace, DocumentUploadResponse } from '../api/client';

interface ProblemIntakeFormProps {
  personaId: PersonaId;
  task: ProblemTask;
  workspaces: Workspace[];
  activeWorkspaceId: string;
  hasUserUploadedDocument: boolean;
  onSelectWorkspace: (id: string) => void;
  onUploadDocument: (file: File) => Promise<DocumentUploadResponse>;
  onProceedToAnalysis: (query: string, customContext?: string) => void;
}

export type UploadStage = 'idle' | 'selected' | 'uploading' | 'parsed' | 'error';

export const ProblemIntakeForm: React.FC<ProblemIntakeFormProps> = ({
  personaId,
  task,
  workspaces,
  activeWorkspaceId,
  hasUserUploadedDocument,
  onSelectWorkspace,
  onUploadDocument,
  onProceedToAnalysis,
}) => {
  const persona = PERSONAS[personaId];
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [query, setQuery] = useState(task.suggestedPromptTemplate || '');
  const [contextNotes, setContextNotes] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  // Explicit upload lifecycle states
  const [uploadStage, setUploadStage] = useState<UploadStage>('idle');
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);
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
    setUploadStage('selected');
    setUploadError(null);
    setUploadResult(null);

    // Progress into upload & indexing
    setUploadStage('uploading');
    try {
      const response = await onUploadDocument(file);
      // Only set parsed/indexed when backend confirms success and returns clauses
      if (response && response.status === 'success') {
        setUploadResult(response);
        setUploadStage('parsed');
      } else {
        throw new Error('Server received file but clause parsing could not be verified.');
      }
    } catch (err) {
      console.error('Document intake upload failed:', err);
      setUploadError(err instanceof Error ? err.message : String(err));
      setUploadStage('error');
    } finally {
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
            Attach your agreement or choose a pre-loaded reference document set. Enter your question and any relevant factual background.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl">
        {/* Left Column (Col 1-5): Document Source & Workspace Reference Material */}
        <div className="lg:col-span-5 space-y-4 pr-0 lg:pr-4 border-b lg:border-b-0 lg:border-r border-slate-800/80 pb-4 lg:pb-0">
          <div>
            <label className="text-xs font-bold text-slate-200 block mb-1.5 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-indigo-400" />
                Active Document Collection
              </span>
              {hasUserUploadedDocument && (
                <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                  Contains Your Uploads
                </span>
              )}
            </label>
            <select
              value={activeWorkspaceId}
              onChange={(e) => onSelectWorkspace(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors"
            >
              {workspaces.map((ws) => (
                <option key={ws.id} value={ws.id}>
                  {ws.name} ({ws.pack_name === 'startup_founder_legal' ? 'Commercial & Founder Agreements' : 'Institutional & Academic Policies'})
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
              A document collection groups related agreements and policies so the engine can check clauses across documents for inconsistencies and conflicting obligations.
            </p>
          </div>

          {/* Document Upload Box with verified lifecycle */}
          <div>
            <label className="text-xs font-bold text-slate-200 block mb-1.5 flex items-center gap-1.5">
              <Upload className="w-3.5 h-3.5 text-indigo-400" />
              Upload an Agreement or Policy (.md, .txt, .pdf)
            </label>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".md,.txt,.pdf"
              className="hidden"
            />

            <div
              onClick={() => uploadStage !== 'uploading' && fileInputRef.current?.click()}
              className={`p-4 rounded-xl border border-dashed transition-all cursor-pointer text-center flex flex-col items-center justify-center ${
                uploadStage === 'parsed'
                  ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                  : uploadStage === 'uploading'
                  ? 'bg-indigo-950/20 border-indigo-500/40 text-indigo-300'
                  : uploadStage === 'error'
                  ? 'bg-rose-950/20 border-rose-500/40 text-rose-300'
                  : 'bg-slate-950/60 border-slate-700/80 hover:bg-slate-950 hover:border-indigo-500/50 text-slate-400'
              }`}
            >
              {uploadStage === 'uploading' ? (
                <div className="py-2 flex flex-col items-center gap-2">
                  <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
                  <span className="text-xs font-semibold text-slate-200">
                    Uploading & parsing clauses into document graph...
                  </span>
                  <span className="text-[10px] text-slate-400">
                    File: {selectedFile?.name}
                  </span>
                </div>
              ) : uploadStage === 'parsed' && uploadResult ? (
                <div className="py-1 flex flex-col items-center gap-1.5">
                  <FileCheck2 className="w-6 h-6 text-emerald-400" />
                  <span className="text-xs font-bold text-slate-200">
                    {uploadResult.title}
                  </span>
                  <span className="text-[10px] text-emerald-400 font-medium">
                    Verified: {uploadResult.clauses_created} clauses parsed and added to active collection.
                  </span>
                  <span className="text-[10px] text-slate-400 underline mt-1">
                    Click to upload another document
                  </span>
                </div>
              ) : uploadStage === 'error' ? (
                <div className="py-1 flex flex-col items-center gap-1.5">
                  <AlertCircle className="w-6 h-6 text-rose-400" />
                  <span className="text-xs font-bold text-rose-300">
                    Upload or Processing Failed
                  </span>
                  <span className="text-[10px] text-slate-400">
                    Click to try selecting the file again.
                  </span>
                </div>
              ) : (
                <div className="py-1 flex flex-col items-center gap-1.5">
                  <FileText className="w-6 h-6 text-slate-500 group-hover:text-indigo-400" />
                  <span className="text-xs font-bold text-slate-300">
                    Click to select agreement or policy
                  </span>
                  <span className="text-[10px] text-slate-400 max-w-xs">
                    Uploaded text is processed into numbered clauses for structural conflict analysis.
                  </span>
                </div>
              )}
            </div>

            {uploadError && (
              <p className="text-[11px] text-rose-400 mt-1.5 flex items-start gap-1">
                <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <span>{uploadError}</span>
              </p>
            )}
          </div>

          {/* Transparent Scope Note */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-[11px] text-slate-400 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-slate-300 text-xs">
              <Info className="w-3.5 h-3.5 text-indigo-400" />
              Scope of Analysis
            </div>
            <p className="leading-relaxed">
              ClauseTrace evaluates structural consistency, cross-clause collisions, and obligation gaps across uploaded documents and indexed reference agreements.
            </p>
          </div>
        </div>

        {/* Right Column (Col 6-12): Legal Question & Submission Form */}
        <div className="lg:col-span-7 flex flex-col justify-between space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4 flex-1 flex flex-col justify-between">
            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-slate-200 block mb-1.5 flex items-center justify-between">
                  <span>Describe the Legal Premise or Term to Examine</span>
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
                    Recommended inquiries for this task:
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
                  <span>Factual Background / Relevant Parties (Optional)</span>
                  <span className="text-[10px] font-normal text-slate-400">Contextualizes agent arguments</span>
                </label>
                <input
                  type="text"
                  value={contextNotes}
                  onChange={(e) => setContextNotes(e.target.value)}
                  placeholder="e.g. Senior developer joined in Jan 2024 with existing open source contributions"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-sans"
                />
              </div>
            </div>

            {/* Launch Action */}
            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-[11px] font-medium text-slate-300">
                  Runs 3-Agent Adversarial Examination
                </span>
                <span className="text-[10px] text-slate-400">
                  Advocate, Skeptic & Adjudicator cross-examine retrieved clauses
                </span>
              </div>

              <button
                type="submit"
                disabled={!query.trim()}
                className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 active:from-indigo-700 active:to-indigo-600 disabled:from-slate-800 disabled:to-slate-800 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-600/20 transition-all border border-indigo-400/30 cursor-pointer disabled:cursor-not-allowed"
              >
                <span>Launch Examination</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
