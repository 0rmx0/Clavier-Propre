# Clavier-Propre — version Rust + Slint

Réécriture en Rust de l'outil Clavier-Propre, avec interface graphique [Slint](https://slint.dev).
Mêmes fonctionnalités que la version Python, mais en un binaire autonome plus léger et sans runtime Python à déployer.

## Fonctionnalités

- **Clavier physique** : bascule `EnableHwkbTextPrediction` (et valeurs associées) dans `HKEY_CURRENT_USER\Software\Microsoft\Input\Settings` via `winreg`.
- **Microsoft Office** : pilotage COM Word (`CheckSpellingAsYouType`, `CheckGrammarAsYouType`, `AutoCorrect`) via PowerShell (COM natif).
- **LibreOffice** : pilotage UNO du nœud `org.openoffice.Office.Writer` (`IsAutoSpellCheck`) via le Python embarqué de LibreOffice.
- **Indicateur visuel au premier plan** : fenêtre Slint `always-on-top`, rouge = protection active / vert = inactive, déplaçable.
- **Bouton de bascule** + cases à cocher Word/LibreOffice.
- **Service** : mode `--service` (headless) installable comme service Windows via NSSM, avec watchdog de re-protection toutes les 30 s.
- **Watchdog** GUI : réapplique la protection si elle a été contournée.

## Compilation (cross-compile depuis Linux)

```bash
rustup target add x86_64-pc-windows-gnu
# un linker MinGW-w64 est requis : voir plus bas
cargo build --release --target x86_64-pc-windows-gnu
```

Sur Windows directement :

```powershell
cargo build --release
```

Le binaire est `target/x86_64-pc-windows-gnu/release/clavier-propre.exe` (ou `target/release/clavier-propre.exe` sur Windows).

## Utilisation

```cmd
:: Interface graphique (indicateur au premier plan + bouton)
clavier-propre.exe

:: Mode service (sans GUI)
clavier-propre.exe --service
```

## Installation comme service Windows

Via [NSSM](https://nssm.cc/) (administrateur requis) :

```cmd
service\install-nssm.bat
```

Arrêt / suppression :

```cmd
nssm stop ClavierPropre
nssm remove ClavierPropre confirm
```

## Configuration

`%LOCALAPPDATA%\Clavier-Propre\config.json` — état de la protection, préférences Word/LibreOffice.

## Cross-compilation Linux -> Windows

Slint nécessite un backend de rendu. Pour produire un binaire Windows depuis Linux
sans dépendances à l'exécution, le plus simple est de compiler sur Windows (VM ou CI).
Pour la cross-compilation, installez MinGW-w64 et le backend Slint approprié.
Le `Cargo.toml` déclare les dépendances Windows-spécifiques (`winreg`, `windows`) via `cfg(windows)`.

## Notes

- **LibreOffice via UNO** : le Python embarqué de LibreOffice (`program\python.exe`) est utilisé prioritairement. À défaut, démarrage d'une instance `soffice --headless --accept=socket,...` ; le bridge UNO depuis un Python externe n'est pas garanti.
- **Microsoft Office** : les options COM sont globales à l'application Word.
- Un `WM_SETTINGCHANGE` est diffusé pour accélérer la prise en compte du registre.
