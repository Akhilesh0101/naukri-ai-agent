# Starts the Next.js dashboard on http://localhost:3000
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $here "..\frontend")
if (-not (Test-Path "node_modules")) { npm install }
npm run dev
