Write-Host "Checking Python imports..." -ForegroundColor Cyan

$errors = @()

Get-ChildItem -Recurse -Path "backend/app" -Filter "*.py" | ForEach-Object {
    $file = $_.FullName
    $result = python -c "
import ast, sys
with open(r'$file', encoding='utf-8') as f:
    src = f.read()
try:
    ast.parse(src)
except SyntaxError as e:
    print(f'SYNTAX ERROR: $file: {e}')
    sys.exit(1)
" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $errors += $result
    }
}

if ($errors.Count -gt 0) {
    Write-Host "FAILED:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    exit 1
}

Write-Host "Checking cross-module imports..." -ForegroundColor Cyan
$result = docker run --rm -v "${PWD}/backend:/app" -w /app `
    python:3.12-slim `
    sh -c "pip install -q -r requirements.txt && python -c 'import app.main'" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "IMPORT CHECK FAILED:" -ForegroundColor Red
    Write-Host $result -ForegroundColor Red
    exit 1
}

Write-Host "All checks passed!" -ForegroundColor Green
Write-Host "Run: docker compose build; docker compose up -d" -ForegroundColor Cyan
