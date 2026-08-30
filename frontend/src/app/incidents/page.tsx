import Link from "next/link";
import { api } from "@/lib/api";
import { PageShell } from "@/components/Shell";
import { Card, ErrorNotice, StateBadge } from "@/components/ui";

export default async function IncidentsPage() {
  try {
    const incidents = await api.listIncidents();
    return (
      <PageShell title="Incidents">
        <Card>
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
                <th className="pb-2">Key</th>
                <th className="pb-2">Process Instance</th>
                <th className="pb-2">Error Type</th>
                <th className="pb-2">Flow Node</th>
                <th className="pb-2">State</th>
              </tr>
            </thead>
            <tbody className="text-slate-200">
              {incidents.map((incident) => (
                <tr key={incident.key} className="border-t border-slate-800">
                  <td className="py-2">
                    <Link href={`/incidents/${incident.key}`} className="text-blue-400 hover:underline">
                      {incident.key}
                    </Link>
                  </td>
                  <td className="py-2">{incident.process_instance_key}</td>
                  <td className="py-2">{incident.error_type}</td>
                  <td className="py-2">{incident.flow_node_id}</td>
                  <td className="py-2">
                    <StateBadge state={incident.state} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </PageShell>
    );
  } catch (error) {
    return (
      <PageShell title="Incidents">
        <ErrorNotice message={error instanceof Error ? error.message : "Unknown error"} />
      </PageShell>
    );
  }
}
