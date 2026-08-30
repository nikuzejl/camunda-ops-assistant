import type {
  ChatResponse,
  HealthResponse,
  Incident,
  ProcessDefinition,
  ProcessInstance,
} from "./types";

/**
 * Thin fetch wrapper for the FastAPI backend.
 * No credentials are stored or sent from the frontend; the backend owns all secrets.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`API error ${response.status}: ${detail}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => apiFetch<HealthResponse>("/api/health"),
  listProcessInstances: () => apiFetch<ProcessInstance[]>("/api/process-instances"),
  getProcessInstance: (key: string) => apiFetch<ProcessInstance>(`/api/process-instances/${key}`),
  listIncidents: () => apiFetch<Incident[]>("/api/incidents"),
  getIncident: (key: string) => apiFetch<Incident>(`/api/incidents/${key}`),
  listProcessDefinitions: () => apiFetch<ProcessDefinition[]>("/api/process-definitions"),
  getProcessDefinition: (key: string) => apiFetch<ProcessDefinition>(`/api/process-definitions/${key}`),
  chat: (message: string, conversationId?: string) =>
    apiFetch<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),
};
