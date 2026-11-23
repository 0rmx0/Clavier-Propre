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

/// État partagé pour le dialogue de mot de passe en attente.
enum PasswordAction {
    DisableProtection,
    DisableWord,
    DisableLibreoffice,
}

fn run_gui() {
    let controller = Arc::new(ProtectionController::new());

    // L'outil démarre TOUJOURS en non protégé.
    controller.apply(false);

    let app = App::new().unwrap();
    app.set_has_teacher_password(controller.config_has_teacher_password());
    refresh_ui(&app, false);

    // Bascule de la protection.
    let app_weak = app.as_weak();
    let controller_toggle = controller.clone();
    let pending_action: Arc<std::sync::Mutex<Option<PasswordAction>>> =
        Arc::new(std::sync::Mutex::new(None));
    let pa_clone = pending_action.clone();
    app.on_toggle_protection(move || {
        let app = app_weak.unwrap();
        let controller = controller_toggle.clone();
        // On veut désactiver la protection (elle est active) => mot de passe.
        if controller.protection_active()
            && controller.config_has_teacher_password()
        {
            // Ouvrir le dialogue de mot de passe.
            *pa_clone.lock().unwrap() = Some(PasswordAction::DisableProtection);
            app.set_password_prompt(
                "Saisissez le mot de passe professeur pour désactiver la protection".into(),
            );
            app.set_password_input("".into());
            app.set_show_password_dialog(true);
            return;
        }
        let new_active = !controller.protection_active();
        controller.apply(new_active);
        refresh_ui(&app, new_active);
    });

    // Cases à cocher Word / LibreOffice.
    let pending_word: Arc<std::sync::Mutex<Option<PasswordAction>>> =
        Arc::new(std::sync::Mutex::new(None));
    let pending_lo: Arc<std::sync::Mutex<Option<PasswordAction>>> =
        Arc::new(std::sync::Mutex::new(None));

    let app_weak = app.as_weak();
    let controller_word = controller.clone();
    let pw_word_clone = pending_word.clone();
    app.on_word_toggled(move |checked| {
        let app = app_weak.unwrap();
        if !checked
            && controller_word.config_has_teacher_password()
        {
            *pw_word_clone.lock().unwrap() = Some(PasswordAction::DisableWord);
            app.set_password_prompt(
                "Saisissez le mot de passe professeur pour désactiver Word".into(),
            );
            app.set_password_input("".into());
            app.set_show_password_dialog(true);
            return;
        }
        controller_word.set_word_managed(checked);
    });

    let app_weak = app.as_weak();
    let controller_lo = controller.clone();
    let pw_lo_clone = pending_lo.clone();
    app.on_libreoffice_toggled(move |checked| {
        let app = app_weak.unwrap();
        if !checked
            && controller_lo.config_has_teacher_password()
        {
            *pw_lo_clone.lock().unwrap() = Some(PasswordAction::DisableLibreoffice);
            app.set_password_prompt(
                "Saisissez le mot de passe professeur pour désactiver LibreOffice".into(),
            );
            app.set_password_input("".into());
            app.set_show_password_dialog(true);
            return;
        }
        controller_lo.set_libreoffice_managed(checked);
    });

    // Validation du dialogue de mot de passe.
    let app_weak = app.as_weak();
    let controller_pw = controller.clone();
    let pa = pending_action.clone();
    let pw_word = pending_word.clone();
    let pw_lo = pending_lo.clone();
    app.on_password_dialog_ok(move || {
        let app = app_weak.unwrap();
        let entered = app.get_password_input().to_string();
        if !controller_pw.check_teacher_password(&entered) {
            app.set_password_message("Mot de passe incorrect.".into());
            return;
        }
        app.set_show_password_dialog(false);
        app.set_password_input("".into());
        // Traiter l'action en attente.
        let mut action_guard = pa.lock().unwrap();
        if let Some(action) = action_guard.take() {
            match action {
                PasswordAction::DisableProtection => {
                    controller_pw.apply(false);
                    refresh_ui(&app, false);
                }
                PasswordAction::DisableWord => {
                    controller_pw.set_word_managed(false);
                }
                PasswordAction::DisableLibreoffice => {
                    controller_pw.set_libreoffice_managed(false);
                }
            }
        } else {
            drop(action_guard);
            let mut g = pw_word.lock().unwrap();
            if g.take().is_some() {
                controller_pw.set_word_managed(false);
            } else {
                drop(g);
                let mut g2 = pw_lo.lock().unwrap();
                if g2.take().is_some() {
                    controller_pw.set_libreoffice_managed(false);
                }
            }
        }
    });

    let app_weak = app.as_weak();
    app.on_password_dialog_cancel(move || {
        let app = app_weak.unwrap();
        app.set_show_password_dialog(false);
        app.set_password_input("".into());
        app.set_password_message("".into());
    });

    // Réglage du mot de passe professeur.
    let app_weak = app.as_weak();
    app.on_open_password_setup(move || {
        let app = app_weak.unwrap();
        app.set_password_cur_input("".into());
        app.set_password_new_input("".into());
        app.set_password_confirm_input("".into());
        app.set_password_message("".into());
        app.set_show_password_setup_dialog(true);
    });

    let app_weak = app.as_weak();
    let controller_setup_ok = controller.clone();
    app.on_password_setup_ok(move || {
        let app = app_weak.unwrap();
        let cur = app.get_password_cur_input().to_string();
        let new = app.get_password_new_input().to_string();
        let confirm = app.get_password_confirm_input().to_string();

        if controller_setup_ok.config_has_teacher_password()
            && !controller_setup_ok.check_teacher_password(&cur)
        {
            app.set_password_message("Mot de passe actuel incorrect.".into());
            return;
        }
        if new != confirm {
            app.set_password_message("Les mots de passe ne correspondent pas.".into());
            return;
        }
        controller_setup_ok.set_teacher_password(&new);
        app.set_show_password_setup_dialog(false);
        app.set_has_teacher_password(controller_setup_ok.config_has_teacher_password());
        app.set_password_message("".into());
    });

    let app_weak = app.as_weak();
    app.on_password_setup_cancel(move || {
        let app = app_weak.unwrap();
        app.set_show_password_setup_dialog(false);
        app.set_password_message("".into());
    });

    // Réduction en pastille.
    let app_weak = app.as_weak();
    app.on_reduce_requested(move || {
        let app = app_weak.unwrap();
        let _ = app.window().hide();
        show_pastille(&app);
    });

    // Watchdog : réapplique la protection si contournée.
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
    std::mem::forget(timer);

    app.run().unwrap();
}

fn show_pastille(app: &App) {
    // En Slint, on crée une petite fenêtre secondaire pour la pastille.
    // Pour rester simple et léger, on réaffiche la fenêtre principale en mode
    // réduit via les propriétés. Ici on délègue à un re-affichage.
    let _ = app.window().show();
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
