@echo off
REM ============================================================
REM  Deploy the built site to the Azure preview (static website).
REM  Requires: az login  (Vasansi-Production subscription).
REM  Path-agnostic. Uploads the whole output site to the $web container.
REM ============================================================
cd /d "%~dp0.."
set SITE=output\andaaz-bvffgzb8fdewg8cq-z03-azurefd-net

echo Fetching storage key...
for /f "delims=" %%K in ('az storage account keys list -n andaazpdpfigma -g rg-andaaz-demo --query "[0].value" -o tsv') do set KEY=%%K
if "%KEY%"=="" (
  echo ERROR: could not get storage key. Run "az login" first.
  pause & exit /b 1
)

echo Deploying %SITE% to Azure...
az storage blob upload-batch --account-name andaazpdpfigma --account-key "%KEY%" -d "$web" -s "%SITE%" --overwrite --only-show-errors

echo.
echo DONE. Live:
echo   https://andaazpdpfigma.z29.web.core.windows.net/sections/index.html
echo   https://andaazpdpfigma.z29.web.core.windows.net/sections/auto-product.html
pause
