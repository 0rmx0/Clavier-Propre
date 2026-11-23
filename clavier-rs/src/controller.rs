//! Contrôleur central : orchestre la bascule entre les trois cibles.

use crate::config::AppConfig;
use crate::keyboard;
use crate::office_lo;
use crate::office_ms;
use std::sync::Mutex;

pub struct ProtectionController {
    pub config: Mutex<AppConfig>,
}

impl ProtectionController {
    pub fn new() -> Self {
        Self {
            config: Mutex::new(AppConfig::load()),
        }
    }

    /// Applique l'état de protection global.
    /// `active=true` -> suggestions et corrections DÉSACTIVÉES.
    pub fn apply(&self, active: bool) {
        {
            let mut cfg = self.config.lock().unwrap();
            cfg.protection_active = active;
            cfg.save();
        }
        // Clavier physique : on désactive les suggestions quand la protection
        // est active.
        keyboard::set_suggestions(!active);

        let cfg = self.config.lock().unwrap();
        if cfg.manage_word {
            office_ms::apply_office_protection(active);
        }
        if cfg.manage_libreoffice {
            office_lo::apply_libreoffice_protection(active);
        }
    }

    pub fn set_word_managed(&self, managed: bool) {
        let active = {
            let mut cfg = self.config.lock().unwrap();
            cfg.manage_word = managed;
            cfg.save();
            cfg.protection_active
        };
        if active {
            office_ms::apply_office_protection(managed);
        }
    }

    pub fn set_libreoffice_managed(&self, managed: bool) {
        let active = {
            let mut cfg = self.config.lock().unwrap();
            cfg.manage_libreoffice = managed;
            cfg.save();
            cfg.protection_active
        };
        if active {
            office_lo::apply_libreoffice_protection(managed);
        }
    }

    pub fn protection_active(&self) -> bool {
        self.config.lock().unwrap().protection_active
    }

    pub fn config_has_teacher_password(&self) -> bool {
        self.config.lock().unwrap().has_teacher_password()
    }

    pub fn check_teacher_password(&self, password: &str) -> bool {
        self.config.lock().unwrap().check_teacher_password(password)
    }

    pub fn set_teacher_password(&self, password: &str) {
        let mut cfg = self.config.lock().unwrap();
        cfg.set_teacher_password(password);
        cfg.save();
    }

    /// Watchdog : si la protection doit être active mais que les suggestions
    /// ont été réactivées, on ré-applique.
    pub fn watchdog(&self) {
        let active = self.protection_active();
        if active && keyboard::suggestions_enabled() {
            eprintln!("Watchdog : réactivation détectée, re-protection.");
            self.apply(true);
        }
    }
}

impl Default for ProtectionController {
    fn default() -> Self {
        Self::new()
    }
}
