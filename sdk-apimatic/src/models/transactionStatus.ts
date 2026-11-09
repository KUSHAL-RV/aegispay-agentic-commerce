/**
 * AegisPay Escrow Transaction Status enumeration.
 */
export enum TransactionStatus {
  PendingReview = 'PENDING_REVIEW',
  PiiScrubbed = 'PII_SCRUBBED',
  AgentApproved = 'AGENT_APPROVED',
  Authorized = 'AUTHORIZED',
  Captured = 'CAPTURED',
  Voided = 'VOIDED',
  PayoutSent = 'PAYOUT_SENT',
  Disputed = 'DISPUTED',
  Failed = 'FAILED',
}
