import { AlertTriangle, Ban, CheckCircle2, Clock, Inbox, Landmark, Lock, TimerOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { Channel } from "@/lib/api";
import { splitAmount } from "@/lib/format";
import { Logo } from "./Logo";
import { PhoneFrame } from "./PhoneFrame";
import { Pill } from "./StatusPill";
import { useCase } from "./useCase";

const NOUN: Record<Channel, string> = {
  counter: "withdrawal",
  atm: "withdrawal",
  transfer: "transfer",
  safe_deposit_box: "box access",
  card: "payment",
};

export function ContactPhone() {
  const demo = useCase();
  const { scenario, ev, view, decide, scenarioId, revocation, config, revocationHours } = demo;
  const pending = view.state === "waiting_contact";
  const hoursLeft =
    revocation && config ? Math.max(0, config.revocation_delay_hours - revocationHours) : 0;

  return (
    <PhoneFrame>
      <div className="flex items-center justify-between">
        <Logo size="sm" />
        {pending && (
          <Pill tone="hold" className="animate-fade">
            Action needed
          </Pill>
        )}
      </div>

      {revocation && (
        <div
          className="mt-4 flex gap-2.5 rounded-2xl bg-alert px-4 py-3 text-sm leading-snug text-alert-foreground animate-fade"
          role="alert"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>
            {revocation.kind === "deactivate"
              ? "A request to switch Sentinel off was made."
              : "A request to change your father's trusted contact was made."}{" "}
            It takes effect in{" "}
            <strong>{hoursLeft} hours</strong>. If you know nothing about it, call your father or the
            bank.
          </span>
        </div>
      )}

      <div className="mt-5 flex min-h-0 flex-1 flex-col" aria-live="polite">
        {pending && scenario && ev ? (
          <div key={`pending-${scenarioId}`} className="flex flex-1 flex-col animate-fade">
            <div className="rounded-3xl bg-surface-2 p-[22px]">
              <p className="text-sm text-subtle">Mendrisio branch · just now</p>
              <Message text={scenario.phone_message} />
              <p className="mt-3 text-base font-semibold text-ink">
                Have you spoken to him? Do you approve?
              </p>
            </div>
            <ul className="mt-4 space-y-2.5 text-[15px] text-ink-2">
              <li className="flex items-center gap-3">
                <Clock className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
                {ev.minutes_left ?? demo.windowMinutes} minutes left, then the bank takes over
              </li>
              <li className="flex items-center gap-3">
                <Lock className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
                You never see his balance or history
              </li>
            </ul>
            <div className="mt-auto space-y-3 pt-4">
              <Button
                variant="alert"
                size="xl"
                className="w-full"
                onClick={() => decide(scenarioId, "blocked")}
              >
                Block
              </Button>
              <Button
                variant="quiet"
                size="xl"
                className="w-full"
                onClick={() => decide(scenarioId, "approved")}
              >
                I spoke to him, approve
              </Button>
            </div>
          </div>
        ) : view.state === "blocked" && view.decidedBy === "contact" ? (
          <Done
            icon={<Ban className="h-8 w-8" />}
            tone="alert"
            text={`You blocked the ${NOUN[ev?.operation.channel ?? "counter"]}. Call your father.`}
          />
        ) : view.state === "approved" && view.decidedBy === "contact" ? (
          <Done icon={<CheckCircle2 className="h-8 w-8" />} tone="ok" text="You approved it." />
        ) : view.state === "expired" ? (
          <Empty
            icon={<TimerOff className="h-7 w-7" />}
            title={`The ${demo.windowMinutes}-minute window has expired.`}
            body="The case has gone to the bank's internal review."
          />
        ) : (view.state === "with_bank" || view.state === "approved" || view.state === "blocked") &&
          ev?.destination === "bank" ? (
          <Empty
            icon={<Landmark className="h-7 w-7" />}
            title="This case was not forwarded to you."
            body={ev.destination_reason ? capitaliseFirst(ev.destination_reason) + "." : ""}
            caption="Sentinel never asks someone with an interest in the transaction to confirm it."
          />
        ) : (
          <Empty icon={<Inbox className="h-7 w-7" />} title="Nothing to verify right now." />
        )}
      </div>
    </PhoneFrame>
  );
}

function capitaliseFirst(t: string) {
  return t.charAt(0).toUpperCase() + t.slice(1);
}

function Message({ text }: { text: string }) {
  const rest = text.replace(/^\s*your father\s*/i, "");
  const parts = splitAmount(rest);
  if (!parts) {
    return <p className="mt-3 text-lg leading-snug text-ink">Your father {rest}</p>;
  }
  return (
    <div className="mt-3 text-lg leading-snug text-ink">
      <p>Your father {parts.before}</p>
      <p className="my-1 font-display text-[44px] font-bold leading-tight text-ink tabular">
        {parts.amount}
      </p>
      {parts.after && <p>{parts.after}</p>}
    </div>
  );
}

function Done({
  icon,
  text,
  tone,
}: {
  icon: React.ReactNode;
  text: string;
  tone: "ok" | "alert";
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center text-center animate-fade">
      <span
        className={
          tone === "ok"
            ? "grid h-16 w-16 place-items-center rounded-full bg-ok-soft text-ok"
            : "grid h-16 w-16 place-items-center rounded-full bg-alert-soft text-alert"
        }
        aria-hidden="true"
      >
        {icon}
      </span>
      <p className="mt-5 font-display text-2xl font-semibold text-ink">{text}</p>
    </div>
  );
}

function Empty({
  icon,
  title,
  body,
  caption,
}: {
  icon: React.ReactNode;
  title: string;
  body?: string;
  caption?: string;
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-2 text-center animate-fade">
      <span
        className="grid h-14 w-14 place-items-center rounded-full bg-surface-2 text-subtle"
        aria-hidden="true"
      >
        {icon}
      </span>
      <p className="mt-5 font-display text-xl font-semibold text-ink">{title}</p>
      {body && <p className="mt-2 text-base text-ink-2">{body}</p>}
      {caption && <p className="mt-4 text-sm text-subtle">{caption}</p>}
    </div>
  );
}
