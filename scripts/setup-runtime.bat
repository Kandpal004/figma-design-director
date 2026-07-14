@echo off
REM ============================================================
REM  ONE-TIME runtime setup for a laptop (run once after clone/pull).
REM  Installs the Python deps the agent + render scripts need.
REM  Path-agnostic: works from any clone location.
REM ============================================================
cd /d "%~dp0.."

echo.
echo [1/3] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/3] Installing Python packages (claude-agent-sdk + playwright)...
python -m pip install "claude-agent-sdk>=0.1.0" "playwright>=1.44"

echo.
echo [3/3] Installing Playwright Chromium browser...
python -m playwright install chromium

echo.
echo ============================================================
echo  DONE. Two manual steps if not already done on this laptop:
echo    1) az login          (needed to deploy to Azure)
echo    2) claude            (Claude Code CLI must be signed in)
echo.
echo  Optional: copy .env.example to .env and add EXA/FIRECRAWL
echo  keys ONLY if you want live web competitor search. The agent
echo  runs fine without them (falls back to Playwright + Reference Engine).
echo.
echo  Test the agent:
echo    python agent\config.py
echo ============================================================
pause
