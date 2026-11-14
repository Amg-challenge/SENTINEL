import type { Evaluation } from "@/lib/api";

export type Decision = "approved" | "blocked";

export type CaseState =
  | "inactive"
  | "loading"
  | "proceed"
  | "waiting_contact"
  | "with_bank"
  | "expired"
  | "approved"
  | "blocked";

export interface CaseView {
  state: CaseState;
  decidedBy: "contact" | "bank" | null;
}

/** Single source of truth for what the counter, phone and bank queue show. */
export function deriveCase(
  consent: boolean,
  ev: Evaluation | undefined,
  contactDecision: Decision | undefined,
  bankDecision: Decision | undefined,
): CaseView {
  if (!consent) return { state: "inactive", decidedBy: null };
  if (!ev) return { state: "loading", decidedBy: null };
  if (!ev.paused) return { state: "proceed", decidedBy: null };
  if (ev.destination === "trusted_contact") {
    if (contactDecision) return { state: contactDecision, decidedBy: "contact" };
    return { state: "waiting_contact", decidedBy: null };
  }
  if (bankDecision) return { state: bankDecision, decidedBy: "bank" };
  if (ev.response_window_expired) return { state: "expired", decidedBy: null };
  return { state: "with_bank", decidedBy: null };
}
