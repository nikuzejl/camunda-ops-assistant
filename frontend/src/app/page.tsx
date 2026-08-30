import { api } from "@/lib/api";
import { PageShell } from "@/components/Shell";
import { Card, ErrorNotice, StatCard, StateBadge } from "@/components/ui";
import Link from "next/link";

export default async function OverviewPage() {
  try {
    const [instances, incidents] = await Promise.all([
      api.listProcessInstances(),
      api.listIncidents(),
    ]);

    const activeInstances = instances.filter((i) => i.state === "ACTIVE" || i.state === "INCIDENT");
    const activeIncidents = incidents.filter((i) => i.state === "ACTIVE");
    const recentFailures = incidents.slice(0, 5);

    return (
      <PageShell title="Overview">
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard label="Active Process Instances" value={activeInstances.length} />
          <StatCard label="Active Incidents" value={activeIncidents.length} tone={activeIncidents.length > 0 ? "danger" : "success"} />
          <StatCard label="Process Definitions" value={(await api.listProcessDefinitions()).length} />
        </div>

        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200">Recent Failures</h3>
            <Link href="/incidents" className="text-xs text-blue-400 hover:underline">
              View all incidents
            </Link>
          </div>
          {recentFailures.length === 0 ? (
            <p className="text-sm text-slate-400">No incidents recorded.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-slate-400">
                <tr>
                  <th className="pb-2">Incident</th>
                  <th className="pb-2">Process Instance</th>
                  <th className="pb-2">Error</th>
                  <th className="pb-2">State</th>
                </tr>
              </thead>
              <tbody className="text-slate-200">
                {recentFailures.map((incident) => (
                  <tr key={incident.key} className="border-t border-slate-800">
                    <td className="py-2">
                      <Link href={`/incidents/${incident.key}`} className="text-blue-400 hover:underline">
                        {incident.key}
                      </Link>
                    </td>
                    <td className="py-2">{incident.process_instance_key}</td>
                    <td className="py-2">{incident.error_type}</td>
                    <td className="py-2">
                      <StateBadge state={incident.state} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <div className="mt-6">
          <Link
            href="/investigation"
            className="inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
          >
            Start AI Investigation
          </Link>
        </div>
      </PageShell>
    );
  } catch (error) {
    return (
      <PageShell title="Overview">
        <ErrorNotice message={error instanceof Error ? error.message : "Unknown error"} />
      </PageShell>
    );
  }
}
