import { Configuration, Environment } from './configuration';
import { HttpClient } from './http/httpClient';
import { TransactionsController } from './controllers/transactionsController';
import { WebhooksController } from './controllers/webhooksController';

/**
 * Main AegisPay SDK Client generated for APIMatic conformance.
 */
export class AegisPayClient {
  public readonly transactions: TransactionsController;
  public readonly webhooks: WebhooksController;

  constructor(config: Configuration = {}) {
    const baseUrl = config.environment || Environment.Local;
    const timeout = config.timeout || 30000;
    const http = new HttpClient(baseUrl, timeout);

    this.transactions = new TransactionsController(http);
    this.webhooks = new WebhooksController(http);
  }
}

