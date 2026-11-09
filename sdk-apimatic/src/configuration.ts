/**
 * Environments supported by the SDK.
 */
export enum Environment {
  Local = 'http://localhost:8000',
  Production = 'https://aegispay-backend.onrender.com',
}

/**
 * Configuration options for AegisPayClient.
 */
export interface Configuration {
  environment?: Environment | string;
  timeout?: number;
}
