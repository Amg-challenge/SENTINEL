import { createFileRoute } from "@tanstack/react-router";

import { ContactPhone } from "@/components/sentinel/ContactPhone";
import { CounterConsole } from "@/components/sentinel/CounterConsole";
import { Logo } from "@/components/sentinel/Logo";
import { PageState } from "@/components/sentinel/PageState";
import { Timeline } from "@/components/sentinel/Timeline";
import { useCase } from "@/components/sentinel/useCase";
import { pageHead } from "@/lib/head";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({
  head: () =>
    pageHead(
      "Stage",
      "Live demo: an unusual withdrawal is put on hold until the trusted contact confirms it, or the bank checks it with the client.",
    ),
  component: StagePage,
});

function StagePage() {
  return (
    <PageState>
      <Stage />
    </PageState>
  );
}

function Stage() {
  const { consent, ev, view } = useCase();
  const paused = consent && !!ev?.paused;
  const steps = [
    { n: 1, label: "Protected person gives consent", on: consent },
    { n: 2, label: "Counter: operation on hold", on: paused },
    {
      n: 3,
      label: "Trusted contact confirms or asks for a bank review",
      on: paused && ev?.destination === "trusted_contact",
    },
    {
      n: 4,
      label: "Bank decides with the client",
      on: paused && (ev?.destination === "bank" || view.state === "stopped_by_contact"),
    },
  ];

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-8 lg:grid-cols-[auto_minmax(0,1fr)] xl:grid-cols-[360px_auto_minmax(0,1fr)] xl:gap-10">
      <section className="lg:col-span-2 xl:col-span-1" aria-labelledby="stage-title">
        <Logo />
        <h1
          id="stage-title"
          className="mt-8 font-display text-[40px] font-bold leading-[1.08] text-ink"
        >
          When the bank sees something strange, it calls the right person.
        </h1>
        <p className="mt-5 text-lg leading-relaxed text-ink-2">
          The person chooses a trusted contact. Unusual cash, safe deposit visits and transfers
          abroad wait for their confirmation.
        </p>
        <ol className="mt-8 space-y-2" aria-label="How Sentinel works">
          {steps.map((s) => (
            <li
              key={s.n}
              className={cn(
                "flex items-center gap-4 rounded-2xl px-4 py-3 text-base font-medium transition-colors duration-200",
                s.on ? "bg-info-soft text-info-soft-foreground" : "text-muted-foreground",
              )}
              aria-current={s.on ? "step" : undefined}
            >
              <span
                className={cn(
                  "grid h-8 w-8 shrink-0 place-items-center rounded-full text-sm font-semibold",
                  s.on ? "bg-primary text-primary-foreground" : "bg-secondary text-muted-foreground",
                )}
              >
                {s.n}
              </span>
              {s.label}
            </li>
          ))}
        </ol>
        <span className="sr-only" aria-live="polite">
          Case status: {view.state.replace(/_/g, " ")}
        </span>
      </section>

      <div className="stage-phone">
        <ContactPhone />
      </div>

      <div className="space-y-5">
        <CounterConsole />
        <Timeline />
      </div>
    </div>
  );
}
