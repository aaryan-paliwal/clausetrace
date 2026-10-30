export type PersonaId = 
  | 'employee' 
  | 'founder' 
  | 'hr' 
  | 'business' 
  | 'individual';

export interface PersonaConfig {
  id: PersonaId;
  title: string;
  badge: string;
  tagline: string;
  description: string;
  defaultWorkspaceId: string;
  highlightCategory: string;
}

export type TaskStatus = 'available' | 'forthcoming';

export interface ProblemTask {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  statusNote?: string;
  recommendedQueries: string[];
  suggestedPromptTemplate: string;
}

export const PERSONAS: Record<PersonaId, PersonaConfig> = {
  employee: {
    id: 'employee',
    title: 'Employee / Job Seeker',
    badge: 'Career & Employment',
    tagline: 'Safeguard your compensation, intellectual property, non-competes, and termination rights.',
    description: 'Analyze offer letters, employment covenants, IP assignment carve-outs, notice periods, and severance terms.',
    defaultWorkspaceId: 'ws_startup_legal',
    highlightCategory: 'Employment & IP Rights',
  },
  founder: {
    id: 'founder',
    title: 'Founder / Startup',
    badge: 'Venture & Governance',
    tagline: 'Audit co-founder covenants, vesting acceleration, contractor terms, and IP ownership supremacy.',
    description: 'Detect dangerous clause collisions between founder agreements, contractor schedules, and confidential IP policies.',
    defaultWorkspaceId: 'ws_startup_legal',
    highlightCategory: 'Startup Governance',
  },
  hr: {
    id: 'hr',
    title: 'HR / Employer',
    badge: 'Workforce & Policy',
    tagline: 'Harmonize handbooks, offer schedules, attendance rules, and mutual dispute obligations.',
    description: 'Ensure institutional consistency across employee agreements, policy manuals, disciplinary codes, and separation rules.',
    defaultWorkspaceId: 'ws_startup_legal',
    highlightCategory: 'Workplace Compliance',
  },
  business: {
    id: 'business',
    title: 'Business / Organisation',
    badge: 'Commercial & Vendor',
    tagline: 'Detect conflicting operational liabilities, service level agreements, and unilateral cancellation terms.',
    description: 'Audit master service agreements, addenda, fee refund policies, and cross-document termination covenants.',
    defaultWorkspaceId: 'ws_startup_legal',
    highlightCategory: 'Commercial Integrity',
  },
  individual: {
    id: 'individual',
    title: 'Individual / General User',
    badge: 'Personal Rights & Policies',
    tagline: 'Navigate complex consumer agreements, institutional policy manuals, and student regulations.',
    description: 'Verify grading appeal deadlines, tuition fee refunds, credit enrollment caps, and administrative procedures.',
    defaultWorkspaceId: 'ws_university_policy',
    highlightCategory: 'Consumer & Institutional',
  },
};

