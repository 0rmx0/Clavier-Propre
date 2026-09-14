@echo off
REM Build de Clavier-Propre en .exe autonome avec PyInstaller.
REM À lancer dans le venv sur une machine Windows.
REM
REM Pré-requis :
REM   python -m venv .venv
REM   .venv\Scripts\activate
REM   pip install -r requirements.txt
REM
REM Puis :
REM   build.bat
REM
REM Le résultat est dist\Clavier-Propre.exe

setlocal

echo === Build Clavier-Propre (PyInstaller) ===

REM On s'assure d'être à la racine du projet.
cd /d "%~dp0"

REM Active le venv si présent.
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

REM Installe les dépendances (idempotent).
pip install -q -r requirements.txt

REM Nettoyage précédents builds.
if exist "build" rmdir /s /q "build"
if exist "dist\Clavier-Propre" rmdir /s /q "dist\Clavier-Propre"

REM Lancement de PyInstaller via le .spec.
pyinstaller --noconfirm --clean Clavier-Propre.spec

if errorlevel 1 (
    echo.
    echo *** Build échoué.
    exit /b 1
)

echo.
echo === Build terminé ===
echo Exécutable : dist\Clavier-Propre.exe
echo.
echo Pour le mode service : dist\Clavier-Propre.exe --service
endlocal
