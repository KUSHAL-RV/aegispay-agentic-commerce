import { TransactionStatus } from './transactionStatus';

/**
 * Full transaction entity response from AegisPay backend.
 */
export interface TransactionResponse {
  id: string;
  vendorName: string;
  vendorEmail: string;
  description: string;
  amount: number;
  currency: string;
  status: TransactionStatus | string;
  paypalOrderId: string | null;
  paypalAuthId: string | null;
  paypalCaptureId: string | null;
  paypalPayoutId: string | null;
  piiOriginal: string | null;
  piiRedacted: string | null;
  piiEntitiesFound: string | null;
  ed25519Signature: string | null;
  ed25519PublicKey: string | null;
  agentReasoning: string | null;
  createdAt: string;
  updatedAt: string;
}
