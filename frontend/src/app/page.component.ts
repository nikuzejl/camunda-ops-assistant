import { CommonModule } from '@angular/common';
import { Component, ElementRef, OnInit, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';
import { ApiService } from './api.service';
import { DocumentSummary, Incident, ProcessInstance, ResolutionLesson, ResolutionLessonInput } from './types';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './page.component.html',
  styleUrl: './page.component.css',
})
export class PageComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  @ViewChild('messagesContainer') messagesContainer?: ElementRef<HTMLDivElement>;
  page = '';
  key = '';
  title = '';
  instances: ProcessInstance[] = [];
  incidents: Incident[] = [];
  instance?: ProcessInstance;
  incident?: Incident;
  resolutionLesson?: ResolutionLesson;
  resolutionForm: ResolutionLessonInput = { diagnosis: '', actions_taken: '', resolution: '' };
  resolutionLoading = false;
  resolutionSaving = false;
  resolutionMessage = '';
  resolutionError = false;
  error = '';
  messages: { role: 'user' | 'assistant'; content: string }[] = [];
  input = '';
  conversationId?: string;
  loading = false;
  dataLoading = false;
  aiSummary = '';
  summaryError = '';
  summaryLoading = false;
  summaryLoaded = false;
  documents: DocumentSummary[] = [];
  documentActionMessage = '';
  documentActionError = false;
  deletingSource?: string;
  documentPendingDeletion?: string;
  ingesting = false;
  ingestionMessage = '';
  searchQuery = '';
  searchResults: { content: string; source: string; chunk_index: number }[] = [];
  searching = false;
  readonly operateBaseUrl = 'http://129.213.191.117:8080/operate';

  ngOnInit(): void {
    this.route.data.subscribe((data) => { this.page = data['page']; this.key = this.route.snapshot.paramMap.get('key') ?? ''; this.load(); });
  }

  load(): void {
    this.error = '';
    this.dataLoading = true;
    const requests: Record<string, () => void> = {
      overview: () => { this.title = 'Overview'; forkJoin({ instances: this.api.listProcessInstances(), incidents: this.api.listIncidents() }).pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (data) => { this.instances = data.instances; this.incidents = data.incidents; }, error: this.fail }); },
      'instance-detail': () => { this.title = `Process Instance ${this.key}`; this.api.getProcessInstance(this.key).pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (v) => this.instance = v, error: this.fail }); },
      'incident-detail': () => { this.title = `Incident ${this.key}`; this.api.getIncident(this.key).pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (v) => { this.incident = v; this.resolutionLesson = undefined; this.resolutionForm = { diagnosis: '', actions_taken: '', resolution: '' }; this.resolutionLoading = true; this.resolutionMessage = ''; this.resolutionError = false; this.api.getResolutionLesson(this.key).pipe(finalize(() => this.resolutionLoading = false)).subscribe({ next: (lesson) => { this.resolutionLesson = lesson ?? undefined; if (lesson) this.resolutionForm = { diagnosis: lesson.diagnosis, actions_taken: lesson.actions_taken, resolution: lesson.resolution }; }, error: (err) => { this.resolutionMessage = err.error?.detail || err.message || 'Could not load the saved resolution.'; this.resolutionError = true; } }); }, error: this.fail }); },
      investigation: () => { this.title = 'AI Investigation'; forkJoin({ instances: this.api.listProcessInstances(), incidents: this.api.listIncidents() }).pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (data) => { this.instances = data.instances; this.incidents = data.incidents; }, error: this.fail }); },
      knowledge: () => { this.title = 'Documents / Knowledge Base'; this.api.listDocuments().pipe(finalize(() => this.dataLoading = false)).subscribe({ next: (v) => this.documents = v, error: this.fail }); },
    };
    requests[this.page]?.();
  }

  fail = (err: Error) => { this.error = err.message || 'Unknown error'; this.dataLoading = false; };
  saveResolution(): void {
    if (this.incident?.state !== 'RESOLVED' || this.resolutionSaving) return;
    this.resolutionSaving = true;
    this.resolutionMessage = '';
    this.resolutionError = false;
    this.api.saveResolutionLesson(this.incident.key, this.resolutionForm).pipe(finalize(() => this.resolutionSaving = false)).subscribe({
      next: (lesson) => { this.resolutionLesson = lesson; this.resolutionMessage = 'Confirmed resolution saved for future investigations.'; },
      error: (err) => { this.resolutionMessage = err.error?.detail || err.message || 'Could not save the resolution.'; this.resolutionError = true; },
    });
  }
  loadAiSummary(): void { this.summaryLoading = true; this.summaryError = ''; this.aiSummary = ''; this.api.getAiSummary().subscribe({ next: (response) => { this.aiSummary = response.summary; this.summaryLoaded = true; this.summaryLoading = false; }, error: (err) => { this.summaryLoaded = false; this.summaryError = err.error?.detail || 'Something went wrong while generating the AI summary. Please try again later.'; this.summaryLoading = false; } }); }
  refreshSummary(): void { if (!this.summaryLoading) this.loadAiSummary(); }
  date(value: string | null | undefined): string { return value ? new Date(value).toLocaleString() : '-'; }
  operateProcessUrl(key: string): string { return `${this.operateBaseUrl}/processes/${key}/incidents`; }
  getInstanceState(item?: ProcessInstance): string {
    if (!item) return '';
    if (item.has_incident || item.state === 'FAILED' || item.state === 'INCIDENT') return 'FAILED';
    return item.state;
  }
  activeInstances(): ProcessInstance[] { return this.instances.filter((item) => this.getInstanceState(item) === 'ACTIVE'); }
  activeIncidents(): Incident[] { return this.incidents.filter((item) => item.state === 'ACTIVE'); }
  resolvedIncidents(): Incident[] { return this.incidents.filter((item) => item.state === 'RESOLVED'); }
  incidentStateLabel(state: string): string { return state === 'ACTIVE' ? 'UNRESOLVED' : state; }
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
    deleteDocument(source: string): void {
      if (this.deletingSource) return;
      this.documentPendingDeletion = source;
    }
    cancelDocumentDeletion(): void {
      if (!this.deletingSource) this.documentPendingDeletion = undefined;
    }
    confirmDocumentDeletion(): void {
      const source = this.documentPendingDeletion;
      if (!source || this.deletingSource) return;
      this.documentPendingDeletion = undefined;
      this.deletingSource = source;
      this.documentActionMessage = '';
      this.documentActionError = false;
      this.api.deleteDocument(source).pipe(finalize(() => this.deletingSource = undefined)).subscribe({
        next: (response) => {
          this.documents = this.documents.filter((document) => document.source !== response.source);
          this.searchResults = this.searchResults.filter((result) => result.source !== response.source);
          this.documentActionMessage = `${response.source} deleted (${response.deleted_chunks} chunks).`;
        },
        error: (err) => { this.documentActionMessage = err.error?.detail || err.message || 'Document deletion failed'; this.documentActionError = true; },
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
    this.messages.push({ role: 'user', content: question }); this.input = ''; this.loading = true; this.error = ''; this.scrollMessagesToBottom();
    this.api.chat(question, this.conversationId).subscribe({ next: (response) => { this.conversationId = response.conversation_id; this.messages.push({ role: 'assistant', content: response.reply }); this.loading = false; this.scrollMessagesToBottom(); }, error: (err) => { this.error = err.message; this.loading = false; } });
  }

  private scrollMessagesToBottom(): void {
    setTimeout(() => {
      const element = this.messagesContainer?.nativeElement;
      if (element) element.scrollTop = element.scrollHeight;
    });
  }
}
