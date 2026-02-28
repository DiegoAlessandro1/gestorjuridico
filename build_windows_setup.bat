@echo off
setlocal EnableExtensions

REM ============================================================================
REM BUILD DO INSTALADOR WINDOWS (EXE + INNO SETUP)
REM ============================================================================
REM Arquivo: build_windows_setup.bat
REM Uso: execute dentro da pasta gestor_juridico
REM Resultado esperado: installer\output\GestorJuridicoSetup.exe
REM ============================================================================

cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║      GESTOR JURÍDICO - BUILD INSTALADOR WINDOWS            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado. Instale em https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo 📦 Criando ambiente virtual .venv...
    python -m venv .venv
)

echo 🔌 Ativando ambiente virtual...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Falha ao ativar .venv
    pause
    exit /b 1
)

echo 📥 Instalando dependências do projeto...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
if errorlevel 1 (
    echo ❌ Falha ao instalar dependências
    pause
    exit /b 1
)

echo 🧹 Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "GestorJuridico.spec" del /q "GestorJuridico.spec"

echo 🏗️ Gerando executável com PyInstaller...
pyinstaller --noconfirm --clean --onedir --name GestorJuridico --add-data "templates;templates" --add-data "static;static" --add-data "tessdata;tessdata" run.py
if errorlevel 1 (
    echo ❌ Falha ao gerar executável
    pause
    exit /b 1
)

if not exist "dist\GestorJuridico\GestorJuridico.exe" (
    echo ❌ Executável não encontrado em dist\GestorJuridico
    pause
    exit /b 1
)

echo 📄 Copiando configurador de banco para o pacote...
copy /Y "setup_config_db.bat" "dist\GestorJuridico\setup_config_db.bat" >nul

set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if not exist "%ISCC_PATH%" (
    echo ⚠️ Inno Setup nao encontrado.
    echo Instale: https://jrsoftware.org/isdl.php
    echo Depois compile manualmente o arquivo:
    echo    installer\windows\GestorJuridico.iss
    pause
    exit /b 0
)

if not exist "installer\windows\GestorJuridico.iss" (
    echo ❌ Arquivo installer\windows\GestorJuridico.iss não encontrado
    pause
    exit /b 1
)

echo 📦 Gerando instalador com Inno Setup...
"%ISCC_PATH%" "installer\windows\GestorJuridico.iss"
if errorlevel 1 (
    echo ❌ Falha ao gerar instalador
    pause
    exit /b 1
)

echo.
echo ✅ Instalador gerado com sucesso!
echo 📁 Saída: installer\output\GestorJuridicoSetup.exe
echo.
pause
