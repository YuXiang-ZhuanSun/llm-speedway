use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SpeedtestResult {
    pub id: String,
    pub provider_id: String,
    pub provider_name: String,
    pub display_name: String,
    pub model: String,
    pub status: String,
    pub ttft_ms: Option<f64>,
    pub decode_tps: Option<f64>,
    pub multi_turn_decode_tps: Option<f64>,
    pub success_rate: Option<f64>,
    pub error_message: Option<String>,
    pub created_at: String,
}
