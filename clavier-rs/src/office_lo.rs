//! Pilotage de la correction automatique de LibreOffice.
//!
//! On délègue au bridge Python de LibreOffice (UNO) via une commande `soffice`
//! / `python` qui ajuste le nœud `org.openoffice.Office.Writer` /
//! `IsAutoSpellCheck`. Démarche identique à la version Python de l'outil,
//! mais pilotée depuis le binaire Rust.
//!
//! `active=true` -> on DÉSACTIVE la correction (mode « propre »).
//! `active=false` -> on RÉACTIVE la correction.

#[cfg(windows)]
use std::process::Command;

#[cfg(windows)]
fn find_soffice() -> Option<std::path::PathBuf> {
    use std::path::PathBuf;
    if let Ok(pf) = std::env::var("PROGRAMFILES") {
        let p = PathBuf::from(pf).join("LibreOffice").join("program").join("soffice.exe");
        if p.exists() {
            return Some(p);
        }
    }
    if let Ok(pf) = std::env::var("PROGRAMFILES(X86)") {
        let p = PathBuf::from(pf).join("LibreOffice").join("program").join("soffice.exe");
        if p.exists() {
            return Some(p);
        }
    }
    None
}

#[cfg(windows)]
fn bootstrap_listener(soffice: &std::path::Path) {
    let _ = Command::new(soffice)
        .args([
            "--headless",
            "--norestore",
            "--nologo",
            "--accept=socket,host=localhost,port=2002;urp;",
        ])
        .spawn();
    std::thread::sleep(std::time::Duration::from_secs(3));
}

#[cfg(windows)]
fn uno_python_script(active: bool) -> String {
    let value = if active { "False" } else { "True" };
    format!(
        r#"
import uno
from com.sun.star.beans import PropertyValue
ctx = uno.getComponentContext()
resolver = ctx.ServiceManager.createInstanceWithContext(
    "com.sun.star.bridge.UnoUrlResolver", ctx)
remote = resolver.resolve(
    "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
smgr = remote.ServiceManager
provider = smgr.createInstanceWithContext(
    "com.sun.star.configuration.ConfigurationProvider", remote)
node = PropertyValue(); node.Name = "nodepath"; node.Value = "org.openoffice.Office.Writer"
async_ = PropertyValue(); async_.Name = "EnableAsync"; async_.Value = False
access = provider.createInstanceWithArguments(
    "com.sun.star.configuration.ConfigurationUpdateAccess", (node, async_))
access.setPropertyValue("IsAutoSpellCheck", {value})
access.commitChanges()
"#
    )
}

#[cfg(windows)]
pub fn apply_libreoffice_protection(active: bool) {
    let soffice = match find_soffice() {
        Some(p) => p,
        None => {
            eprintln!("LibreOffice non trouvé : correction LO non modifiée.");
            return;
        }
    };

    // Tente d'abord d'utiliser le Python embarqué de LibreOffice.
    let py = soffice
        .parent()
        .map(|d| d.join("python.exe"))
        .filter(|p| p.exists());

    let script = uno_python_script(active);

    if let Some(py) = py {
        let _ = Command::new(&py)
            .arg("-c")
            .arg(&script)
            .status();
        return;
    }

    // Sinon on démarre une instance en écoute et on réessaie via `soffice`
    // lui-même (qui embarque uno).
    bootstrap_listener(&soffice);
    let _ = Command::new(&soffice)
        .args(["--headless", "--norestore", "--nologo", "--"])
        .status();
    // Le bridge UNO depuis un Python externe n'est pas garanti ; on signale.
    eprintln!(
        "Pilotage UNO LibreOffice : python embarqué LO non trouvé, \
         ajustez IsAutoSpellCheck manuellement si nécessaire."
    );
}

#[cfg(not(windows))]
pub fn apply_libreoffice_protection(_active: bool) {}
