import Link from "next/link";
import { FlightComposer } from "@/components/flight-composer";
import { getAircraft } from "@/lib/api";

export default async function NewFlightPage() {
  const aircraft = await getAircraft();

  return (
    <>
      <article className="card">
        <h1 className="page-title">Create flight</h1>
        <p>
          This form writes directly to the new FastAPI backend. It is intentionally lean right now: the goal is
          to prove the canonical flight shape before replaying legacy validation and import behavior.
        </p>
        {aircraft.length === 0 ? (
          <div className="actions">
            <Link className="button button--primary" href="/aircraft">
              Add an aircraft first
            </Link>
          </div>
        ) : (
          <FlightComposer aircraft={aircraft} />
        )}
      </article>
    </>
  );
}
