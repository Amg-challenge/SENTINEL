import type { ReactNode } from "react";

/**
 * The trusted contact's phone.
 *
 * On a wide screen (projector, laptop) this draws a 380x780 device mockup, so the
 * audience understands they are looking at a phone. On a real phone the mockup
 * disappears and the content fills the screen: you do not draw a phone around
 * something that is already on one.
 */
export function PhoneFrame({ children, label }: { children: ReactNode; label?: string }) {
  return (
    <div
      className="mx-auto w-full max-w-full shrink-0 sm:h-[780px] sm:w-[380px] sm:rounded-[52px] sm:bg-ink sm:p-3 sm:shadow-card"
      role="region"
      aria-label={label ?? "Trusted contact's phone"}
    >
      <div className="flex h-full flex-col overflow-hidden rounded-none bg-surface px-5 pb-6 pt-6 sm:rounded-[42px] sm:px-6 sm:pb-7 sm:pt-10">
        {children}
      </div>
    </div>
  );
}
