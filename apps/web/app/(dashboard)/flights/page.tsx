import type { Aircraft, Flight } from "@myflightbook/api-client";
import { MyFlightbookApiClient } from "@myflightbook/api-client";
import Link from "next/link";
import { headers } from "next/headers";
import styles from "./page.module.css";

const PAGE_SIZE = 12;

type FlightsPageProps = {
  searchParams?: Promise<{
    page?: string | string[];
  }>;
};

type FlightsLogbookResult = {
  aircraftById: Map<string, Aircraft>;
  error: string | null;
  flights: Flight[];
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

function getPageNumber(pageParam: string | string[] | undefined): number {
  const rawValue = Array.isArray(pageParam) ? pageParam[0] : pageParam;
  const parsedValue = Number.parseInt(rawValue ?? "1", 10);

  if (!Number.isFinite(parsedValue) || parsedValue < 1) {
    return 1;
  }

  return parsedValue;
}

function getFlightsHref(page: number): string {
  return page <= 1 ? "/flights" : `/flights?page=${page}`;
}

function getErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return "Unable to load your logbook right now.";
  }

  if (error.message.includes("401")) {
    return "Authentication is not connected to this dashboard yet. Add a bearer token to preview flight data.";
  }

  return "Unable to load your logbook right now. Check that the new API is running.";
}

function formatDateLabel(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric"
  }).format(new Date(value));
}

function formatHours(value: number): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(value);
}

function getAircraftTailNumber(flight: Flight, aircraftById: Map<string, Aircraft>): string {
  return aircraftById.get(flight.aircraft_id)?.tail_number ?? "Unknown";
}

function getRouteLabel(route: string): string {
  const trimmedRoute = route.trim();
  return trimmedRoute.length > 0 ? trimmedRoute : "Route not logged";
}

async function getFlightLogbook(page: number): Promise<FlightsLogbookResult> {
  const requestHeaders = await headers();
  const authorization = requestHeaders.get("authorization") ?? process.env.MFB_API_BEARER_TOKEN ?? null;

  if (!authorization) {
    return {
      aircraftById: new Map(),
      error: "Authentication is not connected to this dashboard yet. Add a bearer token to preview flight data.",
      flights: []
    };
  }

  const offset = (page - 1) * PAGE_SIZE;
  const client = createApiClient(authorization);

  try {
    const [flights, aircraft] = await Promise.all([
      client.listFlights(PAGE_SIZE + 1, offset),
      client.listAircraft()
    ]);

    return {
      aircraftById: new Map(aircraft.map((item) => [item.id, item])),
      error: null,
      flights
    };
  } catch (error) {
    return {
      aircraftById: new Map(),
      error: getErrorMessage(error),
      flights: []
    };
  }
}

export default async function FlightsPage({ searchParams }: FlightsPageProps) {
  const resolvedSearchParams = await searchParams;
  const currentPage = getPageNumber(resolvedSearchParams?.page);
  const { aircraftById, error, flights } = await getFlightLogbook(currentPage);
  const hasPreviousPage = currentPage > 1;
  const hasNextPage = flights.length > PAGE_SIZE;
  const visibleFlights = flights.slice(0, PAGE_SIZE);

  return (
    <article className={`card ${styles.panel}`}>
      <header className={styles.header}>
        <div className={styles.heading}>
          <p className={styles.kicker}>Flight Logbook</p>
          <h1 className="page-title">Flights</h1>
          <p className={styles.summary}>
            Your logbook now reads directly from the FastAPI backend. This page keeps the dashboard focused on recent
            entries while preserving room for richer editing, filtering, and analytics later in the migration.
          </p>
        </div>
        <Link className={`button button--primary ${styles.primaryAction}`} href="/flights/new">
          Log Flight
        </Link>
      </header>

      {error ? (
        <section className={styles.statusCard}>
          <h2 className={styles.statusTitle}>Logbook preview unavailable</h2>
          <p className={styles.statusCopy}>{error}</p>
        </section>
      ) : null}

      {!error && visibleFlights.length === 0 ? (
        <section className={styles.statusCard}>
          <h2 className={styles.statusTitle}>No flights yet</h2>
          <p className={styles.statusCopy}>
            Once flight entries start flowing into the new backend, they will appear here with time breakdowns and
            aircraft context.
          </p>
        </section>
      ) : null}

      {visibleFlights.length > 0 ? (
        <>
          <section className={styles.tableCard} aria-label="Flight logbook">
            <div className={styles.tableScroll}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th scope="col">Date</th>
                    <th scope="col">Aircraft</th>
                    <th scope="col">Route</th>
                    <th scope="col" className={styles.numericHeader}>
                      Total Time
                    </th>
                    <th scope="col" className={styles.numericHeader}>
                      PIC Time
                    </th>
                    <th scope="col" className={styles.numericHeader}>
                      Landings
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {visibleFlights.map((flight) => (
                    <tr key={flight.id}>
                      <td>
                        <div className={styles.primaryCell}>{formatDateLabel(flight.flight_date)}</div>
                      </td>
                      <td>
                        <div className={styles.primaryCell}>{getAircraftTailNumber(flight, aircraftById)}</div>
                      </td>
                      <td className={styles.routeCell}>
                        <div className={styles.primaryCell}>{getRouteLabel(flight.route)}</div>
                      </td>
                      <td className={styles.numericCell}>{formatHours(flight.total_time)}</td>
                      <td className={styles.numericCell}>{formatHours(flight.pic_time)}</td>
                      <td className={styles.numericCell}>{flight.landings}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <footer className={styles.pagination}>
            <p className={styles.paginationLabel}>Page {currentPage}</p>
            <div className={styles.paginationActions}>
              {hasPreviousPage ? (
                <Link className={`button button--secondary ${styles.paginationButton}`} href={getFlightsHref(currentPage - 1)}>
                  Previous
                </Link>
              ) : (
                <span className={`button button--secondary ${styles.paginationButton} ${styles.paginationButtonDisabled}`}>
                  Previous
                </span>
              )}

              {hasNextPage ? (
                <Link className={`button button--secondary ${styles.paginationButton}`} href={getFlightsHref(currentPage + 1)}>
                  Next
                </Link>
              ) : (
                <span className={`button button--secondary ${styles.paginationButton} ${styles.paginationButtonDisabled}`}>
                  Next
                </span>
              )}
            </div>
          </footer>
        </>
      ) : null}
    </article>
  );
}
