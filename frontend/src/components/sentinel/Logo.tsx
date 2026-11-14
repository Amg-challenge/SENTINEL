import { ShieldCheck } from "lucide-react";

import { cn } from "@/lib/utils";

export function Logo({ size = "md", word = true }: { size?: "md" | "sm"; word?: boolean }) {
  const sm = size === "sm";
  return (
    <span className="inline-flex items-center gap-3">
      <span
        className={cn(
          "grid shrink-0 place-items-center bg-primary text-primary-foreground",
          sm ? "h-9 w-9 rounded-[10px]" : "h-11 w-11 rounded-lg",
        )}
        aria-hidden="true"
      >
        <ShieldCheck className={sm ? "h-5 w-5" : "h-6 w-6"} strokeWidth={2} />
      </span>
      {word && (
        <span className={cn("font-display font-bold text-ink", sm ? "text-xl" : "text-2xl")}>
          Sentinel
        </span>
      )}
    </span>
  );
}
