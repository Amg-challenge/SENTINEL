import { deriveCase } from "@/state/case";
import { useDemo } from "@/state/DemoContext";

/** Evaluation + derived case for one scenario (the current one by default). */
export function useCase(id?: string) {
  const demo = useDemo();
  const scenarioId = id ?? demo.scenarioId;
  const scenario = demo.scenarios.find((s) => s.id === scenarioId);
  const ev = demo.consent ? demo.evaluations[scenarioId] : undefined;
  const view = deriveCase(
    demo.consent,
    ev,
    demo.decisions[scenarioId],
    demo.bankDecisions[scenarioId],
  );
  const contactName = demo.contact.name.trim() || "your trusted contact";
  const windowMinutes = demo.config?.response_window_minutes ?? 0;
  return { ...demo, scenarioId, scenario, ev, view, contactName, windowMinutes };
}
