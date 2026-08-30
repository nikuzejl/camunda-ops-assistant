import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { PageShell } from "@/components/Shell";
import { Card } from "@/components/ui";

export default async function ProcessDefinitionDetailPage({ params }: { params: { key: string } }) {
  let definition;
  try {
    definition = await api.getProcessDefinition(params.key);
  } catch {
    notFound();
  }

  return (
    <PageShell title={`Process Definition ${definition.key}`}>
      <Card className="max-w-xl space-y-3 text-sm">
        <Row label="Key" value={definition.key} />
        <Row label="Process Definition Id" value={definition.process_definition_id} />
        <Row label="Name" value={definition.name} />
        <Row label="Version" value={String(definition.version)} />
        <Row label="Deployed" value={new Date(definition.deployment_time).toLocaleString()} />
      </Card>
      <p className="mt-4 text-xs text-slate-500">
        BPMN visualization will be added when the Camunda integration (Phase 2) provides the BPMN XML.
      </p>
    </PageShell>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between border-b border-slate-800 pb-2">
      <span className="text-slate-400">{label}</span>
      <span className="text-slate-100">{value}</span>
    </div>
  );
}
