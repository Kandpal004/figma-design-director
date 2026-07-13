@echo off
REM Auto-pull. Path-agnostic (works from any clone location). Run every 5 min on the other laptop.
cd /d "%~dp0.."
git pull --rebase --autostash >nul 2>&1
