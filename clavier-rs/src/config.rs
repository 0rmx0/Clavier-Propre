use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Serialize, Deserialize, Clone)]
pub struct AppConfig {
    pub protection_active: bool,
    pub manage_word: bool,
    pub manage_libreoffice: bool,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            protection_active: true,
            manage_word: true,
            manage_libreoffice: true,
        }
    }
}

impl AppConfig {
    pub fn path() -> PathBuf {
        let base = std::env::var("LOCALAPPDATA")
            .map(PathBuf::from)
            .unwrap_or_else(|_| {
                dirs_fallback().unwrap_or_else(|| PathBuf::from("."))
            });
        base.join("Clavier-Propre").join("config.json")
    }

    pub fn load() -> Self {
        let p = Self::path();
        match fs::read_to_string(&p) {
            Ok(s) => serde_json::from_str(&s).unwrap_or_default(),
            Err(_) => Self::default(),
        }
    }

    pub fn save(&self) {
        let p = Self::path();
        if let Some(parent) = p.parent() {
            let _ = fs::create_dir_all(parent);
        }
        if let Ok(s) = serde_json::to_string_pretty(self) {
            let _ = fs::write(p, s);
        }
    }
}

#[cfg(not(windows))]
fn dirs_fallback() -> Option<PathBuf> {
    std::env::var("HOME").ok().map(PathBuf::from)
}

#[cfg(windows)]
fn dirs_fallback() -> Option<PathBuf> {
    std::env::var("USERPROFILE").ok().map(PathBuf::from)
}
