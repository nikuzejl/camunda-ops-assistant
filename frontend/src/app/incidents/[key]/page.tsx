import { notFound } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { PageShell } from "@/components/Shell";
import { Card, StateBadge } from "@/components/ui";

export default async function IncidentDetailPage({ params }: { params: { key: string } }) {
  let incident;
  try {
    incident = await api.getIncident(params.key);
  } catch {
    notFound();
  }

  return (
    <PageShell title={`Incident ${incident.key}`}>
      <Card className="max-w-xl space-y-3 text-sm">
        <Row label="Key" value={incident.key} />
        <Row
          label="Process Instance"
          value={
            <Link href={`/process-instances/${incident.process_instance_key}`} className="text-blue-400 hover:underline">
              {incident.process_instance_key}
            </Link>
          }
        />
        <Row label="Process Definition" value={incident.process_definition_id} />
        <Row label="Error Type" value={incident.error_type} />
        <Row label="Error Message" value={incident.error_message} />
        <Row label="Flow Node" value={incident.flow_node_id} />
        <Row label="State" value={<StateBadge state={incident.state} />} />
        <Row label="Created" value={new Date(incident.creation_time).toLocaleString()} />
        <Row label="Resolved" value={incident.resolved_time ? new Date(incident.resolved_time).toLocaleString() : "-"} />
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
