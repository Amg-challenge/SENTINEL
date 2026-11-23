import { createFileRoute } from "@tanstack/react-router";
import { CheckCircle2, Clock, Info, ShieldOff, UserRoundCog, XCircle } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageState } from "@/components/sentinel/PageState";
import { Panel } from "@/components/sentinel/Panel";
import { pageHead } from "@/lib/head";
import { useDemo } from "@/state/DemoContext";

export const Route = createFileRoute("/person")({
  head: () =>
    pageHead(
      "Protected person",
      "The account holder switches Sentinel on and names a trusted contact, with clear limits on what they can do.",
    ),
  component: PersonPage,
});

function PersonPage() {
  return (
    <PageState>
      <Person />
    </PageState>
  );
}

const checkboxClass = "mt-0.5 h-6 w-6 rounded-md border-[1.5px] border-border-strong data-[state=checked]:border-primary";

function Person() {
  const { consent, setConsent, contact, updateContact, config } = useDemo();
  const name = contact.name.trim() || "your trusted contact";
  const windowMin = config?.response_window_minutes;
  const delayH = config?.revocation_delay_hours;
  const hasAccess = contact.has_power_of_attorney || contact.co_holder;

  return (
    <div className="mx-auto max-w-[1240px]">
      <p className="eyebrow">Step 1</p>
      <h1 className="mt-1 text-[40px] font-bold leading-tight text-ink">Protected person</h1>
      {config && (
        <p className="mt-2 text-lg text-muted-foreground">
          {config.protected_person.label} · {config.protected_person.branch}
        </p>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="sentinel-card p-7" aria-labelledby="activation-title">
          <h2 id="activation-title" className="text-xl font-semibold text-ink">
            Activation
          </h2>

          <div className="mt-6 flex items-start gap-4 rounded-2xl bg-surface-2 p-5">
            <Checkbox
              id="consent"
              checked={consent}
              onCheckedChange={(v) => setConsent(v === true)}
              className={checkboxClass}
            />
            <Label htmlFor="consent" className="cursor-pointer text-lg font-semibold leading-snug text-ink">
              I consent to activating Sentinel on my account
            </Label>
          </div>

          <div className="mt-6 space-y-2">
            <Label htmlFor="contact-name" className="text-sm font-semibold text-ink-2">
              Trusted contact
            </Label>
            <Input
              id="contact-name"
              value={contact.name}
              onChange={(e) => updateContact({ name: e.target.value })}
              className="h-12 rounded-lg border-border-strong bg-surface px-4 text-base md:text-base focus-visible:ring-2"
            />
          </div>

          <div className="mt-6 space-y-4">
            <div className="flex items-start gap-4">
              <Checkbox
                id="poa"
                checked={contact.has_power_of_attorney}
                onCheckedChange={(v) => updateContact({ has_power_of_attorney: v === true })}
                className={checkboxClass}
              />
              <Label htmlFor="poa" className="cursor-pointer text-base leading-snug text-ink-2">
                Holds a power of attorney on my account
              </Label>
            </div>
            <div className="flex items-start gap-4">
              <Checkbox
                id="coholder"
                checked={contact.co_holder}
                onCheckedChange={(v) => updateContact({ co_holder: v === true })}
                className={checkboxClass}
              />
              <Label htmlFor="coholder" className="cursor-pointer text-base leading-snug text-ink-2">
                Is a co-holder of the account
              </Label>
            </div>
          </div>
        </section>

        <section className="sentinel-card p-7" aria-labelledby="sees-title">
          <h2 id="sees-title" className="text-xl font-semibold text-ink">
            What the contact sees, and what they can do
          </h2>

          <div className="mt-6" aria-live="polite">
            {consent ? (
              <Panel tone="ok" icon={<CheckCircle2 />} className="animate-fade" key="on">
                Sentinel is active. Your trusted contact is <strong>{name}</strong>.
              </Panel>
            ) : (
              <Panel tone="alert" icon={<ShieldOff />} className="animate-fade" key="off">
                Sentinel is not active: without your consent it does not intervene.
              </Panel>
            )}
          </div>

          <ul className="mt-6 space-y-3 text-base leading-snug text-ink-2">
            {[
              "Notified only for cash at the counter, safe deposit box visits and transfers to new or foreign accounts outside the normal pattern.",
              "Cannot see your balance or history, and cannot move money.",
              "Can only confirm, or stop it and ask the bank to check: the bank decides with you.",
              "If they have an interest in the transaction, the case goes to the bank.",
              `If they don't answer within ${windowMin} minutes, the bank takes over.`,
              `Switching off or changing the rules waits ${delayH} hours.`,
            ].map((t) => (
              <li key={t} className="flex items-start gap-3">
                <span className="mt-[9px] h-1.5 w-1.5 shrink-0 rounded-full bg-primary" aria-hidden="true" />
                {t}
              </li>
            ))}
          </ul>

          {hasAccess && (
            <Panel tone="info" icon={<Info />} className="mt-6 animate-fade">
              Because {name} has access to your account, every flagged case will go to the bank,
              never to them.
            </Panel>
          )}
        </section>
      </div>

      <RevocationCard />
    </div>
  );
}

function RevocationCard() {
  const {
    config,
    revocation,
    revocationApplied,
    revocationHours,
    requestRevocation,
    cancelRevocation,
    contact,
    consent,
  } = useDemo();
  const [newName, setNewName] = useState("");
  const [busy, setBusy] = useState(false);
  const delay = config?.revocation_delay_hours ?? 0;
  const left = Math.max(0, delay - revocationHours);
  const name = contact.name.trim() || "your trusted contact";

  const request = async (kind: "deactivate" | "change_contact") => {
    setBusy(true);
    try {
      await requestRevocation(kind, newName);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="mt-6 sentinel-card p-7" aria-labelledby="revocation-title">
      <h2 id="revocation-title" className="text-xl font-semibold text-ink">
        Revocation and changes · {delay}-hour safety delay
      </h2>

      <div className="mt-6 flex flex-wrap items-end gap-4">
        <Button
          variant="quiet"
          size="xl"
          onClick={() => request("deactivate")}
          disabled={busy || !!revocation || !consent}
        >
          <XCircle />
          Request deactivation
        </Button>
        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-2">
            <Label htmlFor="new-contact" className="text-sm font-semibold text-ink-2">
              New trusted contact
            </Label>
            <Input
              id="new-contact"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Name"
              className="h-14 w-[240px] rounded-lg border-border-strong bg-surface px-4 text-base md:text-base focus-visible:ring-2"
            />
          </div>
          <Button
            variant="quiet"
            size="xl"
            onClick={() => request("change_contact")}
            disabled={busy || !!revocation || !newName.trim()}
          >
            <UserRoundCog />
            Request contact change
          </Button>
        </div>
      </div>

      <div className="mt-6" aria-live="polite">
        {revocation ? (
          <Panel tone="alert" icon={<Clock />} className="animate-fade" role="status">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p>
                Pending:{" "}
                {revocation.kind === "deactivate"
                  ? "deactivation of Sentinel"
                  : `change of trusted contact to ${revocation.newName.trim()}`}
                . It takes effect in <strong>{left} hours</strong>. Protection stays active
                meanwhile, and {name} has already been notified.
              </p>
              <Button variant="quiet" size="pill" onClick={cancelRevocation}>
                Cancel request
              </Button>
            </div>
          </Panel>
        ) : revocationApplied ? (
          <Panel tone="ok" icon={<CheckCircle2 />} className="animate-fade" role="status">
            {revocationApplied}
          </Panel>
        ) : null}
      </div>
    </section>
  );
}
