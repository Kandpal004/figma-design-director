@echo off
REM Auto-commit + push if there are changes. Run this laptop every ~3 min via Task Scheduler.
cd /d "D:\Projects\AI Agent\figma-design-director"
git add -A
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "auto-sync %date% %time%" >nul 2>&1
  git push >nul 2>&1
)
