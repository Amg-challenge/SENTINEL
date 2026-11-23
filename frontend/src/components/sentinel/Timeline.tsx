import { BellRing, Landmark, ReceiptText } from "lucide-react";

import { addMinutes } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useCase } from "./useCase";

const START = "09:38";

export function Timeline() {
  const { view, windowMinutes } = useCase();
  const active =
    view.state === "waiting_contact"
      ? 1
      : view.state === "with_bank" ||
          view.state === "expired" ||
          view.state === "stopped_by_contact"
        ? 2
        : view.state === "inactive" || view.state === "proceed"
          ? -1
          : 0;

  const items = [
    { icon: ReceiptText, label: "Requested", time: START },
    { icon: BellRing, label: "Contact notified", time: START },
    { icon: Landmark, label: "Bank takes over", time: addMinutes(START, windowMinutes) },
  ];

  return (
    <ol className="grid grid-cols-3 gap-4" aria-label="Case timeline">
      {items.map((it, i) => (
        <li
          key={it.label}
          className={cn(
            "sentinel-card px-5 py-4 transition-colors duration-200",
            i === active && "border-primary",
          )}
          aria-current={i === active ? "step" : undefined}
        >
          <it.icon
            className={cn("h-5 w-5", i === active ? "text-primary" : "text-subtle")}
            aria-hidden="true"
          />
          <p className="mt-3 text-sm font-medium text-muted-foreground">{it.label}</p>
          <p className="font-display text-2xl font-semibold text-ink tabular">{it.time}</p>
        </li>
      ))}
    </ol>
  );
}
