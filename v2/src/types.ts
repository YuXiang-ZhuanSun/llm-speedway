export type ProviderConfig = {
  id: string;
  providerName: string;
  displayName: string;
  baseUrl: string;
  endpoint: string;
  model: string;
  apiKeyPreview: string;
  enabled: boolean;
  tags: string[];
  note?: string;
  updatedAt: string;
  apiFormat?: ApiFormat;
};

export type ApiFormat = "openai" | "anthropic";

export type CreateProviderInput = {
  providerName: string;
  baseUrl: string;
  endpoint: string;
  apiKey: string;
  model: string;
  apiFormat: ApiFormat;
  tags: string[];
  note?: string;
};

export type SpeedtestStatus = "success" | "failed" | "running" | "canceled";

export type SpeedtestResult = {
  id: string;
  providerId: string;
  providerName: string;
  displayName: string;
  model: string;
  status: SpeedtestStatus;
  ttftMs?: number;
  decodeTps?: number;
  multiTurnDecodeTps?: number;
  successRate?: number;
  errorMessage?: string;
  createdAt: string;
};

export type SpeedtestStage =
  | "connection"
  | "short_chat"
  | "long_generation"
  | "multi_turn"
  | "summary";
