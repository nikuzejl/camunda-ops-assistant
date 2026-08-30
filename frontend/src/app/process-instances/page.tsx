import Link from "next/link";
import { api } from "@/lib/api";
import { PageShell } from "@/components/Shell";
import { Card, ErrorNotice, StateBadge } from "@/components/ui";

export default async function ProcessInstancesPage() {
  try {
    const instances = await api.listProcessInstances();
    return (
      <PageShell title="Process Instances">
        <Card>
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
                <th className="pb-2">Key</th>
                <th className="pb-2">Process Definition</th>
                <th className="pb-2">Version</th>
                <th className="pb-2">State</th>
                <th className="pb-2">Started</th>
              </tr>
            </thead>
            <tbody className="text-slate-200">
              {instances.map((instance) => (
                <tr key={instance.key} className="border-t border-slate-800">
                  <td className="py-2">
                    <Link href={`/process-instances/${instance.key}`} className="text-blue-400 hover:underline">
                      {instance.key}
                    </Link>
                  </td>
                  <td className="py-2">{instance.process_definition_id}</td>
                  <td className="py-2">{instance.version}</td>
                  <td className="py-2">
                    <StateBadge state={instance.state} />
                  </td>
                  <td className="py-2">{new Date(instance.start_date).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </PageShell>
    );
  } catch (error) {
    return (
      <PageShell title="Process Instances">
        <ErrorNotice message={error instanceof Error ? error.message : "Unknown error"} />
      </PageShell>
    );
  }
}
