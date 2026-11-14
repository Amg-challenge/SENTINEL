import { createFileRoute } from "@tanstack/react-router";

import { ContactPhone } from "@/components/sentinel/ContactPhone";
import { PageState } from "@/components/sentinel/PageState";
import { useCase } from "@/components/sentinel/useCase";
import { pageHead } from "@/lib/head";

export const Route = createFileRoute("/contact")({
  head: () =>
    pageHead(
      "Trusted contact",
      "What the trusted contact sees on their phone, and how they approve or block in one tap.",
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
      <p className="eyebrow">Step 3</p>
      <h1 className="mt-1 text-center text-[40px] font-bold leading-tight text-ink">
        {contactName}'s phone
      </h1>
      <div className="mt-8">
        <ContactPhone />
      </div>
    </div>
  );
}
