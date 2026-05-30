# Build the memory-engine binary in release mode (Windows PowerShell)
Write-Host "Building memory-engine..." -ForegroundColor Cyan

cargo build --release

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Binary ready at:" -ForegroundColor Green
    Write-Host "   $PSScriptRoot\target\release\memory-engine.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "   .\target\release\memory-engine.exe --json C:\path\to\repo"
    Write-Host "   .\target\release\memory-engine.exe --json --verbose C:\path\to\repo"
    Write-Host "   .\target\release\memory-engine.exe --json --min-severity high C:\path\to\repo"
} else {
    Write-Host "Build failed." -ForegroundColor Red
    exit 1
}
