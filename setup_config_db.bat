@echo off
setlocal
REM ============================================================================
REM SETUP DE CONFIGURAÇÃO DO BANCO (Windows)
REM ============================================================================
REM Arquivo: setup_config_db.bat
REM Propósito: Criar/atualizar .env perguntando usuário e senha do MongoDB
REM Uso: Execute na pasta gestor_juridico
REM ============================================================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║    GESTOR JURÍDICO - CONFIGURAÇÃO DO BANCO (MongoDB)      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo Este configurador cria/atualiza o arquivo .env na pasta atual.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$ErrorActionPreference='Stop';" ^
"$envPath = Join-Path (Get-Location) '.env';" ^
"if (Test-Path $envPath) {" ^
"  $overwrite = Read-Host '.env ja existe. Deseja sobrescrever? (S/N)';" ^
"  if ($overwrite -notmatch '^[sS]$') { Write-Host 'Configuracao cancelada. .env mantido.'; exit 0 }" ^
"}" ^
"$hostMongo = Read-Host 'Host do cluster MongoDB [cluster0.mongodb.net]';" ^
"if ([string]::IsNullOrWhiteSpace($hostMongo)) { $hostMongo = 'cluster0.mongodb.net' }" ^
"$usuario = Read-Host 'Usuario MongoDB';" ^
"if ([string]::IsNullOrWhiteSpace($usuario)) { throw 'Usuario nao pode ficar vazio.' }" ^
"$senhaSegura = Read-Host 'Senha MongoDB' -AsSecureString;" ^
"$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($senhaSegura);" ^
"try { $senha = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }" ^
"if ([string]::IsNullOrWhiteSpace($senha)) { throw 'Senha nao pode ficar vazia.' }" ^
"$dbName = Read-Host 'Nome do banco [gestor_juridico]';" ^
"if ([string]::IsNullOrWhiteSpace($dbName)) { $dbName = 'gestor_juridico' }" ^
"$secret = [guid]::NewGuid().ToString('N');" ^
"$userEnc = [uri]::EscapeDataString($usuario);" ^
"$passEnc = [uri]::EscapeDataString($senha);" ^
"$mongoUri = 'mongodb+srv://' + $userEnc + ':' + $passEnc + '@' + $hostMongo + '/' + $dbName + '?retryWrites=true&w=majority';" ^
"$linhas = @(" ^
"  'MONGODB_URI=' + $mongoUri," ^
"  'MONGODB_DB_NAME=' + $dbName," ^
"  'SECRET_KEY=' + $secret," ^
"  'FLASK_ENV=development'," ^
"  'FLASK_DEBUG=True'," ^
"  'PORT=5000'" ^
");" ^
"Set-Content -Path $envPath -Value ($linhas -join [Environment]::NewLine) -Encoding UTF8;" ^
"Write-Host '';" ^
"Write-Host '✅ .env configurado com sucesso!';" ^
"Write-Host ('📁 Arquivo: ' + $envPath);" ^
"Write-Host ('🗄️ Banco: ' + $dbName);"

if errorlevel 1 (
    echo.
    echo ❌ Falha ao configurar o .env.
    pause
    exit /b 1
)

echo.
echo Próximo passo:
echo 1) Ativar ambiente virtual: venv\Scripts\activate.bat
echo 2) Executar aplicacao: python run.py
echo.
pause
