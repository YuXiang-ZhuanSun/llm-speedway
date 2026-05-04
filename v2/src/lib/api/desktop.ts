import { invoke } from "@tauri-apps/api/core";
import type { CreateProviderInput, ProviderConfig, SpeedtestResult } from "../../types";
import { mockProviders, mockResults } from "./mockData";

type BrowserProviderConfig = ProviderConfig & {
  apiKey?: string;
};

let browserProviders: BrowserProviderConfig[] = [...mockProviders];
let browserResults = [...mockResults];

const isTauriRuntime = "__TAURI_INTERNALS__" in window;

export function isDesktopRuntime() {
  return isTauriRuntime;
}

export async function listProviders(): Promise<ProviderConfig[]> {
  if (isTauriRuntime) {
    return invoke("list_providers");
  }
  return browserProviders;
}

export async function listResults(): Promise<SpeedtestResult[]> {
  if (isTauriRuntime) {
    return invoke("list_speedtest_results");
  }
  return browserResults;
}

export async function createProvider(input: CreateProviderInput): Promise<ProviderConfig> {
  if (isTauriRuntime) {
    return invoke("create_provider", { input });
  }

  const provider: BrowserProviderConfig = {
    id: crypto.randomUUID(),
    providerName: input.providerName,
    displayName: input.providerName,
    baseUrl: input.baseUrl,
    endpoint: input.endpoint || defaultEndpoint(input.apiFormat),
    model: input.model,
    apiFormat: input.apiFormat,
    apiKey: input.apiKey,
    apiKeyPreview: maskApiKey(input.apiKey),
    enabled: true,
    tags: input.tags,
    note: input.note,
    updatedAt: new Date().toLocaleString(),
  };
  browserProviders = [provider, ...browserProviders];
  return provider;
}

export async function duplicateProvider(providerId: string): Promise<ProviderConfig> {
  if (isTauriRuntime) {
    return invoke("duplicate_provider", { providerId });
  }

  const source = browserProviders.find((provider) => provider.id === providerId);
  if (!source) throw new Error("Provider not found");
  const provider = {
    ...source,
    id: crypto.randomUUID(),
    displayName: `${source.displayName} Copy`,
    updatedAt: new Date().toLocaleString(),
  };
  browserProviders = [provider, ...browserProviders];
  return provider;
}

export async function deleteProvider(providerId: string): Promise<void> {
  if (isTauriRuntime) {
    return invoke("delete_provider", { providerId });
  }

  browserProviders = browserProviders.filter((provider) => provider.id !== providerId);
  browserResults = browserResults.filter((result) => result.providerId !== providerId);
}

export async function runSpeedtest(providerId: string): Promise<SpeedtestResult> {
  if (isTauriRuntime) {
    return invoke("run_speedtest", { providerId });
  }

  const provider = browserProviders.find((item) => item.id === providerId);
  if (!provider) throw new Error("Provider not found");

  const result = await runBrowserSpeedtest(provider);
  browserResults = [result, ...browserResults];
  return result;
}

async function runBrowserSpeedtest(provider: BrowserProviderConfig): Promise<SpeedtestResult> {
  const createdAt = nowString();

  try {
    if (!provider.apiKey) {
      throw new Error("浏览器预览中的示例配置没有保存 API key，请先新增一个真实配置。");
    }

    const short = await measureBrowserRequest(
      provider,
      [{ role: "user", content: "Say hello in one short sentence." }],
      128,
    );
    const long = await measureBrowserRequest(
      provider,
      [
        {
          role: "user",
          content:
            "Write a concise but detailed 6 bullet checklist for evaluating an LLM API for coding agents.",
        },
      ],
      512,
    );
    const multi = await measureBrowserRequest(
      provider,
      [
        { role: "user", content: "We are comparing LLM API latency for an agent product." },
        {
          role: "assistant",
          content:
            "Understood. We should compare first-token latency, sustained generation speed, and reliability.",
        },
        { role: "user", content: "Now summarize the most important tradeoff in two sentences." },
      ],
      256,
    );

    return {
      id: crypto.randomUUID(),
      providerId: provider.id,
      providerName: provider.providerName,
      displayName: provider.displayName,
      model: provider.model,
      status: "success",
      ttftMs: short.ttftMs,
      decodeTps: long.decodeTps,
      multiTurnDecodeTps: multi.decodeTps,
      successRate: 1,
      createdAt,
    };
  } catch (error) {
    return {
      id: crypto.randomUUID(),
      providerId: provider.id,
      providerName: provider.providerName,
      displayName: provider.displayName,
      model: provider.model,
      status: "failed",
      successRate: 0,
      errorMessage: error instanceof Error ? error.message : String(error),
      createdAt,
    };
  }
}

