export interface AnalysisRequest {
  incident: string;
}

export interface Route {
  domain: string;
  confidence: number;
  reason: string;
}

export interface Facts {
  summary: string;
  alleged_conduct: string[];
  event_type: string | null;
  victim: string | null;
  accused: string | null;
  relationship_between_parties: string | null;
  location: string | null;
  time_or_date: string | null;
  intent: string | null;
  harm: string[];
  property_or_money: boolean;
  violence_or_threat: boolean;
  deception_or_fraud: boolean;
  digital_element: boolean;
  property_items: string[];
  money_amount: string | null;
  injuries: string[];
  weapons_or_tools: string[];
  evidence: string[];
  missing_or_uncertain_facts: string[];
}

export interface Candidate {
  act: string;
  section: string;
  title: string;
  text: string;
  distance: number;
  semantic_score: number;
  lexical_score: number;
  retrieval_score: number;
}

export interface Classification {
  section: string | null;
  confidence: number;
  explanation: string;
  candidate_rank: number | null;
  missing_information: string[];
}

export interface Verification {
  supported: boolean;
  confidence: number;
  reasoning: string;
  evidence_support: string[];
  contradictions: string[];
  missing_facts: string[];
}

export interface LegalResult {
  act: string;
  section: string;
  title: string;
  text: string;
}

export interface AnalysisResponse {
  status: string;
  message?: string | null;
  route?: Route | null;
  facts?: Facts | null;
  candidates?: Candidate[] | null;
  classification?: Classification | null;
  verification?: Verification | null;
  result?: LegalResult | null;
}