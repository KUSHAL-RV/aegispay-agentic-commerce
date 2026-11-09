"use client";

import { useMemo, useCallback, useRef } from "react";
import { AgGridReact } from "ag-grid-react";
import type { ColDef, GridReadyEvent, ICellRendererParams, RowClickedEvent } from "ag-grid-community";
import { RefreshCw, ExternalLink, ShieldCheck, Lock, AlertCircle, FileCheck, ArrowUpRight } from "lucide-react";
import { Transaction } from "@/lib/api";

interface Props {
  transactions: Transaction[];
  onSelect: (txn: Transaction) => void;
  onRefresh: () => void;
}

// ── Status Badge Renderer ──────────────────────────────────────────

function StatusRenderer(params: ICellRendererParams) {
  const status = (params.value as string) || "UNKNOWN";

  const colorStyles: Record<string, string> = {
    AUTHORIZED: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    CAPTURED: "bg-emerald-600/20 text-emerald-200 border-emerald-400/40",
    PAYOUT_SENT: "bg-teal-500/20 text-teal-300 border-teal-500/40",
    AGENT_APPROVED: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
    PII_SCRUBBED: "bg-sky-500/15 text-sky-300 border-sky-500/30",
    PENDING_REVIEW: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    VOIDED: "bg-slate-700/40 text-slate-400 border-slate-600/30",
    FAILED: "bg-rose-500/15 text-rose-300 border-rose-500/30",
    DISPUTED: "bg-purple-500/15 text-purple-300 border-purple-500/30",
  };

  const style = colorStyles[status] || "bg-slate-800 text-slate-400 border-slate-700";

  return (
    <div className="flex items-center h-full">
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${style}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-current" />
        {status.replace(/_/g, " ")}
      </span>
    </div>
  );
}

// ── Amount Currency Renderer ───────────────────────────────────────

