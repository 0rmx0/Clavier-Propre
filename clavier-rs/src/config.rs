use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Serialize, Deserialize, Clone)]
pub struct AppConfig {
    pub protection_active: bool,
    pub manage_word: bool,
    pub manage_libreoffice: bool,
    pub teacher_password_salt: String,
    pub teacher_password_hash: String,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            protection_active: false,
            manage_word: true,
            manage_libreoffice: true,
            teacher_password_salt: String::new(),
            teacher_password_hash: String::new(),
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

    pub fn has_teacher_password(&self) -> bool {
        !self.teacher_password_hash.is_empty() && !self.teacher_password_salt.is_empty()
    }

    pub fn set_teacher_password(&mut self, password: &str) {
        if password.is_empty() {
            self.teacher_password_salt.clear();
            self.teacher_password_hash.clear();
            return;
        }
        let salt = random_salt();
        let hash = hash_password(password, &salt);
        self.teacher_password_salt = salt;
        self.teacher_password_hash = hash;
    }

    pub fn check_teacher_password(&self, password: &str) -> bool {
        if !self.has_teacher_password() {
            return true;
        }
        let expected = hash_password(password, &self.teacher_password_salt);
        constant_time_eq(expected.as_bytes(), self.teacher_password_hash.as_bytes())
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

fn random_salt() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let seed = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0) as u64;
    let mut state = seed ^ 0x9E3779B97F4A7C15;
    let mut bytes = [0u8; 32];
    for b in bytes.iter_mut() {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        *b = (state & 0xFF) as u8;
    }
    hex_encode(&bytes)
}

fn hex_encode(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push_str(&format!("{:02x}", b));
    }
    s
}

fn hash_password(password: &str, salt: &str) -> String {
    use pbkdf2::pbkdf2_hmac;
    use sha2::Sha256;

    let mut derived = [0u8; 32];
    pbkdf2_hmac::<Sha256>(
        password.as_bytes(),
        salt.as_bytes(),
        200_000,
        &mut derived,
    );
    hex_encode(&derived)
}

fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut diff = 0u8;
    for (x, y) in a.iter().zip(b.iter()) {
        diff |= x ^ y;
    }
    diff == 0
}
