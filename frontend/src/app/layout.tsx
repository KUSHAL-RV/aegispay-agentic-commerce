import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AegisPay | Agentic Escrow & Settlement Engine",
  description:
    "Autonomous B2B Proof-of-Work Escrow, Presidio PII-Sanitized Compliance, and PayPal Settlement Engine with AG Grid Financial Ledger",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-aegis-bg text-slate-100 antialiased selection:bg-aegis-accent/30 selection:text-aegis-accent">
        {children}
      </body>
    </html>
  );
}

