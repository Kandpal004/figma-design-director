@echo off
REM Auto-pull. Run on the OTHER (office) laptop every 5 min via Task Scheduler.
REM Edit the path below to where the project lives on that laptop.
cd /d "D:\Projects\AI Agent\figma-design-director"
git pull --rebase --autostash >nul 2>&1
