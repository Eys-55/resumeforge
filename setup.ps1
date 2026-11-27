# ResumeForge one-time setup (Windows PowerShell). Safe to re-run.
# Run with:  powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "ResumeForge setup"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    $local = Join-Path $env:USERPROFILE ".local\bin"
    if (Test-Path (Join-Path $local "uv.exe")) { $env:Path = "$local;$env:Path" }
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "  ! uv (the Python tool runner) is not installed." -ForegroundColor Yellow
    Write-Host '    Install it with:  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
    Write-Host "    Then open a new terminal and run setup.ps1 again."
    exit 1
}
Write-Host "  OK uv $(uv --version)" -ForegroundColor Green

uv sync --quiet
Write-Host "  OK Python environment ready" -ForegroundColor Green

uv run --quiet resumeforge db init | Out-Null
Write-Host "  OK Game database ready at data\resumes.db" -ForegroundColor Green

uv run --quiet python -c "from tools.render_pdf import _find_chrome_binary as f; f()" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK Browser found for PDF rendering" -ForegroundColor Green
} else {
    Write-Host "  ! No Chrome/Edge found. PDFs will be saved as HTML you can print to PDF." -ForegroundColor Yellow
}

New-Item -ItemType Directory -Force -Path my_resumes | Out-Null
Write-Host "  OK Your own resumes go in my_resumes\ (private)" -ForegroundColor Green
Write-Host ""
Write-Host "Done. Open this folder in Claude Code and type:  /make-my-resume"
