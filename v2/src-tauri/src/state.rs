use crate::services::{ProviderService, SpeedtestService};

pub struct AppState {
    pub provider_service: ProviderService,
    pub speedtest_service: SpeedtestService,
}
