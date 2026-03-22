import { CreateNodeResponse, GraphData, Node } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const BLOCKCHAIN_URL = "https://special-oriole-remotely.ngrok-free.app/";

// Algorand App IDs (LocalNet Deployment)
export const APP_IDS = {
  liveProof: 1002,
  debateStake: 1034,
};

// Deployer Account
export const DEPLOYER_ADDRESS =
  "NMNRVAW7ZYZAKXFFSTTLHHNDXLG742E36OSJMEW524XXXQTZO3R6HGOQT4";

export async function createNode(
  text: string,
  source?: string,
  author_wallet?: string,
): Promise<CreateNodeResponse> {
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
    const timer = setTimeout(() => controller.abort(), 5000); // 5s timeout
    const url = `${BLOCKCHAIN_URL}/proof/${nodeId}`;
    console.log(`[getProof] Fetching from: ${url}`);

    const response = await fetch(url, {
      signal: controller.signal,
    });
    clearTimeout(timer);

    if (!response.ok) {
      console.warn(
        `[getProof] Non-200 response: ${response.status} ${response.statusText}`,
      );
      return null;
    }

    const data = await response.json();
    console.log(`[getProof] Success for node ${nodeId}`);
    return data;
  } catch (error) {
    if (error instanceof Error) {
      console.error(
        `[getProof] Error fetching proof for ${nodeId}:`,
        error.message,
      );
      // Re-throw so the component can handle it
      throw new Error(`Proof fetch failed: ${error.message}`);
    }
    console.error(`[getProof] Unknown error for ${nodeId}`);
    throw new Error("Failed to fetch proof");
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
  request: CreateDebateSessionRequest,
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

export async function getDebateSession(
  sessionId: string,
): Promise<DebateSessionResponse> {
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
  request: DebateTranscriptionRequest,
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

export async function getSpeakerStats(
  speakerName: string,
): Promise<SpeakerStats> {
  const response = await fetch(
    `${API_BASE_URL}/debate/speaker/${encodeURIComponent(speakerName)}/stats`,
  );
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

export async function getDebateLeaderboard(
  limit: number = 10,
): Promise<LeaderboardResponse> {
  const response = await fetch(
    `${API_BASE_URL}/debate/leaderboard?limit=${Math.min(limit, 100)}`,
  );
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

export async function getDebateConclusion(
  sessionId?: string,
): Promise<DebateConclusion> {
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

// ==================== NODE ANALYSIS APIs ====================

export interface NodeStats {
  total_nodes: number;
  total_evolutions: number;
  unique_contributors: number;
  contributors: string[];
  avg_evolutions_per_node: number;
  avg_creativity_score: number;
}

export async function getNodeStats(): Promise<NodeStats> {
  const response = await fetch(`${API_BASE_URL}/nodes/stats`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface ContributorNodeStats {
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

export async function getContributorNodeStats(
  contributorName: string,
): Promise<ContributorNodeStats> {
  const response = await fetch(
    `${API_BASE_URL}/nodes/contributor/${encodeURIComponent(contributorName)}/stats`,
  );
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface NodesLeaderboard {
  contributors: Array<{
    rank: number;
    speaker_name: string;
    overall_score: number;
    credibility_score: number;
    innovation_score: number;
    total_contributions: number;
    badge: string;
  }>;
  total: number;
}

export async function getNodesLeaderboard(
  limit: number = 10,
): Promise<NodesLeaderboard> {
  const response = await fetch(
    `${API_BASE_URL}/nodes/leaderboard?limit=${Math.min(limit, 100)}`,
  );
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface NodeTopic {
  node_id: string;
  primary_text: string;
  preview_text: string;
  health: {
    controversy_score: number;
    speaker_diversity: number;
    evolution_velocity: number;
    engagement_level: number;
  };
  dominance: {
    content_volume: number;
    time_span_minutes: number;
    merge_count: number;
    speaker_count: number;
    cross_references: number;
  };
  speakers: string[];
  top_contributor: string | null;
  importance_score: number;
  rank: number | null;
}

export interface NodesAnalysis {
  total_nodes: number;
  top_nodes: NodeTopic[];
  high_engagement_nodes: NodeTopic[];
  active_nodes: NodeTopic[];
  creative_nodes: NodeTopic[];
  diverse_nodes: NodeTopic[];
}

export async function getNodesAnalysis(): Promise<NodesAnalysis> {
  const response = await fetch(`${API_BASE_URL}/nodes/analysis`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface TrendTopic {
  topic_id: string;
  topic_preview: string;
  trend_type: string;
  velocity: number;
  speakers_involved: string[];
  description: string;
}

export interface NodesConclusion {
  total_nodes: number;
  total_contributions: number;
  unique_speakers: number;
  debate_duration_minutes: number;
  top_speakers: Array<{
    rank: number;
    speaker_name: string;
    overall_score: number;
    badge: string;
    total_contributions: number;
  }>;
  top_topics: NodeTopic[];
  controversial_topics: NodeTopic[];
  consensus_topics: NodeTopic[];
  trends: TrendTopic[];
  insights: string[];
  overall_quality_score: number;
}

export async function getNodesConclusion(): Promise<NodesConclusion> {
  const response = await fetch(`${API_BASE_URL}/nodes/conclusion`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface NodesAIAnalysis {
  summary: string;
  key_insights: string[];
  best_stance?: string;
  creative_ideas?: string[];
  synthesis?: string;
  strongest_arguments?: string[];
  weakest_arguments?: string[];
  emerging_patterns?: string[];
  recommendations: string[];
  metadata: {
    total_nodes: number;
    unique_contributors: number;
    total_evolutions: number;
    average_creativity: number;
    analysis_model: string;
  };
}

export async function getNodesAIAnalysis(): Promise<NodesAIAnalysis> {
  const response = await fetch(`${API_BASE_URL}/nodes/ai-analysis`);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}

export interface NodeListResponse {
  nodes: Node[];
  total: number;
}

export async function listNodes(
  limit: number = 50,
  offset: number = 0,
): Promise<NodeListResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/nodes/?limit=${limit}&offset=${offset}`,
  );
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}
