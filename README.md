# Clavier-Propre

Outil Windows 11 (Python / PySide6) qui **désactive les suggestions de mots du
clavier physique**, ainsi que la **correction automatique de Microsoft Office
et de LibreOffice**, pendant les phases d'évaluation. Il fonctionne comme un
**service Windows** et affiche en permanence un **indicateur visuel au premier
plan** pour l'instituteur, avec un **bouton de bascule** pour réactiver la
fonctionnalité hors évaluation.

## Fonctionnalités

- **Clavier physique** : bascule la valeur `EnableHwkbTextPrediction` de la clé
  `HKEY_CURRENT_USER\Software\Microsoft\Input\Settings` (et valeurs associées :
  autocorrection, mise en évidence des fautes, suggestions multilingues).
- **Microsoft Office** : pilotage **COM** (`win32com`) de Word/Excel/PowerPoint —
  `Options.CheckSpellingAsYouType`, `Options.CheckGrammarAsYouType`,
  `AutoCorrect`.
- **LibreOffice** : pilotage **UNO** via le nœud de configuration
  `org.openoffice.Office.Writer` (`IsAutoSpellCheck`).
- **Indicateur visuel** : fenêtre PySide6 sans bordure, toujours au premier plan,
  déplaçable à la souris. Rouge = protection active, vert = inactive.
- **Bouton de bascule** : l'élève/instituteur peut activer ou désactiver la
  protection à la demande.
- **Service Windows** : exécution en arrière-plan (sans GUI) qui réapplique
  automatiquement la protection si elle a été contournée.
- **Watchdog** : surveillance périodique de l'état du registre.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Utilisation interactive (avec interface)

```bash
python -m clavier_propre
```

La fenêtre apparaît au premier plan. Bouton central pour basculer la
protection ; cases à cocher pour activer/désactiver la gestion de Word et
LibreOffice.

## Service Windows

Le service s'appuie sur `pywin32` (`win32serviceutil`). L'installation se fait
en **administrateur** :

```cmd
:: Installe et démarre le service
python -m clavier_propre.service_runner install
python -m clavier_propre.service_runner start

:: Arrêt / suppression
python -m clavier_propre.service_runner stop
python -m clavier_propre.service_runner remove
```

Le service exécute le mode `--service` qui applique la protection et la
réapplique toutes les 30 s si elle a été désactivée. Les journaux sont écrits
dans `%LOCALAPPDATA%\Clavier-Propre\clavier-propre.log`.

## Compilation en exécutable

```cmd
pyinstaller --noconfirm --onefile --windowed --name Clavier-Propre ^
  --hidden-import win32service ^
  --hidden-import win32serviceutil ^
  --hidden-import servicemanager ^
  clavier_propre\__main__.py
```

## Configuration

Fichier JSON : `%LOCALAPPDATA%\Clavier-Propre\config.json`. Conserve l'état de
la protection, les préférences Word/LibreOffice et les valeurs d'origine du
registre pour restauration fidèle.

## Limites

- **LibreOffice via UNO** : nécessite que LibreOffice soit démarré en mode
  écoute socket. L'outil tente de le lancer automatiquement (`--headless
  --accept=socket,host=localhost,port=2002;urp;`). Le module `uno` fourni avec
  LibreOffice doit être accessible à Python (typiquement le Python embarqué par
  LibreOffice, ou via `PYTHONPATH` pointant vers le dossier `program`).
- **Microsoft Office** : les options COM sont globales à l'application Word et
  persistent pour tous les documents.
- Le registre ne prend effet qu'après rechargement de la session pour certaines
  applications ; un `WM_SETTINGCHANGE` est diffusé pour accélérer la prise en
  compte.
