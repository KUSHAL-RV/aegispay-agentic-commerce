/**
 * Payload to create a new escrow transaction.
 */
export interface CreateTransactionRequest {
  vendorName: string;
  vendorEmail: string;
  description: string;
  amount: number;
  currency?: string;
}
