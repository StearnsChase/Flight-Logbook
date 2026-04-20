import type {
  Aircraft,
  Flight,
  ImageAsset,
  TelemetryUpload,
  TotalsSummary,
  UserProfile
} from "@myflightbook/api-client";

type AircraftCreatePayload = {
  tail_number: string;
  display_name: string;
  model_name: string | null;
  category_class: string | null;
  engine_type: string | null;
  is_complex: boolean;
  is_high_performance: boolean;
  is_retractable: boolean;
};

type FlightCreatePayload = {
  aircraft_id: string;
  flight_date: string;
  route: string;
  remarks: string | null;
  total_time: number;
  pic_time: number;
  sic_time: number;
  dual_given: number;
  dual_received: number;
  cross_country: number;
  night: number;
  imc: number;
  simulated_instrument: number;
  landings: number;
  full_stop_landings_day: number;
  full_stop_landings_night: number;
  approaches: number;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(new URL(path, API_BASE_URL), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

async function safeRequest<T>(path: string): Promise<T | null> {
  try {
    return await request<T>(path);
  } catch {
    return null;
  }
}

export async function getApiHealth(): Promise<{ status: string } | null> {
  return safeRequest<{ status: string }>("/healthz");
}

export async function getProfile(): Promise<UserProfile | null> {
  return safeRequest<UserProfile>("/api/v1/profile");
}

export async function getAircraft(): Promise<Aircraft[]> {
  return (await safeRequest<Aircraft[]>("/api/v1/aircraft")) ?? [];
}

export async function getFlights(): Promise<Flight[]> {
  return (await safeRequest<Flight[]>("/api/v1/flights")) ?? [];
}

export async function getTotals(): Promise<TotalsSummary | null> {
  return safeRequest<TotalsSummary>("/api/v1/totals");
}

export async function getTelemetryUploads(): Promise<TelemetryUpload[]> {
  return (await safeRequest<TelemetryUpload[]>("/api/v1/telemetry/uploads")) ?? [];
}

export async function getImages(): Promise<ImageAsset[]> {
  return (await safeRequest<ImageAsset[]>("/api/v1/images")) ?? [];
}

export async function createAircraft(payload: AircraftCreatePayload): Promise<Aircraft> {
  return request<Aircraft>("/api/v1/aircraft", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createFlight(payload: FlightCreatePayload): Promise<Flight> {
  return request<Flight>("/api/v1/flights", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
