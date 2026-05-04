use crate::models::provider::{CreateProviderInput, ProviderConfig};
use crate::state::AppState;
use tauri::State;

#[tauri::command]
pub fn list_providers(state: State<AppState>) -> Result<Vec<ProviderConfig>, String> {
    state.provider_service.list().map_err(|error| error.to_string())
}

#[tauri::command]
pub fn create_provider(
    input: CreateProviderInput,
    state: State<AppState>,
) -> Result<ProviderConfig, String> {
    state
        .provider_service
        .create(input)
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn duplicate_provider(
    provider_id: String,
    state: State<AppState>,
) -> Result<ProviderConfig, String> {
    state
        .provider_service
        .duplicate(&provider_id)
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn delete_provider(provider_id: String, state: State<AppState>) -> Result<(), String> {
    state
        .provider_service
        .delete(&provider_id)
        .map_err(|error| error.to_string())
}
