# ============================================================================
# MODELOS DE DADOS - CLIENTE
# ============================================================================
# Arquivo: app/models.py
# Propósito: Define a estrutura de dados (schema) para Clientes e Processos
#           Inclui validações básicas e conversão de ObjectId para String
#
# Obs: MongoDB é schemaless (sem schema rígido), mas definimos aqui
#      para manter consistência e facilitar a compreensão
# ============================================================================

from datetime import datetime
from bson import ObjectId
import re


class Cliente:
    """
    Modelo de Cliente Jurídico
    
    Atributos:
    - nome: Nome completo do cliente (obrigatório)
    - email: Email único para contato
    - telefone: Telefone para contato
    - cpf_cnpj: CPF (pessoa física) ou CNPJ (pessoa jurídica)
    - endereco: Endereço completo
    - cidade: Cidade do cliente
    - uf: Estado (sigla)
    - data_cadastro: Data de criação do registro
    - ativo: Se o cliente está ativo ou inativo
    """
    
    @staticmethod
    def validar(dados):
        """
        Valida os dados obrigatórios de um cliente.
        
        Argumentos:
            dados (dict): Dicionário com dados do cliente
            
        Retorna:
            tuple: (é_válido, mensagem_erro)
        """
        erros = []
        
        if not dados.get('nome') or len(dados['nome'].strip()) < 3:
            erros.append('Nome deve ter pelo menos 3 caracteres')
        
        if not dados.get('email') or '@' not in dados['email']:
            erros.append('Email inválido')
        
        cpf_cnpj = dados.get('cpf_cnpj')
        if not cpf_cnpj:
            erros.append('CPF/CNPJ é obrigatório')
        else:
            # Remove caracteres não numéricos
            somente_digitos = re.sub(r"\D", "", cpf_cnpj)
            # Se aparenta ser CPF (11 dígitos), valida usando algoritmo
            if len(somente_digitos) == 11:
                if not Cliente.validar_cpf(somente_digitos):
                    erros.append('CPF inválido')
            # Se for CNPJ (14 dígitos), valida com algoritmo de CNPJ
            elif len(somente_digitos) == 14:
                if not Cliente.validar_cnpj(somente_digitos):
                    erros.append('CNPJ inválido')
            else:
                erros.append('CPF/CNPJ inválido')
        
        # Validações específicas para Pessoa Física
        tipo = dados.get('tipo', 'PF')
        if tipo == 'PF':
            if not dados.get('endereco') or len(dados.get('endereco').strip()) < 5:
                erros.append('Endereço residencial é obrigatório')
            # Se casado, exige cônjuge e regime
            if dados.get('estado_civil') == 'Casado':
                if not dados.get('conjuge_nome'):
                    erros.append('Nome do cônjuge obrigatório para casados')
                if not dados.get('regime_bens'):
                    erros.append('Regime de bens obrigatório para casados')

        return (len(erros) == 0, erros)

    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """
        Valida um CPF brasileiro.

        - Remove quaisquer caracteres não numéricos antes de chamar.
        - Implementa o algoritmo oficial de dígitos verificadores.
        """
        if not cpf or len(cpf) != 11:
            return False

        # Rejeita CPFs com todos os dígitos iguais (ex: 11111111111)
        if cpf == cpf[0] * 11:
            return False

        try:
            nums = [int(ch) for ch in cpf]
        except ValueError:
            return False

        # Primeiro dígito verificador
        s = sum((10 - i) * nums[i] for i in range(9))
        r = (s * 10) % 11
        if r == 10:
            r = 0
        if r != nums[9]:
            return False

        # Segundo dígito verificador
        s = sum((11 - i) * nums[i] for i in range(10))
        r = (s * 10) % 11
        if r == 10:
            r = 0
        if r != nums[10]:
            return False

        return True
    
    @staticmethod
    def preparar_para_mongodb(dados):
        """
        Prepara dados do cliente para inserção no MongoDB.
        
        Adiciona:
        - data_cadastro: Timestamp do registro
        - ativo: Começa como True
        
        Argumentos:
            dados (dict): Dados brutos do cliente
            
        Retorna:
            dict: Dados formatados para MongoDB
        """
        return {
            'tipo': dados.get('tipo', 'PF'),
            'nome': dados.get('nome', '').strip(),
            'razao_social': dados.get('razao_social', '').strip(),
            'nome_fantasia': dados.get('nome_fantasia', '').strip(),
            'nacionalidade': dados.get('nacionalidade', ''),
            'estado_civil': dados.get('estado_civil', ''),
            'profissao': dados.get('profissao', ''),
            'rg': dados.get('rg', ''),
            'orgao_expedidor': dados.get('orgao_expedidor', ''),
            'conjuge_nome': dados.get('conjuge_nome', ''),
            'regime_bens': dados.get('regime_bens', ''),
            'email': dados.get('email', '').strip().lower(),
            'telefone': dados.get('telefone', ''),
            'cpf_cnpj': dados.get('cpf_cnpj', ''),
            'inscricao_estadual': dados.get('inscricao_estadual', ''),
            'inscricao_municipal': dados.get('inscricao_municipal', ''),
            'socio_nome': dados.get('socio_nome', ''),
            'socio_cpf': dados.get('socio_cpf', ''),
            'socio_rg': dados.get('socio_rg', ''),
            'cargo': dados.get('cargo', ''),
            'forma_pagamento': dados.get('forma_pagamento', ''),
            'referencia_pagamento': dados.get('referencia_pagamento', ''),
            'valor_honorarios': dados.get('valor_honorarios', None),
            'dia_vencimento': dados.get('dia_vencimento', None),
            'observacoes_pagamento': dados.get('observacoes_pagamento', ''),
            'numero_parcelas': dados.get('numero_parcelas', None),
            'parcelas_pagamento': dados.get('parcelas_pagamento', []),
            'pagamentos_contratos': dados.get('pagamentos_contratos', []),
            'endereco': dados.get('endereco', ''),
            'cidade': dados.get('cidade', ''),
            'uf': dados.get('uf', ''),
            'anotacoes': dados.get('anotacoes', ''),
            'data_cadastro': datetime.utcnow(),
            'ativo': True
        }

    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        """
        Valida um CNPJ brasileiro (apenas dígitos).
        Implementa o cálculo dos dígitos verificadores.
        """
        if not cnpj or len(cnpj) != 14:
            return False
        if cnpj == cnpj[0] * 14:
            return False
        try:
            nums = [int(ch) for ch in cnpj]
        except ValueError:
            return False

        def calc(digs):
            s = 0
            weight = len(digs) - 7
            for i, n in enumerate(digs):
                s += n * (weight - i)
                if (weight - i) - 1 < 2:
                    weight = 10
            r = s % 11
            return 0 if r < 2 else 11 - r

        n1 = calc([int(x) for x in cnpj[:12]])
        n2 = calc([int(x) for x in cnpj[:12]] + [n1])
        return n1 == nums[12] and n2 == nums[13]
    
    @staticmethod
    def converter_para_json(cliente):
        """
        IMPORTANTE: Converte ObjectId do MongoDB para String no JSON.
        
        MongoDB armazena _id como ObjectId (tipo BSON).
        JavaScript/Frontend não entende ObjectId nativamente.
        Essa função converte para String para transmissão JSON.
        
        Argumentos:
            cliente (dict): Documento do MongoDB com _id como ObjectId
            
        Retorna:
            dict: Cliente com _id como string para envio ao Frontend
        """
        if cliente and '_id' in cliente:
            cliente['_id'] = str(cliente['_id'])  # ObjectId -> String
        return cliente