async function measureBrowserRequest(
  provider: BrowserProviderConfig,
  messages: Array<{ role: "user" | "assistant"; content: string }>,
  maxTokens: number,
) {
  const apiFormat = provider.apiFormat || "openai";
  const url = joinUrl(provider.baseUrl, provider.endpoint || defaultEndpoint(apiFormat));
  const headers: Record<string, string> = {
    "content-type": "application/json",
  };

  let body: unknown;
  if (apiFormat === "anthropic") {
    headers["x-api-key"] = provider.apiKey || "";
    headers["anthropic-version"] = "2023-06-01";
    body = {
      model: provider.model,
      max_tokens: maxTokens,
      stream: true,
      messages,
    };
  } else {
    headers.authorization = `Bearer ${provider.apiKey}`;
    body = {
      model: provider.model,
      stream: true,
      max_tokens: maxTokens,
      messages,
    };
  }

  const start = performance.now();
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${truncate(await response.text(), 500)}`);
  }
  if (!response.body) {
    throw new Error("API did not return a readable stream.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let visible = "";
  let ttftMs: number | undefined;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let newlineIndex = buffer.indexOf("\n");
    while (newlineIndex >= 0) {
      const line = buffer.slice(0, newlineIndex).trim();
      buffer = buffer.slice(newlineIndex + 1);
      newlineIndex = buffer.indexOf("\n");

      if (!line.startsWith("data:")) continue;
      const data = line.replace(/^data:\s*/, "");
      if (!data || data === "[DONE]") continue;

      const text = extractStreamText(data, apiFormat);
      if (text) {
        if (!ttftMs && text.trim()) {
          ttftMs = performance.now() - start;
        }
        visible += text;
      }
    }
  }

  if (!ttftMs) {
    throw new Error("No visible streamed assistant text.");
  }

  const elapsedAfterTtft = Math.max((performance.now() - start - ttftMs) / 1000, 0.001);
  return {
    ttftMs: roundTwo(ttftMs),
    decodeTps: roundOne(estimateTokens(visible) / elapsedAfterTtft),
  };
}

function extractStreamText(data: string, apiFormat: "openai" | "anthropic") {
  try {
    const value = JSON.parse(data);
    if (apiFormat === "anthropic") {
      return value?.delta?.text || value?.content_block?.text || "";
    }
    return value?.choices?.[0]?.delta?.content || "";
  } catch {
    return "";
  }
}

function defaultEndpoint(apiFormat: "openai" | "anthropic") {
  return apiFormat === "anthropic" ? "/v1/messages" : "/chat/completions";
}

function joinUrl(baseUrl: string, endpoint: string) {
  return `${baseUrl.replace(/\/+$/, "")}/${endpoint.replace(/^\/+/, "")}`;
}

function estimateTokens(text: string) {
  return Math.max(Array.from(text).length / 4, 1);
}

function roundOne(value: number) {
  return Math.round(value * 10) / 10;
}

function roundTwo(value: number) {
  return Math.round(value * 100) / 100;
}

function truncate(text: string, maxChars: number) {
  return Array.from(text).slice(0, maxChars).join("");
}

function nowString() {
  const now = new Date();
  const pad = (value: number, length = 2) => String(value).padStart(length, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(
    now.getHours(),
  )}:${pad(now.getMinutes())}:${pad(now.getSeconds())}.${pad(now.getMilliseconds(), 3)}`;
}

function maskApiKey(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return "empty";
  if (trimmed.length <= 8) return "****";
  return `${trimmed.slice(0, 3)}-...${trimmed.slice(-4)}`;
}
