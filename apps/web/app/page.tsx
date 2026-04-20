import Link from "next/link";
import { getApiHealth } from "@/lib/api";

export default async function HomePage() {
  const health = await getApiHealth();

  return (
    <main className="page">
      <section className="hero">
        <div className="hero__panel">
          <div className="eyebrow">Migration Workspace</div>
          <h1 className="headline">MyFlightbook, rebuilt for the next decade.</h1>
          <p className="lede">
            This workspace stands up the first greenfield slice of the migration plan: a typed FastAPI
            backend, a Next.js web experience, a canonical Postgres/PostGIS schema, and import scaffolding
            against the current MySQL application.
          </p>
          <div className="pill-row">
            <span className="pill">FastAPI + SQLAlchemy</span>
            <span className="pill">Next.js App Router</span>
            <span className="pill">Postgres + PostGIS</span>
            <span className="pill">Legacy import mapping</span>
          </div>
          <div className="cta-row">
            <Link className="button button--primary" href="/profile">
              Open v1 dashboard
            </Link>
            <Link className="button button--secondary" href="/flights/new">
              Create a new flight
            </Link>
          </div>
        </div>
        <div className="hero__stats">
          <article className="stat-card hero__panel">
            <div className="stat-card__label">API health</div>
            <div className="stat-card__value">{health ? "Online-ready" : "Needs backend"}</div>
            <div className="stat-card__meta">
              The web app is wired to the new REST API. If the backend is not running yet, pages still render
              with empty-state messaging instead of failing hard.
            </div>
          </article>
          <article className="stat-card hero__panel">
            <div className="stat-card__label">Core v1</div>
            <div className="stat-card__value">Profile, aircraft, flights, totals</div>
            <div className="stat-card__meta">
              Admin, billing, public sharing extras, and partner integrations remain outside this first
              release boundary.
            </div>
          </article>
          <article className="stat-card hero__panel">
            <div className="stat-card__label">Legacy status</div>
            <div className="stat-card__value">Reference and import source</div>
            <div className="stat-card__meta">
              The existing .NET application stays intact while the new platform grows beside it.
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
