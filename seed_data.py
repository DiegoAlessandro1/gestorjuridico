# ============================================================================
# ARQUIVO DE TESTE - DADOS INICIAIS
# ============================================================================
# Arquivo: seed_data.py
# Propósito: Insere dados de teste no banco de dados para facilitar testes
#
# Uso: python seed_data.py
# ============================================================================

from app import create_app
from app.config import get_db
from datetime import datetime, timedelta
from bson import ObjectId

def seed_database():
    """
    Insere dados de teste no MongoDB para facilitar testes da aplicação
    
    Cria:
    - 3 clientes fictícios
    - 5 processos fictícios associados aos clientes
    """
    
    app = create_app()
    
    with app.app_context():
        db = get_db()
        
        # Limpar collections existentes (CUIDADO em produção!)
        print("🗑️  Limpando dados de teste anteriores...")
        db['clientes'].delete_many({})
        db['processos'].delete_many({})
        
        # ========== INSERIR CLIENTES DE TESTE ==========
        print("👥 Inserindo clientes de teste...")
        
        clientes = [
            {
                'nome': 'João Silva Santos',
                'email': 'joao.silva@example.com',
                'telefone': '(11) 98765-4321',
                'cpf_cnpj': '123.456.789-00',
                'endereco': 'Rua Principal, 100, Apto 42',
                'cidade': 'São Paulo',
                'uf': 'SP',
                'data_cadastro': datetime.utcnow(),
                'ativo': True
            },
            {
                'nome': 'Maria Oliveira Costa',
                'email': 'maria.oliveira@example.com',
                'telefone': '(11) 99876-5432',
                'cpf_cnpj': '987.654.321-00',
                'endereco': 'Avenida Brasil, 500',
                'cidade': 'Rio de Janeiro',
                'uf': 'RJ',
                'data_cadastro': datetime.utcnow() - timedelta(days=30),
                'ativo': True
            },
            {
                'nome': 'Tech Solutions LTDA',
                'email': 'contato@techsolutions.com',
                'telefone': '(21) 3333-4444',
                'cpf_cnpj': '12.345.678/0001-99',
                'endereco': 'Praia de Copacabana, 1000',
                'cidade': 'Rio de Janeiro',
                'uf': 'RJ',
                'data_cadastro': datetime.utcnow() - timedelta(days=60),
                'ativo': True
            }
        ]
        
        resultado_clientes = db['clientes'].insert_many(clientes)
        print(f"✅ {len(resultado_clientes.inserted_ids)} clientes inseridos")
        
        # Obtém IDs dos clientes para referenciar nos processos
        cliente_ids = resultado_clientes.inserted_ids
        
        # ========== INSERIR PROCESSOS DE TESTE ==========
        print("⚖️  Inserindo processos de teste...")
        
        processos = [
            {
                'numero_processo': '0000001-23.2024.8.26.0100',
                'cliente_id': cliente_ids[0],
                'cliente_nome': 'João Silva Santos',
                'tipo_acao': 'Cível',
                'tribunal': 'Tribunal de Justiça do Estado de São Paulo',
                'vara': '1ª Vara Cível',
                'juiz': 'Dra. Ana Paula Martins',
                'status': 'Aberto',
                'data_abertura': datetime.utcnow() - timedelta(days=120),
                'data_ultima_movimentacao': datetime.utcnow() - timedelta(days=10),
                'descricao': 'Ação de cobrança por inadimplência contratual'
            },
            {
                'numero_processo': '0000002-45.2024.8.26.0100',
                'cliente_id': cliente_ids[0],
                'cliente_nome': 'João Silva Santos',
                'tipo_acao': 'Trabalhista',
                'tribunal': 'Tribunal Regional do Trabalho da 15ª Região',
                'vara': '3ª Vara do Trabalho',
                'juiz': 'Dr. Carlos Alberto',
                'status': 'Suspenso',
                'data_abertura': datetime.utcnow() - timedelta(days=200),
                'data_ultima_movimentacao': datetime.utcnow() - timedelta(days=60),
                'descricao': 'Demanda por diferenças salariais'
            },
            {
                'numero_processo': '0000003-67.2024.8.26.0100',
                'cliente_id': cliente_ids[1],
                'cliente_nome': 'Maria Oliveira Costa',
                'tipo_acao': 'Penal',
                'tribunal': 'Tribunal de Justiça do Estado do Rio de Janeiro',
                'vara': '4ª Vara Criminal',
                'juiz': 'Dr. Felipe Gomes',
                'status': 'Aberto',
                'data_abertura': datetime.utcnow() - timedelta(days=85),
                'data_ultima_movimentacao': datetime.utcnow() - timedelta(days=5),
                'descricao': 'Investigação por fraude eletrônica'
            },
            {
                'numero_processo': '0000004-89.2024.8.26.0100',
                'cliente_id': cliente_ids[2],
                'cliente_nome': 'Tech Solutions LTDA',
                'tipo_acao': 'Cível',
                'tribunal': 'Tribunal de Justiça do Estado do Rio de Janeiro',
                'vara': '2ª Vara Comercial',
                'juiz': 'Dra. Patricia Silva',
                'status': 'Julgado',
                'data_abertura': datetime.utcnow() - timedelta(days=365),
                'data_ultima_movimentacao': datetime.utcnow() - timedelta(days=30),
                'descricao': 'Ação de dissolução de parceria comercial'
            },
            {
                'numero_processo': '0000005-01.2024.8.26.0100',
                'cliente_id': cliente_ids[1],
                'cliente_nome': 'Maria Oliveira Costa',
                'tipo_acao': 'Administrativo',
                'tribunal': 'Tribunal de Contas do Estado do Rio de Janeiro',
                'vara': 'Câmara I',
                'juiz': 'Dr. Roberto Costa',
                'status': 'Aberto',
                'data_abertura': datetime.utcnow() - timedelta(days=45),
                'data_ultima_movimentacao': datetime.utcnow(),
                'descricao': 'Contestação de decisão administrativa'
            }
        ]
        
        resultado_processos = db['processos'].insert_many(processos)
        print(f"✅ {len(resultado_processos.inserted_ids)} processos inseridos")
        
        # ========== RESUMO ==========
        print("\n✅ Dados de teste inseridos com sucesso!\n")
        print("Clientes adicionados:")
        for i, cliente in enumerate(clientes, 1):
            print(f"  {i}. {cliente['nome']} ({cliente['email']})")
        
        print("\nProcessos adicionados:")
        for i, processo in enumerate(processos, 1):
            print(f"  {i}. {processo['numero_processo']} - {processo['tipo_acao']} ({processo['status']})")
        
        print("\n💡 Dica: Acesse http://localhost:5000 para ver os dados carregados!")


if __name__ == '__main__':
    seed_database()
