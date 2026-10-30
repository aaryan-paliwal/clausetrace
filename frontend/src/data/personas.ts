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
    badge: 'Employment & Career',
    tagline: 'Audit compensation clauses, IP assignment terms, non-compete covenants, and termination notice rules.',
    description: 'Examine employment contracts, appointment letters, IP carve-out clauses, notice periods, and separation terms for conflicting obligations.',
    defaultWorkspaceId: 'ws_startup_legal',
    highlightCategory: 'Employment & IP Terms',
  },
  founder: {
    id: 'founder',
    title: 'Founder / Startup',
    badge: 'Founder & Venture',
    tagline: 'Audit founder agreements, vesting acceleration, contractor covenants, and IP assignment overrides.',
    description: 'Detect cross-clause collisions between founder agreements, consultant contracts, and proprietary IP policies.',
    defaultWorkspaceId: 'ws_startup_legal',
    highlightCategory: 'Startup & Governance',
  },
  hr: {
    id: 'hr',
    title: 'HR / Employer',
    badge: 'Workforce & Policy',
    tagline: 'Harmonize workplace policy handbooks, offer schedules, attendance rules, and mutual dispute obligations.',
    description: 'Check consistency across employee agreements, policy manuals, disciplinary codes, and exit procedures.',
    defaultWorkspaceId: 'ws_startup_legal',
    highlightCategory: 'Workplace Policies',
  },
  business: {
    id: 'business',
    title: 'Business / Organisation',
    badge: 'Commercial & Vendor',
    tagline: 'Detect conflicting operational liabilities, service level agreements, and unilateral cancellation terms.',
    description: 'Audit master service agreements, addenda, fee refund policies, and cross-document termination covenants.',
    defaultWorkspaceId: 'ws_startup_legal',
    highlightCategory: 'Commercial Contracts',
  },
  individual: {
    id: 'individual',
    title: 'Individual / General User',
    badge: 'Personal & Institutional',
    tagline: 'Review institutional policies, consumer agreements, academic guidelines, and administrative rules.',
    description: 'Verify grade appeal deadlines, tuition fee refunds, credit enrollment caps, and institutional dispute procedures.',
    defaultWorkspaceId: 'ws_university_policy',
    highlightCategory: 'Institutional & Consumer',
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
      description: 'Examine definitions, conditional prerequisites, and exception terms for hidden obligations.',
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
      description: 'Examine cross-document conflicts between core employment covenants and separate IP or confidentiality addenda.',
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
      description: 'Review post-separation restrictions, non-disclosure survival periods, and property return obligations.',
      status: 'available',
      recommendedQueries: [
        'What is the exact survival duration of confidentiality obligations: 5 years or 2 years?',
      ],
      suggestedPromptTemplate: 'What is the exact survival duration of confidentiality obligations: 5 years or 2 years?',
    },
    {
      id: 'emp_statutory_violations',
      title: 'Identify Statutory Legal Violations',
      description: 'Verify contractual covenants against statutory labor enactments and employment guidelines.',
      status: 'forthcoming',
      statusNote: 'Forthcoming: Statutory legal research and legislative compliance checking are planned for a subsequent release.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
    {
      id: 'emp_draft_representation',
      title: 'Draft Formal Legal Representation',
      description: 'Draft formal legal notices, representation letters, or dispute replies.',
      status: 'forthcoming',
      statusNote: 'Forthcoming: Formal legal correspondence drafting will be supported once Indian statutory reference modules are integrated.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
  ],

  founder: [
    {
      id: 'fnd_review_contract',
      title: 'Review Founder & Executive Contracts',
      description: 'Verify cross-document harmony between founder agreements, board resolutions, and IP assignments.',
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
      description: 'Examine vesting terms, acceleration events, and forfeiture triggers for contractual ambiguity.',
      status: 'available',
      recommendedQueries: [
        'What defines a Critical Deliverable Breach that triggers termination?',
        'What are the mandatory notice and cure requirements before termination for cause?',
      ],
      suggestedPromptTemplate: 'What defines a Critical Deliverable Breach that triggers termination?',
    },
    {
      id: 'fnd_find_unfair_terms',
      title: 'Detect Structural Collisions & Loopholes',
      description: 'Identify direct modality clashes, notice discrepancies, and unresolved override clauses.',
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
      description: 'Verify non-disclosure durations, restrictive covenants, and trade secret obligations across documents.',
      status: 'available',
      recommendedQueries: [
        'What is the exact duration of the confidentiality covenant across all documents?',
      ],
      suggestedPromptTemplate: 'What is the exact duration of the confidentiality covenant across all documents?',
    },
    {
      id: 'fnd_remedies',
      title: 'Understand Legal Rights & Remedies',
      description: 'Analyze contractual remedies, breach provisions, and damages caps.',
      status: 'forthcoming',
      statusNote: 'Forthcoming: Statutory remedies analysis and legal damage estimation modules will be introduced in future updates.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
    {
      id: 'fnd_draft_representation',
      title: 'Draft Board & Co-Founder Redlines',
      description: 'Generate bilateral contract amendments and waiver certificates.',
      status: 'forthcoming',
      statusNote: 'Forthcoming: Formal contract amendment drafting is planned for a subsequent release.',
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
      title: 'Employment Regulation Audit',
      description: 'Evaluate workplace policy compliance against applicable statutory employment standards.',
      status: 'forthcoming',
      statusNote: 'Forthcoming: Statutory workplace regulation verification is planned once Indian legal intelligence modules are active.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
    {
      id: 'hr_draft_representation',
      title: 'Draft Employee Notice of Breach',
      description: 'Generate standardized formal cure notices and termination documentation.',
      status: 'forthcoming',
      statusNote: 'Forthcoming: Automated drafting of formal employee breach notices is planned for Phase 2.',
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
      description: 'Audit clauses for vague contractual triggers, unilateral cancellation terms, and notice obligations.',
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
      description: 'Identify where vendor addenda contradict core covenants or modify agreed protection windows.',
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
      description: 'Audit how long confidential commercial terms and customer lists remain legally protected across documents.',
      status: 'available',
      recommendedQueries: [
        'What is the exact duration of confidentiality survival across the master agreement and addenda?',
      ],
      suggestedPromptTemplate: 'What is the exact duration of confidentiality survival across the master agreement and addenda?',
    },
    {
      id: 'biz_remedies',
      title: 'Assess Breach Remedies & Liquidated Damages',
      description: 'Evaluate statutory enforceability of limitation of liability and indemnification caps.',
      status: 'forthcoming',
      statusNote: 'Forthcoming: Statutory remedies analysis and commercial damage assessment are planned for a future update.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
    {
      id: 'biz_draft_representation',
      title: 'Draft Contract Amendment / Addendum',
      description: 'Generate legally binding addendum language to neutralize unilateral exploit clauses.',
      status: 'forthcoming',
      statusNote: 'Forthcoming: Formal contract amendment and addenda drafting will be enabled in Phase 2.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
  ],

  individual: [
    {
      id: 'ind_review_contract',
      title: 'Review Institutional Policy / Consumer Agreement',
      description: 'Audit institutional policy documents, codes of conduct, or consumer agreements for rights and caps.',
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
      description: 'Scan institutional cancellation fees against statutory consumer protection standards.',
      status: 'forthcoming',
      statusNote: 'Forthcoming: Statutory consumer protection verification is planned for Phase 2.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
    {
      id: 'ind_draft_representation',
      title: 'Draft Formal Administrative Appeal',
      description: 'Generate formatted administrative appeal petitions citing governing handbook sections.',
      status: 'forthcoming',
      statusNote: 'Forthcoming: Automated administrative appeal letter generation will be added in a future release.',
      recommendedQueries: [],
      suggestedPromptTemplate: '',
    },
  ],
};
