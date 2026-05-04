use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ProviderConfig {
    pub id: String,
    pub provider_name: String,
    pub display_name: String,
    pub base_url: String,
    pub endpoint: String,
    pub model: String,
    pub api_key_preview: String,
    pub enabled: bool,
    pub tags: Vec<String>,
    pub note: Option<String>,
    pub updated_at: String,
    pub api_format: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateProviderInput {
    pub provider_name: String,
    pub base_url: String,
    pub endpoint: String,
    pub api_key: String,
    pub model: String,
    pub api_format: String,
    pub tags: Vec<String>,
    pub note: Option<String>,
}
