import type { Evaluation, Fallback, Operation } from "@/lib/api";

// Test-only fixture. Values are arbitrary and never shown in the app.
const op: Operation = {
  channel: "counter",
  amount: 40000,
  payee: "self",
  new_payee: false,
  foreign: false,
  initiated_by: "client",
  bank_alert: false,
};

const ev = (patch: Partial<Evaluation>): Evaluation => ({
  score: 0.7,
  threshold: 0.5,
  paused: true,
  pause_origin: "score",
  destination: "trusted_contact",
  destination_reason: "",
  response_window_expired: false,
  minutes_left: 30,
  reasons: [{ text: "large cash amount", weight: 0.4 }],
  operation: op,
  ...patch,
});

const results = {
  default: ev({}),
  contact_has_power_of_attorney: ev({
    destination: "bank",
    destination_reason: "the contact holds a power of attorney",
  }),
  contact_did_not_answer_30min: ev({
    destination: "bank",
    response_window_expired: true,
    minutes_left: 0,
  }),
};

export const fixture: Fallback = {
  config: {
    engine_version: "test",
    threshold: 0.5,
    response_window_minutes: 30,
    revocation_delay_hours: 72,
    scope: ["counter"],
    out_of_scope: {},
    default_contact: { name: "Anna", has_power_of_attorney: false, co_holder: false },
    protected_person: { label: "Client", branch: "Branch", usual_weekly_cash_chf: 100 },
  },
  scenarios: [
    { id: "fake-police-cash", title: "A", story: "", phone_message: "", operation: op, results },
    {
      id: "internal-abuse",
      title: "B",
      story: "",
      phone_message: "",
      operation: op,
      results: { ...results, default: ev({ destination: "bank", destination_reason: "insider" }) },
    },
  ],
  stats: {} as Fallback["stats"],
};
