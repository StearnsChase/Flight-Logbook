import type { ReactNode } from "react";
import { AppShell } from "@/components/app-shell";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <main className="page dashboard">
      <AppShell />
      <section className="content">{children}</section>
    </main>
  );
}