function AmountRenderer(params: ICellRendererParams) {
  const val = params.value as number;
  if (val === undefined || val === null) return null;
  const currency = params.data?.currency || "USD";

  const isTotalRow = params.data?.id === "TOTAL_ROW";

  return (
    <div className={`flex items-center justify-end h-full font-mono font-bold ${
      isTotalRow ? "text-aegis-accent text-sm" : "text-slate-100 text-xs"
    }`}>
      {currency === "USD" ? "$" : `${currency} `}
      {val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
    </div>
  );
}

// ── PII Status Renderer ───────────────────────────────────────────

function PIIRenderer(params: ICellRendererParams) {
  const txn = params.data as Transaction;
  if (!txn || txn.id === "TOTAL_ROW") return null;

  const hasRedaction = Boolean(txn.pii_redacted && txn.pii_redacted !== txn.pii_original);
  let entityCount = 0;

  try {
    if (txn.pii_entities_found) {
      const parsed = JSON.parse(txn.pii_entities_found);
      if (Array.isArray(parsed)) entityCount = parsed.length;
    }
  } catch {
    // Ignore JSON parse errors
  }

  if (hasRedaction || entityCount > 0) {
    return (
      <div className="flex items-center h-full">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-sky-500/20 text-sky-300 border border-sky-500/40 font-mono">
          <Lock className="w-3 h-3 text-sky-400" />
          Scrubbed ({entityCount})
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center h-full">
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        <ShieldCheck className="w-3 h-3 text-emerald-400" />
        Clean
      </span>
    </div>
  );
}

// ── Crypto Signature Renderer ──────────────────────────────────────

function SignatureRenderer(params: ICellRendererParams) {
  const sig = params.value as string | null;
  if (params.data?.id === "TOTAL_ROW") return null;

  if (sig) {
    return (
      <div className="flex items-center h-full">
        <span
          className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 px-2 py-0.5 rounded"
          title={`Ed25519: ${sig}`}
        >
          <FileCheck className="w-3 h-3 text-emerald-400 shrink-0" />
          {sig.slice(0, 10)}…{sig.slice(-4)}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center h-full text-slate-500 text-xs font-mono">
      <AlertCircle className="w-3 h-3 mr-1 text-slate-600" />
      Unsigned
    </div>
  );
}

// ── PayPal Reference Renderer ──────────────────────────────────────

function PayPalRefRenderer(params: ICellRendererParams) {
  const data = params.data as Transaction;
  if (!data || data.id === "TOTAL_ROW") return null;

  const orderId = data.paypal_order_id;
  const authId = data.paypal_auth_id;

  if (authId) {
    return (
      <div className="flex items-center h-full">
        <span className="font-mono text-[11px] text-aegis-paypal bg-blue-950/40 border border-blue-500/30 px-2 py-0.5 rounded flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
          {authId.slice(0, 14)}…
        </span>
      </div>
    );
  }

  if (orderId) {
    return (
      <div className="flex items-center h-full">
        <span className="font-mono text-[11px] text-slate-300 bg-slate-800/60 border border-slate-700 px-2 py-0.5 rounded">
          {orderId.slice(0, 14)}…
        </span>
      </div>
    );
  }

  return <span className="text-slate-600 text-xs">—</span>;
}

// ── Action / Inspect Renderer ──────────────────────────────────────

function ActionRenderer(params: ICellRendererParams) {
  if (params.data?.id === "TOTAL_ROW") return null;

  return (
    <div className="flex items-center justify-center h-full">
      <button
        type="button"
        className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-aegis-accent bg-aegis-accent/10 hover:bg-aegis-accent/20 border border-aegis-accent/30 rounded transition-colors"
      >
        Audit
        <ArrowUpRight className="w-3 h-3" />
      </button>
    </div>
  );
}

export function LedgerGrid({ transactions, onSelect, onRefresh }: Props) {
  const gridRef = useRef<AgGridReact>(null);

  const columnDefs = useMemo<ColDef[]>(
    () => [
      {
        headerName: "TXN ID",
        field: "id",
        width: 110,
        pinned: "left",
        cellRenderer: (params: ICellRendererParams) => {
          if (params.value === "TOTAL_ROW") {
            return <span className="font-bold text-xs uppercase text-slate-300">SUMMARY</span>;
          }
          return (
            <div className="flex items-center h-full font-mono text-xs text-slate-400">
              {String(params.value || "").slice(0, 8)}…
            </div>
          );
        },
      },
      {
        headerName: "Vendor / Beneficiary",
        field: "vendor_name",
        minWidth: 170,
        flex: 1,
        cellRenderer: (params: ICellRendererParams) => {
          if (params.data?.id === "TOTAL_ROW") {
            return (
              <span className="text-xs font-semibold text-slate-400">
                {transactions.length} Total Escrow Records
              </span>
            );
          }
          return (
            <div className="flex flex-col justify-center h-full py-1">
              <span className="text-xs font-semibold text-slate-200 truncate">
                {params.value}
              </span>
              <span className="text-[10px] text-slate-400 truncate font-mono">
                {params.data?.vendor_email}
              </span>
            </div>
          );
        },
      },
      {
        headerName: "Amount",
        field: "amount",
        width: 130,
        type: "numericColumn",
        cellRenderer: AmountRenderer,
      },
      {
        headerName: "Escrow Status",
        field: "status",
        width: 175,
        cellRenderer: StatusRenderer,
      },
      {
        headerName: "Presidio PII",
        field: "pii_redacted",
        width: 135,
        cellRenderer: PIIRenderer,
      },
      {
        headerName: "Ed25519 Proof",
        field: "ed25519_signature",
        width: 155,
        cellRenderer: SignatureRenderer,
      },
      {
        headerName: "PayPal Auth / Order",
        field: "paypal_auth_id",
        width: 170,
        cellRenderer: PayPalRefRenderer,
      },
      {
        headerName: "Timestamp",
        field: "created_at",
        width: 145,
        valueFormatter: (params) => {
          if (!params.value || params.data?.id === "TOTAL_ROW") return "";
          try {
            return new Date(params.value).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            });
          } catch {
            return params.value;
          }
        },
      },
      {
        headerName: "Actions",
        width: 95,
        pinned: "right",
        cellRenderer: ActionRenderer,
      },
    ],
    [transactions.length]
  );

  const defaultColDef = useMemo<ColDef>(
    () => ({
      sortable: true,
      resizable: true,
      filter: true,
    }),
    []
  );

  // Bottom pinned summary totals row
  const pinnedBottomRowData = useMemo(() => {
    const totalAmount = transactions.reduce((sum, item) => sum + (item.amount || 0), 0);
    return [
      {
        id: "TOTAL_ROW",
        vendor_name: `${transactions.length} Records`,
        amount: totalAmount,
        currency: "USD",
        status: "",
        pii_redacted: null,
        ed25519_signature: null,
        paypal_auth_id: null,
        created_at: null,
      },
    ];
  }, [transactions]);

  const onGridReady = useCallback((params: GridReadyEvent) => {
    params.api.sizeColumnsToFit();
  }, []);

  const onRowClicked = useCallback(
    (event: RowClickedEvent) => {
      if (event.data && event.data.id !== "TOTAL_ROW") {
        onSelect(event.data as Transaction);
      }
    },
    [onSelect]
  );

  return (
    <div className="bg-aegis-surface rounded-xl border border-aegis-border overflow-hidden shadow-xl">
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-aegis-border bg-aegis-surface/90">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-sm bg-aegis-accent rotate-45" />
          <h2 className="text-sm font-bold text-slate-100 tracking-wide uppercase">
            Enterprise Escrow Ledger
          </h2>
          <span className="text-[11px] font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
            AG Grid Financial Command
          </span>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onRefresh}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-aegis-accent bg-aegis-card hover:bg-slate-800 border border-aegis-border rounded-lg transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Sync Ledger
          </button>
        </div>
      </div>

      <div className="ag-theme-alpine-dark" style={{ height: 490, width: "100%" }}>
        <AgGridReact
          ref={gridRef}
          rowData={transactions}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          pinnedBottomRowData={pinnedBottomRowData}
          onGridReady={onGridReady}
          onRowClicked={onRowClicked}
          rowSelection="single"
          animateRows={true}
          getRowId={(params) => params.data.id}
          enableCellTextSelection={true}
          suppressCellFocus={false}
        />
      </div>
    </div>
  );
}

