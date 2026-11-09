$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$env:QDRANT_URL = "http://127.0.0.1:6333"
$logDir = Join-Path $projectRoot ".local\logs"
$qdrantData = Join-Path $projectRoot ".local\qdrant"
New-Item -ItemType Directory -Force -Path $logDir, $qdrantData | Out-Null

function Wait-ForPort([int]$Port, [string]$Name) {
    $deadline = (Get-Date).AddSeconds(30)
    do {
        if (Test-NetConnection 127.0.0.1 -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue) {
            Write-Host "$Name is ready on port $Port"
            return
        }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    throw "$Name did not start on port $Port. Check .local\logs."
}

if (-not (Test-NetConnection 127.0.0.1 -Port 6333 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
    Start-Process -FilePath (Join-Path $projectRoot ".tools\qdrant\qdrant.exe") `
        -WorkingDirectory $qdrantData -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "qdrant.out.log") `
        -RedirectStandardError (Join-Path $logDir "qdrant.err.log")
    Wait-ForPort 6333 "Qdrant"
}

if (-not (Test-NetConnection 127.0.0.1 -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
    Start-Process -FilePath (Join-Path $projectRoot ".venv\Scripts\python.exe") `
        -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $projectRoot -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "api.out.log") `
        -RedirectStandardError (Join-Path $logDir "api.err.log")
    Wait-ForPort 8000 "RAG API"
}

if (-not (Test-NetConnection 127.0.0.1 -Port 8288 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
    Start-Process -FilePath (Join-Path $projectRoot ".tools\inngest\node_modules\inngest-cli\bin\inngest.exe") `
        -ArgumentList @("dev", "-u", "http://127.0.0.1:8000/api/inngest") `
        -WorkingDirectory $projectRoot -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "inngest.out.log") `
        -RedirectStandardError (Join-Path $logDir "inngest.err.log")
    Wait-ForPort 8288 "Inngest dev server"
}

if (-not (Test-NetConnection 127.0.0.1 -Port 8501 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
    Start-Process -FilePath (Join-Path $projectRoot ".venv\Scripts\python.exe") `
        -ArgumentList @("-m", "streamlit", "run", "streamlit_app.py", "--server.address", "127.0.0.1") `
        -WorkingDirectory $projectRoot -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "streamlit.out.log") `
        -RedirectStandardError (Join-Path $logDir "streamlit.err.log")
    Wait-ForPort 8501 "Streamlit UI"
}

Write-Host "RAG app is running: http://127.0.0.1:8501"
Write-Host "Inngest dashboard: http://127.0.0.1:8288"