class Processo:
    """
    Modelo de Processo Jurídico
    
    Atributos:
    - numero_processo: Identificação única do processo (ex: 0000001-23.2024.8.26.0100)
    - cliente_id: Referência ao cliente (ObjectId)
    - cliente_nome: Nome do cliente (cache para exibição)
    - tipo_acao: Tipo de ação (ex: Cível, Penal, Trabalhista)
    - tribunal: Tribunal responsável
    - vara: Vara do tribunal
    - juiz: Juiz responsável
    - status: Status do processo (Aberto, Suspenso, Arquivado, Julgado)
    - data_abertura: Data de abertura do processo
    - data_ultima_movimentacao: Última atualização
    - descricao: Descrição do caso
    """
    
    TIPOS_ACAO_VALIDOS = ['Cível', 'Penal', 'Trabalhista', 'Administrativo', 'Outro']
    STATUS_VALIDOS = ['Aberto', 'Suspenso', 'Arquivado', 'Julgado']
    
    @staticmethod
    def validar(dados):
        """
        Valida os dados obrigatórios de um processo.
        
        Argumentos:
            dados (dict): Dicionário com dados do processo
            
        Retorna:
            tuple: (é_válido, lista_de_erros)
        """
        erros = []
        
        if not dados.get('numero_processo') or len(dados['numero_processo'].strip()) < 5:
            erros.append('Número do processo inválido')
        
        if not dados.get('cliente_id'):
            erros.append('Cliente é obrigatório')
        
        if dados.get('tipo_acao') not in Processo.TIPOS_ACAO_VALIDOS:
            erros.append(f'Tipo de ação inválido. Opções: {", ".join(Processo.TIPOS_ACAO_VALIDOS)}')
        
        if dados.get('status') not in Processo.STATUS_VALIDOS:
            erros.append(f'Status inválido. Opções: {", ".join(Processo.STATUS_VALIDOS)}')
        
        return (len(erros) == 0, erros)
    
    @staticmethod
    def preparar_para_mongodb(dados):
        """
        Prepara dados do processo para inserção no MongoDB.
        
        Converte cliente_id de String para ObjectId (como armazenado no MongoDB).
        Adiciona timestamps de auditoria.
        
        Argumentos:
            dados (dict): Dados brutos do processo
            
        Retorna:
            dict: Dados formatados para MongoDB
        """
        # Converte String cliente_id para ObjectId (necessário para relacionamento)
        try:
            cliente_id = ObjectId(dados['cliente_id'])
        except:
            cliente_id = None
        
        anexos = dados.get('anexos', [])
        if not isinstance(anexos, list):
            anexos = []

        anexo_legado = dados.get('anexo', '')
        if not anexos and anexo_legado:
            anexos = [anexo_legado]

        primeiro_anexo = anexos[0] if anexos else ''

        return {
            'numero_processo': dados.get('numero_processo', '').strip(),
            'cliente_id': cliente_id,
            'cliente_nome': dados.get('cliente_nome', ''),  # Cache para performance
            'tipo_acao': dados.get('tipo_acao', 'Cível'),
            'tribunal': dados.get('tribunal', ''),
            'vara': dados.get('vara', ''),
            'juiz': dados.get('juiz', ''),
            'status': dados.get('status', 'Aberto'),
            'anexo': primeiro_anexo,
            'anexos': anexos,
            'prazo_data': dados.get('prazo_data', ''),
            'data_abertura': datetime.utcnow(),
            'data_ultima_movimentacao': datetime.utcnow(),
            'descricao': dados.get('descricao', '')
        }
    
    @staticmethod
    def converter_para_json(processo):
        """
        Converte ObjectIds para Strings para transmissão JSON.
        
        Argumentos:
            processo (dict): Documento do processo
            
        Retorna:
            dict: Processo com IDs como strings
        """
        if processo:
            if '_id' in processo:
                processo['_id'] = str(processo['_id'])
            if 'cliente_id' in processo and isinstance(processo['cliente_id'], ObjectId):
                processo['cliente_id'] = str(processo['cliente_id'])

            anexos = processo.get('anexos')
            if not isinstance(anexos, list):
                anexos = []

            if not anexos and processo.get('anexo'):
                anexos = [processo.get('anexo')]

            processo['anexos'] = anexos
            processo['anexo'] = anexos[0] if anexos else ''

            # Formata datas para string legível
            if 'data_abertura' in processo and isinstance(processo['data_abertura'], datetime):
                processo['data_abertura'] = processo['data_abertura'].strftime('%d/%m/%Y')
            if 'data_ultima_movimentacao' in processo and isinstance(processo['data_ultima_movimentacao'], datetime):
                processo['data_ultima_movimentacao'] = processo['data_ultima_movimentacao'].strftime('%d/%m/%Y %H:%M')
        return processo
