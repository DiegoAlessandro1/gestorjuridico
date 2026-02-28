#!/bin/bash
# ============================================================================
# SCRIPT DE INICIALIZAÇÃO RÁPIDA
# ============================================================================
# Arquivo: setup.sh (macOS/Linux) ou setup.bat (Windows)
# Propósito: Automatizar instalação inicial do projeto
#
# Uso: bash setup.sh (macOS/Linux) ou setup.bat (Windows)
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     GESTOR JURÍDICO MVP - SETUP INICIAL                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale em: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python encontrado:"
python3 --version
echo ""

# Criar ambiente virtual
echo "📦 Criando ambiente virtual..."
python3 -m venv venv

# Ativar ambiente virtual
echo "🔌 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📥 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup completo!"
echo ""
echo "Próximos passos:"
echo "1. Configure o arquivo .env com sua URI do MongoDB"
echo "2. Execute: source venv/bin/activate"
echo "3. Execute: python run.py"
echo ""
echo "Aplicação estará em: http://localhost:5000"
