import Link from "next/link";
import { ReactNode } from "react";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/process-instances", label: "Process Instances" },
  { href: "/incidents", label: "Incidents" },
  { href: "/process-definitions", label: "Process Definitions" },
  { href: "/investigation", label: "AI Investigation" },
  { href: "/knowledge-base", label: "Documents / Knowledge Base" },
];

export function Sidebar() {
  return (
    <aside className="w-64 shrink-0 border-r border-slate-800 bg-panel/60 p-4">
      <div className="mb-6 px-2">
        <h1 className="text-lg font-semibold text-slate-100">Camunda AI Ops</h1>
        <p className="text-xs text-slate-400">Operations Assistant</p>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-md px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}

export function PageShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex-1 p-8">
      <h2 className="mb-6 text-2xl font-semibold text-slate-100">{title}</h2>
      {children}
    </div>
  );
}
