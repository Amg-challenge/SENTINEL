import { cva } from "class-variance-authority";

import type { CaseState } from "@/state/case";
import { cn } from "@/lib/utils";

const pillVariants = cva(
  "inline-flex items-center gap-2 whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm font-semibold animate-fade",
  {
    variants: {
      tone: {
        hold: "bg-alert-soft text-alert-soft-foreground",
        ok: "bg-ok-soft text-ok-soft-foreground",
        alert: "bg-alert text-alert-foreground",
        info: "bg-info-soft text-info-soft-foreground",
        neutral: "bg-secondary text-muted-foreground",
      },
    },
  },
);

const MAP: Record<CaseState, { label: string; tone: "hold" | "ok" | "alert" | "info" | "neutral" }> =
  {
    inactive: { label: "Proceed", tone: "ok" },
    loading: { label: "Checking", tone: "neutral" },
    proceed: { label: "Proceed", tone: "ok" },
    waiting_contact: { label: "On hold", tone: "hold" },
    with_bank: { label: "With the bank", tone: "info" },
    expired: { label: "With the bank", tone: "info" },
    approved: { label: "Approved", tone: "ok" },
    blocked: { label: "Blocked", tone: "alert" },
  };

export function StatusPill({ state }: { state: CaseState }) {
  const { label, tone } = MAP[state];
  return (
    <span key={state} className={cn(pillVariants({ tone }))}>
      {tone === "hold" && <span className="h-2 w-2 rounded-full bg-alert" aria-hidden="true" />}
      {label}
    </span>
  );
}

export function Pill({
  tone,
  children,
  className,
}: {
  tone: "hold" | "ok" | "alert" | "info" | "neutral";
  children: React.ReactNode;
  className?: string;
}) {
  return <span className={cn(pillVariants({ tone }), className)}>{children}</span>;
}
