slint::include_modules!();

use std::sync::Arc;
use std::time::Duration;

use crate::controller::ProtectionController;

mod config;
mod controller;
mod keyboard;
mod office_lo;
mod office_ms;
mod service;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|a| a == "--service") {
        std::process::exit(service::run_headless());
    }

    run_gui();
}

fn run_gui() {
    let controller = Arc::new(ProtectionController::new());

    // Applique l'état initial.
    let initial_active = controller.protection_active();
    controller.apply(initial_active);

    let app = App::new().unwrap();
    refresh_ui(&app, initial_active);

    // Bascule de la protection : on capture un Weak<App> pour mettre à jour
    // l'interface depuis le callback.
    let app_weak = app.as_weak();
    let controller_toggle = controller.clone();
    app.on_toggle_protection(move || {
        let new_active = !controller_toggle.protection_active();
        controller_toggle.apply(new_active);
        if let Some(app) = app_weak.upgrade() {
            refresh_ui(&app, new_active);
        }
    });

    // Gestion des cases à cocher Word / LibreOffice.
    let controller_word = controller.clone();
    app.on_word_toggled(move |checked| {
        controller_word.set_word_managed(checked);
    });

    let controller_lo = controller.clone();
    app.on_libreoffice_toggled(move |checked| {
        controller_lo.set_libreoffice_managed(checked);
    });

    // Surveillance périodique : si les suggestions ont été réactivées par un
    // tiers (l'élève via les Paramètres), on ré-applique la protection.
    let controller_watch = controller.clone();
    let app_weak = app.as_weak();
    let timer = slint::Timer::default();
    timer.start(slint::TimerMode::Repeated, Duration::from_secs(15), move || {
        controller_watch.watchdog();
        if let Some(app) = app_weak.upgrade() {
            let active = controller_watch.protection_active();
            refresh_ui(&app, active);
        }
    });

    // L'argument `timer` doit rester vivant pendant l'exécution de la boucle.
    std::mem::forget(timer);

    app.run().unwrap();
}

fn refresh_ui(app: &App, active: bool) {
    app.set_protection_active(active);
    if active {
        app.set_status_text("Protection ACTIVE".into());
        app.set_detail_text("Suggestions clavier désactivées".into());
    } else {
        app.set_status_text("Protection inactive".into());
        app.set_detail_text("Suggestions clavier autorisées".into());
    }
}
