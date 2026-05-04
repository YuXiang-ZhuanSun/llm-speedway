import type { ProviderConfig, SpeedtestResult } from "../../types";

export const mockProviders: ProviderConfig[] = [
  {
    id: "deepseek-v4-flash",
    providerName: "DeepSeek",
    displayName: "DeepSeek V4 Flash",
    baseUrl: "https://api.deepseek.com/v1",
    endpoint: "/chat/completions",
    model: "deepseek-v4-flash",
    apiFormat: "openai",
    apiKeyPreview: "sk-...demo",
    enabled: true,
    tags: ["fast", "agent"],
    updatedAt: "2026-05-03 17:20",
  },
  {
    id: "ark-doubao-seed",
    providerName: "Ark",
    displayName: "Doubao Seed Code",
    baseUrl: "https://ark.example.com/api/v3",
    endpoint: "/chat/completions",
    model: "doubao-seed-2.0-code",
    apiFormat: "openai",
    apiKeyPreview: "volc-...demo",
    enabled: true,
    tags: ["code"],
    updatedAt: "2026-05-03 17:20",
  },
];

export const mockResults: SpeedtestResult[] = [
  {
    id: "run-1",
    providerId: "deepseek-v4-flash",
    providerName: "DeepSeek",
    displayName: "DeepSeek V4 Flash",
    model: "deepseek-v4-flash",
    status: "success",
    ttftMs: 6330,
    decodeTps: 97.6,
    multiTurnDecodeTps: 91.2,
    successRate: 1,
    createdAt: "2026-05-03 17:25",
  },
];
