# Voice Command Demo - File Mode
# Run this script to process voice commands from an audio file

param(
    [Parameter(Mandatory=$true)]
    [string]$AudioFile
)

Write-Host "Starting Voice Command Demo (File Mode)..." -ForegroundColor Green
Write-Host "Processing file: $AudioFile" -ForegroundColor Cyan
Write-Host ""

# Check if file exists
if (-not (Test-Path $AudioFile)) {
    Write-Host "Error: Audio file not found: $AudioFile" -ForegroundColor Red
    exit 1
}

# Change to script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Run the Python script
python src/main.py --source file --file $AudioFile --wake "ai" --model base --log-level INFO