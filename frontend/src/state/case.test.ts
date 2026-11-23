import { describe, expect, it } from "vitest";

import { fixture } from "@/test/fixtures/fallback";
import { deriveCase, inBankQueue } from "./case";

const results = fixture.scenarios[0]!.results;

describe("case state", () => {
  it("does nothing when consent is off", () => {
    expect(deriveCase(false, results.default, undefined, undefined).state).toBe("inactive");
  });
  it("waits for the trusted contact", () => {
    expect(deriveCase(true, results.default, undefined, undefined).state).toBe("waiting_contact");
  });
  it("releases the hold when the contact confirms", () => {
    expect(deriveCase(true, results.default, "confirmed", undefined)).toEqual({
      state: "approved",
      decidedBy: "contact",
    });
  });
  it("sends a contact's stop to the bank: not a veto", () => {
    expect(deriveCase(true, results.default, "stopped", undefined)).toEqual({
      state: "stopped_by_contact",
      decidedBy: "contact",
    });
    expect(deriveCase(true, results.default, "stopped", "approved")).toEqual({
      state: "approved",
      decidedBy: "bank",
    });
  });
  it("lets the bank refuse after a stop, never the contact alone", () => {
    expect(deriveCase(true, results.default, "stopped", "blocked")).toEqual({
      state: "blocked",
      decidedBy: "bank",
    });
    // whatever the contact answers, the contact alone never produces a final block
    for (const d of ["confirmed", "stopped"] as const) {
      expect(deriveCase(true, results.default, d, undefined).state).not.toBe("blocked");
    }
  });
  it("puts stopped, conflicted and unanswered cases in the bank queue", () => {
    expect(inBankQueue(results.default, undefined)).toBe(false);
    expect(inBankQueue(results.default, "confirmed")).toBe(false);
    expect(inBankQueue(results.default, "stopped")).toBe(true);
    expect(inBankQueue(results.contact_has_power_of_attorney, undefined)).toBe(true);
    expect(inBankQueue(results.contact_did_not_answer_30min, undefined)).toBe(true);
  });
  it("marks an unanswered case as expired and with the bank", () => {
    expect(deriveCase(true, results.contact_did_not_answer_30min, undefined, undefined).state).toBe(
      "expired",
    );
  });
  it("lets the bank decide bank cases", () => {
    expect(deriveCase(true, results.contact_has_power_of_attorney, undefined, "approved")).toEqual({
      state: "approved",
      decidedBy: "bank",
    });
  });
});
