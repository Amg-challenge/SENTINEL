import { createFileRoute } from "@tanstack/react-router";
import { Inbox } from "lucide-react";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { PageState } from "@/components/sentinel/PageState";
import { Pill } from "@/components/sentinel/StatusPill";
import { CHANNEL_LABEL, capitalise, formatChf, formatScore } from "@/lib/format";
import { pageHead } from "@/lib/head";
import { inBankQueue } from "@/state/case";
import { useDemo } from "@/state/DemoContext";

export const Route = createFileRoute("/bank")({
  head: () =>
    pageHead(
      "Bank case queue",
      "Cases with a conflict of interest, no answer, or stopped by the trusted contact go to the bank's review.",
    ),
  component: BankPage,
});

function BankPage() {
  return (
    <PageState>
      <Bank />
    </PageState>
  );
}

function Bank() {
  const { scenarios, evaluations, consent, bankDecisions, bankDecide, setEvaluateAll, config, decisions, contact } =
    useDemo();

  useEffect(() => {
    setEvaluateAll(true);
    return () => setEvaluateAll(false);
  }, [setEvaluateAll]);

  const windowMin = config?.response_window_minutes ?? 0;
  const rows = consent
    ? scenarios
        .map((s) => ({ s, ev: evaluations[s.id] }))
        .filter(({ s, ev }) => inBankQueue(ev, decisions[s.id]))
    : [];

  return (
    <div className="mx-auto max-w-[1600px]">
      <p className="eyebrow">Step 4</p>
      <h1 className="mt-1 text-[40px] font-bold leading-tight text-ink">Bank case queue</h1>
      <p className="mt-2 text-lg text-muted-foreground">
        Conflicts of interest, unanswered cases and operations the trusted contact stopped land
        here. The bank speaks with the client and takes the final decision.
      </p>

      <section className="mt-8 sentinel-card overflow-hidden" aria-label="Cases to review">
        {rows.length === 0 ? (
          <div className="flex flex-col items-center px-6 py-16 text-center animate-fade">
            <span className="grid h-14 w-14 place-items-center rounded-full bg-surface-2 text-subtle" aria-hidden="true">
              <Inbox className="h-7 w-7" />
            </span>
            <p className="mt-5 font-display text-2xl font-semibold text-ink">No cases in the queue.</p>
            <p className="mt-2 max-w-lg text-base text-muted-foreground">
              {consent
                ? "Stop an operation on the contact's phone, tick 'holds a power of attorney' on screen 1, or pick the internal-abuse scenario."
                : "Sentinel is not active: switch it on in screen 1, then tick 'holds a power of attorney' or pick the internal-abuse scenario."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1100px] text-left text-base">
              <thead>
                <tr className="border-b border-border bg-surface-2">
                  {[
                    "Scenario",
                    "Transaction",
                    "Score",
                    "Why it was paused",
                    "Why it came to the bank",
                    "Status",
                  ].map((h) => (
                    <th key={h} scope="col" className="eyebrow px-6 py-4 font-semibold">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map(({ s, ev }) => {
                  const d = bankDecisions[s.id];
                  return (
                    <tr key={s.id} className="border-b border-border align-top last:border-0 animate-fade">
                      <td className="px-6 py-5 font-semibold text-ink">{s.title}</td>
                      <td className="px-6 py-5 text-ink-2">
                        <span className="block">{CHANNEL_LABEL[ev!.operation.channel]}</span>
                        <span className="font-display text-lg font-semibold text-ink tabular">
                          {ev!.operation.amount > 0 ? formatChf(ev!.operation.amount) : "—"}
                        </span>
                      </td>
                      <td className="px-6 py-5 font-semibold text-ink tabular">
                        {formatScore(ev!.score)}
                      </td>
                      <td className="max-w-[320px] px-6 py-5 text-ink-2">
                        {ev!.reasons.map((r) => capitalise(r.text)).join("; ") || "—"}
                      </td>
                      <td className="max-w-[280px] px-6 py-5 text-ink-2">
                        {ev!.destination !== "bank"
                          ? `${contact.name.trim() || "The trusted contact"} stopped it and asked for a check`
                          : ev!.response_window_expired
                            ? `No answer within ${windowMin} minutes`
                            : capitalise(ev!.destination_reason)}
                      </td>
                      <td className="px-6 py-5">
                        <div className="flex flex-col items-start gap-3">
                          <Pill tone={d === "blocked" ? "alert" : d === "approved" ? "ok" : "hold"} key={d ?? "review"}>
                            {d === "blocked" ? "Blocked" : d === "approved" ? "Approved" : "To review"}
                          </Pill>
                          <div className="flex gap-2">
                            <Button
                              variant="alert"
                              size="pill"
                              onClick={() => bankDecide(s.id, "blocked")}
                              aria-label={`Block: ${s.title}`}
                            >
                              Block
                            </Button>
                            <Button
                              variant="quiet"
                              size="pill"
                              onClick={() => bankDecide(s.id, "approved")}
                              aria-label={`Approve: ${s.title}`}
                            >
                              Approve
                            </Button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
