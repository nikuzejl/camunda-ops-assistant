import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';
import { ApiService } from './api.service';
import { DocumentSummary, Incident, ProcessDefinition, ProcessInstance } from './types';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './page.component.html',
  styleUrl: './page.component.css',
})
export class PageComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  page = '';
  key = '';
  title = '';
  instances: ProcessInstance[] = [];
  incidents: Incident[] = [];
  definitions: ProcessDefinition[] = [];
  instance?: ProcessInstance;
  incident?: Incident;
  definition?: ProcessDefinition;
  error = '';
  messages: { role: 'user' | 'assistant'; content: string }[] = [];
  input = '';
  conversationId?: string;
  loading = false;
  dataLoading = false;
  aiSummary = '';
  summaryLoading = false;
  summaryLoaded = false;
  documents: DocumentSummary[] = [];
  ingesting = false;
  ingestionMessage = '';
  searchQuery = '';
  searchResults: { content: string; source: string; chunk_index: number }[] = [];
  searching = false;
  readonly operateBaseUrl = 'http://localhost:8080/operate';

  ngOnInit(): void {
    this.route.data.subscribe((data) => { this.page = data['page']; this.key = this.route.snapshot.paramMap.get('key') ?? ''; this.load(); });
  }

  load(): void {
    this.error = '';
    this.dataLoading = true;
    const requests: Record<string, () => void> = {
      overview: () => { this.title = 'Overview'; forkJoin({ instances: this.api.listProcessInstances(), incidents: this.api.listIncidents(), definitions: this.api.listProcessDefinitions() }).pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (data) => { this.instances = data.instances; this.incidents = data.incidents; this.definitions = data.definitions; }, error: this.fail }); if (!this.summaryLoaded && !this.summaryLoading) this.loadAiSummary(); },
      instances: () => { this.title = 'Process Instances'; this.api.listProcessInstances().pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (v) => this.instances = v, error: this.fail }); },
      incidents: () => { this.title = 'Incidents'; this.api.listIncidents().pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (v) => this.incidents = v, error: this.fail }); },
      definitions: () => { this.title = 'Process Definitions'; this.api.listProcessDefinitions().pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (v) => this.definitions = v, error: this.fail }); },
      'instance-detail': () => { this.title = `Process Instance ${this.key}`; this.api.getProcessInstance(this.key).pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (v) => this.instance = v, error: this.fail }); },
      'incident-detail': () => { this.title = `Incident ${this.key}`; this.api.getIncident(this.key).pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (v) => this.incident = v, error: this.fail }); },
      'definition-detail': () => { this.title = `Process Definition ${this.key}`; this.api.getProcessDefinition(this.key).pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (v) => this.definition = v, error: this.fail }); },
      investigation: () => { this.title = 'AI Investigation'; forkJoin({ instances: this.api.listProcessInstances(), incidents: this.api.listIncidents(), definitions: this.api.listProcessDefinitions() }).pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (data) => { this.instances = data.instances; this.incidents = data.incidents; this.definitions = data.definitions; }, error: this.fail }); },
      knowledge: () => { this.title = 'Documents / Knowledge Base'; this.api.listDocuments().pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (v) => this.documents = v, error: this.fail }); },
    };
    requests[this.page]?.();
  }

  fail = (err: Error) => { this.error = err.message || 'Unknown error'; this.dataLoading = false; };
  loadAiSummary(): void { this.summaryLoading = true; this.aiSummary = ''; this.api.getAiSummary().subscribe({ next: (response) => { this.aiSummary = response.summary; this.summaryLoaded = true; this.summaryLoading = false; }, error: (err) => { this.aiSummary = `Unable to generate AI summary: ${err.message}`; this.summaryLoading = false; } }); }
  refreshSummary(): void { if (!this.summaryLoading) this.loadAiSummary(); }
  date(value: string | null | undefined): string { return value ? new Date(value).toLocaleString() : '-'; }
  operateProcessUrl(key: string): string { return `${this.operateBaseUrl}/processes/${key}/incidents`; }
  getInstanceState(item?: ProcessInstance): string {
    if (!item) return '';
    if (item.has_incident || item.state === 'FAILED' || item.state === 'INCIDENT') return 'FAILED';
    return item.state;
  }
  activeInstances(): ProcessInstance[] { return this.instances.filter((item) => this.getInstanceState(item) === 'ACTIVE'); }
    onDocumentSelected(event: Event): void {
      const input = event.target as HTMLInputElement;
      const file = input.files?.[0];
      input.value = '';
      if (!file || this.ingesting) return;
      this.ingesting = true;
      this.ingestionMessage = '';
      this.error = '';
      this.api.ingestDocument(file).pipe(finalize(() => this.ingesting = false)).subscribe({
        next: (response) => { this.ingestionMessage = `${response.source} indexed in ${response.chunk_count} chunks.`; this.api.listDocuments().subscribe({ next: (v) => this.documents = v }); },
        error: (err) => { this.error = err.error?.detail || err.message || 'Document ingestion failed'; },
      });
    }
    searchKnowledge(): void {
      const query = this.searchQuery.trim();
      if (query.length < 2 || this.searching) return;
      this.searching = true;
      this.error = '';
      this.api.searchDocuments(query).pipe(finalize(() => this.searching = false)).subscribe({
        next: (results) => this.searchResults = results,
        error: (err) => { this.error = err.error?.detail || err.message || 'Document search failed'; },
      });
    }
  send(): void {
    const question = this.input.trim();
    if (!question || this.loading) return;
    this.messages.push({ role: 'user', content: question }); this.input = ''; this.loading = true; this.error = '';
    this.api.chat(question, this.conversationId).subscribe({ next: (response) => { this.conversationId = response.conversation_id; this.messages.push({ role: 'assistant', content: response.reply }); this.loading = false; }, error: (err) => { this.error = err.message; this.loading = false; } });
  }
}
