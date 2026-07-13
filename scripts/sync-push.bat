@echo off
REM Auto-commit + push if there are changes. Path-agnostic (works from any clone location).
cd /d "%~dp0.."
git add -A
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "auto-sync %date% %time%" >nul 2>&1
  git push >nul 2>&1
)
