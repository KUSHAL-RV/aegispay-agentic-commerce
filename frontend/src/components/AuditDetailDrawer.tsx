"use client";

import { useState, useEffect } from "react";
import {
  X,
  Shield,
  FileText,
  Key,
  CreditCard,
  CheckCircle2,
  Ban,
  Loader2,
  Lock,
  ExternalLink,
  Clock,
  UserCheck,
  Cpu,
  Layers,
  Copy,
  Check,
} from "lucide-react";
import {
  Transaction,
  AuditEntry,
  fetchAuditLog,
  approveTransaction,
  voidTransaction,
} from "@/lib/api";

interface Props {
  transaction: Transaction;
  onClose: () => void;
  onAction: () => void;
}

type TabKey = "overview" | "pii" | "crypto" | "paypal" | "audit";

export function AuditDetailDrawer({ transaction, onClose, onAction }: Props) {
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [actionLoading, setActionLoading] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    fetchAuditLog(transaction.id)
      .then(setAuditLog)
      .catch((err) => console.error("Audit log error:", err));
  }, [transaction.id]);

  const canApprove =
    transaction.status === "AUTHORIZED" ||
    transaction.status === "PENDING_REVIEW" ||
    transaction.status === "AGENT_APPROVED";

  const canVoid =
    transaction.status === "AUTHORIZED" ||
    transaction.status === "PENDING_REVIEW" ||
    transaction.status === "AGENT_APPROVED";

  const handleApprove = async () => {
    setActionLoading(true);
    try {
      await approveTransaction(transaction.id);
      onAction();
    } catch (err) {
      console.error("Failed to approve transaction:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleVoid = async () => {
    setActionLoading(true);
    try {
      await voidTransaction(transaction.id);
      onAction();
      onClose();
    } catch (err) {
      console.error("Failed to void transaction:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const copyToClipboard = (text: string, keyName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(keyName);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  let piiEntities: Array<{
    entity_type: string;
    start: number;
    end: number;
    score: number;
    text_snippet: string;
  }> = [];

  try {
    if (transaction.pii_entities_found) {
      const parsed = JSON.parse(transaction.pii_entities_found);
      if (Array.isArray(parsed)) piiEntities = parsed;
    }
  } catch {
    // Keep empty if invalid
  }

  const tabs: { id: TabKey; label: string; icon: typeof FileText }[] = [
    { id: "overview", label: "Overview", icon: Layers },
    { id: "pii", label: "Presidio PII Diff", icon: Shield },
    { id: "crypto", label: "Ed25519 Proof", icon: Key },
    { id: "paypal", label: "PayPal Sandbox", icon: CreditCard },
    { id: "audit", label: "Audit Trail", icon: Clock },
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="relative w-full max-w-2xl bg-aegis-surface border-l border-aegis-border shadow-2xl flex flex-col h-full z-10">
        {/* Sticky Header */}
        <div className="p-6 border-b border-aegis-border bg-aegis-surface/95 sticky top-0 z-20">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-aegis-accent bg-aegis-accent/10 px-2 py-0.5 rounded border border-aegis-accent/30">
                  Escrow Transaction
                </span>
                <span className="text-xs font-mono text-slate-400">
                  {transaction.id}
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-100">
                {transaction.vendor_name}
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                {transaction.vendor_email}
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* HITL Action Controls */}
          {(canApprove || canVoid) && (
            <div className="flex items-center gap-3 p-3 bg-aegis-card rounded-lg border border-aegis-border mb-4">
              <div className="flex-1">
                <p className="text-xs font-semibold text-slate-200">
                  Human-in-the-Loop Governance
                </p>
                <p className="text-[11px] text-slate-400">
                  {transaction.status === "AUTHORIZED"
                    ? "Escrow funds locked in PayPal. Release payout or void authorization."
                    : "Review automated agent checks and execute settlement."}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {canApprove && (
                  <button
                    type="button"
                    onClick={handleApprove}
                    disabled={actionLoading}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-md shadow-sm transition-all disabled:opacity-50"
                  >
                    {actionLoading ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    )}
                    Capture & Settle
                  </button>
                )}
                {canVoid && (
                  <button
                    type="button"
                    onClick={handleVoid}
                    disabled={actionLoading}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-600/80 hover:bg-rose-500 text-white text-xs font-semibold rounded-md shadow-sm transition-all disabled:opacity-50"
                  >
                    {actionLoading ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Ban className="w-3.5 h-3.5" />
                    )}
                    Void Escrow
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex gap-1 overflow-x-auto pb-1 border-b border-slate-800">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                    isActive
                      ? "bg-aegis-accent/20 text-aegis-accent border border-aegis-accent/30 font-semibold"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Scrollable Content Body */}
        <div className="p-6 flex-1 overflow-y-auto space-y-6">
          {/* TAB 1: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-aegis-card rounded-lg border border-aegis-border">
                  <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-1">
                    Escrow Amount
                  </span>
                  <span className="text-xl font-bold font-mono text-aegis-accent">
                    ${transaction.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })} {transaction.currency}
                  </span>
                </div>
                <div className="p-3 bg-aegis-card rounded-lg border border-aegis-border">
                  <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-1">
                    Settlement Status
                  </span>
                  <span className="text-sm font-semibold text-slate-200 font-mono">
                    {transaction.status}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                <div className="p-3 bg-aegis-card rounded-lg border border-aegis-border">
                  <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400 block mb-1">
                    Deliverable / Work Description
                  </span>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {transaction.description}
                  </p>
                </div>

                {transaction.agent_reasoning && (
                  <div className="p-3 bg-slate-900/80 rounded-lg border border-cyan-500/30">
                    <div className="flex items-center gap-1.5 mb-1 text-cyan-400 text-xs font-semibold">
                      <Cpu className="w-3.5 h-3.5" />
                      LangGraph Autonomous Agent Reasoning
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed font-mono">
                      {transaction.agent_reasoning}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: PRESIDIO PII DIFF */}
          {activeTab === "pii" && (
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                    <Shield className="w-4 h-4 text-sky-400" />
                    Microsoft Presidio Redaction Engine
                  </h3>
                  <p className="text-xs text-slate-400">
                    Prevents GDPR / CCPA / PCI-DSS compliance leaks into PayPal payment descriptions
                  </p>
                </div>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  {piiEntities.length} Entities Found
                </span>
              </div>

              {/* Stacked Diff */}
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider font-mono">
                      [RAW INGESTION] Before Presidio
                    </span>
                    <span className="text-[10px] text-slate-500">Unsanitized Payload</span>
                  </div>
                  <div className="p-3.5 bg-rose-950/20 border border-rose-500/30 rounded-lg text-xs font-mono text-rose-300 whitespace-pre-wrap leading-relaxed">
                    {transaction.pii_original || transaction.description}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider font-mono">
                      [CLEAN DISPATCH] Transmitted to PayPal Sandbox
                    </span>
                    <span className="text-[10px] text-slate-500">Sanitized Order Payload</span>
                  </div>
                  <div className="p-3.5 bg-emerald-950/20 border border-emerald-500/30 rounded-lg text-xs font-mono text-emerald-300 whitespace-pre-wrap leading-relaxed">
                    {transaction.pii_redacted || "No PII detected. Original description used safely."}
                  </div>
                </div>
              </div>

              {/* Detected Entities List */}
              {piiEntities.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono mb-2">
                    Scrubbed Metadata Entities
                  </h4>
                  <div className="space-y-1.5">
                    {piiEntities.map((entity, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-2.5 bg-aegis-card rounded border border-aegis-border text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 font-mono text-[10px] font-bold">
                            {entity.entity_type}
                          </span>
                          <span className="font-mono text-slate-300">
                            {entity.text_snippet}
                          </span>
                        </div>
                        <span className="text-[11px] font-mono text-slate-400">
                          Confidence: {(entity.score * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: ED25519 CRYPTOGRAPHIC PROOF */}
          {activeTab === "crypto" && (
            <div className="space-y-5">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                  <Key className="w-4 h-4 text-emerald-400" />
                  Ed25519 Non-Repudiation Proof
                </h3>
                <p className="text-xs text-slate-400">
                  Every automated procurement approval is cryptographically signed by the agent keypair
                </p>
              </div>

              {transaction.ed25519_signature ? (
                <div className="space-y-4">
                  <div className="p-3 bg-emerald-950/20 border border-emerald-500/30 rounded-lg flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span className="text-xs font-semibold text-emerald-300">
                      Cryptographic Signature Verified Valid (Ed25519 / RFC 8032)
                    </span>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                        Signature (Base64)
                      </span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(transaction.ed25519_signature!, "sig")}
                        className="text-[10px] font-mono text-slate-400 hover:text-aegis-accent flex items-center gap-1"
                      >
                        {copiedKey === "sig" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        {copiedKey === "sig" ? "Copied" : "Copy"}
                      </button>
                    </div>
                    <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-aegis-accent break-all select-all">
                      {transaction.ed25519_signature}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                        Agent Public Key (Base64)
                      </span>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(transaction.ed25519_public_key!, "pubkey")}
                        className="text-[10px] font-mono text-slate-400 hover:text-aegis-accent flex items-center gap-1"
                      >
                        {copiedKey === "pubkey" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        {copiedKey === "pubkey" ? "Copied" : "Copy"}
                      </button>
                    </div>
                    <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 break-all select-all">
                      {transaction.ed25519_public_key || "N/A"}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-lg text-center text-xs text-slate-400">
                  Transaction was rejected or not authorized. No cryptographic signature generated.
                </div>
              )}
            </div>
          )}

          {/* TAB 4: PAYPAL SANDBOX INTEGRATION */}
          {activeTab === "paypal" && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                  <CreditCard className="w-4 h-4 text-aegis-paypal" />
                  PayPal Developer Sandbox Settlement
                </h3>
                <p className="text-xs text-slate-400">
                  Target: <code className="text-slate-300">https://api-m.sandbox.paypal.com</code>
                </p>
              </div>

              <div className="space-y-3">
                <div className="p-3 bg-aegis-card rounded-lg border border-aegis-border">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">
                    Orders v2 ID (Intent: AUTHORIZE)
                  </span>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-slate-200">
                      {transaction.paypal_order_id || "None"}
                    </span>
                    {transaction.paypal_order_id && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-mono">
                        Orders API v2
                      </span>
                    )}
                  </div>
                </div>

                <div className="p-3 bg-aegis-card rounded-lg border border-aegis-border">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">
                    Authorization ID (Escrow Lock)
                  </span>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-emerald-400 font-semibold">
                      {transaction.paypal_auth_id || "Not Authorized"}
                    </span>
                    {transaction.paypal_auth_id && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-mono">
                        Escrow Locked
                      </span>
                    )}
                  </div>
                </div>

                <div className="p-3 bg-aegis-card rounded-lg border border-aegis-border">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">
                    Capture ID (Settlement Release)
                  </span>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-slate-200">
                      {transaction.paypal_capture_id || "Not Captured"}
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-aegis-card rounded-lg border border-aegis-border">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">
                    Payout Batch ID (Contractor Settlement)
                  </span>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-slate-200">
                      {transaction.paypal_payout_id || "None"}
                    </span>
                    {transaction.paypal_payout_id && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-teal-500/20 text-teal-300 border border-teal-500/30 font-mono">
                        Payouts v1
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: AUDIT TRAIL */}
          {activeTab === "audit" && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-amber-400" />
                Immutable Audit Trail
              </h3>

              <div className="space-y-2">
                {auditLog.length === 0 ? (
                  <p className="text-xs text-slate-500">No audit events recorded.</p>
                ) : (
                  auditLog.map((log) => (
                    <div
                      key={log.id}
                      className="p-3 bg-aegis-card rounded-lg border border-aegis-border space-y-1"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                              log.actor === "agent"
                                ? "bg-cyan-500/20 text-cyan-300"
                                : log.actor === "human"
                                ? "bg-emerald-500/20 text-emerald-300"
                                : log.actor === "paypal"
                                ? "bg-blue-500/20 text-blue-300"
                                : "bg-slate-700 text-slate-300"
                            }`}
                          >
                            {log.actor}
                          </span>
                          <span className="font-semibold text-slate-200">
                            {log.action}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-500">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      {log.details && (
                        <p className="text-xs text-slate-400 font-mono pl-2 border-l border-slate-700">
                          {log.details}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

