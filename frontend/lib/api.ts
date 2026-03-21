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
