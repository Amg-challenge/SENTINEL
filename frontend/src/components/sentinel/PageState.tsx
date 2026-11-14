import { Loader2, WifiOff } from "lucide-react";
import type { ReactNode } from "react";

import { useDemo } from "@/state/DemoContext";

/** Shows a calm loading / unavailable state until config and scenarios are ready. */
export function PageState({ children }: { children: ReactNode }) {
  const { status } = useDemo();
  if (status === "ready") return <>{children}</>;
  if (status === "loading") {
    return (
      <div className="flex min-h-[50vh] items-center justify-center gap-3 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />
        <span className="text-base">Loading the demo…</span>
      </div>
    );
  }
  return (
    <div className="mx-auto mt-16 max-w-xl sentinel-card p-8 text-center">
      <WifiOff className="mx-auto h-8 w-8 text-subtle" aria-hidden="true" />
      <h2 className="mt-4 text-xl font-semibold text-ink">Demo data unavailable</h2>
      <p className="mt-2 text-base text-muted-foreground">
        The API did not answer and the offline file <code>demo-fallback.json</code> could not be
        loaded.
      </p>
    </div>
  );
}
