import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { PageShell } from "@/components/Shell";
import { Card, StateBadge } from "@/components/ui";

export default async function ProcessInstanceDetailPage({ params }: { params: { key: string } }) {
  let instance;
  try {
    instance = await api.getProcessInstance(params.key);
  } catch {
    notFound();
  }

  return (
    <PageShell title={`Process Instance ${instance.key}`}>
      <Card className="max-w-xl space-y-3 text-sm">
        <Row label="Key" value={instance.key} />
        <Row label="Process Definition" value={instance.process_definition_id} />
        <Row label="Version" value={String(instance.version)} />
        <Row label="State" value={<StateBadge state={instance.state} />} />
        <Row label="Started" value={new Date(instance.start_date).toLocaleString()} />
        <Row label="Ended" value={instance.end_date ? new Date(instance.end_date).toLocaleString() : "-"} />
        <Row label="Has Incident" value={instance.has_incident ? "Yes" : "No"} />
      </Card>
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
