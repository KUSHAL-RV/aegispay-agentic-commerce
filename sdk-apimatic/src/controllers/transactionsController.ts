import { HttpClient } from '../http/httpClient';
import { CreateTransactionRequest } from '../models/createTransactionRequest';
import { TransactionResponse } from '../models/transactionResponse';
import { AuditEntry } from '../models/auditEntry';

/**
 * Controller for managing escrow transactions and settlements.
 */
export class TransactionsController {
  private http: HttpClient;

  constructor(http: HttpClient) {
    this.http = http;
  }

  /**
   * Create and verify a new escrow transaction through the autonomous LangGraph pipeline.
   */
  async createTransaction(request: CreateTransactionRequest): Promise<TransactionResponse> {
    return this.http.request<TransactionResponse>('POST', '/api/transactions/create', {
      vendor_name: request.vendorName,
      vendor_email: request.vendorEmail,
      description: request.description,
      amount: request.amount,
      currency: request.currency || 'USD',
    });
  }

  /**
   * Capture authorized PayPal escrow funds and release payouts.
   */
  async approveTransaction(transactionId: string): Promise<TransactionResponse> {
    return this.http.request<TransactionResponse>(
      'POST',
      `/api/transactions/${encodeURIComponent(transactionId)}/approve`
    );
  }

  /**
   * Void PayPal escrow authorization without capturing.
   */
  async voidTransaction(transactionId: string): Promise<TransactionResponse> {
    return this.http.request<TransactionResponse>(
      'POST',
      `/api/transactions/${encodeURIComponent(transactionId)}/void`
    );
  }

  /**
   * List all escrow transactions with optional status filter.
   */
  async listTransactions(status?: string): Promise<TransactionResponse[]> {
    return this.http.request<TransactionResponse[]>('GET', '/api/transactions', undefined, {
      status,
    });
  }

  /**
   * Retrieve a single transaction by ID.
   */
  async getTransaction(transactionId: string): Promise<TransactionResponse> {
    return this.http.request<TransactionResponse>(
      'GET',
      `/api/transactions/${encodeURIComponent(transactionId)}`
    );
  }

  /**
   * Retrieve immutable audit trail entries for a transaction.
   */
  async getAuditLog(transactionId: string): Promise<AuditEntry[]> {
    return this.http.request<AuditEntry[]>(
      'GET',
      `/api/transactions/${encodeURIComponent(transactionId)}/audit`
    );
  }

  /**
   * Execute a judge simulator demo scenario (happy_path, pii_heavy, policy_breach).
   */
  async simulateScenario(
    scenario: 'happy_path' | 'pii_heavy' | 'policy_breach'
  ): Promise<TransactionResponse> {
    return this.http.request<TransactionResponse>(
      'POST',
      `/api/transactions/simulate/${encodeURIComponent(scenario)}`
    );
  }
}
