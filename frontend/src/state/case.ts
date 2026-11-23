import type { Evaluation } from "@/lib/api";

/** The bank's final decision. */
export type Decision = "approved" | "blocked";

/**
 * The trusted contact's answer. "confirmed" releases the hold the client asked for;
 * "stopped" is not a veto: the operation stays on hold and goes to the bank, which
 * speaks with the client and takes the final decision.
 */
export type ContactDecision = "confirmed" | "stopped";

export type CaseState =
  | "inactive"
  | "loading"
  | "proceed"
  | "waiting_contact"
  | "with_bank"
  | "stopped_by_contact"
  | "expired"
  | "approved"
  | "blocked";

export interface CaseView {
  state: CaseState;
  decidedBy: "contact" | "bank" | null;
}

/**
 * Does this case belong in the bank's queue? Conflicts of interest and unanswered cases
 * (routed to the bank by the engine), and every operation the trusted contact stopped.
 */
export function inBankQueue(
  ev: Pick<Evaluation, "paused" | "destination"> | undefined,
  contactDecision: ContactDecision | undefined,
): boolean {
  if (!ev?.paused) return false;
  return ev.destination === "bank" || contactDecision === "stopped";
}

/** Single source of truth for what the counter, phone and bank queue show. */
export function deriveCase(
  consent: boolean,
  ev: Evaluation | undefined,
  contactDecision: ContactDecision | undefined,
  bankDecision: Decision | undefined,
): CaseView {
  if (!consent) return { state: "inactive", decidedBy: null };
  if (!ev) return { state: "loading", decidedBy: null };
  if (!ev.paused) return { state: "proceed", decidedBy: null };
  if (ev.destination === "trusted_contact") {
    if (contactDecision === "confirmed") return { state: "approved", decidedBy: "contact" };
    if (contactDecision === "stopped") {
      // Not a veto: the bank reviews it with the client and decides.
      if (bankDecision) return { state: bankDecision, decidedBy: "bank" };
      return { state: "stopped_by_contact", decidedBy: "contact" };
    }
    return { state: "waiting_contact", decidedBy: null };
  }
  if (bankDecision) return { state: bankDecision, decidedBy: "bank" };
  if (ev.response_window_expired) return { state: "expired", decidedBy: null };
  return { state: "with_bank", decidedBy: null };
}
