import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  createApi,
  type Config,
  type Contact,
  type DataSource,
  type Evaluation,
  type Revocation,
  type Scenario,
  type Stats,
} from "@/lib/api";
import type { Decision } from "./case";

export interface PendingRevocation {
  kind: "deactivate" | "change_contact";
  newName: string;
  data: Revocation;
}

interface DemoState {
  status: "loading" | "ready" | "error";
  source: DataSource;
  config: Config | null;
  scenarios: Scenario[];
  stats: Stats | null;

  consent: boolean;
  setConsent: (v: boolean) => void;
  contact: Contact;
  updateContact: (patch: Partial<Contact>) => void;

  scenarioId: string;
  setScenarioId: (id: string) => void;
  scenario: Scenario | undefined;

  evaluations: Record<string, Evaluation>;
  /** Every scenario scored once with the default contact — used by the Appendix. */
  baseline: Record<string, Evaluation>;
  evaluating: boolean;
  setEvaluateAll: (v: boolean) => void;

  decisions: Record<string, Decision>;
  decide: (scenarioId: string, d: Decision) => void;
  bankDecisions: Record<string, Decision>;
  bankDecide: (scenarioId: string, d: Decision) => void;

  minutes: number;
  setMinutes: (n: number) => void;
  revocationHours: number;
  setRevocationHours: (n: number) => void;
  forceOffline: boolean;
  setForceOffline: (v: boolean) => void;

  revocation: PendingRevocation | null;
  revocationApplied: string | null;
  requestRevocation: (kind: PendingRevocation["kind"], newName?: string) => Promise<void>;
  cancelRevocation: () => void;

  resetDemo: () => void;
}

const DemoContext = createContext<DemoState | null>(null);

const DEFAULT_SCENARIO = "fake-police-cash";

