"use client";

import { useState } from "react";
import { Beaker, Sparkles, ShieldAlert, ShieldX, Loader2 } from "lucide-react";
import { simulateScenario } from "@/lib/api";

interface Props {
  onCreated: () => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

interface ScenarioConfig {
  key: "happy_path" | "pii_heavy" | "policy_breach";
  title: string;
  badge: string;
  badgeColor: string;
  description: string;
  impactTag: string;
  icon: typeof Sparkles;
  borderColor: string;
  hoverColor: string;
}

const SCENARIOS: ScenarioConfig[] = [
  {
    key: "happy_path",
    title: "Scenario 1: Happy Path Escrow",
    badge: "Auto-Approve & Authorize",
    badgeColor: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
    description: "Clean $12.5K cloud license renewal. Passes Presidio & policy caps. Locks funds in PayPal Sandbox escrow.",
    impactTag: "AUTHORIZE ➔ Capturable",
    icon: Sparkles,
    borderColor: "border-emerald-500/30",
    hoverColor: "hover:border-emerald-400/70 hover:bg-emerald-950/20",
  },
  {
    key: "pii_heavy",
    title: "Scenario 2: PII Compliance Scrub",
    badge: "Presidio Active Redaction",
    badgeColor: "bg-sky-500/20 text-sky-400 border-sky-500/40",
    description: "Metadata with SSN, credit card, personal cell & IP. Microsoft Presidio scrubs PII before PayPal order transmission.",
    impactTag: "Ed25519 Signed & Cleaned",
    icon: ShieldAlert,
    borderColor: "border-sky-500/30",
    hoverColor: "hover:border-sky-400/70 hover:bg-sky-950/20",
  },
  {
    key: "policy_breach",
    title: "Scenario 3: Policy Breach Defense",
    badge: "Auto-Rejected / Blocklist",
    badgeColor: "bg-rose-500/20 text-rose-400 border-rose-500/40",
    description: "Blocked entity (FraudCorp) and $75K exceeding $50K cap. Agent halts execution; prevents PayPal fund lock.",
    impactTag: "Rejected ➔ Zero Risk",
    icon: ShieldX,
    borderColor: "border-rose-500/30",
    hoverColor: "hover:border-rose-400/70 hover:bg-rose-950/20",
  },
];

export function JudgeSimulatorBar({ onCreated, isLoading, setIsLoading }: Props) {
  const [activeScenario, setActiveScenario] = useState<string | null>(null);

  const handleSimulate = async (scenarioKey: "happy_path" | "pii_heavy" | "policy_breach") => {
    setActiveScenario(scenarioKey);
    setIsLoading(true);
    try {
      await simulateScenario(scenarioKey);
      onCreated();
    } catch (err) {
      console.error(`Simulation for ${scenarioKey} failed:`, err);
    } finally {
      setIsLoading(false);
      setActiveScenario(null);
    }
  };

  return (
    <div className="bg-aegis-surface rounded-xl border border-aegis-border p-4 shadow-lg backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2 border-b border-aegis-border/60">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <Beaker className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              Judge Evaluation Bar
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-aegis-accent/20 text-aegis-accent border border-aegis-accent/30">
                1-Click Proof Scenarios
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Trigger pre-configured agent flows to verify autonomous escrow, PII redaction, and policy enforcement
            </p>
          </div>
        </div>
        <div className="text-xs text-slate-400 flex items-center gap-1.5 font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          PayPal Sandbox: Active
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {SCENARIOS.map((scenario) => {
          const Icon = scenario.icon;
          const isCurrentActive = activeScenario === scenario.key;

          return (
            <button
              key={scenario.key}
              type="button"
              onClick={() => handleSimulate(scenario.key)}
              disabled={isLoading}
              className={`relative text-left p-3.5 rounded-lg border transition-all duration-200 bg-aegis-card/80 ${scenario.borderColor} ${scenario.hoverColor} ${
                isLoading ? "opacity-60 cursor-not-allowed" : "cursor-pointer"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4 text-slate-300" />
                  <span className="text-sm font-semibold text-slate-100">{scenario.title}</span>
                </div>
                {isCurrentActive && <Loader2 className="w-4 h-4 text-aegis-accent animate-spin" />}
              </div>

              <div className="mb-2">
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border inline-block ${scenario.badgeColor}`}>
                  {scenario.badge}
                </span>
              </div>

              <p className="text-xs text-slate-300/90 leading-relaxed mb-3">
                {scenario.description}
              </p>

              <div className="flex items-center justify-between pt-2 border-t border-slate-800/70 text-[11px] font-mono text-slate-400">
                <span>Result Target:</span>
                <span className="font-semibold text-slate-200">{scenario.impactTag}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

