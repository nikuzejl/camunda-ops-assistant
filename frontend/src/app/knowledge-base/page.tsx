import { PageShell } from "@/components/Shell";
import { Card } from "@/components/ui";

export default function KnowledgeBasePage() {
  return (
    <PageShell title="Documents / Knowledge Base">
      <Card>
        <p className="text-sm text-slate-300">
          Document ingestion (Markdown, TXT, PDF), chunking, embeddings, and pgvector-backed
          semantic search will be implemented in Phase 3. This page will let operators upload
          operational documentation and browse indexed knowledge sources.
        </p>
      </Card>
    </PageShell>
  );
}