export const PERSONA_TASKS: Record<PersonaId, ProblemTask[]> = {
  employee: [
    {
      id: 'emp_review_contract',
      title: 'Review an Employment Agreement',
      description: 'Audit employment agreements or offer letters against standard protections and corporate addenda.',
      status: 'available',
      recommendedQueries: [
        'Can the company immediately terminate employment without notice or cure upon a missed milestone?',
        'What is the base salary of the Executive?',
        'Does the company claim ownership over weekend side projects created on personal equipment?',
      ],
      suggestedPromptTemplate: 'Can the company immediately terminate employment without notice or cure upon a missed milestone?',
    },
    {
      id: 'emp_understand_clause',
      title: 'Understand a Legal Clause',
      description: 'Break down ambiguous definitions, conditional prerequisites, and deceptive exception traps.',
      status: 'available',
      recommendedQueries: [
        'What defines a Critical Deliverable Breach that triggers termination?',
        'What are the mandatory notice and cure requirements before termination for cause?',
      ],
      suggestedPromptTemplate: 'What defines a Critical Deliverable Breach that triggers termination?',
    },
    {
      id: 'emp_find_unfair_terms',
      title: 'Find Unfair or Colliding Terms',
      description: 'Examine cross-document conflicts between core employment terms and proprietary IP addenda.',
      status: 'available',
      recommendedQueries: [
        'Is there a conflict between my side project IP ownership carveout and the universal invention assignment override?',
        'How long does my confidentiality obligation survive after employment separation?',
      ],
      suggestedPromptTemplate: 'Is there a conflict between my side project IP ownership carveout and the universal invention assignment override?',
    },
    {
      id: 'emp_check_compliance',
      title: 'Check Compliance Obligations',
      description: 'Cross-examine mandatory post-termination restrictions, non-disclosure durations, and return of property.',
      status: 'available',
      recommendedQueries: [
        'What is the exact survival duration of confidentiality obligations: 5 years or 2 years?',
      ],
      suggestedPromptTemplate: 'What is the exact survival duration of confidentiality obligations: 5 years or 2 years?',
    },
    {
      id: 'emp_statutory_violations',
      title: 'Identify Statutory Legal Violations',
      description: 'Scan covenants against jurisdictional statutory labor codes and unfair competition jurisprudence.',
      status: 'forthcoming',
      statusNote: 'Planned for Phase 2: Jurisdiction-specific labor statute verification engine (e.g., CA Bus & Prof Code § 16600).',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
    {
      id: 'emp_draft_representation',
      title: 'Draft Formal Legal Representation',
      description: 'Generate attorney-ready formal letters or cure contestations backed by statutory citations.',
      status: 'forthcoming',
      statusNote: 'Planned for Phase 2: Formal legal dispatch drafting engine.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
  ],

  founder: [
    {
      id: 'fnd_review_contract',
      title: 'Review Founder & Executive Contracts',
      description: 'Verify cross-document harmony between founder agreements, board mandates, and IP assignments.',
      status: 'available',
      recommendedQueries: [
        'Can an executive be dismissed immediately without written cure notice upon subjective milestone failure?',
        'Does the universal IP assignment clause prevail over personal IP carve-outs?',
      ],
      suggestedPromptTemplate: 'Can an executive be dismissed immediately without written cure notice upon subjective milestone failure?',
    },
    {
      id: 'fnd_understand_clause',
      title: 'Understand Acceleration & Vesting Covenants',
      description: 'Examine single and double trigger vesting terms, acceleration events, and forfeiture triggers.',
      status: 'available',
      recommendedQueries: [
        'What defines a Critical Deliverable Breach that triggers termination?',
        'What are the mandatory notice and cure requirements before termination for cause?',
      ],
      suggestedPromptTemplate: 'What defines a Critical Deliverable Breach that triggers termination?',
    },
    {
      id: 'fnd_find_unfair_terms',
      title: 'Detect Deontic Collisions & Loopholes',
      description: 'Run the proactive conflict matrix to pinpoint direct modality clashes and unresolved overrides.',
      status: 'available',
      recommendedQueries: [
        'Does Section 6.4 notwithstanding clause erase the Section 2.1 personal equipment carve-out?',
        'How many days of notice are required before termination takes effect?',
      ],
      suggestedPromptTemplate: 'Does Section 6.4 notwithstanding clause erase the Section 2.1 personal equipment carve-out?',
    },
    {
      id: 'fnd_check_compliance',
      title: 'Check Post-Termination Survival Terms',
      description: 'Verify non-disclosure durations, restrictive covenants, and trade secret obligations.',
      status: 'available',
      recommendedQueries: [
        'What is the exact duration of the confidentiality covenant across all documents?',
      ],
      suggestedPromptTemplate: 'What is the exact duration of the confidentiality covenant across all documents?',
    },
    {
      id: 'fnd_remedies',
      title: 'Understand Legal Rights & Remedies',
      description: 'Map breach remedies, injunctive relief clauses, and indemnification caps.',
      status: 'forthcoming',
      statusNote: 'Planned for Phase 2: Statutory damage calculation and multi-jurisdictional remedies matrix.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
    {
      id: 'fnd_draft_representation',
      title: 'Draft Board & Co-Founder Redlines',
      description: 'Produce bilateral contract amendments and waiver certificates.',
      status: 'forthcoming',
      statusNote: 'Planned for Phase 2: Automated bilateral redline agreement pack generation.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
  ],

  hr: [
    {
      id: 'hr_review_contract',
      title: 'Harmonize Workplace Policies & Handbooks',
      description: 'Ensure baseline employment agreement terms do not clash with company policy manuals.',
      status: 'available',
      recommendedQueries: [
        'Can an employee be terminated immediately without the standard 30-day notice period?',
        'What are the mandatory notice and cure requirements before termination for cause?',
      ],
      suggestedPromptTemplate: 'Can an employee be terminated immediately without the standard 30-day notice period?',
    },
    {
      id: 'hr_understand_clause',
      title: 'Clarify Disciplinary & Termination Prerequisites',
      description: 'Audit whether breach criteria like "Critical Deliverable Breach" are procedurally defined.',
      status: 'available',
      recommendedQueries: [
        'What defines a Critical Deliverable Breach that triggers termination?',
      ],
      suggestedPromptTemplate: 'What defines a Critical Deliverable Breach that triggers termination?',
    },
    {
      id: 'hr_find_unfair_terms',
      title: 'Identify Conflicting Notice & Severance Terms',
      description: 'Audit contradictions between offer letters, master agreements, and severance policy schedules.',
      status: 'available',
      recommendedQueries: [
        'Is there a direct modality clash between 30 days notice and immediate termination?',
        'How long does confidentiality survive across company agreements?',
      ],
      suggestedPromptTemplate: 'Is there a direct modality clash between 30 days notice and immediate termination?',
    },
    {
      id: 'hr_check_compliance',
      title: 'Verify Standard Policy Survival Terms',
      description: 'Check whether all departing employees are bound by consistent confidentiality durations.',
      status: 'available',
      recommendedQueries: [
        'What is the exact survival duration of confidentiality obligations: 5 years or 2 years?',
      ],
      suggestedPromptTemplate: 'What is the exact survival duration of confidentiality obligations: 5 years or 2 years?',
    },
    {
      id: 'hr_statutory_violations',
      title: 'Jurisdictional Labor Law Audit',
      description: 'Evaluate handbook compliance against federal and local labor board directives.',
      status: 'forthcoming',
      statusNote: 'Planned for Phase 2: EEOC and state labor standards harmonization module.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
    {
      id: 'hr_draft_representation',
      title: 'Draft Employee Notice of Breach',
      description: 'Generate standardized formal cure notices and termination documentation.',
      status: 'forthcoming',
      statusNote: 'Planned for Phase 2: Formal notice letter generation.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
  ],

  business: [
    {
      id: 'biz_review_contract',
      title: 'Audit Master Services & Vendor Contracts',
      description: 'Verify cross-document alignment between master agreements, statements of work, and fee schedules.',
      status: 'available',
      recommendedQueries: [
        'Can either party cancel the agreement immediately without prior written notice?',
        'Does the universal ownership clause claim pre-existing background intellectual property?',
      ],
      suggestedPromptTemplate: 'Can either party cancel the agreement immediately without prior written notice?',
    },
    {
      id: 'biz_understand_clause',
      title: 'Analyze Liability & Termination Provisions',
      description: 'Audit clauses for vague contractual triggers, unilateral cancellation traps, and notice obligations.',
      status: 'available',
      recommendedQueries: [
        'What defines a Critical Deliverable Breach that triggers termination?',
        'What are the mandatory notice and cure requirements before termination for cause?',
      ],
      suggestedPromptTemplate: 'What defines a Critical Deliverable Breach that triggers termination?',
    },
    {
      id: 'biz_find_unfair_terms',
      title: 'Detect Master vs Addendum Discrepancies',
      description: 'Identify where vendor addenda covertly override core covenants or shorten protection windows.',
      status: 'available',
      recommendedQueries: [
        'Is there a conflict between the baseline agreement and the addendum regarding notice period?',
        'Does the addendum override the IP ownership carve-out?',
      ],
      suggestedPromptTemplate: 'Is there a conflict between the baseline agreement and the addendum regarding notice period?',
    },
    {
      id: 'biz_check_compliance',
      title: 'Check Confidentiality & Survival Clauses',
      description: 'Audit how long confidential commercial terms and customer lists remain legally protected.',
      status: 'available',
      recommendedQueries: [
        'What is the exact duration of confidentiality survival across the master agreement and addenda?',
      ],
      suggestedPromptTemplate: 'What is the exact duration of confidentiality survival across the master agreement and addenda?',
    },
    {
      id: 'biz_remedies',
      title: 'Assess Breach Remedies & Liquidated Damages',
      description: 'Evaluate statutory compliance of limitation of liability and indemnification caps.',
      status: 'forthcoming',
      statusNote: 'Planned for Phase 2: Commercial UCC and CISG statutory remedies engine.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
    {
      id: 'biz_draft_representation',
      title: 'Draft Contract Amendment / Addendum',
      description: 'Generate legally binding addendum language to neutralize unilateral exploit clauses.',
      status: 'forthcoming',
      statusNote: 'Planned for Phase 2: Multiparty amendment pack drafting.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
  ],

  individual: [
    {
      id: 'ind_review_contract',
      title: 'Review Institutional Policy / Consumer Contract',
      description: 'Audit institutional policy documents, university codes, or consumer agreements for rights and caps.',
      status: 'available',
      recommendedQueries: [
        'What is the maximum number of credits an undergraduate student can register for in a regular semester?',
        'What is the deadline to file a formal grade appeal after semester grades are posted?',
        'What percentage of tuition is refunded if a student withdraws during Week 4 of the semester?',
      ],
      suggestedPromptTemplate: 'What is the maximum number of credits an undergraduate student can register for in a regular semester?',
    },
    {
      id: 'ind_understand_clause',
      title: 'Understand a Policy Rule or Prerequisite',
      description: 'Clarify institutional requirements, attendance thresholds, and medical exception procedures.',
      status: 'available',
      recommendedQueries: [
        'What is the minimum physical attendance rate required in classes for undergraduate and graduate students?',
        'What reduced attendance percentage applies to a student with an approved medical exemption?',
        'Within how many days of the initial absence must a student submit medical documentation for an attendance exemption?',
      ],
      suggestedPromptTemplate: 'What is the minimum physical attendance rate required in classes for undergraduate and graduate students?',
    },
    {
      id: 'ind_find_unfair_terms',
      title: 'Detect Conflicting Policy Standards',
      description: 'Uncover contradictory rules across academic codes, fee schedules, and registration manuals.',
      status: 'available',
      recommendedQueries: [
        'What is the normal undergraduate semester credit load ceiling before needing an overload petition?',
        'If I withdraw from the university during week four, do I receive a 50% or 25% tuition refund?',
        'Can I submit a formal grade appeal 35 calendar days after grades are posted?',
      ],
      suggestedPromptTemplate: 'What is the normal undergraduate semester credit load ceiling before needing an overload petition?',
    },
    {
      id: 'ind_check_compliance',
      title: 'Verify Graduation & Residency Criteria',
      description: 'Check degree credit hour requirements, upper-division criteria, and academic probation ceilings.',
      status: 'available',
      recommendedQueries: [
        'How many total semester credit hours are required to earn an undergraduate baccalaureate degree?',
        'What is the maximum number of credit hours an undergraduate on academic probation may register for?',
      ],
      suggestedPromptTemplate: 'How many total semester credit hours are required to earn an undergraduate baccalaureate degree?',
    },
    {
      id: 'ind_statutory_violations',
      title: 'Identify Consumer Protection Violations',
      description: 'Scan institutional cancellation fees against state consumer protection statutes.',
      status: 'forthcoming',
      statusNote: 'Planned for Phase 2: Educational consumer protection & Title IX compliance checker.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
    {
      id: 'ind_draft_representation',
      title: 'Draft Formal Administrative Appeal',
      description: 'Generate formatted administrative appeal petitions citing governing handbook sections.',
      status: 'forthcoming',
      statusNote: 'Planned for Phase 2: Administrative appeal and waiver petition letter generator.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
  ],
};
