import type { ReactNode } from "react";

/** 380×780 device mockup. No fake status bar. */
export function PhoneFrame({ children, label }: { children: ReactNode; label?: string }) {
  return (
    <div
      className="mx-auto h-[780px] w-[380px] max-w-full shrink-0 rounded-[52px] bg-ink p-3 shadow-card"
      role="region"
      aria-label={label ?? "Trusted contact's phone"}
    >
      <div className="flex h-full flex-col overflow-hidden rounded-[42px] bg-surface px-6 pb-7 pt-10">
        {children}
      </div>
    </div>
  );
}
