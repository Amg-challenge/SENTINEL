import { Link } from "@tanstack/react-router";
import { BarChart3, MonitorPlay, RotateCcw, SlidersHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import { useDemo } from "@/state/DemoContext";
import { Logo } from "./Logo";

export const TAGLINE =
  "When the bank sees something strange, it calls the right person: the one you trust.";

const STEPS = [
  { to: "/person", n: 1, label: "Person" },
  { to: "/counter", n: 2, label: "Counter" },
  { to: "/contact", n: 3, label: "Contact" },
  { to: "/bank", n: 4, label: "Bank" },
] as const;

const navLink =
  "group inline-flex h-11 items-center gap-2 whitespace-nowrap rounded-full px-2.5 pr-3.5 text-[15px] font-semibold text-muted-foreground transition-colors duration-150 hover:bg-surface-2 hover:text-ink data-[status=active]:bg-primary data-[status=active]:text-primary-foreground";
const navDot =
  "grid h-7 w-7 place-items-center rounded-full bg-secondary text-sm font-semibold text-muted-foreground group-data-[status=active]:bg-primary-foreground/20 group-data-[status=active]:text-primary-foreground";

export function TopBar() {
  const { scenarios, scenarioId, setScenarioId, resetDemo, source, status } = useDemo();

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-surface/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-[1880px] flex-wrap items-center gap-x-4 gap-y-3 px-5 py-3 lg:px-8">
        <Link to="/" className="flex min-w-0 shrink items-center gap-4 rounded-xl">
          <Logo />
          <span className="hidden min-w-0 max-w-[260px] truncate text-sm text-muted-foreground min-[1760px]:block">
            {TAGLINE}
          </span>
        </Link>

        <nav
          aria-label="Demo steps"
          className="order-last flex basis-full items-center gap-0.5 overflow-x-auto min-[1440px]:order-none min-[1440px]:mx-auto min-[1440px]:basis-auto"
        >
          <Link to="/" className={navLink} activeOptions={{ exact: true }}>
            <span className={navDot} aria-hidden="true">
              <MonitorPlay className="h-4 w-4" />
            </span>
            Stage
          </Link>
          {STEPS.map((s) => (
            <Link key={s.to} to={s.to} className={navLink}>
              <span className={navDot} aria-hidden="true">
                {s.n}
              </span>
              {s.label}
            </Link>
          ))}
          <Link to="/appendix" className={navLink}>
            <span className={navDot} aria-hidden="true">
              <BarChart3 className="h-4 w-4" />
            </span>
            Appendix
          </Link>
        </nav>

        <div className="ml-auto flex items-center gap-2 min-[1440px]:ml-0">
          <span
            className={cn(
              "hidden items-center gap-2 whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-semibold sm:inline-flex",
              source === "live"
                ? "bg-info-soft text-info-soft-foreground"
                : "bg-secondary text-muted-foreground",
            )}
            role="status"
          >
            <span
              className={cn("h-2 w-2 rounded-full", source === "live" ? "bg-primary" : "bg-subtle")}
              aria-hidden="true"
            />
            {status === "loading" ? "Connecting" : source === "live" ? "Live API" : "Offline data"}
          </span>

          <Select value={scenarioId} onValueChange={setScenarioId} disabled={scenarios.length === 0}>
            <SelectTrigger
              className="h-11 w-[210px] rounded-xl border-border bg-surface text-[15px] font-medium focus:ring-2 min-[1700px]:w-[240px]"
              aria-label="Scenario"
            >
              <SelectValue placeholder="Scenario" />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              {scenarios.map((s) => (
                <SelectItem key={s.id} value={s.id} className="py-2.5 text-[15px]">
                  {s.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button variant="quiet" size="pill" onClick={resetDemo} aria-label="Reset demo" title="Reset demo">
            <RotateCcw />
            <span className="hidden min-[1700px]:inline">Reset demo</span>
          </Button>

          <DemoControls />
        </div>
      </div>
    </header>
  );
}

function DemoControls() {
  const {
    minutes,
    setMinutes,
    revocationHours,
    setRevocationHours,
    forceOffline,
    setForceOffline,
    config,
    revocation,
  } = useDemo();
  const maxHours = config?.revocation_delay_hours ?? 72;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="quiet" size="pill" aria-label="Demo controls" title="Demo controls">
          <SlidersHorizontal />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-[360px] rounded-3xl p-6 shadow-card">
        <p className="eyebrow">Demo controls</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Simulated clocks: nobody waits 30 minutes on stage.
        </p>

        <div className="mt-6 space-y-3">
          <div className="flex items-baseline justify-between">
            <Label htmlFor="minutes-slider" className="text-[15px] font-semibold text-ink">
              Minutes since the notification
            </Label>
            <span className="text-sm font-semibold text-primary tabular">{minutes} min</span>
          </div>
          <Slider
            id="minutes-slider"
            min={0}
            max={60}
            step={1}
            value={[minutes]}
            onValueChange={([v]) => setMinutes(v ?? 0)}
            aria-label="Minutes since the notification"
          />
        </div>

        <div className="mt-6 space-y-3">
          <div className="flex items-baseline justify-between">
            <Label htmlFor="hours-slider" className="text-[15px] font-semibold text-ink">
              Hours since the revocation request
            </Label>
            <span className="text-sm font-semibold text-primary tabular">{revocationHours} h</span>
          </div>
          <Slider
            id="hours-slider"
            min={0}
            max={maxHours}
            step={1}
            value={[revocationHours]}
            onValueChange={([v]) => setRevocationHours(v ?? 0)}
            aria-label="Hours since the revocation request"
          />
          {!revocation && (
            <p className="text-sm text-subtle">No revocation request is pending.</p>
          )}
        </div>

        <div className="mt-6 flex items-center justify-between gap-4 rounded-2xl bg-surface-2 px-4 py-3">
          <Label htmlFor="force-offline" className="text-[15px] font-semibold text-ink">
            Force offline data
          </Label>
          <Switch id="force-offline" checked={forceOffline} onCheckedChange={setForceOffline} />
        </div>
      </PopoverContent>
    </Popover>
  );
}
