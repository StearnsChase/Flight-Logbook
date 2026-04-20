import { getFlights, getTotals } from "@/lib/api";
import { formatHours } from "@/lib/format";

export default async function TotalsPage() {
  const [totals, flights] = await Promise.all([getTotals(), getFlights()]);

  return (
    <>
      <article className="card">
        <h1 className="page-title">Totals</h1>
        <p>This summary is computed by the new backend service so it can become the parity harness for legacy totals later.</p>
        {totals ? (
          <div className="metric-grid">
            <div className="metric-tile">
              <span>Total time</span>
              <strong>{formatHours(totals.total_flight_time)}</strong>
            </div>
            <div className="metric-tile">
              <span>PIC</span>
              <strong>{formatHours(totals.pic_time)}</strong>
            </div>
            <div className="metric-tile">
              <span>Cross-country</span>
              <strong>{formatHours(totals.cross_country)}</strong>
            </div>
            <div className="metric-tile">
              <span>Night</span>
              <strong>{formatHours(totals.night)}</strong>
            </div>
            <div className="metric-tile">
              <span>Approaches</span>
              <strong>{totals.approaches}</strong>
            </div>
            <div className="metric-tile">
              <span>Flights</span>
              <strong>{totals.flight_count}</strong>
            </div>
          </div>
        ) : (
          <p className="muted">The backend is not reachable yet, so totals cannot be calculated.</p>
        )}
      </article>
      <article className="card">
        <h2>Recent flight sample</h2>
        <p>The totals service currently derives from canonical flights only. Legacy replay checks will attach here next.</p>
        <ul className="data-list">
          {flights.slice(0, 5).map((flight) => (
            <li key={flight.id} className="data-row">
              <div className="data-row__title">{flight.route || "No route"}</div>
              <div className="data-row__meta">{formatHours(flight.total_time)} total</div>
            </li>
          ))}
        </ul>
      </article>
    </>
  );
}
