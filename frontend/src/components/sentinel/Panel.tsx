import { cva, type VariantProps } from "class-variance-authority";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const panelVariants = cva("flex items-start gap-3 rounded-2xl px-5 py-4 text-base leading-snug", {
  variants: {
    tone: {
      info: "bg-info-soft text-info-soft-foreground",
      ok: "bg-ok-soft text-ok-soft-foreground",
      alert: "bg-alert-soft text-alert-soft-foreground",
      neutral: "bg-surface-2 text-ink-2 border border-border",
    },
  },
  defaultVariants: { tone: "info" },
});

export function Panel({
  tone,
  icon,
  children,
  className,
  role,
}: VariantProps<typeof panelVariants> & {
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  role?: "status" | "alert";
}) {
  return (
    <div className={cn(panelVariants({ tone }), className)} role={role}>
      {icon && <span className="mt-0.5 shrink-0 [&_svg]:h-5 [&_svg]:w-5">{icon}</span>}
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
