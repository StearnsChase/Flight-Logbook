import type { Aircraft } from "@myflightbook/api-client";
import { MyFlightbookApiClient } from "@myflightbook/api-client";
import { headers } from "next/headers";
import styles from "./page.module.css";

type AircraftFleetResult = {
  aircraft: Aircraft[];
  error: string | null;
};

function createApiClient(authorization: string | null): MyFlightbookApiClient {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

  return new MyFlightbookApiClient(baseUrl, {
    defaultInit: authorization
      ? {
          headers: {
            Authorization: authorization
          }
        }
      : undefined
  });
}

function getErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return "Unable to load your aircraft right now.";
  }

  if (error.message.includes("401")) {
    return "Authentication is not connected to this dashboard yet. Add a bearer token to preview fleet data.";
  }

  return "Unable to load your aircraft right now. Check that the new API is running.";
}

async function getAircraftFleet(): Promise<AircraftFleetResult> {
  const requestHeaders = await headers();
  const authorization = requestHeaders.get("authorization") ?? process.env.MFB_API_BEARER_TOKEN ?? null;

  if (!authorization) {
    return {
      aircraft: [],
      error: "Authentication is not connected to this dashboard yet. Add a bearer token to preview fleet data."
    };
  }

  try {
    const aircraft = await createApiClient(authorization).listAircraft();
    return { aircraft, error: null };
  } catch (error) {
    return { aircraft: [], error: getErrorMessage(error) };
  }
}

function getCapabilityLabels(aircraft: Aircraft): string[] {
  return [
    aircraft.category_class ?? "Category pending",
    aircraft.engine_type ?? "Engine pending",
    aircraft.is_complex ? "Complex" : "Standard",
    aircraft.is_high_performance ? "High performance" : "Normal performance",
    aircraft.is_retractable ? "Retractable" : "Fixed gear"
  ];
}

export default async function AircraftPage() {
  const { aircraft, error } = await getAircraftFleet();

  return (
    <article className={`card ${styles.panel}`}>
      <header className={styles.header}>
        <div className={styles.heading}>
          <p className={styles.kicker}>Aircraft Fleet</p>
          <h1 className="page-title">Aircraft</h1>
          <p className={styles.summary}>
            Your fleet now lives in the new canonical backend. This dashboard page reads directly from the FastAPI
            aircraft endpoint and gives the migration a cleaner home than the old Web Forms flow.
          </p>
        </div>
        <button className={`button button--primary ${styles.placeholderButton}`} type="button" disabled>
          Add Aircraft
        </button>
      </header>

      {error ? (
        <section className={styles.statusCard}>
          <h2 className={styles.statusTitle}>Fleet preview unavailable</h2>
          <p className={styles.statusCopy}>{error}</p>
        </section>
      ) : null}

      {!error && aircraft.length === 0 ? (
        <section className={styles.statusCard}>
          <h2 className={styles.statusTitle}>No aircraft yet</h2>
          <p className={styles.statusCopy}>
            Once aircraft records start flowing into the new backend, they will appear here with configuration and
            capability details.
          </p>
        </section>
      ) : null}

      {aircraft.length > 0 ? (
        <section className={styles.fleetGrid} aria-label="Aircraft fleet">
          {aircraft.map((item) => (
            <article key={item.id} className={styles.aircraftCard}>
              <div className={styles.cardTop}>
                <span className={styles.tailBadge}>{item.tail_number}</span>
                <span className={styles.timestamp}>
                  Added {new Date(item.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                </span>
              </div>

              <div className={styles.cardHeading}>
                <h2 className={styles.aircraftName}>{item.display_name}</h2>
                <p className={styles.aircraftModel}>{item.model_name ?? "Model details pending"}</p>
              </div>

              <dl className={styles.metaGrid}>
                <div>
                  <dt className={styles.metaLabel}>Class</dt>
                  <dd className={styles.metaValue}>{item.category_class ?? "Unknown"}</dd>
                </div>
                <div>
                  <dt className={styles.metaLabel}>Engine</dt>
                  <dd className={styles.metaValue}>{item.engine_type ?? "TBD"}</dd>
                </div>
              </dl>

              <div className={styles.chipRow}>
                {getCapabilityLabels(item).map((label) => (
                  <span key={label} className={styles.chip}>
                    {label}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </section>
      ) : null}
    </article>
  );
}