export function DemoProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<DemoState["status"]>("loading");
  const [source, setSource] = useState<DataSource>("offline");
  const [config, setConfig] = useState<Config | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);

  const [consent, setConsent] = useState(false);
  const [contact, setContact] = useState<Contact>({
    name: "",
    has_power_of_attorney: false,
    co_holder: false,
  });
  const contactTouched = useRef(false);

  const [scenarioId, setScenarioId] = useState(DEFAULT_SCENARIO);
  const [evaluations, setEvaluations] = useState<Record<string, Evaluation>>({});
  const [baseline, setBaseline] = useState<Record<string, Evaluation>>({});
  const [evaluating, setEvaluating] = useState(false);
  const [evaluateAll, setEvaluateAll] = useState(false);

  const [decisions, setDecisions] = useState<Record<string, Decision>>({});
  const [bankDecisions, setBankDecisions] = useState<Record<string, Decision>>({});
  const [minutes, setMinutes] = useState(0);
  const [revocationHours, setRevocationHours] = useState(0);
  const [forceOffline, setForceOffline] = useState(false);

  const [revocation, setRevocation] = useState<PendingRevocation | null>(null);
  const [revocationApplied, setRevocationApplied] = useState<string | null>(null);

  // The API client reads the live/offline decision through a ref so calls in flight stay consistent.
  const liveRef = useRef(false);
  const api = useMemo(() => createApi(() => liveRef.current), []);

  // Start-up (and whenever "Force offline data" changes): health, then config/scenarios/stats.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const healthy = forceOffline ? false : await api.health();
      if (cancelled) return;
      liveRef.current = healthy && !forceOffline;
      try {
        const [c, s, st] = await Promise.all([api.getConfig(), api.getScenarios(), api.getStats()]);
        if (cancelled) return;
        setConfig(c.data);
        setScenarios(s.data);
        setStats(st.data);
        setSource([c, s, st].every((r) => r.source === "live") ? "live" : "offline");
        if (!contactTouched.current) {
          setContact({ ...c.data.default_contact });
        }
        setScenarioId((cur) =>
          s.data.some((x) => x.id === cur) ? cur : (s.data[0]?.id ?? cur),
        );
        setStatus("ready");

        const scored = await Promise.all(
          s.data.map((sc) =>
            api
              .evaluate({
                scenario_id: sc.id,
                contact: c.data.default_contact,
                contact_answered: false,
                minutes_elapsed: 0,
              })
              .then((r) => [sc.id, r.data] as const)
              .catch(() => null),
          ),
        );
        if (cancelled) return;
        setBaseline(
          Object.fromEntries(scored.filter((x): x is NonNullable<typeof x> => x !== null)),
        );
      } catch {
        if (!cancelled) setStatus((cur) => (cur === "ready" ? cur : "error"));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [api, forceOffline]);

  // Re-evaluate (debounced 250 ms); previous results stay visible while loading.
  const answeredKey = Object.keys(decisions).sort().join(",");
  const requestId = useRef(0);
  useEffect(() => {
    if (status !== "ready" || !consent) return;
    const ids = evaluateAll ? scenarios.map((s) => s.id) : [scenarioId];
    if (ids.length === 0) return;
    const answered = new Set(answeredKey ? answeredKey.split(",") : []);
    const myId = ++requestId.current;
    const timer = setTimeout(async () => {
      setEvaluating(true);
      try {
        const results = await Promise.all(
          ids.map((id) =>
            api.evaluate({
              scenario_id: id,
              contact,
              contact_answered: answered.has(id),
              minutes_elapsed: minutes,
            }),
          ),
        );
        if (myId !== requestId.current) return;
        setEvaluations((prev) => {
          const next = { ...prev };
          results.forEach((r, i) => {
            const id = ids[i];
            if (id) next[id] = r.data;
          });
          return next;
        });
        setSource(results.every((r) => r.source === "live") ? "live" : "offline");
      } catch {
        /* keep the previous result on stage */
      } finally {
        if (myId === requestId.current) setEvaluating(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [
    api,
    status,
    consent,
    contact,
    answeredKey,
    minutes,
    scenarioId,
    evaluateAll,
    scenarios,
    forceOffline,
  ]);

  // Apply a pending revocation once the simulated clock reaches the safety delay.
  useEffect(() => {
    if (!revocation || !config) return;
    if (revocationHours >= config.revocation_delay_hours) {
      if (revocation.kind === "deactivate") {
        setConsent(false);
      } else if (revocation.newName.trim()) {
        contactTouched.current = true;
        setContact((c) => ({ ...c, name: revocation.newName.trim() }));
      }
      setRevocation(null);
      setRevocationApplied(
        `The ${config.revocation_delay_hours}-hour delay has elapsed: the request has been applied.`,
      );
    }
  }, [revocation, revocationHours, config]);

  const updateContact = useCallback((patch: Partial<Contact>) => {
    contactTouched.current = true;
    setContact((c) => ({ ...c, ...patch }));
  }, []);

  const decide = useCallback((id: string, d: Decision) => {
    setDecisions((prev) => ({ ...prev, [id]: d }));
  }, []);
  const bankDecide = useCallback((id: string, d: Decision) => {
    setBankDecisions((prev) => ({ ...prev, [id]: d }));
  }, []);

  const requestRevocation = useCallback(
    async (kind: PendingRevocation["kind"], newName = "") => {
      const r = await api.revocation();
      setRevocation({ kind, newName, data: r.data });
      setRevocationApplied(null);
      setRevocationHours(0);
      if (r.source === "offline") setSource("offline");
    },
    [api],
  );

  const cancelRevocation = useCallback(() => {
    setRevocation(null);
  }, []);

  const resetDemo = useCallback(() => {
    setDecisions({});
    setBankDecisions({});
    setMinutes(0);
    setRevocationHours(0);
    setRevocation(null);
    setRevocationApplied(null);
  }, []);

  const scenario = scenarios.find((s) => s.id === scenarioId);

  const value: DemoState = {
    status,
    source,
    config,
    scenarios,
    stats,
    consent,
    setConsent,
    contact,
    updateContact,
    scenarioId,
    setScenarioId,
    scenario,
    evaluations,
    baseline,
    evaluating,
    setEvaluateAll,
    decisions,
    decide,
    bankDecisions,
    bankDecide,
    minutes,
    setMinutes,
    revocationHours,
    setRevocationHours,
    forceOffline,
    setForceOffline,
    revocation,
    revocationApplied,
    requestRevocation,
    cancelRevocation,
    resetDemo,
  };

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}

export function useDemo(): DemoState {
  const ctx = useContext(DemoContext);
  if (!ctx) throw new Error("useDemo must be used inside <DemoProvider>");
  return ctx;
}

/** Convenience: the current scenario's evaluation and its derived case. */
export function useContactName(): string {
  const { contact } = useDemo();
  return contact.name.trim() || "your trusted contact";
}
