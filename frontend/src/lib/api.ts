/**
 * Sentinel API client — contract with the FastAPI back-end (do not rename fields).
 * Every request has a 3 s timeout; on any failure the bundled /demo-fallback.json is used.
 */

export type Channel = "counter" | "atm" | "safe_deposit_box" | "transfer" | "card";
export interface Operation {
  channel: Channel;
  amount: number;
  payee: string;
  new_payee: boolean;
  foreign: boolean;
  initiated_by: string;
  bank_alert: boolean;
}
export interface Contact {
  name: string;
  has_power_of_attorney: boolean;
  co_holder: boolean;
}
export interface Reason {
  text: string;
  weight: number | null;
}
export interface Evaluation {
  score: number;
  threshold: number;
  paused: boolean;
  pause_origin: "score" | "bank_antifraud" | null;
  destination: "trusted_contact" | "bank" | null;
  destination_reason: string;
  response_window_expired: boolean;
  minutes_left: number | null;
  reasons: Reason[];
  operation: Operation;
}
export interface Scenario {
  id: string;
  title: string;
  story: string;
  phone_message: string;
  operation: Operation;
}
export interface Config {
  engine_version: string;
  threshold: number;
  response_window_minutes: number;
  revocation_delay_hours: number;
  scope: Channel[];
  out_of_scope: Record<string, string>;
  default_contact: Contact;
  protected_person: { label: string; branch: string; usual_weekly_cash_chf: number };
}
export interface Stats {
  threshold: number;
  auc: number;
  simulated_clients: number;
  alerts_per_client_year: number;
  share_resolved_by_contact: number;
  share_escalated_to_bank: number;
  cost_to_serve_chf: number;
  fraud_episodes_caught: number;
  fraud_money_protected: number;
  note: string;
  cost_curve: { threshold: number; cost_chf: number }[];
  roc_curve: { fpr: number; tpr: number }[];
}
export interface Revocation {
  requested_at: string;
  effective_at: string;
  delay_hours: number;
  contact_notified: boolean;
}

export interface EvaluateRequest {
  scenario_id: string;
  contact: Contact;
  contact_answered: boolean;
  minutes_elapsed: number;
}

export interface FallbackScenario extends Scenario {
  results: {
    default: Evaluation;
    contact_has_power_of_attorney: Evaluation;
    contact_did_not_answer_30min: Evaluation;
  };
}
export interface Fallback {
  config: Config;
  scenarios: FallbackScenario[];
  stats: Stats;
}

export type DataSource = "live" | "offline";
export interface Sourced<T> {
  data: T;
  source: DataSource;
}

export const API_URL: string = ((import.meta.env["VITE_API_URL"] as string | undefined) ?? "")
  .trim()
  .replace(/\/+$/, "");

const TIMEOUT_MS = 3000;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_URL) throw new Error("VITE_API_URL is not set");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
    if (!res.ok) throw new Error(`${path} answered ${res.status}`);
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

let fallbackPromise: Promise<Fallback> | null = null;
export function loadFallback(): Promise<Fallback> {
  if (!fallbackPromise) {
    fallbackPromise = fetch("/demo-fallback.json")
      .then((res) => {
        if (!res.ok) throw new Error("demo-fallback.json not found");
        return res.json() as Promise<Fallback>;
      })
      .catch((err) => {
        fallbackPromise = null; // allow a retry later
        throw err;
      });
  }
  return fallbackPromise;
}

/** Offline equivalent of POST /evaluate, following the rules agreed with the back-end. */
export function offlineEvaluate(fb: Fallback, req: EvaluateRequest): Evaluation {
  const scenario = fb.scenarios.find((s) => s.id === req.scenario_id);
  if (!scenario) throw new Error(`Unknown scenario ${req.scenario_id}`);
  const { results } = scenario;
  const windowMinutes = fb.config.response_window_minutes;
  const clone = (e: Evaluation): Evaluation => JSON.parse(JSON.stringify(e)) as Evaluation;

  // Internal abuse is always a bank case: keep the precomputed result.
  if (scenario.id === "internal-abuse") return clone(results.default);

  const { has_power_of_attorney, co_holder } = req.contact;
  if (has_power_of_attorney || co_holder) {
    const r = clone(results.contact_has_power_of_attorney);
    if (co_holder && !has_power_of_attorney) {
      r.destination_reason = "the contact is a co-holder of the account";
    }
    return r;
  }
  if (!req.contact_answered && req.minutes_elapsed >= windowMinutes) {
    return clone(results.contact_did_not_answer_30min);
  }
  const r = clone(results.default);
  if (r.destination === "trusted_contact") {
    r.minutes_left = Math.max(0, windowMinutes - req.minutes_elapsed);
  }
  return r;
}

export function offlineRevocation(fb: Fallback, now: Date = new Date()): Revocation {
  const delay = fb.config.revocation_delay_hours;
  return {
    requested_at: now.toISOString(),
    effective_at: new Date(now.getTime() + delay * 3_600_000).toISOString(),
    delay_hours: delay,
    contact_notified: true,
  };
}

function stripResults(s: FallbackScenario): Scenario {
  const { results: _results, ...rest } = s;
  return rest;
}

/** Client bound to the current "online" decision; falls back on any error. */
export function createApi(useLive: () => boolean) {
  async function withFallback<T>(
    live: () => Promise<T>,
    offline: (fb: Fallback) => T,
  ): Promise<Sourced<T>> {
    if (useLive()) {
      try {
        return { data: await live(), source: "live" };
      } catch {
        /* fall through to offline data */
      }
    }
    const fb = await loadFallback();
    return { data: offline(fb), source: "offline" };
  }

  return {
    health: async (): Promise<boolean> => {
      if (!API_URL) return false;
      try {
        const h = await request<{ status: string; version?: string }>("/health");
        return h.status === "ok";
      } catch {
        return false;
      }
    },
    getConfig: () => withFallback(() => request<Config>("/config"), (fb) => fb.config),
    getScenarios: () =>
      withFallback(
        () => request<Scenario[]>("/scenarios"),
        (fb) => fb.scenarios.map(stripResults),
      ),
    getStats: () => withFallback(() => request<Stats>("/stats"), (fb) => fb.stats),
    evaluate: (body: EvaluateRequest) =>
      withFallback(
        () => request<Evaluation>("/evaluate", { method: "POST", body: JSON.stringify(body) }),
        (fb) => offlineEvaluate(fb, body),
      ),
    revocation: () =>
      withFallback(
        () => request<Revocation>("/revocation", { method: "POST", body: "{}" }),
        (fb) => offlineRevocation(fb),
      ),
  };
}

export type SentinelApi = ReturnType<typeof createApi>;
