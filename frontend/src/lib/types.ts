/** Shared types mirroring the backend Pydantic schemas (app/models/schemas.py). */

export type ProcessInstanceState = "ACTIVE" | "COMPLETED" | "TERMINATED" | "INCIDENT";

export interface ProcessInstance {
  key: string;
  process_definition_id: string;
  process_definition_key: string;
  version: number;
  state: ProcessInstanceState;
  start_date: string;
  end_date: string | null;
  has_incident: boolean;
  tenant_id: string | null;
}

export type IncidentState = "ACTIVE" | "RESOLVED";

export interface Incident {
  key: string;
  process_instance_key: string;
  process_definition_id: string;
  error_type: string;
  error_message: string;
  flow_node_id: string;
  state: IncidentState;
  creation_time: string;
  resolved_time: string | null;
}

export interface ProcessDefinition {
  key: string;
  process_definition_id: string;
  name: string;
  version: number;
  bpmn_xml: string | null;
  deployment_time: string;
}

export interface ChatResponse {
  conversation_id: string;
  reply: string;
}

export interface HealthResponse {
  status: string;
  environment: string;
  camunda_mode: string;
}
