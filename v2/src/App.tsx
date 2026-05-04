import { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  Gauge,
  Loader2,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createProvider,
  deleteProvider,
  isDesktopRuntime,
  listProviders,
  listResults,
  runSpeedtest as runSpeedtestCommand,
} from "./lib/api/desktop";
import type {
  CreateProviderInput,
  ProviderConfig,
  SpeedtestResult,
  SpeedtestStage,
} from "./types";

const stageLabels: Record<SpeedtestStage, string> = {
  connection: "连接检查",
  short_chat: "短对话",
  long_generation: "长生成",
  multi_turn: "多轮测试",
  summary: "汇总保存",
};

const stageMessages: Record<SpeedtestStage, string> = {
  connection: "正在连接 API",
  short_chat: "正在等待首 token",
  long_generation: "正在计算生成速度",
  multi_turn: "正在执行多轮测试",
  summary: "正在保存结果",
};

function App() {
  const queryClient = useQueryClient();
  const providersQuery = useQuery({ queryKey: ["providers"], queryFn: listProviders });
  const resultsQuery = useQuery({ queryKey: ["speedtest-results"], queryFn: listResults });
  const [query, setQuery] = useState("");
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [expandedProviderIds, setExpandedProviderIds] = useState<Set<string>>(new Set());
  const [activeRuns, setActiveRuns] = useState<
    Record<string, { provider: ProviderConfig; stage: SpeedtestStage; startedAt: number }>
  >({});

  useEffect(() => {
    if (Object.keys(activeRuns).length === 0) return;

    const stages: SpeedtestStage[] = [
      "connection",
      "short_chat",
      "long_generation",
      "multi_turn",
      "summary",
    ];

    const timer = window.setInterval(() => {
      setActiveRuns((current) => {
        const next = { ...current };
        for (const [providerId, run] of Object.entries(next)) {
          const currentIndex = stages.indexOf(run.stage);
          const nextStage = stages[Math.min(currentIndex + 1, stages.length - 1)];
          next[providerId] = { ...run, stage: nextStage };
        }
        return next;
      });
    }, 1200);

    return () => window.clearInterval(timer);
  }, [Object.keys(activeRuns).join("|")]);

  const providers = providersQuery.data ?? [];
  const results = resultsQuery.data ?? [];

  const createProviderMutation = useMutation({
    mutationFn: createProvider,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["providers"] });
      setIsEditorOpen(false);
    },
  });

  const deleteProviderMutation = useMutation({
    mutationFn: deleteProvider,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["providers"] });
      void queryClient.invalidateQueries({ queryKey: ["speedtest-results"] });
    },
  });

  const runSpeedtestMutation = useMutation({
    mutationFn: runSpeedtestCommand,
    onSuccess: (result) => {
      setExpandedProviderIds((current) => new Set(current).add(result.providerId));
      setActiveRuns((current) => {
        const next = { ...current };
        delete next[result.providerId];
        return next;
      });
      queryClient.setQueryData<SpeedtestResult[]>(["speedtest-results"], (current = []) => [
        result,
        ...current.filter((item) => item.id !== result.id),
      ]);
      void queryClient.invalidateQueries({ queryKey: ["speedtest-results"] });
    },
    onError: (_error, providerId) => {
      setActiveRuns((current) => {
        const next = { ...current };
        delete next[providerId];
        return next;
      });
    },
  });

  const filteredProviders = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return providers;
    return providers.filter((provider) =>
      [
        provider.providerName,
        provider.model,
        provider.baseUrl,
        provider.tags.join(" "),
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalized),
    );
  }, [providers, query]);

  function latestResultFor(providerId: string) {
    return results.find((result) => result.providerId === providerId);
  }

  function addProvider(formData: FormData) {
    const providerName = String(formData.get("providerName") || "").trim();
    const baseUrl = String(formData.get("baseUrl") || "").trim();
    const model = String(formData.get("model") || "").trim();

    if (!providerName || !baseUrl || !model) return;

    const apiFormat = String(formData.get("apiFormat") || "openai") as CreateProviderInput["apiFormat"];

    const input: CreateProviderInput = {
      providerName,
      baseUrl,
      endpoint: defaultEndpoint(apiFormat),
      model,
      apiFormat,
      apiKey: String(formData.get("apiKey") || ""),
      tags: String(formData.get("tags") || "")
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      note: String(formData.get("note") || "").trim(),
    };

    createProviderMutation.mutate(input);
  }

  function handleRunSpeedtest(provider: ProviderConfig) {
    setExpandedProviderIds((current) => new Set(current).add(provider.id));
    setActiveRuns((current) => ({
      ...current,
      [provider.id]: { provider, stage: "connection", startedAt: Date.now() },
    }));
    runSpeedtestMutation.reset();
    runSpeedtestMutation.mutate(provider.id);
  }

  function collapseResult(providerId: string) {
    setExpandedProviderIds((current) => {
      const next = new Set(current);
      next.delete(providerId);
      return next;
    });
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              llm-speedway V2 · {isDesktopRuntime() ? "Tauri 桌面版" : "浏览器预览"}
            </p>
            <h1>模型 API 测速</h1>
          </div>
          <button className="primary-button" onClick={() => setIsEditorOpen(true)}>
            <Plus size={18} />
            添加配置
          </button>
        </header>

        <section className="toolbar" aria-label="Provider filters">
          <div className="search-box">
            <Search size={18} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索供应商、模型、标签或 API 地址"
            />
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>API 配置</h2>
            <span>{filteredProviders.length} 个</span>
          </div>

          <div className="provider-list">
            {filteredProviders.map((provider) => {
              const latestResult = latestResultFor(provider.id);
              const activeRun = activeRuns[provider.id];
              const isRunning = Boolean(activeRun);
              const isExpanded = expandedProviderIds.has(provider.id) || isRunning;

              return (
                <article className="provider-row" key={provider.id}>
                  <div className="provider-main">
                    <div>
                      <div className="row-title">
                        <strong>{provider.providerName}</strong>
                        <span>{formatApiFormat(provider.apiFormat)}</span>
                      </div>
                      <p>{provider.model}</p>
                      <code>{provider.baseUrl}</code>
                      <div className="tag-list">
                        {provider.tags.map((tag) => (
                          <span key={tag}>{tag}</span>
                        ))}
                      </div>
                    </div>

                    <div className="row-actions">
                      <span className="key-preview">{provider.apiKeyPreview}</span>
                      <button
                        className="icon-button danger"
                        title="删除配置"
                        onClick={() => deleteProviderMutation.mutate(provider.id)}
                      >
                        <Trash2 size={17} />
                      </button>
                      <button
                        className="primary-button"
                        disabled={isRunning}
                        onClick={() => handleRunSpeedtest(provider)}
                      >
                        {isRunning ? <Loader2 className="spin-icon" size={17} /> : <Gauge size={17} />}
                        {isRunning ? "测速中" : "测速"}
                      </button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="inline-result">
                      {isRunning && activeRun ? (
                        <SpeedtestProgress
                          stage={activeRun.stage}
                          provider={provider}
                          onCollapse={() => collapseResult(provider.id)}
                        />
                      ) : (
                        <SpeedtestResultView
                          result={latestResult}
                          onCollapse={() => collapseResult(provider.id)}
                        />
                      )}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        </section>
      </section>

      {isEditorOpen && (
        <div className="modal-backdrop">
          <form
            className="modal"
            onSubmit={(event) => {
              event.preventDefault();
              addProvider(new FormData(event.currentTarget));
            }}
          >
            <div className="modal-header">
              <h2>添加 API 配置</h2>
              <button className="icon-button" type="button" onClick={() => setIsEditorOpen(false)}>
                <X size={18} />
              </button>
            </div>
            <div className="form-grid">
              <label>
                供应商
                <input name="providerName" placeholder="DeepSeek" required />
              </label>
              <label>
                Base URL
                <input name="baseUrl" placeholder="https://api.example.com/v1" required />
              </label>
              <label>
                API 格式
                <select name="apiFormat" defaultValue="openai">
                  <option value="openai">OpenAI compatible</option>
                  <option value="anthropic">Anthropic compatible</option>
                </select>
              </label>
              <label>
                模型
                <input name="model" placeholder="model-name" required />
              </label>
              <label>
                API key
                <input name="apiKey" type="password" placeholder="sk-..." required />
              </label>
              <label>
                标签
                <input name="tags" placeholder="fast, code, agent" />
              </label>
              <label>
                备注
                <input name="note" placeholder="可选" />
              </label>
            </div>
            <div className="modal-actions">
              <button className="secondary-button" type="button" onClick={() => setIsEditorOpen(false)}>
                取消
              </button>
              <button className="primary-button" type="submit">
                保存
              </button>
            </div>
          </form>
        </div>
      )}
    </main>
  );
}

function SpeedtestProgress({
  stage,
  provider,
  onCollapse,
}: {
  stage: SpeedtestStage;
  provider: ProviderConfig;
  onCollapse: () => void;
}) {
  return (
    <>
      <div className="inline-result-header">
        <div>
          <strong>正在测速</strong>
          <span>{provider.model}</span>
        </div>
        <span className="status-pill running">
          <Loader2 className="spin-icon" size={15} />
          {stageLabels[stage]}
        </span>
        <button className="secondary-button compact-button" type="button" onClick={onCollapse}>
          收起
        </button>
      </div>
      <div className="progress-bar" aria-label="Speedtest progress">
        <span style={{ width: `${progressForStage(stage)}%` }} />
      </div>
      <p className="status-text">{stageMessages[stage]}</p>
    </>
  );
}

function SpeedtestResultView({
  result,
  onCollapse,
}: {
  result?: SpeedtestResult;
  onCollapse: () => void;
}) {
  if (!result) {
    return (
      <div className="empty-result">
        <strong>还没有测速结果</strong>
        <span>点击测速后，结果会显示在这里。</span>
      </div>
    );
  }

  return (
    <>
      <div className="inline-result-header">
        <div>
          <strong>测速结果</strong>
          <span>{result.createdAt}</span>
        </div>
        <span className={`status-pill ${result.status}`}>
          <CheckCircle2 size={15} />
          {result.status}
        </span>
        <button className="secondary-button compact-button" type="button" onClick={onCollapse}>
          收起
        </button>
      </div>
      {result.status === "failed" ? (
        <p className="error-text">{result.errorMessage || "测速失败"}</p>
      ) : (
        <div className="metric-grid">
          <Metric label="首 token" value={formatMs(result.ttftMs)} />
          <Metric label="生成速度" value={formatTps(result.decodeTps)} />
          <Metric label="多轮速度" value={formatTps(result.multiTurnDecodeTps)} />
          <Metric label="成功率" value={formatPercent(result.successRate)} />
        </div>
      )}
    </>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatMs(value?: number) {
  if (value === undefined) return "-";
  return `${(value / 1000).toFixed(2)}s`;
}

function formatTps(value?: number) {
  if (value === undefined) return "-";
  return `${value.toFixed(1)} tok/s`;
}

function formatPercent(value?: number) {
  if (value === undefined) return "-";
  return `${Math.round(value * 100)}%`;
}

function formatApiFormat(value?: string) {
  return value === "anthropic" ? "Anthropic" : "OpenAI";
}

function defaultEndpoint(apiFormat: CreateProviderInput["apiFormat"]) {
  return apiFormat === "anthropic" ? "/v1/messages" : "/chat/completions";
}

function progressForStage(stage: SpeedtestStage) {
  const order: SpeedtestStage[] = [
    "connection",
    "short_chat",
    "long_generation",
    "multi_turn",
    "summary",
  ];
  return ((order.indexOf(stage) + 1) / order.length) * 100;
}

export default App;
