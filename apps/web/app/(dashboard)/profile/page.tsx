import { getProfile, getTelemetryUploads } from "@/lib/api";

export default async function ProfilePage() {
  const [profile, telemetry] = await Promise.all([getProfile(), getTelemetryUploads()]);

  return (
    <>
      <article className="card">
        <h1 className="page-title">Pilot profile</h1>
        <p>
          This page is already backed by the new REST API. The current implementation uses a development
          bootstrap identity until Google and Apple verification are wired in.
        </p>
        {profile ? (
          <div className="grid grid--2">
            <div className="metric-tile">
              <span>Email</span>
              <strong>{profile.email}</strong>
            </div>
            <div className="metric-tile">
              <span>Display name</span>
              <strong>{profile.display_name}</strong>
            </div>
            <div className="metric-tile">
              <span>Locale</span>
              <strong>{profile.locale}</strong>
            </div>
            <div className="metric-tile">
              <span>Legacy username</span>
              <strong>{profile.legacy_username ?? "Not linked yet"}</strong>
            </div>
          </div>
        ) : (
          <p className="muted">The backend is not reachable yet. Start the API to load profile data.</p>
        )}
      </article>
      <article className="card">
        <h2>Telemetry queue</h2>
        <p>The worker handoff is deferred, but uploads are already modeled in the canonical schema.</p>
        <ul className="data-list">
          {telemetry.length === 0 ? (
            <li className="muted">No telemetry uploads queued yet.</li>
          ) : (
            telemetry.map((upload) => (
              <li key={upload.id} className="data-row">
                <div>
                  <div className="data-row__title">{upload.original_filename}</div>
                  <div className="data-row__meta">
                    {upload.source_format.toUpperCase()} · {upload.parse_status}
                  </div>
                </div>
                <div className="data-row__meta">{new Date(upload.created_at).toLocaleString()}</div>
              </li>
            ))
          )}
        </ul>
      </article>
    </>
  );
}
