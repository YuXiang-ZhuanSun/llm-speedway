use crate::database::Database;
use crate::models::provider::{CreateProviderInput, ProviderConfig};
use chrono::Utc;
use rusqlite::{params, OptionalExtension};
use uuid::Uuid;

#[derive(Clone)]
pub struct ProviderService {
    database: Database,
}

impl ProviderService {
    pub fn new(database: Database) -> Self {
        Self { database }
    }

    pub fn list(&self) -> rusqlite::Result<Vec<ProviderConfig>> {
        self.database.with_connection(|connection| {
            let mut statement = connection.prepare(
                "
                SELECT id, provider_name, display_name, base_url, endpoint, model,
                       api_key_cipher, enabled, tags_json, note, updated_at, api_format
                FROM providers
                ORDER BY sort_order ASC, updated_at DESC
                ",
            )?;

            let rows = statement.query_map([], |row| {
                let tags_json: String = row.get(8)?;
                let tags = serde_json::from_str(&tags_json).unwrap_or_default();
                let api_key_cipher: String = row.get(6)?;

                Ok(ProviderConfig {
                    id: row.get(0)?,
                    provider_name: row.get(1)?,
                    display_name: row.get(2)?,
                    base_url: row.get(3)?,
                    endpoint: row.get(4)?,
                    model: row.get(5)?,
                    api_key_preview: mask_api_key(&api_key_cipher),
                    enabled: row.get::<_, i64>(7)? == 1,
                    tags,
                    note: row.get(9)?,
                    updated_at: row.get(10)?,
                    api_format: row.get(11)?,
                })
            })?;

            rows.collect()
        })
    }

    pub fn create(&self, input: CreateProviderInput) -> rusqlite::Result<ProviderConfig> {
        let now = Utc::now().to_rfc3339();
        let provider_name = input.provider_name;
        let provider = ProviderConfig {
            id: Uuid::new_v4().to_string(),
            provider_name: provider_name.clone(),
            display_name: provider_name,
            base_url: input.base_url,
            endpoint: if input.endpoint.trim().is_empty() {
                default_endpoint(&input.api_format)
            } else {
                input.endpoint
            },
            model: input.model,
            api_key_preview: mask_api_key(&input.api_key),
            enabled: true,
            tags: input.tags,
            note: input.note,
            updated_at: now.clone(),
            api_format: Some(input.api_format),
        };

        let tags_json = serde_json::to_string(&provider.tags).unwrap_or_else(|_| "[]".to_string());

        self.database.with_connection(|connection| {
            connection.execute(
                "
                INSERT INTO providers (
                    id, provider_name, display_name, base_url, endpoint, api_key_cipher,
                    model, enabled, sort_order, tags_json, note, api_format, created_at, updated_at
                )
                VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, 1, 0, ?8, ?9, ?10, ?11, ?11)
                ",
                params![
                    provider.id,
                    provider.provider_name,
                    provider.display_name,
                    provider.base_url,
                    provider.endpoint,
                    input.api_key,
                    provider.model,
                    tags_json,
                    provider.note,
                    provider.api_format,
                    now
                ],
            )?;
            Ok(provider)
        })
    }

    pub fn duplicate(&self, provider_id: &str) -> rusqlite::Result<ProviderConfig> {
        let source = self.find(provider_id)?;
        let input = CreateProviderInput {
            provider_name: source.provider_name,
            base_url: source.base_url,
            endpoint: source.endpoint,
            api_key: source.api_key_preview,
            model: source.model,
            api_format: source.api_format.unwrap_or_else(|| "openai".to_string()),
            tags: source.tags,
            note: source.note,
        };
        self.create(input)
    }

    pub fn delete(&self, provider_id: &str) -> rusqlite::Result<()> {
        self.database.with_connection(|connection| {
            connection.execute(
                "DELETE FROM speedtest_runs WHERE provider_id = ?1",
                params![provider_id],
            )?;
            connection.execute("DELETE FROM providers WHERE id = ?1", params![provider_id])?;
            Ok(())
        })
    }

    pub fn find(&self, provider_id: &str) -> rusqlite::Result<ProviderConfig> {
        self.database.with_connection(|connection| {
            connection
                .query_row(
                    "
                    SELECT id, provider_name, display_name, base_url, endpoint, model,
                           api_key_cipher, enabled, tags_json, note, updated_at, api_format
                    FROM providers
                    WHERE id = ?1
                    ",
                    params![provider_id],
                    |row| {
                        let tags_json: String = row.get(8)?;
                        let tags = serde_json::from_str(&tags_json).unwrap_or_default();
                        let api_key_cipher: String = row.get(6)?;
                        Ok(ProviderConfig {
                            id: row.get(0)?,
                            provider_name: row.get(1)?,
                            display_name: row.get(2)?,
                            base_url: row.get(3)?,
                            endpoint: row.get(4)?,
                            model: row.get(5)?,
                            api_key_preview: mask_api_key(&api_key_cipher),
                            enabled: row.get::<_, i64>(7)? == 1,
                            tags,
                            note: row.get(9)?,
                            updated_at: row.get(10)?,
                            api_format: row.get(11)?,
                        })
                    },
                )
                .optional()?
                .ok_or(rusqlite::Error::QueryReturnedNoRows)
        })
    }
}

fn default_endpoint(api_format: &str) -> String {
    if api_format == "anthropic" {
        "/v1/messages".to_string()
    } else {
        "/chat/completions".to_string()
    }
}

fn mask_api_key(value: &str) -> String {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return "empty".to_string();
    }
    if trimmed.len() <= 8 {
        return "****".to_string();
    }
    format!("{}-...{}", &trimmed[..3], &trimmed[trimmed.len() - 4..])
}
