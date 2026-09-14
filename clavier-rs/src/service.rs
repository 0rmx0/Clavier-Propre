//! Mode « service » (sans interface graphique).
//!
//! Lancé avec l'argument `--service`, l'application applique la protection au
//! démarrage puis s'exécute en boucle, en réappliquant périodiquement la
//! protection si elle a été désactivée par un tiers.
//!
//! Pour l'installer en tant que service Windows natif, on fournit un script
//! NSSM (voir `service/install-nssm.bat`). Rust ne peut pas facilement déclarer
//! un service natif sans dépendances C lourdes ; NSSM est la solution la plus
//! simple et la plus robuste pour un exécutable autonome.

use crate::controller::ProtectionController;
use std::sync::Arc;
use std::time::Duration;

pub fn run_headless() -> i32 {
    let controller = Arc::new(ProtectionController::new());
    controller.apply(true);
    println!("Service Clavier-Propre démarré (mode headless).");

    loop {
        std::thread::sleep(Duration::from_secs(30));
        controller.watchdog();
    }
}
