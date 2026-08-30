import { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-lg border border-slate-800 bg-panel/60 p-4 ${className}`}>
      {children}
    </div>
  );
}

export function StatCard({ label, value, tone = "default" }: { label: string; value: string | number; tone?: "default" | "danger" | "warning" | "success" }) {
  const toneClasses: Record<string, string> = {
    default: "text-slate-100",
    danger: "text-red-400",
    warning: "text-amber-400",
    success: "text-emerald-400",
  };
  return (
    <Card>
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-2 text-3xl font-semibold ${toneClasses[tone]}`}>{value}</p>
    </Card>
  );
}

export function StateBadge({ state }: { state: string }) {
  const colors: Record<string, string> = {
    ACTIVE: "bg-blue-500/20 text-blue-300",
    COMPLETED: "bg-emerald-500/20 text-emerald-300",
    TERMINATED: "bg-slate-500/20 text-slate-300",
    INCIDENT: "bg-red-500/20 text-red-300",
    RESOLVED: "bg-emerald-500/20 text-emerald-300",
  };
  return (
    <span className={`rounded-full px-2 py-1 text-xs font-medium ${colors[state] ?? "bg-slate-500/20 text-slate-300"}`}>
      {state}
    </span>
  );
}

export function ErrorNotice({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-800 bg-red-950/40 p-4 text-sm text-red-300">
      Failed to load data from the backend: {message}
    </div>
  );
}
