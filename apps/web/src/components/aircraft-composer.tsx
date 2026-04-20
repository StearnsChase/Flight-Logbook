"use client";

import { useRouter } from "next/navigation";
import { startTransition, useState } from "react";
import { createAircraft } from "@/lib/api";

const initialState = {
  tail_number: "",
  display_name: "",
  model_name: "",
  category_class: "",
  engine_type: ""
};

export function AircraftComposer() {
  const [form, setForm] = useState(initialState);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const router = useRouter();

  async function onSubmit(formData: FormData) {
    setError(null);
    setSuccess(null);

    try {
      await createAircraft({
        tail_number: String(formData.get("tail_number") ?? ""),
        display_name: String(formData.get("display_name") ?? ""),
        model_name: String(formData.get("model_name") ?? "") || null,
        category_class: String(formData.get("category_class") ?? "") || null,
        engine_type: String(formData.get("engine_type") ?? "") || null,
        is_complex: Boolean(formData.get("is_complex")),
        is_high_performance: Boolean(formData.get("is_high_performance")),
        is_retractable: Boolean(formData.get("is_retractable"))
      });
      setForm(initialState);
      setSuccess("Aircraft saved to the new canonical backend.");
      startTransition(() => router.refresh());
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "Unable to create aircraft.");
    }
  }

  return (
    <article className="form-card">
      <h2>Add aircraft</h2>
      <p className="muted">Seed the new aircraft context here before wiring the legacy import path.</p>
      <form action={onSubmit} className="form-grid">
        <div className="field">
          <label htmlFor="tail_number">Tail number</label>
          <input
            id="tail_number"
            name="tail_number"
            value={form.tail_number}
            onChange={(event) => setForm((current) => ({ ...current, tail_number: event.target.value }))}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="display_name">Display name</label>
          <input
            id="display_name"
            name="display_name"
            value={form.display_name}
            onChange={(event) => setForm((current) => ({ ...current, display_name: event.target.value }))}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="model_name">Model</label>
          <input
            id="model_name"
            name="model_name"
            value={form.model_name}
            onChange={(event) => setForm((current) => ({ ...current, model_name: event.target.value }))}
          />
        </div>
        <div className="field">
          <label htmlFor="category_class">Category/class</label>
          <input
            id="category_class"
            name="category_class"
            value={form.category_class}
            onChange={(event) => setForm((current) => ({ ...current, category_class: event.target.value }))}
          />
        </div>
        <div className="field">
          <label htmlFor="engine_type">Engine type</label>
          <input
            id="engine_type"
            name="engine_type"
            value={form.engine_type}
            onChange={(event) => setForm((current) => ({ ...current, engine_type: event.target.value }))}
          />
        </div>
        <div className="field">
          <label>Flags</label>
          <div className="actions" style={{ marginTop: 0 }}>
            <label><input name="is_complex" type="checkbox" /> Complex</label>
            <label><input name="is_high_performance" type="checkbox" /> High performance</label>
            <label><input name="is_retractable" type="checkbox" /> Retractable</label>
          </div>
        </div>
        <div className="field field--full">
          <button className="button button--primary" type="submit">Create aircraft</button>
          {error ? <div className="error">{error}</div> : null}
          {success ? <div className="success">{success}</div> : null}
        </div>
      </form>
    </article>
  );
}
