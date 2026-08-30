import Link from "next/link";
import { api } from "@/lib/api";
import { PageShell } from "@/components/Shell";
import { Card, ErrorNotice } from "@/components/ui";

export default async function ProcessDefinitionsPage() {
  try {
    const definitions = await api.listProcessDefinitions();
    return (
      <PageShell title="Process Definitions">
        <Card>
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
                <th className="pb-2">Key</th>
                <th className="pb-2">Process Definition Id</th>
                <th className="pb-2">Name</th>
                <th className="pb-2">Version</th>
                <th className="pb-2">Deployed</th>
              </tr>
            </thead>
            <tbody className="text-slate-200">
              {definitions.map((definition) => (
                <tr key={definition.key} className="border-t border-slate-800">
                  <td className="py-2">
                    <Link href={`/process-definitions/${definition.key}`} className="text-blue-400 hover:underline">
                      {definition.key}
                    </Link>
                  </td>
                  <td className="py-2">{definition.process_definition_id}</td>
                  <td className="py-2">{definition.name}</td>
                  <td className="py-2">{definition.version}</td>
                  <td className="py-2">{new Date(definition.deployment_time).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </PageShell>
    );
  } catch (error) {
    return (
      <PageShell title="Process Definitions">
        <ErrorNotice message={error instanceof Error ? error.message : "Unknown error"} />
      </PageShell>
    );
  }
}
