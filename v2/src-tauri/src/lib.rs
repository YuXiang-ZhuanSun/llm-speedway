mod commands;
mod database;
mod models;
mod services;
mod state;

use database::Database;
use services::{ProviderService, SpeedtestService};
use state::AppState;
use tauri::Manager;

pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let database = Database::open(app.handle())?;
            app.manage(AppState {
                provider_service: ProviderService::new(database.clone()),
                speedtest_service: SpeedtestService::new(database),
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::providers::list_providers,
            commands::providers::create_provider,
            commands::providers::duplicate_provider,
            commands::providers::delete_provider,
            commands::speedtests::list_speedtest_results,
            commands::speedtests::run_speedtest,
        ])
        .run(tauri::generate_context!())
        .expect("error while running llm-speedway");
}
