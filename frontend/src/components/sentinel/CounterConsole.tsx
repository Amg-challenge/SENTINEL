import { Ban, CheckCircle2, Landmark, ShieldOff, Smartphone, TimerOff } from "lucide-react";

import { CHANNEL_LABEL, capitalise, formatChf, formatScore } from "@/lib/format";
import { Panel } from "./Panel";
import { StatusPill } from "./StatusPill";
import { useCase } from "./useCase";

export function CounterConsole() {
  const { scenario, ev, view, contactName, windowMinutes } = useCase();
  const op = ev?.operation ?? scenario?.operation;
  if (!op) return null;

  const score = ev ? Math.min(1, Math.max(0, ev.score)) : 0;
  const threshold = ev ? Math.min(1, Math.max(0, ev.threshold)) : 0;

  return (
    <section className="sentinel-card p-7" aria-label="Counter console">
      <div className="flex items-center justify-between gap-4">
        <span className="eyebrow">Counter 2 · Mendrisio</span>
        <StatusPill state={view.state} />
      </div>

      <div className="mt-5 flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
        <p className="font-display text-[44px] font-bold leading-none text-ink tabular xl:text-[52px]">
          {op.amount > 0 ? formatChf(op.amount) : "Safe deposit box access"}
        </p>
        <p className="pb-1 text-lg font-medium text-ink-2">{CHANNEL_LABEL[op.channel]}</p>
      </div>

      {ev && (
        <div className="animate-fade">
          <div className="mt-7">
            <div className="flex items-baseline justify-between text-sm">
              <span className="font-medium text-muted-foreground">Anomaly score</span>
              <span className="font-semibold text-ink tabular">
                {formatScore(ev.score)} · threshold {formatScore(ev.threshold)}
              </span>
            </div>
            <div
              className="relative mt-2 h-2.5 rounded-full bg-border"
              role="meter"
              aria-label="Anomaly score"
              aria-valuemin={0}
              aria-valuemax={1}
              aria-valuenow={ev.score}
            >
              <div
                className="h-full rounded-full bg-primary transition-[width] duration-200"
                style={{ width: `${score * 100}%` }}
              />
              <div
                className="absolute -top-1 h-[18px] w-0.5 rounded-full bg-ink"
                style={{ left: `calc(${threshold * 100}% - 1px)` }}
                aria-hidden="true"
              />
            </div>
          </div>

          {ev.reasons.length > 0 && (
            <div className="mt-6">
              <h3 className="text-base font-semibold text-ink">Why it was paused</h3>
              <ul className="mt-2 space-y-1.5">
                {ev.reasons.map((r) => (
                  <li key={r.text} className="flex items-start gap-3 text-base text-ink-2">
                    <span
                      className="mt-[9px] h-1.5 w-1.5 shrink-0 rounded-full bg-primary"
                      aria-hidden="true"
                    />
                    {capitalise(r.text)}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="mt-6" aria-live="polite">
        <BottomPanel
          state={view.state}
          decidedBy={view.decidedBy}
          contactName={contactName}
          windowMinutes={windowMinutes}
          reason={ev?.destination_reason ?? ""}
        />
      </div>

      {ev?.pause_origin === "bank_antifraud" && (
        <p className="mt-3 text-sm text-subtle">
          Flagged by the bank's antifraud system — Sentinel works on top of it.
        </p>
      )}
    </section>
  );
}

function BottomPanel({
  state,
  decidedBy,
  contactName,
  windowMinutes,
  reason,
}: {
  state: ReturnType<typeof useCase>["view"]["state"];
  decidedBy: "contact" | "bank" | null;
  contactName: string;
  windowMinutes: number;
  reason: string;
}) {
  switch (state) {
    case "inactive":
      return (
        <Panel tone="neutral" icon={<ShieldOff />} className="animate-fade">
          Sentinel is not active on this account: the transaction proceeds without verification.
        </Panel>
      );
    case "loading":
      return (
        <Panel tone="neutral" className="animate-fade">
          Checking the operation…
        </Panel>
      );
    case "proceed":
      return (
        <Panel tone="ok" icon={<CheckCircle2 />} className="animate-fade">
          Within normal behaviour: no verification needed, proceed.
        </Panel>
      );
    case "waiting_contact":
      return (
        <Panel tone="info" icon={<Smartphone />} className="animate-fade">
          Waiting for {contactName}, the trusted contact. <strong>Do not pay out.</strong>
        </Panel>
      );
    case "stopped_by_contact":
      return (
        <Panel tone="alert" icon={<Landmark />} className="animate-fade">
          <strong>Do not pay out.</strong> {contactName} stopped it and asked the bank to check.
          The bank will speak with the client before anything is paid out.
        </Panel>
      );
    case "with_bank":
      return (
        <Panel tone="info" icon={<Landmark />} className="animate-fade">
          Escalated to the bank's internal review: {reason}.
        </Panel>
      );
    case "expired":
      return (
        <Panel tone="info" icon={<TimerOff />} className="animate-fade">
          {contactName} did not answer within {windowMinutes} minutes: the case has been escalated
          to the bank's internal review. A transaction is never left hanging.
        </Panel>
      );
    case "approved":
      return (
        <Panel tone="ok" icon={<CheckCircle2 />} className="animate-fade">
          {decidedBy === "bank"
            ? "Approved by the bank after its review with the client. The teller may proceed."
            : `Confirmed by ${contactName}. The teller may proceed.`}
        </Panel>
      );
    case "blocked":
      return (
        <Panel tone="alert" icon={<Ban />} className="animate-fade">
          <strong>Not executed.</strong> The bank decided after its review with the client; suggest
          contacting the police.
        </Panel>
      );
  }
}
