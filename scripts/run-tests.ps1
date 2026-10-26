# Runs the backend test suite (SQLite, no PostgreSQL needed).
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $here "..\backend")
& ".\.venv\Scripts\python.exe" -m pytest
