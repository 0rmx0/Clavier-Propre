//! Bascule des suggestions du clavier physique (Windows 11).
//!
//! La valeur DWORD `EnableHwkbTextPrediction` de la clé
//! `HKEY_CURRENT_USER\Software\Microsoft\Input\Settings` contrôle les
//! suggestions de mots sur le clavier physique :
//!   0 = suggestions désactivées (mode « propre »)
//!   1 = suggestions activées (comportement par défaut)

#[cfg(windows)]
use winreg::enums::HKEY_CURRENT_USER;
#[cfg(windows)]
use winreg::RegKey;

const INPUT_SETTINGS: &str = "Software\\Microsoft\\Input\\Settings";
const PREDICTION_VALUE: &str = "EnableHwkbTextPrediction";

/// Retourne `true` si les suggestions du clavier physique sont ACTIVÉES.
#[cfg(windows)]
pub fn suggestions_enabled() -> bool {
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    match hkcu.open_subkey(INPUT_SETTINGS) {
        Ok(key) => key
            .get_value::<u32, _>(PREDICTION_VALUE)
            .map(|v| v != 0)
            .unwrap_or(true),
        Err(_) => true,
    }
}

/// Active (`enabled=true`) ou désactive (`enabled=false`) les suggestions.
#[cfg(windows)]
pub fn set_suggestions(enabled: bool) {
    let hkcu = RegKey::predef(HKEY_CURRENT_USER);
    let key = match hkcu.create_subkey(INPUT_SETTINGS) {
        Ok((k, _)) => k,
        Err(_) => hkcu
            .open_subkey(INPUT_SETTINGS)
            .expect("ouverture clé Input\\Settings"),
    };
    let value: u32 = if enabled { 1 } else { 0 };
    for name in [
        "EnableHwkbTextPrediction",
        "IsAutocorrectionEnabled",
        "IsPredictionEnabled",
        "IsSpellcheckingEnabled",
        "IsHyphenationEnabled",
        "MultilingualEnabled",
        "EnableNextWordPrediction",
    ] {
        let _ = key.set_value(name, &value);
    }
    broadcast_setting_change();
}

#[cfg(not(windows))]
pub fn suggestions_enabled() -> bool {
    true
}

#[cfg(not(windows))]
pub fn set_suggestions(_enabled: bool) {}

/// Diffuse `WM_SETTINGCHANGE` pour accélérer la prise en compte du registre.
#[cfg(windows)]
fn broadcast_setting_change() {
    use windows::Win32::Foundation::LPARAM;
    use windows::Win32::UI::WindowsAndMessaging::{
        SendMessageTimeoutW, HWND_BROADCAST, SMTO_ABORTIFHUNG, WM_SETTINGCHANGE,
    };

    unsafe {
        let _ = SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            None,
            LPARAM(0),
            SMTO_ABORTIFHUNG,
            1000,
            None,
        );
    }
}

#[cfg(not(windows))]
fn broadcast_setting_change() {}
