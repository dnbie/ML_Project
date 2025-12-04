Write-Host "=== RAG Chatbot Setup and Launch ===" -ForegroundColor Cyan
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created successfully" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
}

Write-Host ""

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host "Virtual environment activated" -ForegroundColor Green
Write-Host ""

Write-Host "Installing dependencies from requirement.txt..." -ForegroundColor Yellow
pip install -r requirement.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "Dependencies installed successfully" -ForegroundColor Green
Write-Host ""

if (-Not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found. Please create it with your OPENAI_API_KEY" -ForegroundColor Yellow
    Write-Host "Example: OPENAI_API_KEY=your-api-key-here" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Starting RAG Chatbot application..." -ForegroundColor Cyan
Write-Host ""
streamlit run RAG_bot.py
