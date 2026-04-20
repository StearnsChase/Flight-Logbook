"use client";

import type { Aircraft } from "@myflightbook/api-client";
import { useRouter } from "next/navigation";
import { startTransition, useState } from "react";
import { createFlight } from "@/lib/api";

interface FlightComposerProps {
  aircraft: Aircraft[];
}

export function FlightComposer({ aircraft }: FlightComposerProps) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(formData: FormData) {
    setError(null);
    setSuccess(null);

    try {
      await createFlight({
        aircraft_id: String(formData.get("aircraft_id")),
        flight_date: String(formData.get("flight_date")),
        route: String(formData.get("route") ?? ""),
        remarks: String(formData.get("remarks") ?? "") || null,
        total_time: Number(formData.get("total_time") ?? 0),
        pic_time: Number(formData.get("pic_time") ?? 0),
        cross_country: Number(formData.get("cross_country") ?? 0),
        night: Number(formData.get("night") ?? 0),
        approaches: Number(formData.get("approaches") ?? 0),
        landings: Number(formData.get("landings") ?? 0),
        full_stop_landings_day: Number(formData.get("full_stop_landings_day") ?? 0),
        full_stop_landings_night: Number(formData.get("full_stop_landings_night") ?? 0),
        dual_given: 0,
        dual_received: 0,
        sic_time: 0,
        imc: 0,
        simulated_instrument: 0
      });
      setSuccess("Flight saved to the canonical v1 backend.");
      startTransition(() => router.push("/flights"));
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "Unable to save flight.");
    }
  }

  return (
    <form action={onSubmit} className="form-grid">
      <div className="field">
        <label htmlFor="aircraft_id">Aircraft</label>
        <select id="aircraft_id" name="aircraft_id" defaultValue={aircraft[0]?.id} required>
          {aircraft.map((item) => (
            <option key={item.id} value={item.id}>
              {item.tail_number} · {item.display_name}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="flight_date">Date</label>
        <input id="flight_date" name="flight_date" type="date" required defaultValue={new Date().toISOString().slice(0, 10)} />
      </div>
      <div className="field field--full">
        <label htmlFor="route">Route</label>
        <input id="route" name="route" placeholder="KDEN-KASE" />
      </div>
      <div className="field">
        <label htmlFor="total_time">Total time</label>
        <input id="total_time" name="total_time" type="number" step="0.1" min="0" defaultValue="1.0" />
      </div>
      <div className="field">
        <label htmlFor="pic_time">PIC time</label>
        <input id="pic_time" name="pic_time" type="number" step="0.1" min="0" defaultValue="1.0" />
      </div>
      <div className="field">
        <label htmlFor="cross_country">Cross-country</label>
        <input id="cross_country" name="cross_country" type="number" step="0.1" min="0" defaultValue="0" />
      </div>
      <div className="field">
        <label htmlFor="night">Night</label>
        <input id="night" name="night" type="number" step="0.1" min="0" defaultValue="0" />
      </div>
      <div className="field">
        <label htmlFor="approaches">Approaches</label>
        <input id="approaches" name="approaches" type="number" step="1" min="0" defaultValue="0" />
      </div>
      <div className="field">
        <label htmlFor="landings">Landings</label>
        <input id="landings" name="landings" type="number" step="1" min="0" defaultValue="1" />
      </div>
      <div className="field">
        <label htmlFor="full_stop_landings_day">Full-stop day</label>
        <input id="full_stop_landings_day" name="full_stop_landings_day" type="number" step="1" min="0" defaultValue="1" />
      </div>
      <div className="field">
        <label htmlFor="full_stop_landings_night">Full-stop night</label>
        <input id="full_stop_landings_night" name="full_stop_landings_night" type="number" step="1" min="0" defaultValue="0" />
      </div>
      <div className="field field--full">
        <label htmlFor="remarks">Remarks</label>
        <textarea id="remarks" name="remarks" rows={5} placeholder="Migration bootstrap entry" />
      </div>
      <div className="field field--full">
        <button className="button button--primary" type="submit">Save flight</button>
        {error ? <div className="error">{error}</div> : null}
        {success ? <div className="success">{success}</div> : null}
      </div>
    </form>
  );
}
