import React from 'react';
import { 
  Briefcase, 
  Rocket, 
  Users, 
  Building2, 
  User, 
  CheckCircle2, 
  ChevronRight,
  ShieldCheck,
  Scale,
  Sparkles
} from 'lucide-react';
import { PersonaId, PersonaConfig, PERSONAS } from '../data/personas';

interface PersonaSelectorProps {
  selectedPersona: PersonaId;
  onSelectPersona: (persona: PersonaId) => void;
}

const PERSONA_ICONS: Record<PersonaId, React.ReactNode> = {
  employee: <Briefcase className="w-5 h-5 text-sky-400" />,
  founder: <Rocket className="w-5 h-5 text-indigo-400" />,
  hr: <Users className="w-5 h-5 text-violet-400" />,
  business: <Building2 className="w-5 h-5 text-amber-400" />,
  individual: <User className="w-5 h-5 text-emerald-400" />,
};

const PERSONA_ACCENTS: Record<PersonaId, { border: string; bg: string; badge: string }> = {
  employee: {
    border: 'border-sky-500/40 hover:border-sky-400',
    bg: 'bg-sky-500/10',
    badge: 'text-sky-300 bg-sky-500/10 border-sky-500/20',
  },
  founder: {
    border: 'border-indigo-500/40 hover:border-indigo-400',
    bg: 'bg-indigo-500/10',
    badge: 'text-indigo-300 bg-indigo-500/10 border-indigo-500/20',
  },
  hr: {
    border: 'border-violet-500/40 hover:border-violet-400',
    bg: 'bg-violet-500/10',
    badge: 'text-violet-300 bg-violet-500/10 border-violet-500/20',
  },
  business: {
    border: 'border-amber-500/40 hover:border-amber-400',
    bg: 'bg-amber-500/10',
    badge: 'text-amber-300 bg-amber-500/10 border-amber-500/20',
  },
  individual: {
    border: 'border-emerald-500/40 hover:border-emerald-400',
    bg: 'bg-emerald-500/10',
    badge: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20',
  },
};

export const PersonaSelector: React.FC<PersonaSelectorProps> = ({
  selectedPersona,
  onSelectPersona,
}) => {
  const personas = Object.values(PERSONAS) as PersonaConfig[];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-mono font-bold">1</span>
            Identify Your Legal Context
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Select who you are representing. This contextualizes query recommendations, conflict severity priorities, and intake questions.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {personas.map((persona) => {
          const isSelected = selectedPersona === persona.id;
          const accents = PERSONA_ACCENTS[persona.id];

          return (
            <button
              key={persona.id}
              type="button"
              onClick={() => onSelectPersona(persona.id)}
              className={`p-3.5 rounded-xl border text-left transition-all relative flex flex-col justify-between ${
                isSelected
                  ? `bg-slate-900 border-2 ${accents.border} shadow-lg shadow-indigo-500/10 ring-1 ring-indigo-500/20`
                  : 'bg-slate-900/60 border-slate-800 hover:bg-slate-900/90 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${accents.bg}`}>
                    {PERSONA_ICONS[persona.id]}
                  </div>
                  {isSelected ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <span className="w-3.5 h-3.5 rounded-full border border-slate-700" />
                  )}
                </div>

                <div className="text-xs font-bold text-white tracking-tight mb-1">
                  {persona.title}
                </div>

                <span className={`inline-block text-[10px] font-semibold px-2 py-0.5 rounded border mb-2 ${accents.badge}`}>
                  {persona.badge}
                </span>

                <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-3">
                  {persona.description}
                </p>
              </div>

              <div className="pt-3 mt-3 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                <span className="truncate">{persona.highlightCategory}</span>
                <ChevronRight className={`w-3 h-3 transition-transform ${isSelected ? 'translate-x-0.5 text-indigo-400' : 'text-slate-600'}`} />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

