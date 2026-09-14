@echo off
REM Installation du service Windows Clavier-Propre via NSSM.
REM Nécessite nssm.exe dans le PATH et d'être lancé en administrateur.

set SERVICE_NAME=ClavierPropre
set EXE_PATH=%~dp0clavier-propre.exe

nssm install %SERVICE_NAME% %EXE_PATH%
nssm set %SERVICE_NAME% AppParameters --service
nssm set %SERVICE_NAME% AppDirectory %~dp0
nssm set %SERVICE_NAME% DisplayName "Clavier-Propre - Protection clavier"
nssm set %SERVICE_NAME% Description "Désactive les suggestions de mots du clavier physique et la correction automatique pendant les évaluations."
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

net start %SERVICE_NAME%

echo.
echo Service %SERVICE_NAME% installé et démarré.
echo Pour le retirer : nssm stop %SERVICE_NAME% ^& nssm remove %SERVICE_NAME% confirm
