export interface Node {
  id: string;
  text: string;
  embedding?: number[];
  timestamp: number;
  hash?: string;
  txId?: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface Link {
  source: string | Node;
  target: string | Node;
  score: number;
  semantic: number;
  keyword: number;
  time: number;
}

export interface GraphData {
  nodes: Node[];
  links: Link[];
}

export interface CreateNodeRequest {
  text: string;
  source?: string;
  author_wallet?: string;
}

export interface SimilarityBreakdown {
  semantic: number;
  keyword: number;
  fuzzy: number;
  edit_distance: number;
  length_ratio: number;
  token_overlap: number;
  composite_score: number;
  confidence: string; // "strong" | "moderate" | "weak" | "none"
}

export interface CreateNodeResponse {
  node: Node;
  connections: Link[];
  action: string; // "created" | "merged"
  merge_count: number;
  creativity_score: number;
  contributors: string[];
  evolution_analysis?: any;
  similarity_breakdown?: SimilarityBreakdown;
}
