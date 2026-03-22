import { CreateNodeResponse, GraphData } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const BLOCKCHAIN_URL =
  process.env.NEXT_PUBLIC_BLOCKCHAIN_URL || "http://localhost:8001";

export async function createNode(text: string, source?: string, author_wallet?: string): Promise<CreateNodeResponse> {
  const response = await fetch(`${API_BASE_URL}/node`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, source, author_wallet }),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || response.statusText);
  }
  const data = await response.json();
  return {
    node: data.node,
    connections: data.edges || [],
    action: data.action || "created",
    merge_count: data.merge_count || 0,
    creativity_score: data.creativity_score || 1.0,
    contributors: data.contributors || [],
    evolution_analysis: data.evolution_analysis,
    similarity_breakdown: data.similarity_breakdown,
  };
}

export async function getGraph(): Promise<GraphData> {
  const response = await fetch(`${API_BASE_URL}/graph`);
  if (!response.ok) throw new Error(response.statusText);
  const data = await response.json();
  return { nodes: data.nodes || [], links: data.edges || [] };
}

export async function getProof(nodeId: string) {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 3000); // 3s timeout
    const response = await fetch(`${BLOCKCHAIN_URL}/proof/${nodeId}`, {
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null; // blockchain API down = silently show "not anchored"
  }
}

// ==================== DEBATE MODE APIs ====================

export interface DebateSessionParticipant {
  name?: string;
  wallet_address: string;
}

export interface CreateDebateSessionRequest {
  topic_name: string;
  creator_wallet: string;
  creator_names: string[];
  participants: DebateSessionParticipant[];
}

export interface DebateSessionResponse {
  session_id: string;
  topic_name: string;
  creator_wallet: string;
  creator_names: string[];
  participants: DebateSessionParticipant[];
  created_at: number;
  status: string;
  message?: string;
}

export async function createDebateSession(
  request: CreateDebateSessionRequest
): Promise<DebateSessionResponse> {
  const response = await fetch(`${API_BASE_URL}/debate/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || response.statusText);
  }
  return response.json();
}

export async function getDebateSession(sessionId: string): Promise<DebateSessionResponse> {
  const response = await fetch(`${API_BASE_URL}/debate/session/${sessionId}`);
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || response.statusText);
  }
  return response.json();
}

export interface DebateTranscriptionRequest {
  speaker: string; // wallet address
  text: string;
  debate_id?: string;
  timestamp?: number;
}

export interface DebateTranscriptionResponse {
  action: "merged" | "created";
  node_id: string;
  similarity_score?: number;
  merge_count?: number;
  accumulated_length?: number;
}

export async function addDebateTranscription(
  request: DebateTranscriptionRequest
): Promise<DebateTranscriptionResponse> {
  const response = await fetch(`${API_BASE_URL}/debate/transcription`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      speaker: request.speaker,
      text: request.text,
      debate_id: request.debate_id,
      timestamp: request.timestamp || Math.floor(Date.now() / 1000),
    }),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || response.statusText);
  }
  return response.json();
}

export interface DebateNode {
  id: string;
  primary_text: string;
  accumulated_text: string;
  created_at: number;
  last_updated: number;
  merge_count: number;
  speakers: string[];
  merge_history?: any[];
}

export async function getDebateNode(nodeId: string): Promise<DebateNode> {
  const response = await fetch(`${API_BASE_URL}/debate/node/${nodeId}`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface DebateNodesResponse {
  nodes: DebateNode[];
  total: number;
}

export async function getAllDebateNodes(): Promise<DebateNodesResponse> {
  const response = await fetch(`${API_BASE_URL}/debate/nodes`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface DebateStats {
  total_nodes: number;
  total_merges: number;
  unique_speakers: number;
  speakers: string[];
  avg_merges_per_node: number;
}

export async function getDebateStats(): Promise<DebateStats> {
  const response = await fetch(`${API_BASE_URL}/debate/stats`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface SpeakerStats {
  speaker_name: string;
  total_contributions: number;
  nodes_created: number;
  nodes_merged: number;
  credibility: {
    consistency_score: number;
    quality_score: number;
    influence_score: number;
    engagement_depth: number;
    overall_credibility: number;
  };
  innovation: {
    novelty_score: number;
    creativity_average: number;
    diversity_score: number;
    catalyst_score: number;
    overall_innovation: number;
  };
  overall_score: number;
  rank: number;
}

export async function getSpeakerStats(speakerName: string): Promise<SpeakerStats> {
  const response = await fetch(`${API_BASE_URL}/debate/speaker/${encodeURIComponent(speakerName)}/stats`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface LeaderboardSpeaker {
  rank: number;
  speaker_name: string;
  overall_score: number;
  credibility_score: number;
  innovation_score: number;
  total_contributions: number;
  badge?: "thought_leader" | "innovator" | "mediator" | "catalyst";
}

export interface LeaderboardResponse {
  speakers: LeaderboardSpeaker[];
  total: number;
}

export async function getDebateLeaderboard(limit: number = 10): Promise<LeaderboardResponse> {
  const response = await fetch(`${API_BASE_URL}/debate/leaderboard?limit=${Math.min(limit, 100)}`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface TopicAnalysis {
  total_topics: number;
  top_topics: any[];
  controversial_topics: any[];
  active_topics: any[];
  diverse_topics: any[];
}

export async function getTopicsAnalysis(): Promise<TopicAnalysis> {
  const response = await fetch(`${API_BASE_URL}/debate/topics/analysis`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface DebateConclusion {
  total_nodes: number;
  total_contributions: number;
  unique_speakers: number;
  debate_duration_minutes: number;
  top_speakers: LeaderboardSpeaker[];
  top_topics: any[];
  controversial_topics: any[];
  consensus_topics: any[];
  trends: any[];
  insights: string[];
  overall_quality_score: number;
}

export async function getDebateConclusion(sessionId?: string): Promise<DebateConclusion> {
  let url = `${API_BASE_URL}/debate/conclusion`;
  if (sessionId) {
    url += `?session_id=${encodeURIComponent(sessionId)}`;
  }
  const response = await fetch(url);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface AIAnalysis {
  summary: string;
  key_insights: string[];
  best_stance: string;
  creative_ideas: string[];
  synthesis: string;
  strongest_arguments: string[];
  weakest_arguments: string[];
  emerging_patterns: string[];
  recommendations: string[];
  metadata: {
    total_nodes: number;
    unique_speakers: number;
    total_contributions: number;
    analysis_model: string;
    session_id: string | null;
  };
}

export async function getAIAnalysis(sessionId?: string): Promise<AIAnalysis> {
  let url = `${API_BASE_URL}/debate/ai-analysis`;
  if (sessionId) {
    url += `?session_id=${encodeURIComponent(sessionId)}`;
  }
  const response = await fetch(url);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}
