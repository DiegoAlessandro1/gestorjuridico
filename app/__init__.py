# ============================================================================
# APLICAÇÃO PRINCIPAL FLASK
# ============================================================================
# Arquivo: app/__init__.py
# Propósito: Inicializa a aplicação Flask
#           Registra blueprints (módulos de rotas)
#           Inicializa banco de dados
#
# Uso: from app import create_app
#      app = create_app()
# ============================================================================

from flask import Flask
from app.config import Config, init_db
import os
from app.scheduler import iniciar_scheduler


def create_app():
    """
    Factory function para criar e configurar a aplicação Flask.
    
    Processo:
    1. Cria instância do Flask
    2. Carrega configurações do arquivo config.py
    3. Inicializa banco de dados MongoDB
    4. Registra rotas (blueprints)
    5. Retorna aplicação pronta para usar
    
    Retorna:
        Flask: Aplicação Flask configurada
    """
    
    # ========== CRIAÇÃO DA APLICAÇÃO ==========
    # Cria instância do Flask usando this file's package
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # ========== CARREGAMENTO DE CONFIGURAÇÕES ==========
    # Carrega todas as configurações do arquivo config.py
    app.config.from_object(Config)
    
    # ========== CONFIGURAÇÃO DE SESSÃO ==========
    # Usa chave secreta e política de sessão definidas em Config
    app.secret_key = app.config.get('SECRET_KEY')

    @app.template_filter('brl_currency')
    def brl_currency(value):
        try:
            numero = float(value or 0)
        except Exception:
            numero = 0.0
        return f"R$ {numero:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # ========== INICIALIZAÇÃO DO BANCO DE DADOS ==========
    try:
        # Inicializa coleções e índices no MongoDB
        init_db()
        print("✅ Aplicação inicializada com sucesso!")
        
        # Inicia scheduler para tarefas agendadas
        iniciar_scheduler()
        
    except Exception as e:
        print(f"⚠️  Aviso ao inicializar: {e}")
    
    # ========== REGISTRO DE ROTAS ==========
    # Importa o blueprint de rotas
    from app.routes import main_bp
    
    # Registra todas as rotas (blueprints)
    app.register_blueprint(main_bp)
    
    # ========== CONFIGURAÇÕES DE CONTEXTO ==========
    # Torna as variáveis config disponíveis no template Jinja2
    @app.context_processor
    def inject_config():
        """
        Injeta variáveis globais no contexto de templates Jinja2.
        Útil para dados que precisam estar disponíveis em todos os templates.
        """
        from flask import session as sess
        return {
            'app_name': 'Gestor Jurídico MVP',
            'app_version': '1.0.0',
            'session': sess
        }
    
    return app
