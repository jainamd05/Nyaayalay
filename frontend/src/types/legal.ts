export interface LegalSource {
    title: string;
    source?: string;
    content?: string;
    relevance_score?: number;
  }
  
  export interface LegalResponse {
    status: string;
    category?: string;
    summary?: string;
    answer: string;
    sources?: LegalSource[];
    disclaimer?: string;
  }