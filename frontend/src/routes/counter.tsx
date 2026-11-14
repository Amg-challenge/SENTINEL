import { createFileRoute } from "@tanstack/react-router";
import { ShieldOff } from "lucide-react";

import { CounterConsole } from "@/components/sentinel/CounterConsole";
import { PageState } from "@/components/sentinel/PageState";
import { Timeline } from "@/components/sentinel/Timeline";
import { useCase } from "@/components/sentinel/useCase";
import { pageHead } from "@/lib/head";

export const Route = createFileRoute("/counter")({
  head: () =>
    pageHead(
      "Bank counter",
      "The teller's console: anomaly score, why the operation was paused and what to do next.",
    ),
  component: CounterPage,
});

function CounterPage() {
  return (
    <PageState>
      <Counter />
    </PageState>
  );
}

function Counter() {
  const { scenario, consent } = useCase();
  return (
    <div className="mx-auto max-w-[820px]">
      <p className="eyebrow">Step 2</p>
      <h1 className="mt-1 text-[40px] font-bold leading-tight text-ink">Bank counter</h1>
      {scenario && (
        <p className="mt-3 text-lg italic leading-relaxed text-muted-foreground">
          {scenario.story}
        </p>
      )}
      {!consent && (
        <div className="mt-6 flex items-start gap-3 sentinel-card p-6 text-lg text-ink" role="status">
          <ShieldOff className="mt-1 h-5 w-5 shrink-0 text-alert" aria-hidden="true" />
          Sentinel is not active on this account: the transaction proceeds without verification.
        </div>
      )}
      <div className="mt-6 space-y-5">
        <CounterConsole />
        <Timeline />
      </div>
    </div>
  );
}
