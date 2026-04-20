"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/profile", label: "Profile" },
  { href: "/aircraft", label: "Aircraft" },
  { href: "/flights", label: "Flights" },
  { href: "/flights/new", label: "New Flight" },
  { href: "/totals", label: "Totals" }
];

export function AppShell() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <p className="eyebrow">Core Logbook v1</p>
      <h1 className="brand">MyFlightbook</h1>
      <p className="sidebar__copy">
        Side-by-side migration shell for the next web experience. The legacy .NET system remains in the repo while
        this dashboard grows into the new source of truth.
      </p>
      <nav className="nav" aria-label="Primary">
        {navItems.map((item) => {
          const isCurrent = pathname === item.href;
          return (
            <Link key={item.href} href={item.href} aria-current={isCurrent ? "page" : undefined}>
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
