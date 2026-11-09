"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Shield,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Activity,
  Zap,
  Lock,
  ArrowRight,
  TrendingUp,
  Cpu,
  Layers,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { Transaction, WSMessage, fetchTransactions, WSManager } from "@/lib/api";
import { JudgeSimulatorBar } from "@/components/JudgeSimulatorBar";
import { LedgerGrid } from "@/components/LedgerGrid";
import { AuditDetailDrawer } from "@/components/AuditDetailDrawer";

export default function DashboardPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedTxn, setSelectedTxn] = useState<Transaction | null>(null);
  const [agentTrace, setAgentTrace] = useState<WSMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WSManager | null>(null);

  // Load transactions from REST endpoint
  const loadTransactions = useCallback(async () => {
    try {
      const data = await fetchTransactions();
      setTransactions(data);
    } catch (e) {
      console.error("Failed to load transactions:", e);
    }
  }, []);

  // Sync selected transaction when transactions update
  useEffect(() => {
    if (selectedTxn) {
      const updated = transactions.find((t) => t.id === selectedTxn.id);
      if (updated) setSelectedTxn(updated);
    }
  }, [transactions, selectedTxn]);

  useEffect(() => {
    loadTransactions();

    const ws = new WSManager();
    wsRef.current = ws;
    ws.connect();

    const unsub = ws.subscribe((msg: WSMessage) => {
      setWsConnected(true);

      if (msg.type === "transaction_update") {
        loadTransactions();
      }

      if (msg.type === "agent_trace") {
        setAgentTrace((prev) => [msg, ...prev.slice(0, 49)]);
      }
    });

    return () => {
      unsub();
      ws.disconnect();
    };
  }, [loadTransactions]);

  const handleTransactionCreated = useCallback(() => {
    loadTransactions();
  }, [loadTransactions]);

  // Aggregate KPI Calculations
  const totalVolume = transactions.reduce((sum, t) => sum + (t.amount || 0), 0);

  const authorizedCount = transactions.filter(
    (t) =>
      t.status === "AUTHORIZED" ||
      t.status === "CAPTURED" ||
      t.status === "PAYOUT_SENT"
  ).length;

  const piiScrubbedCount = transactions.filter((t) => {
    if (t.pii_redacted && t.pii_redacted !== t.pii_original) return true;
    try {
      if (t.pii_entities_found) {
        const parsed = JSON.parse(t.pii_entities_found);
        return Array.isArray(parsed) && parsed.length > 0;
      }
    } catch {
      return false;
    }
    return false;
  }).length;

  const capturedOrSettledCount = transactions.filter(
    (t) => t.status === "CAPTURED" || t.status === "PAYOUT_SENT"
  ).length;

  return (
    <div className="min-h-screen bg-aegis-bg flex flex-col">
      {/* Top Enterprise Header */}
      <header className="border-b border-aegis-border bg-aegis-surface/90 backdrop-blur-md sticky top-0 z-30 shadow-md">
        <div className="max-w-[1720px] mx-auto px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-aegis-accent-dim to-aegis-accent p-0.5 shadow-lg shadow-aegis-accent/20">
              <div className="w-full h-full bg-aegis-bg rounded-[10px] flex items-center justify-center">
                <Shield className="w-5 h-5 text-aegis-accent" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black tracking-tight text-slate-100 uppercase">
                  AegisPay
                </h1>
                <span className="text-[10px] font-mono font-bold bg-aegis-paypal/20 text-sky-400 border border-aegis-paypal/40 px-2 py-0.5 rounded-full">
                  PayPal AI Hackathon
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Autonomous B2B Proof-of-Work Escrow & PayPal Settlement Engine
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-lg bg-aegis-card border border-aegis-border text-slate-300">
              <span className="text-slate-400">Engine:</span>
              <span className="text-emerald-400 font-semibold">LangGraph v0.2</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400">PII:</span>
              <span className="text-sky-400 font-semibold">Presidio</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400">Signer:</span>
              <span className="text-purple-400 font-semibold">Ed25519</span>
            </div>

            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-aegis-card border border-aegis-border">
              <span
                className={`w-2 h-2 rounded-full ${
                  wsConnected ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                }`}
              />
              <span className="text-slate-300">
                {wsConnected ? "Telemetry Streaming" : "WS Connecting..."}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Workspace Body */}
      <main className="max-w-[1720px] mx-auto px-6 py-6 space-y-6 flex-1 w-full">
        {/* KPI Financial Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard
            icon={<DollarSign className="w-5 h-5" />}
            label="Total Escrow Volume"
            value={`$${totalVolume.toLocaleString("en-US", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}`}
            subtitle="Committed across all pipelines"
            color="text-aegis-accent"
            accentBorder="border-aegis-accent/30"
          />
          <KPICard
            icon={<CheckCircle className="w-5 h-5" />}
            label="Active Escrow Locks"
            value={String(authorizedCount)}
            subtitle="PayPal Orders v2 AUTHORIZE intent"
            color="text-emerald-400"
            accentBorder="border-emerald-500/30"
          />
          <KPICard
            icon={<Lock className="w-5 h-5" />}
            label="Presidio Scrubbed"
            value={String(piiScrubbedCount)}
            subtitle="Zero GDPR / CCPA leakage"
            color="text-sky-400"
            accentBorder="border-sky-500/30"
          />
          <KPICard
            icon={<TrendingUp className="w-5 h-5" />}
            label="Settled & Paid"
            value={String(capturedOrSettledCount)}
            subtitle="PayPal Capture & Payouts v1 executed"
            color="text-teal-300"
            accentBorder="border-teal-500/30"
          />
        </div>

        {/* Judge Simulator Bar */}
        <JudgeSimulatorBar
          onCreated={handleTransactionCreated}
          isLoading={isLoading}
          setIsLoading={setIsLoading}
        />

        {/* Ledger Grid and Live Agent Telemetry Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left / Central: Enterprise AG Grid Ledger */}
          <div className="lg:col-span-2">
            <LedgerGrid
              transactions={transactions}
              onSelect={setSelectedTxn}
              onRefresh={loadTransactions}
            />
          </div>

          {/* Right: Live Agent Reasoning & Node Trace Stream */}
          <div className="bg-aegis-surface rounded-xl border border-aegis-border p-4 shadow-xl flex flex-col h-[540px]">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-aegis-border">
              <div className="flex items-center gap-2">
                <div className="p-1 rounded bg-aegis-accent/10 text-aegis-accent">
                  <Activity className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                    Live Agent Trace
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 px-1.5 py-0.2 rounded">
                      WebSocket
                    </span>
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Real-time LangGraph state transitions & cryptographic verification
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAgentTrace([])}
                className="text-[10px] text-slate-500 hover:text-slate-300 font-mono transition-colors"
              >
                Clear
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-mono text-xs">
              {agentTrace.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 space-y-2">
                  <Cpu className="w-8 h-8 text-slate-600 animate-pulse" />
                  <p className="text-xs">
                    No active node transitions in buffer.
                  </p>
                  <p className="text-[11px] text-slate-600 max-w-[240px]">
                    Click one of the 3 scenarios above to watch the 4-node LangGraph pipeline stream in real-time.
                  </p>
                </div>
              ) : (
                agentTrace.map((trace, index) => {
                  const nodeName = trace.node || trace.action || "node";
                  const decision = trace.state?.decision;
                  const isApproved = decision === "APPROVE";
                  const isRejected = decision === "REJECT";
                  const isEscalated = decision === "ESCALATE";

                  return (
                    <div
                      key={index}
                      className="p-3 bg-aegis-card rounded-lg border border-aegis-border/80 transition-all hover:border-slate-600 space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-[11px]">
                        <div className="flex items-center gap-1.5 font-semibold text-slate-200">
                          <Zap className="w-3.5 h-3.5 text-amber-400" />
                          <span className="text-aegis-accent uppercase tracking-wide">
                            {nodeName}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-500">
                          {trace.timestamp
                            ? new Date(trace.timestamp).toLocaleTimeString()
                            : ""}
                        </span>
                      </div>

                      {trace.transaction_id && (
                        <div className="text-[10px] text-slate-400 flex items-center gap-1">
                          <span>TXN:</span>
                          <span className="text-slate-300 font-bold">
                            {trace.transaction_id.slice(0, 8)}…
                          </span>
                        </div>
                      )}

                      {decision && (
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              isApproved
                                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                                : isRejected
                                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                            }`}
                          >
                            Decision: {decision}
                          </span>
                        </div>
                      )}

                      {trace.state?.reasoning && (
                        <p className="text-[11px] text-slate-300/90 leading-tight bg-slate-900/60 p-2 rounded border border-slate-800">
                          {trace.state.reasoning}
                        </p>
                      )}

                      {trace.state?.pii_detected !== undefined && (
                        <div className="flex items-center gap-1.5 text-[10px]">
                          <span className="text-slate-400">Presidio Guard:</span>
                          <span
                            className={
                              trace.state.pii_detected
                                ? "text-sky-300 font-semibold"
                                : "text-emerald-400"
                            }
                          >
                            {trace.state.pii_detected
                              ? "Scrubbed PII Entities"
                              : "Clean / No PII"}
                          </span>
                        </div>
                      )}

                      {trace.state?.signature && (
                        <div className="text-[10px] text-emerald-400 flex items-center gap-1 truncate font-mono">
                          <span>Ed25519:</span>
                          <span className="truncate">{trace.state.signature}</span>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Slide-over Audit Detail Drawer */}
      {selectedTxn && (
        <AuditDetailDrawer
          transaction={selectedTxn}
          onClose={() => setSelectedTxn(null)}
          onAction={loadTransactions}
        />
      )}
    </div>
  );
}

function KPICard({
  icon,
  label,
  value,
  subtitle,
  color,
  accentBorder,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtitle: string;
  color: string;
  accentBorder: string;
}) {
  return (
    <div
      className={`bg-aegis-surface rounded-xl border border-aegis-border p-4 shadow-md transition-all hover:bg-slate-900/70 border-t-2 ${accentBorder}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs uppercase tracking-wider font-semibold text-slate-400 font-mono">
          {label}
        </span>
        <div className={`p-1.5 rounded-lg bg-slate-800/80 ${color}`}>
          {icon}
        </div>
      </div>
      <p className={`text-2xl font-bold font-mono tracking-tight ${color}`}>
        {value}
      </p>
      <p className="text-[11px] text-slate-400 mt-1 truncate">{subtitle}</p>
    </div>
  );
}

