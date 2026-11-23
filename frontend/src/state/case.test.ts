import { describe, expect, it } from "vitest";

import { fixture } from "@/test/fixtures/fallback";
import { deriveCase } from "./case";

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
