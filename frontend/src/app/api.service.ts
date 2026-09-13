import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AiSummaryResponse, ChatResponse, DocumentSearchResult, DocumentSummary, Incident, IngestionResponse, ProcessDefinition, ProcessInstance } from './types';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000';
  listProcessInstances(): Observable<ProcessInstance[]> { return this.http.get<ProcessInstance[]>(`${this.baseUrl}/api/process-instances`); }
  getProcessInstance(key: string): Observable<ProcessInstance> { return this.http.get<ProcessInstance>(`${this.baseUrl}/api/process-instances/${key}`); }
  listIncidents(): Observable<Incident[]> { return this.http.get<Incident[]>(`${this.baseUrl}/api/incidents`); }
  getIncident(key: string): Observable<Incident> { return this.http.get<Incident>(`${this.baseUrl}/api/incidents/${key}`); }
  listProcessDefinitions(): Observable<ProcessDefinition[]> { return this.http.get<ProcessDefinition[]>(`${this.baseUrl}/api/process-definitions`); }
  getProcessDefinition(key: string): Observable<ProcessDefinition> { return this.http.get<ProcessDefinition>(`${this.baseUrl}/api/process-definitions/${key}`); }
  getAiSummary(): Observable<AiSummaryResponse> { return this.http.get<AiSummaryResponse>(`${this.baseUrl}/api/ai-summary`); }
  chat(message: string, conversationId?: string): Observable<ChatResponse> { return this.http.post<ChatResponse>(`${this.baseUrl}/api/chat`, { message, conversation_id: conversationId }); }
  listDocuments(): Observable<DocumentSummary[]> { return this.http.get<DocumentSummary[]>(`${this.baseUrl}/api/documents`); }
  ingestDocument(file: File): Observable<IngestionResponse> { const form = new FormData(); form.append('file', file, file.name); return this.http.post<IngestionResponse>(`${this.baseUrl}/api/documents/ingest`, form); }
  searchDocuments(query: string): Observable<DocumentSearchResult[]> { return this.http.post<DocumentSearchResult[]>(`${this.baseUrl}/api/documents/search`, { query, limit: 8 }); }
}
