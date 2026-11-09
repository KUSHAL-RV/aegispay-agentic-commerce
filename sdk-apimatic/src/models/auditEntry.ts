/**
 * Chronological immutable audit trail entry.
 */
export interface AuditEntry {
  id: string;
  action: string;
  actor: 'system' | 'agent' | 'human' | 'paypal';
  details: string | null;
  timestamp: string;
}
