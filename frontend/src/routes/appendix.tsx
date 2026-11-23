import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageState } from "@/components/sentinel/PageState";
import { capitalise, formatPercent, formatScore } from "@/lib/format";
import { pageHead } from "@/lib/head";
import { useDemo } from "@/state/DemoContext";

export const Route = createFileRoute("/appendix")({
  head: () =>
    pageHead(
      "How the engine is calibrated",
      "Alerts per client, share confirmed by the contact, cost curve and ROC curve on synthetic data.",
    ),
  component: AppendixPage,
});

function AppendixPage() {
  return (
    <PageState>
      <Appendix />
    </PageState>
  );
}

const num = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

function Appendix() {
  const { stats, scenarios, baseline } = useDemo();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!stats) return null;

  const tiles = [
    { label: "Alerts per client per year", value: num.format(stats.alerts_per_client_year) },
    { label: "Confirmed by the contact", value: formatPercent(stats.share_resolved_by_contact) },
    { label: "Escalated to the bank", value: formatPercent(stats.share_escalated_to_bank) },
    { label: "Cost to serve (CHF/client/year)", value: num.format(stats.cost_to_serve_chf) },
    { label: "Fraud money protected", value: formatPercent(stats.fraud_money_protected) },
    { label: "AUC", value: formatScore(stats.auc) },
  ];

  const cost = stats.cost_curve.filter((p) => p.cost_chf > 0);
  // The API lists ROC points by threshold; draw them left to right.
  const roc = [...stats.roc_curve].sort((a, b) => a.fpr - b.fpr || a.tpr - b.tpr);
  const axis = { fontSize: 13, fill: "var(--subtle)" };

  return (
    <div className="mx-auto max-w-[1600px]">
      <p className="eyebrow">Appendix</p>
      <h1 className="mt-1 text-[40px] font-bold leading-tight text-ink">
        How the engine is calibrated
      </h1>
      <p className="mt-2 text-lg text-muted-foreground">
        Synthetic data — the real test is a pilot with a bank.
      </p>

      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-3 2xl:grid-cols-6">
        {tiles.map((t) => (
          <div key={t.label} className="sentinel-card p-6">
            <p className="text-sm font-medium text-muted-foreground">{t.label}</p>
            <p className="mt-3 font-display text-[40px] font-bold leading-none text-ink tabular">
              {t.value}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="sentinel-card p-7" aria-labelledby="cost-title">
          <h2 id="cost-title" className="text-xl font-semibold text-ink">
            Cost curve
          </h2>
          <div className="mt-4 h-[320px]">
            {mounted && (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={cost} margin={{ top: 10, right: 16, bottom: 8, left: 8 }}>
                  <CartesianGrid stroke="var(--border)" vertical={false} />
                  <XAxis
                    dataKey="threshold"
                    type="number"
                    domain={[0, 1]}
                    ticks={[0, 0.2, 0.4, 0.6, 0.8, 1]}
                    tick={axis}
                    stroke="var(--border)"
                    label={{ value: "Threshold", position: "insideBottom", offset: -4, ...axis }}
                  />
                  <YAxis
                    dataKey="cost_chf"
                    scale="log"
                    domain={["auto", "auto"]}
                    allowDataOverflow
                    tick={axis}
                    stroke="var(--border)"
                    width={64}
                    tickFormatter={(v: number) => num.format(v)}
                  />
                  <Tooltip
                    formatter={(v: number) => [`CHF ${num.format(v)}`, "Cost"]}
                    labelFormatter={(l: number) => `Threshold ${formatScore(l)}`}
                    contentStyle={{ borderRadius: 12, borderColor: "var(--border)" }}
                  />
                  <ReferenceLine
                    x={stats.threshold}
                    stroke="var(--alert)"
                    strokeDasharray="6 6"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="cost_chf"
                    stroke="var(--primary)"
                    strokeWidth={3}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
          <p className="mt-3 text-base text-muted-foreground">
            The threshold is an economic decision: it balances disturbing the contact and letting
            money go.
          </p>
        </section>

        <section className="sentinel-card p-7" aria-labelledby="roc-title">
          <h2 id="roc-title" className="text-xl font-semibold text-ink">
            ROC curve
          </h2>
          <div className="mt-4 h-[320px]">
            {mounted && (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={roc} margin={{ top: 10, right: 16, bottom: 8, left: 8 }}>
                  <CartesianGrid stroke="var(--border)" vertical={false} />
                  <XAxis
                    dataKey="fpr"
                    type="number"
                    domain={[0, 1]}
                    ticks={[0, 0.2, 0.4, 0.6, 0.8, 1]}
                    tick={axis}
                    stroke="var(--border)"
                    label={{ value: "False positive rate", position: "insideBottom", offset: -4, ...axis }}
                  />
                  <YAxis
                    type="number"
                    domain={[0, 1]}
                    ticks={[0, 0.2, 0.4, 0.6, 0.8, 1]}
                    tick={axis}
                    stroke="var(--border)"
                    width={48}
                  />
                  <ReferenceLine
                    segment={[
                      { x: 0, y: 0 },
                      { x: 1, y: 1 },
                    ]}
                    stroke="var(--subtle)"
                    strokeDasharray="6 6"
                  />
                  <Line
                    type="monotone"
                    dataKey="tpr"
                    stroke="var(--primary)"
                    strokeWidth={3}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
          <p className="mt-3 text-base text-muted-foreground">
            Area under the curve (AUC): {formatScore(stats.auc)}.
          </p>
        </section>
      </div>

      <section className="mt-6 sentinel-card overflow-hidden" aria-labelledby="scores-title">
        <h2 id="scores-title" className="px-7 pt-7 text-xl font-semibold text-ink">
          Scenario scores
        </h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[800px] text-left text-base">
            <thead>
              <tr className="border-y border-border bg-surface-2">
                {["Scenario", "Score", "Paused", "Reasons"].map((h) => (
                  <th key={h} scope="col" className="eyebrow px-7 py-4 font-semibold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {scenarios.map((s) => {
                const ev = baseline[s.id];
                return (
                  <tr key={s.id} className="border-b border-border align-top last:border-0">
                    <td className="px-7 py-4 font-semibold text-ink">{s.title}</td>
                    <td className="px-7 py-4 font-semibold text-ink tabular">
                      {ev ? formatScore(ev.score) : "—"}
                    </td>
                    <td className="px-7 py-4 text-ink-2">{ev ? (ev.paused ? "Yes" : "No") : "—"}</td>
                    <td className="px-7 py-4 text-ink-2">
                      {ev ? ev.reasons.map((r) => capitalise(r.text)).join("; ") || "—" : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <p className="mt-6 max-w-[1100px] text-base text-muted-foreground">{stats.note}</p>
    </div>
  );
}
