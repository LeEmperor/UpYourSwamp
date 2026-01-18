# Voice Command Demo - Microphone Mode
# Run this script to start listening for voice commands via microphone

Write-Host "Starting Voice Command Demo (Microphone Mode)..." -ForegroundColor Green
Write-Host "Say 'AI [command]' to trigger commands" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Change to script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Run the Python script
python src/main.py --source mic --wake "ai" --model base --log-level INFO