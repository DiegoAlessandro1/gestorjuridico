# ============================================================================
# ARQUIVO PRINCIPAL - EXECUTAR A APLICAÇÃO
# ============================================================================
# Arquivo: run.py
# Propósito: Ponto de entrada da aplicação
#           Executa o servidor Flask em modo desenvolvimento
#
# Uso:
#   Local:      python run.py
#   Produção:   gunicorn run:app
#
# IMPORTANTE: Em produção, não use Flask direto. Use Gunicorn!
# ============================================================================

import os
from app import create_app
from app.config import Config

# ========== CRIAR APLICAÇÃO ==========
# Chama a factory function para criar a app Flask
app = create_app()


# ========== EXECUTAR APLICAÇÃO ==========
if __name__ == '__main__':
    """
    Ponto de entrada da aplicação em modo desenvolvimento.
    
    Configurações:
    - debug=True: Recarrega servidor a cada mudança de código
    - host='0.0.0.0': Permite conexões de outras máquinas
    - port=5000: Porta padrão (pode ser alterada em .env)
    
    AVISO: Use apenas em desenvolvimento!
           Para produção, use Gunicorn ou outro servidor WSGI.
    """
    
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║           GESTOR JURÍDICO MVP - SERVIDOR INICIADO          ║
    ╠════════════════════════════════════════════════════════════╣
    ║ 🚀 Servidor rodando em: http://localhost:{PORT:<41}║
    ║ 🔧 Modo: {'DESENVOLVIMENTO' if DEBUG else 'PRODUÇÃO':<51}║
    ║ 📝 Versão: 1.0.0{' '*48}║
    ║ 📊 Banco: MongoDB Atlas{' '*42}║
    ╠════════════════════════════════════════════════════════════╣
    ║ ⚠️  AVISO: Abra o navegador e acesse o URL acima{' '*13}║
    ║ 🔐 Certifique-se de que o .env foi configurado{' '*12}║
    ║ 🛑 Pressione CTRL+C para parar o servidor{' '*19}║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Executa o servidor Flask
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=DEBUG
    )
