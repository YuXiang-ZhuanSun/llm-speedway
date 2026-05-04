use crate::models::speedtest::SpeedtestResult;
use crate::state::AppState;
use tauri::State;

#[tauri::command]
pub fn list_speedtest_results(state: State<AppState>) -> Result<Vec<SpeedtestResult>, String> {
    state
        .speedtest_service
        .list_results()
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub async fn run_speedtest(
    provider_id: String,
    state: State<'_, AppState>,
) -> Result<SpeedtestResult, String> {
    state
        .speedtest_service
        .run(&provider_id)
        .await
        .map_err(|error| error.to_string())
}
