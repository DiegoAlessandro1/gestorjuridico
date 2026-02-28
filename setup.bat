@echo off
REM ============================================================================
REM SCRIPT DE INICIALIZAÇÃO RÁPIDA (Windows)
REM ============================================================================
REM Arquivo: setup.bat
REM Propósito: Automatizar instalação inicial do projeto no Windows
REM
REM Uso: Duplo clique ou execute: setup.bat
REM ============================================================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     GESTOR JURÍDICO MVP - SETUP INICIAL (Windows)          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo Baixe em: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python encontrado:
python --version
echo.

REM Criar ambiente virtual
echo 📦 Criando ambiente virtual...
python -m venv venv

REM Ativar ambiente virtual
echo 🔌 Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instalar dependências
echo 📥 Instalando dependências...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
set /p CONFIGURAR_DB=🗄️ Deseja configurar agora o acesso ao banco MongoDB? (S/N): 
if /I "%CONFIGURAR_DB%"=="S" (
    if exist "setup_config_db.bat" (
        call setup_config_db.bat
    ) else (
        echo ⚠️ setup_config_db.bat não encontrado. Configure o .env manualmente.
    )
)

echo.
echo ✅ Setup completo!
echo.
echo Próximos passos:
echo 1. Se ainda nao configurou, execute: setup_config_db.bat
echo 2. Execute: venv\Scripts\activate.bat
echo 3. Execute: python run.py
echo.
echo Aplicação estará em: http://localhost:5000
echo.
pause
