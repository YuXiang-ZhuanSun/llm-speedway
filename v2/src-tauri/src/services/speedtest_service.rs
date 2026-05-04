use crate::database::Database;
use crate::models::speedtest::SpeedtestResult;
use chrono::Local;
use futures_util::StreamExt;
use reqwest::Client;
use rusqlite::params;
use serde_json::{json, Value};
use std::time::Instant;
use uuid::Uuid;

#[derive(Clone)]
pub struct SpeedtestService {
    database: Database,
    http: Client,
}

impl SpeedtestService {
    pub fn new(database: Database) -> Self {
        Self {
            database,
            http: Client::builder()
                .timeout(std::time::Duration::from_secs(60))
                .build()
                .expect("failed to build HTTP client"),
        }
    }

    pub fn list_results(&self) -> rusqlite::Result<Vec<SpeedtestResult>> {
        self.database.with_connection(|connection| {
            let mut statement = connection.prepare(
                "
                SELECT id, provider_id, provider_name, display_name, model, status,
                       ttft_ms, decode_tps, multi_turn_decode_tps, success_rate,
                       error_message, COALESCE(finished_at, started_at)
                FROM speedtest_runs
                ORDER BY started_at DESC
                ",
            )?;

            let rows = statement.query_map([], |row| {
                Ok(SpeedtestResult {
                    id: row.get(0)?,
                    provider_id: row.get(1)?,
                    provider_name: row.get(2)?,
                    display_name: row.get(3)?,
                    model: row.get(4)?,
                    status: row.get(5)?,
                    ttft_ms: row.get(6)?,
                    decode_tps: row.get(7)?,
                    multi_turn_decode_tps: row.get(8)?,
                    success_rate: row.get(9)?,
                    error_message: row.get(10)?,
                    created_at: row.get(11)?,
                })
            })?;

            rows.collect()
        })
    }

    pub async fn run(&self, provider_id: &str) -> rusqlite::Result<SpeedtestResult> {
        let provider = self.load_provider(provider_id)?;
        let run_id = Uuid::new_v4().to_string();
        let started_at = now_string();

        let measured = self.measure_provider(&provider).await;
        let finished_at = now_string();

        let result = match measured {
            Ok(metrics) => SpeedtestResult {
                id: run_id,
                provider_id: provider.id,
                provider_name: provider.provider_name,
                display_name: provider.display_name,
                model: provider.model,
                status: "success".to_string(),
                ttft_ms: Some(metrics.ttft_ms),
                decode_tps: metrics.decode_tps,
                multi_turn_decode_tps: metrics.multi_turn_decode_tps,
                success_rate: Some(1.0),
                error_message: None,
                created_at: finished_at.clone(),
            },
            Err(error) => SpeedtestResult {
                id: run_id,
                provider_id: provider.id,
                provider_name: provider.provider_name,
                display_name: provider.display_name,
                model: provider.model,
                status: "failed".to_string(),
                ttft_ms: None,
                decode_tps: None,
                multi_turn_decode_tps: None,
                success_rate: Some(0.0),
                error_message: Some(error),
                created_at: finished_at.clone(),
            },
        };

        self.save_result(&result, &started_at, &finished_at)?;
        Ok(result)
    }

    async fn measure_provider(&self, provider: &ProviderSnapshot) -> Result<SpeedMetrics, String> {
        let short = self
            .measure_request(
                provider,
                vec![ChatMessage::user("Say hello in one short sentence.")],
                128,
            )
            .await?;

        let long = self
            .measure_request(
                provider,
                vec![ChatMessage::user(
                    "Write a concise but detailed 6 bullet checklist for evaluating an LLM API for coding agents.",
                )],
                512,
            )
            .await?;

        let multi = self
            .measure_request(
                provider,
                vec![
                    ChatMessage::user("We are comparing LLM API latency for an agent product."),
                    ChatMessage::assistant(
                        "Understood. We should compare first-token latency, sustained generation speed, and reliability.",
                    ),
                    ChatMessage::user("Now summarize the most important tradeoff in two sentences."),
                ],
                256,
            )
            .await?;

        Ok(SpeedMetrics {
            ttft_ms: short.ttft_ms,
            decode_tps: long.decode_tps,
            multi_turn_decode_tps: multi.decode_tps,
        })
    }

