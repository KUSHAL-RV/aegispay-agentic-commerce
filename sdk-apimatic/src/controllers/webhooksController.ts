import { HttpClient } from '../http/httpClient';

/**
 * Controller for dispatching PayPal sandbox webhook events.
 */
export class WebhooksController {
  private http: HttpClient;

  constructor(http: HttpClient) {
    this.http = http;
  }

  /**
   * Dispatch a simulated or live PayPal sandbox webhook event.
   */
  async receivePayPalWebhook(eventPayload: Record<string, unknown>): Promise<{ status: string; event_id: string }> {
    return this.http.request<{ status: string; event_id: string }>(
      'POST',
      '/api/webhooks/paypal',
      eventPayload
    );
  }
}
