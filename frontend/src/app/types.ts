export type ProcessInstanceState = 'ACTIVE' | 'FAILED' | 'COMPLETED' | 'TERMINATED' | 'INCIDENT';
export interface ProcessInstance { key: string; process_definition_id: string; process_definition_key: string; version: number; state: ProcessInstanceState; start_date: string; end_date: string | null; has_incident: boolean; tenant_id: string | null; }
export type IncidentState = 'ACTIVE' | 'RESOLVED';
export interface Incident { key: string; process_instance_key: string; process_definition_id: string; error_type: string; error_message: string; flow_node_id: string; state: IncidentState; creation_time: string; resolved_time: string | null; }
export interface ProcessDefinition { key: string; process_definition_id: string; name: string; version: number; deployment_time: string; }
export interface ChatResponse { conversation_id: string; reply: string; }
export interface AiSummaryResponse { summary: string; }
export interface DocumentSummary { source: string; chunk_count: number; content_type: string; }
export interface IngestionResponse { source: string; chunk_count: number; characters: number; }
export interface DocumentSearchResult { content: string; source: string; chunk_index: number; }
