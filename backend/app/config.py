# ============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================================================
# Arquivo: config.py
# Propósito: Centralizar todas as configurações da aplicação
#           Conectar ao MongoDB Atlas via variáveis de ambiente
#           Separar ambientes (desenvolvimento vs produção)
#
# Uso: from app.config import Config, mongo
# ============================================================================

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import timedelta

# Carrega as variáveis do arquivo .env (necessário para local)
load_dotenv()

# ============================================================================
# CLASSE DE CONFIGURAÇÃO - Centraliza todas as settings
# ============================================================================

class Config:
    """
    Classe de configuração principal da aplicação Flask.
    Todos os settings da aplicação estão aqui para fácil manutenção.
    """
    
    # ========== CONFIGURAÇÕES FLASK ==========
    # Chave secreta para criptografar sessões e cookies
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave_padrao_desenvolvimento')
    
    # Ambiente (development ou production)
    ENV = os.getenv('FLASK_ENV', 'development')
    
    # Modo debug (True = reinicia o servidor a cada mudança)
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    # ========== CONFIGURAÇÕES DE SESSÃO ==========
    # Duração da sessão do usuário
    SESSION_LIFETIME_MINUTES = int(os.getenv('SESSION_LIFETIME_MINUTES', '30'))
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSION_LIFETIME_MINUTES)

    _secure_default = 'True' if ENV == 'production' else 'False'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', _secure_default) == 'True'
    SESSION_COOKIE_HTTPONLY = True  # Protege contra XSS
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')  # Proteção contra CSRF
    
    # ========== CONFIGURAÇÕES MONGODB ==========
    # URI de conexão com MongoDB Atlas (obtida do .env)
    MONGODB_URI = os.getenv(
        'MONGODB_URI',
        'mongodb+srv://user:password@cluster0.mongodb.net/gestor_juridico?retryWrites=true&w=majority'
    )
    
    # Nome do banco de dados
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'gestor_juridico')


# ============================================================================
# CONEXÃO COM MONGODB - Inicialização
# ============================================================================

try:
    """
    IMPORTANTE: Conexão com MongoDB Atlas
    
    Como obter a URI:
    1. Acesse https://www.mongodb.com/cloud/atlas
    2. Crie uma conta (gratuita)
    3. Crie um cluster M0 (gratuito)
    4. Vá em "Connect" > "Connect your application"
    5. Selecione "Python 3.6 or later"
    6. Copie a connection string e adicione ao .env
    
    A conexão usa pooling automático para melhor performance.
    timeout=30 = espera 30 segundos antes de falhar
    """
    
    client = MongoClient(
        Config.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        retryWrites=True
    )

    # Importante para ambiente serverless:
    # não realizar ping aqui para evitar timeout/bloqueio no cold start.
    print("[OK] Cliente MongoDB configurado")
    
except Exception as e:
    print(f"[ERRO] Falha ao conectar ao MongoDB: {e}")
    print("[AVISO] Verifique variaveis de ambiente e URI de conexao")
    client = None


# ============================================================================
# OBTENÇÃO DO BANCO DE DADOS
# ============================================================================

def get_db():
    """
    Função para obter a referência do banco de dados MongoDB.
    
    Uso:
        from app.config import get_db
        db = get_db()
        clientes = db['clientes'].find()
    
    Retorna: Objeto do banco de dados do MongoDB
    """
    if client:
        return client[Config.MONGODB_DB_NAME]
    else:
        raise ConnectionError("MongoDB não conectado. Verifique o arquivo .env")


# ============================================================================
# INICIALIZAÇÃO DE COLEÇÕES (Collections)
# ============================================================================

def init_db():
    """
    Inicializa as coleções e índices do MongoDB.
    Chamada uma única vez ao iniciar a aplicação.
    
    Collections criadas:
    - clientes: Armazena dados dos clientes jurídicos
    - processos: Armazena processos jurídicos
    - usuarios: Armazena usuários do sistema (futuro)
    """
    db = get_db()
    
    # Cria coleção de clientes se não existir
    if 'clientes' not in db.list_collection_names():
        db.create_collection('clientes')
        db['clientes'].create_index('email', unique=True)  # Email único
        print("[OK] Colecao 'clientes' criada")
    
    # Cria coleção de processos se não existir
    if 'processos' not in db.list_collection_names():
        db.create_collection('processos')
        db['processos'].create_index('numero_processo', unique=True)
        print("[OK] Colecao 'processos' criada")

    # Cria coleção de agenda se não existir
    if 'agenda' not in db.list_collection_names():
        db.create_collection('agenda')
        print("[OK] Colecao 'agenda' criada")

    # Cria coleção de advogados se não existir
    if 'advogados' not in db.list_collection_names():
        db.create_collection('advogados')
        print("[OK] Colecao 'advogados' criada")

    # Índice único de OAB apenas para documentos com OAB preenchida
    # (evita conflito para Secretaria/Estagiário sem OAB)
    try:
        info_indices_adv = db['advogados'].index_information()
        if 'oab_1' in info_indices_adv:
            db['advogados'].drop_index('oab_1')
        db['advogados'].create_index(
            'oab',
            unique=True,
            name='oab_unique_non_empty',
            partialFilterExpression={
                'oab': {
                    '$exists': True,
                    '$type': 'string',
                    '$gt': ''
                }
            }
        )
    except Exception as e:
        print(f"[AVISO] Nao foi possivel ajustar indice de OAB: {e}")
    
    # Cria índices para melhorar performance em buscas frequentes
    db['clientes'].create_index('nome')  # Busca por nome
    db['processos'].create_index('cliente_id')  # Busca por cliente
    db['processos'].create_index('status')  # Filtro por status
    db['agenda'].create_index('data')  # Busca por data
    db['agenda'].create_index('cliente_id')  # Busca por cliente
    db['advogados'].create_index('nome')  # Busca por nome
    
    print("[OK] Banco de dados inicializado com sucesso")
