import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Shell";

export const metadata: Metadata = {
  title: "Camunda AI Operations Assistant",
  description: "Investigate Camunda 8 process instances and incidents with AI assistance.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <Sidebar />
          {children}
        </div>
      </body>
    </html>
  );
}
