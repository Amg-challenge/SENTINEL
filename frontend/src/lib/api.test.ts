import { describe, expect, it } from "vitest";

import { fixture } from "@/test/fixtures/fallback";
import { offlineEvaluate, offlineRevocation } from "./api";
import { formatChf, splitAmount } from "./format";

const base = {
  scenario_id: "fake-police-cash",
  contact: { name: "Anna", has_power_of_attorney: false, co_holder: false },
  contact_answered: false,
  minutes_elapsed: 0,
};

describe("offline evaluate rules", () => {
  it("sends the case to the bank when the contact holds a power of attorney", () => {
    const r = offlineEvaluate(fixture, {
      ...base,
      contact: { ...base.contact, has_power_of_attorney: true },
    });
    expect(r.destination).toBe("bank");
    expect(r.destination_reason).toBe("the contact holds a power of attorney");
  });

  it("uses the co-holder reason when the contact is only a co-holder", () => {
    const r = offlineEvaluate(fixture, { ...base, contact: { ...base.contact, co_holder: true } });
    expect(r.destination).toBe("bank");
    expect(r.destination_reason).toBe("the contact is a co-holder of the account");
  });

  it("escalates to the bank after 30 minutes without an answer", () => {
    const r = offlineEvaluate(fixture, { ...base, minutes_elapsed: 30 });
    expect(r.response_window_expired).toBe(true);
  });

  it("does not escalate on time-out once the contact has answered", () => {
    const r = offlineEvaluate(fixture, { ...base, minutes_elapsed: 45, contact_answered: true });
    expect(r.response_window_expired).toBe(false);
    expect(r.minutes_left).toBe(0);
  });

  it("recomputes minutes left for the trusted contact", () => {
    const r = offlineEvaluate(fixture, { ...base, minutes_elapsed: 12 });
    expect(r.minutes_left).toBe(18);
  });

  it("always keeps internal abuse with the bank", () => {
    const r = offlineEvaluate(fixture, { ...base, scenario_id: "internal-abuse", minutes_elapsed: 50 });
    expect(r.destination).toBe("bank");
    expect(r.destination_reason).toBe("insider");
  });

  it("revocation takes effect 72 hours after the request", () => {
    const now = new Date("2026-01-01T09:00:00Z");
    const r = offlineRevocation(fixture, now);
    expect(r.effective_at).toBe("2026-01-04T09:00:00.000Z");
  });
});

describe("formatting", () => {
  it("formats amounts as CHF 40,000", () => {
    expect(formatChf(40000)).toBe("CHF 40,000");
  });

  it("splits the amount out of the phone message", () => {
    expect(splitAmount("is withdrawing CHF 40,000 in cash at the Mendrisio branch.")).toEqual({
      before: "is withdrawing",
      amount: "CHF 40,000",
      after: "in cash at the Mendrisio branch.",
    });
  });
});