    async fn measure_request(
        &self,
        provider: &ProviderSnapshot,
        messages: Vec<ChatMessage>,
        max_tokens: u32,
    ) -> Result<RequestMetrics, String> {
        let url = join_url(&provider.base_url, &provider.endpoint);
        let body = if provider.api_format == "anthropic" {
            json!({
                "model": provider.model,
                "max_tokens": max_tokens,
                "stream": true,
                "messages": messages
                    .iter()
                    .map(|message| json!({
                        "role": message.role,
                        "content": message.content,
                    }))
                    .collect::<Vec<_>>()
            })
        } else {
            json!({
                "model": provider.model,
                "stream": true,
                "max_tokens": max_tokens,
                "messages": messages
                    .iter()
                    .map(|message| json!({
                        "role": message.role,
                        "content": message.content,
                    }))
                    .collect::<Vec<_>>()
            })
        };

        let mut request = self.http.post(&url).json(&body);
        if provider.api_format == "anthropic" {
            request = request
                .header("x-api-key", &provider.api_key)
                .header("anthropic-version", "2023-06-01");
        } else {
            request = request.bearer_auth(&provider.api_key);
        }

        let start = Instant::now();
        let response = request
            .send()
            .await
            .map_err(|error| format!("Request failed: {error}"))?;
        let status = response.status();
        if !status.is_success() {
            let text = response.text().await.unwrap_or_default();
            return Err(format!("HTTP {status}: {}", truncate(&text, 500)));
        }

        let mut stream = response.bytes_stream();
        let mut buffer = String::new();
        let mut visible = String::new();
        let mut ttft_ms: Option<f64> = None;

        while let Some(chunk) = stream.next().await {
            let chunk = chunk.map_err(|error| format!("Stream failed: {error}"))?;
            buffer.push_str(&String::from_utf8_lossy(&chunk));

            while let Some(index) = buffer.find('\n') {
                let line = buffer[..index].trim().to_string();
                buffer = buffer[index + 1..].to_string();
                if !line.starts_with("data:") {
                    continue;
                }

                let data = line.trim_start_matches("data:").trim();
                if data == "[DONE]" {
                    break;
                }
                if data.is_empty() {
                    continue;
                }

                if let Some(text) = extract_stream_text(data, &provider.api_format) {
                    if !text.trim().is_empty() && ttft_ms.is_none() {
                        ttft_ms = Some(start.elapsed().as_secs_f64() * 1000.0);
                    }
                    visible.push_str(&text);
                }
            }
        }

        let ttft_ms = ttft_ms.ok_or_else(|| "No visible streamed assistant text".to_string())?;
        let elapsed_after_ttft = (start.elapsed().as_secs_f64() - ttft_ms / 1000.0).max(0.001);
        let estimated_tokens = estimate_tokens(&visible);

        Ok(RequestMetrics {
            ttft_ms: round_two(ttft_ms),
            decode_tps: Some(round_one(estimated_tokens / elapsed_after_ttft)),
        })
    }

    fn load_provider(&self, provider_id: &str) -> rusqlite::Result<ProviderSnapshot> {
        self.database.with_connection(|connection| {
            connection.query_row(
                "
                SELECT id, provider_name, display_name, model, base_url,
                       endpoint, api_key_cipher, api_format
                FROM providers
                WHERE id = ?1
                ",
                params![provider_id],
                |row| {
                    Ok(ProviderSnapshot {
                        id: row.get(0)?,
                        provider_name: row.get(1)?,
                        display_name: row.get(2)?,
                        model: row.get(3)?,
                        base_url: row.get(4)?,
                        endpoint: row.get(5)?,
                        api_key: row.get(6)?,
                        api_format: row
                            .get::<_, Option<String>>(7)?
                            .unwrap_or_else(|| "openai".to_string()),
                    })
                },
            )
        })
    }

    fn save_result(
        &self,
        result: &SpeedtestResult,
        started_at: &str,
        finished_at: &str,
    ) -> rusqlite::Result<()> {
        self.database.with_connection(|connection| {
            connection.execute(
                "
                INSERT INTO speedtest_runs (
                    id, provider_id, provider_name, display_name, model, status,
                    started_at, finished_at, ttft_ms, decode_tps,
                    multi_turn_decode_tps, total_latency_ms, success_rate,
                    error_message, summary_json
                )
                VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, '{}')
                ",
                params![
                    result.id,
                    result.provider_id,
                    result.provider_name,
                    result.display_name,
                    result.model,
                    result.status,
                    started_at,
                    finished_at,
                    result.ttft_ms,
                    result.decode_tps,
                    result.multi_turn_decode_tps,
                    result.ttft_ms,
                    result.success_rate,
                    result.error_message,
                ],
            )?;
            Ok(())
        })
    }
}

struct ProviderSnapshot {
    id: String,
    provider_name: String,
    display_name: String,
    model: String,
    base_url: String,
    endpoint: String,
    api_key: String,
    api_format: String,
}

struct ChatMessage {
    role: &'static str,
    content: &'static str,
}

impl ChatMessage {
    fn user(content: &'static str) -> Self {
        Self {
            role: "user",
            content,
        }
    }

    fn assistant(content: &'static str) -> Self {
        Self {
            role: "assistant",
            content,
        }
    }
}

struct SpeedMetrics {
    ttft_ms: f64,
    decode_tps: Option<f64>,
    multi_turn_decode_tps: Option<f64>,
}

struct RequestMetrics {
    ttft_ms: f64,
    decode_tps: Option<f64>,
}

fn extract_stream_text(data: &str, api_format: &str) -> Option<String> {
    let value: Value = serde_json::from_str(data).ok()?;
    if api_format == "anthropic" {
        value
            .get("delta")
            .and_then(|delta| delta.get("text"))
            .and_then(Value::as_str)
            .map(ToString::to_string)
            .or_else(|| {
                value
                    .get("content_block")
                    .and_then(|block| block.get("text"))
                    .and_then(Value::as_str)
                    .map(ToString::to_string)
            })
    } else {
        value
            .get("choices")
            .and_then(Value::as_array)
            .and_then(|choices| choices.first())
            .and_then(|choice| choice.get("delta"))
            .and_then(|delta| delta.get("content"))
            .and_then(Value::as_str)
            .map(ToString::to_string)
    }
}

fn join_url(base_url: &str, endpoint: &str) -> String {
    format!(
        "{}/{}",
        base_url.trim_end_matches('/'),
        endpoint.trim_start_matches('/')
    )
}

fn now_string() -> String {
    Local::now().format("%Y-%m-%d %H:%M:%S%.3f").to_string()
}

fn estimate_tokens(text: &str) -> f64 {
    let chars = text.chars().count() as f64;
    (chars / 4.0).max(1.0)
}

fn round_one(value: f64) -> f64 {
    (value * 10.0).round() / 10.0
}

fn round_two(value: f64) -> f64 {
    (value * 100.0).round() / 100.0
}

fn truncate(text: &str, max_chars: usize) -> String {
    text.chars().take(max_chars).collect()
}
