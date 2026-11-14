import type { Channel } from "./api";

const chf = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

/** "CHF 40,000" — comma grouping, matching the API messages. */
export function formatChf(amount: number): string {
  return `CHF ${chf.format(Math.round(amount))}`;
}

export function formatScore(n: number): string {
  return n.toFixed(2);
}

/** Shares arrive as 0–1 fractions; values above 1 are treated as already-percent. */
export function formatPercent(n: number): string {
  const pct = n <= 1 ? n * 100 : n;
  return `${pct.toFixed(0)}%`;
}

export function capitalise(text: string): string {
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : text;
}

export const CHANNEL_LABEL: Record<Channel, string> = {
  counter: "Cash withdrawal",
  atm: "ATM withdrawal",
  transfer: "Transfer",
  safe_deposit_box: "Box access",
  card: "Card payment",
};

/** Adds minutes to an "HH:MM" clock string. */
export function addMinutes(clock: string, minutes: number): string {
  const [h = 0, m = 0] = clock.split(":").map(Number);
  const total = (h * 60 + m + minutes) % (24 * 60);
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

/** Splits a phone message around its first CHF amount, if any. */
export function splitAmount(message: string): { before: string; amount: string; after: string } | null {
  const match = message.match(/CHF\s?\d[\d,'’.]*\d|CHF\s?\d/);
  if (!match || match.index === undefined) return null;
  return {
    before: message.slice(0, match.index).trim(),
    amount: match[0].replace(/\s+/, " "),
    after: message.slice(match.index + match[0].length).trim(),
  };
}
