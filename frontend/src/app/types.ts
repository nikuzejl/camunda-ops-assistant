export type ProcessInstanceState = 'ACTIVE' | 'FAILED' | 'COMPLETED' | 'TERMINATED' | 'INCIDENT';
export interface ProcessInstance { key: string; process_definition_id: string; process_definition_key: string; version: number; state: ProcessInstanceState; start_date: string; end_date: string | null; has_incident: boolean; tenant_id: string | null; }
export type IncidentState = 'ACTIVE' | 'RESOLVED';
export interface Incident { key: string; process_instance_key: string; process_definition_id: string; error_type: string; error_message: string; flow_node_id: string; state: IncidentState; creation_time: string; resolved_time: string | null; }
export interface ResolutionLessonInput { diagnosis: string; actions_taken: string; resolution: string; }
export interface ResolutionLesson extends ResolutionLessonInput { incident_key: string; process_instance_key: string; process_definition_id: string; error_type: string; flow_node_id: string; created_at: string; updated_at: string; }
export interface ChatResponse { conversation_id: string; reply: string; }
export interface AiSummaryResponse { summary: string; }
export interface DocumentSummary { source: string; chunk_count: number; content_type: string; }
export interface DocumentDeleteResponse { source: string; deleted_chunks: number; }
export interface IngestionResponse { source: string; chunk_count: number; characters: number; }
export interface DocumentSearchResult { content: string; source: string; chunk_index: number; }
