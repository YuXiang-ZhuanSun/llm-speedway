use rusqlite::Connection;
use std::fs;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Manager};

#[derive(Clone)]
pub struct Database {
    connection: Arc<Mutex<Connection>>,
}

impl Database {
    pub fn open(app: &AppHandle) -> Result<Self, Box<dyn std::error::Error>> {
        let data_dir = app
            .path()
            .app_data_dir()
            .unwrap_or_else(|_| fallback_data_dir());
        fs::create_dir_all(&data_dir)?;

        let db_path = data_dir.join("llm-speedway.db");
        let connection = Connection::open(db_path)?;
        let database = Self {
            connection: Arc::new(Mutex::new(connection)),
        };
        database.init()?;
        Ok(database)
    }

    pub fn with_connection<T>(
        &self,
        operation: impl FnOnce(&Connection) -> rusqlite::Result<T>,
    ) -> rusqlite::Result<T> {
        let connection = self
            .connection
            .lock()
            .map_err(|_| rusqlite::Error::ExecuteReturnedResults)?;
        operation(&connection)
    }

    fn init(&self) -> rusqlite::Result<()> {
        self.with_connection(|connection| {
            connection.execute_batch(
                "
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS providers (
                  id TEXT PRIMARY KEY,
                  provider_name TEXT NOT NULL,
                  display_name TEXT NOT NULL,
                  base_url TEXT NOT NULL,
                  endpoint TEXT NOT NULL,
                  api_key_cipher TEXT NOT NULL,
                  model TEXT NOT NULL,
                  enabled INTEGER NOT NULL DEFAULT 1,
                  sort_order INTEGER NOT NULL DEFAULT 0,
                  tags_json TEXT NOT NULL DEFAULT '[]',
                  note TEXT,
                  api_format TEXT NOT NULL DEFAULT 'openai',
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS speedtest_runs (
                  id TEXT PRIMARY KEY,
                  provider_id TEXT NOT NULL,
                  provider_name TEXT NOT NULL,
                  display_name TEXT NOT NULL,
                  model TEXT NOT NULL,
                  status TEXT NOT NULL,
                  started_at TEXT NOT NULL,
                  finished_at TEXT,
                  ttft_ms REAL,
                  decode_tps REAL,
                  multi_turn_decode_tps REAL,
                  total_latency_ms REAL,
                  success_rate REAL,
                  error_message TEXT,
                  summary_json TEXT NOT NULL DEFAULT '{}',
                  FOREIGN KEY(provider_id) REFERENCES providers(id)
                );
                ",
            )?;
            let has_api_format = {
                let mut statement = connection.prepare("PRAGMA table_info(providers)")?;
                let columns = statement.query_map([], |row| row.get::<_, String>(1))?;
                let found = columns.filter_map(Result::ok).any(|name| name == "api_format");
                found
            };
            if !has_api_format {
                connection.execute(
                    "ALTER TABLE providers ADD COLUMN api_format TEXT NOT NULL DEFAULT 'openai'",
                    [],
                )?;
            }
            Ok(())
        })
    }
}

fn fallback_data_dir() -> PathBuf {
    let home = std::env::var("HOME")
        .or_else(|_| std::env::var("USERPROFILE"))
        .unwrap_or_else(|_| ".".to_string());
    PathBuf::from(home).join(".llm-speedway")
}
