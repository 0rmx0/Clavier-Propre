//! Pilotage de la correction automatique de Microsoft Office.
//!
//! Sur Windows, on délègue à PowerShell (qui pilote nativement COM) plutôt
//! qu'embarquer les liaisons COM Word en Rust. L'effet est identique et le
//! binaire reste léger.
//!
//! `active=true` -> on DÉSACTIVE la correction (mode « propre »).
//! `active=false` -> on RÉACTIVE la correction.

#[cfg(windows)]
use std::process::Command;

#[cfg(windows)]
fn ps_script(active: bool) -> String {
    let value = if active { "$false" } else { "$true" };
    format!(
        r#"
$ErrorActionPreference = 'SilentlyContinue'
try {{
  $word = [System.Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application')
}} catch {{
  try {{ $word = New-Object -ComObject Word.Application }} catch {{ $word = $null }}
}}
if ($word -ne $null) {{
  $word.Options.CheckSpellingAsYouType = {value}
  $word.Options.CheckGrammarAsYouType = {value}
  try {{ $word.AutoCorrect.ReplaceText = {value} }} catch {{}}
  try {{ $word.Application.ScreenRefresh() }} catch {{}}
  if (-not $word.Visible) {{ $word.Quit() }}
}}
"#
    )
}

#[cfg(windows)]
pub fn apply_office_protection(active: bool) {
    let script = ps_script(active);
    let status = Command::new("powershell")
        .args([
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            &script,
        ])
        .status();
    match status {
        Ok(s) if s.success() => {}
        Ok(s) => eprintln!("PowerShell Office a retourné: {s}"),
        Err(e) => eprintln!("Lancement PowerShell Office impossible: {e}"),
    }
}

#[cfg(not(windows))]
pub fn apply_office_protection(_active: bool) {}
