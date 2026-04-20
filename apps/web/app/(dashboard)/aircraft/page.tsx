import { AircraftComposer } from "@/components/aircraft-composer";
import { getAircraft } from "@/lib/api";

export default async function AircraftPage() {
  const aircraft = await getAircraft();

  return (
    <>
      <AircraftComposer />
      <article className="card">
        <h1 className="page-title">Aircraft</h1>
        <p>The new canonical aircraft records are owned per pilot and no longer depend on legacy Web Forms models.</p>
        <ul className="data-list">
          {aircraft.length === 0 ? (
            <li className="muted">No aircraft yet. Add one using the composer above.</li>
          ) : (
            aircraft.map((item) => (
              <li key={item.id} className="data-row">
                <div>
                  <div className="data-row__title">
                    {item.tail_number} · {item.display_name}
                  </div>
                  <div className="data-row__meta">
                    {item.model_name ?? "Unspecified model"} · {item.category_class ?? "Unknown class"}
                  </div>
                </div>
                <div className="data-row__meta">
                  {item.is_complex ? "Complex" : "Standard"} / {item.engine_type ?? "Engine TBD"}
                </div>
              </li>
            ))
          )}
        </ul>
      </article>
    </>
  );
}
