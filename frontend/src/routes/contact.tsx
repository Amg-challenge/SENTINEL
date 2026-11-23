import { createFileRoute } from "@tanstack/react-router";

import { ContactPhone } from "@/components/sentinel/ContactPhone";
import { PageState } from "@/components/sentinel/PageState";
import { useCase } from "@/components/sentinel/useCase";
import { pageHead } from "@/lib/head";

export const Route = createFileRoute("/contact")({
  head: () =>
    pageHead(
      "Trusted contact",
      "What the trusted contact sees on their phone, and how they confirm, or stop and ask the bank to check, in one tap.",
    ),
  component: ContactPage,
});

function ContactPage() {
  return (
    <PageState>
      <Contact />
    </PageState>
  );
}

function Contact() {
  const { contactName } = useCase();
  return (
    <div className="flex flex-col items-center">
      {/* On a real phone this heading is scaffolding that breaks the illusion,
          and it costs the screen space the two buttons need. Wide screens keep it. */}
      <p className="eyebrow hidden sm:block">Step 3</p>
      <h1 className="mt-1 hidden text-center text-[40px] font-bold leading-tight text-ink sm:block">
        {contactName}'s phone
      </h1>
      <div className="w-full sm:mt-8 sm:w-auto">
        <ContactPhone />
      </div>
    </div>
  );
}
