import Link from "next/link";
import { getFlights } from "@/lib/api";
import { formatDateLabel, formatHours } from "@/lib/format";

export default async function FlightsPage() {
  const flights = await getFlights();

  return (
    <article className="card">
      <div style={{ display: "flex", justifyContent: "space-between", gap: "16px", alignItems: "center" }}>
        <div>
          <h1 className="page-title">Flights</h1>
          <p>Logbook entries created in the new canonical schema. Edit flows and validation parity come next.</p>
        </div>
        <Link className="button button--primary" href="/flights/new">
          New flight
        </Link>
      </div>
      <ul className="data-list">
        {flights.length === 0 ? (
          <li className="muted">No flights yet. Seed one from the composer to exercise the new stack.</li>
        ) : (
          flights.map((flight) => (
            <li key={flight.id} className="data-row">
              <div>
                <div className="data-row__title">{formatDateLabel(flight.flight_date)} · {flight.route || "No route"}</div>
                <div className="data-row__meta">
                  PIC {formatHours(flight.pic_time)} · XC {formatHours(flight.cross_country)} · Night {formatHours(flight.night)}
                </div>
              </div>
              <div className="data-row__meta">{formatHours(flight.total_time)} total</div>
            </li>
          ))
        )}
      </ul>
    </article>
  );
}
