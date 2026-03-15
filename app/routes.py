# ============================================================================
# ROTAS DA APLICAÇÃO - CRUD COMPLETO
# ============================================================================
# Arquivo: app/routes.py
# Propósito: Define todas as rotas HTTP (GET, POST, PUT, DELETE)
#           Implementa lógica CRUD para Clientes e Processos
#           Gerencia a comunicação entre Frontend e Banco de Dados
#
# IMPORTANTE: Todas as conversões ObjectId <-> String estão comentadas
# ============================================================================

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session, get_flashed_messages
from bson import ObjectId
from app.config import get_db
from app.models import Cliente, Processo
from datetime import datetime, timedelta
from functools import wraps
import os
import secrets
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import re
import html

# Cria um Blueprint (módulo de rotas)
main_bp = Blueprint('main', __name__)

SECRETARIA_ENDPOINTS_PERMITIDOS = {
    'main.listar_agenda',
    'main.lista_agenda_api',
    'main.adicionar_compromisso_agenda',
    'main.atualizar_compromisso_agenda',
    'main.deletar_compromisso_agenda',
    'main.perfil_usuario',
    'main.logout'
}

ESTAGIARIO_ENDPOINTS_PERMITIDOS = {
    'main.listar_agenda',
    'main.lista_agenda_api',
    'main.adicionar_compromisso_agenda',
    'main.atualizar_compromisso_agenda',
    'main.deletar_compromisso_agenda',
    'main.listar_clientes',
    'main.lista_clientes',
    'main.adicionar_cliente',
    'main.atualizar_cliente',
    'main.cliente_anotacoes',
    'main.deletar_cliente',
    'main.obter_processos_cliente',
    'main.obter_referencias_pagamento_cliente',
    'main.procurar_procuracao',
    'main.adicionar_procuracao',
    'main.upload_folha',
    'main.gerar_procuracao_automatica',
    'main.download_procuracao',
    'main.logout'
}

UNSAFE_HTTP_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW_MINUTES = 15
LOGIN_LOCK_MINUTES = 15
FAILED_LOGIN_ATTEMPTS = {}


def obter_ip_cliente():
    x_forwarded_for = (request.headers.get('X-Forwarded-For') or '').strip()
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return (request.remote_addr or 'desconhecido').strip()


def chave_login_attempt(usuario_norm):
    return f"{obter_ip_cliente()}|{(usuario_norm or '').strip().lower()}"


def limpar_login_attempts_expirados():
    agora = datetime.utcnow()
    janela = timedelta(minutes=LOGIN_ATTEMPT_WINDOW_MINUTES)
    remover = []

    for chave, estado in FAILED_LOGIN_ATTEMPTS.items():
        tentativas = [
            ts for ts in estado.get('attempts', [])
            if (agora - ts) <= janela
        ]
        lock_until = estado.get('lock_until')

        if lock_until and lock_until <= agora:
            lock_until = None

        if not tentativas and not lock_until:
            remover.append(chave)
        else:
            estado['attempts'] = tentativas
            estado['lock_until'] = lock_until

    for chave in remover:
        FAILED_LOGIN_ATTEMPTS.pop(chave, None)


def login_bloqueado(chave):
    limpar_login_attempts_expirados()
    estado = FAILED_LOGIN_ATTEMPTS.get(chave, {})
    lock_until = estado.get('lock_until')
    agora = datetime.utcnow()

    if lock_until and lock_until > agora:
        segundos_restantes = int((lock_until - agora).total_seconds())
        minutos_restantes = max(1, (segundos_restantes + 59) // 60)
        return True, minutos_restantes

    return False, 0


def registrar_falha_login(chave):
    limpar_login_attempts_expirados()
    agora = datetime.utcnow()
    janela = timedelta(minutes=LOGIN_ATTEMPT_WINDOW_MINUTES)

    estado = FAILED_LOGIN_ATTEMPTS.get(chave, {'attempts': [], 'lock_until': None})
    tentativas = [
        ts for ts in estado.get('attempts', [])
        if (agora - ts) <= janela
    ]
    tentativas.append(agora)
    estado['attempts'] = tentativas

    if len(tentativas) >= MAX_LOGIN_ATTEMPTS:
        estado['lock_until'] = agora + timedelta(minutes=LOGIN_LOCK_MINUTES)

    FAILED_LOGIN_ATTEMPTS[chave] = estado


def limpar_falha_login(chave):
    FAILED_LOGIN_ATTEMPTS.pop(chave, None)


def obter_csrf_token():
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['csrf_token'] = token
    return token


def validar_csrf_request():
    token_sessao = session.get('csrf_token')
    if not token_sessao:
        return False

    token_requisicao = (
        request.headers.get('X-CSRF-Token')
        or request.form.get('csrf_token')
    )

    if not token_requisicao:
        payload_json = request.get_json(silent=True) or {}
        token_requisicao = payload_json.get('csrf_token')

    if not token_requisicao:
        return False

    return secrets.compare_digest(token_sessao, token_requisicao)


def normalizar_tipo_usuario(tipo_usuario):
    tipo = (tipo_usuario or '').strip().lower()
    return (tipo
            .replace('á', 'a')
            .replace('ã', 'a')
            .replace('â', 'a')
            .replace('à', 'a'))


def endpoint_permitido_para_tipo(tipo_usuario, endpoint_atual):
    if tipo_usuario == 'secretaria':
        return endpoint_atual in SECRETARIA_ENDPOINTS_PERMITIDOS

    if tipo_usuario == 'estagiario':
        return endpoint_atual in ESTAGIARIO_ENDPOINTS_PERMITIDOS

    if tipo_usuario == 'advogado':
        return True

    return True


def permissoes_menu_por_tipo(tipo_usuario):
    if tipo_usuario == 'secretaria':
        return {
            'can_access_perfil': True,
            'can_access_dashboard': False,
            'can_access_clientes': False,
            'can_access_processos': False,
            'can_access_usuarios': False,
            'can_access_contratos': False,
            'can_access_procuracao': False,
            'can_access_agenda': True,
            'can_access_financeiro': False
        }

    if tipo_usuario == 'estagiario':
        return {
            'can_access_perfil': False,
            'can_access_dashboard': False,
            'can_access_clientes': True,
            'can_access_processos': False,
            'can_access_usuarios': False,
            'can_access_contratos': False,
            'can_access_procuracao': True,
            'can_access_agenda': True,
            'can_access_financeiro': False
        }

    if tipo_usuario == 'advogado':
        return {
            'can_access_perfil': True,
            'can_access_dashboard': True,
            'can_access_clientes': True,
            'can_access_processos': True,
            'can_access_usuarios': True,
            'can_access_contratos': True,
            'can_access_procuracao': True,
            'can_access_agenda': True,
            'can_access_financeiro': True
        }

    return {
        'can_access_perfil': True,
        'can_access_dashboard': True,
        'can_access_clientes': True,
        'can_access_processos': True,
        'can_access_usuarios': True,
        'can_access_contratos': True,
        'can_access_procuracao': True,
        'can_access_agenda': True,
        'can_access_financeiro': True
    }


def rotulo_perfil_usuario(tipo_usuario):
    tipo = normalizar_tipo_usuario(tipo_usuario)
    mapa = {
        'admin': 'Administrador',
        'administrador': 'Administrador',
        'advogado': 'Advogado',
        'secretaria': 'Secretaria',
        'estagiario': 'Estagiário'
    }
    return mapa.get(tipo, 'Usuário')


def tipo_usuario_canonico(tipo_usuario):
    tipo = normalizar_tipo_usuario(tipo_usuario)
    mapa = {
        'advogado': 'Advogado',
        'secretaria': 'Secretaria',
        'estagiario': 'Estagiário'
    }
    return mapa.get(tipo, 'Advogado')


def normalizar_parcelas_pagamento(parcelas_raw, numero_parcelas):
    """Normaliza parcelas para o formato esperado no MongoDB."""
    try:
        total = int(numero_parcelas or 0)
    except Exception:
        total = 0

    if total <= 0:
        return []

    parcelas_validas = []
    itens = parcelas_raw if isinstance(parcelas_raw, list) else []

    for item in itens:
        if not isinstance(item, dict):
            continue

        try:
            numero = int(item.get('numero'))
        except Exception:
            continue

        if numero < 1 or numero > total:
            continue

        paga = bool(item.get('paga'))
        data_vencimento = (item.get('data_vencimento') or '').strip()
        if data_vencimento:
            try:
                datetime.strptime(data_vencimento, '%Y-%m-%d')
            except Exception:
                data_vencimento = ''

        parcelas_validas.append({
            'numero': numero,
            'paga': paga,
            'data_vencimento': data_vencimento
        })

    parcelas_por_numero = {}
    for parcela in parcelas_validas:
        parcelas_por_numero[parcela['numero']] = parcela

    resultado = []
    for numero in range(1, total + 1):
        existente = parcelas_por_numero.get(numero)
        if existente:
            resultado.append(existente)
        else:
            resultado.append({'numero': numero, 'paga': False, 'data_vencimento': ''})

    return resultado


def gerar_data_vencimento_parcela(numero_parcela, dia_vencimento):
    """Gera data ISO para parcela usando o dia de vencimento no mês corrente + deslocamento."""
    try:
        parcela_num = int(numero_parcela)
        dia = int(dia_vencimento)
    except Exception:
        return ''

    if parcela_num < 1 or dia < 1 or dia > 31:
        return ''

    hoje = datetime.now()
    ano = hoje.year
    mes = hoje.month + (parcela_num - 1)

    while mes > 12:
        mes -= 12
        ano += 1

    if mes == 12:
        prox_ano = ano + 1
        prox_mes = 1
    else:
        prox_ano = ano
        prox_mes = mes + 1

    ultimo_dia_mes = (datetime(prox_ano, prox_mes, 1) - timedelta(days=1)).day
    dia_final = min(dia, ultimo_dia_mes)
    return datetime(ano, mes, dia_final).strftime('%Y-%m-%d')


def sincronizar_recebimentos_agenda_cliente(db, cliente_id, cliente_nome, forma_pagamento, valor_honorarios, numero_parcelas, parcelas_pagamento, dia_vencimento, referencia_pagamento=''):
    """Cria/atualiza compromissos de recebimento na Agenda com base nas parcelas do cliente."""
    cliente_id_str = str(cliente_id)
    colecao = db['agenda']

    try:
        total_parcelas = int(numero_parcelas or 0)
    except Exception:
        total_parcelas = 0

    forma = (forma_pagamento or '').strip()
    referencia = (referencia_pagamento or '').strip()
    if not forma or total_parcelas <= 0:
        colecao.delete_many({'origem': 'cliente_pagamento', 'cliente_id': cliente_id_str})
        return

    valor_parcela = None
    try:
        valor_total = float(valor_honorarios)
        if total_parcelas > 0 and valor_total > 0:
            valor_parcela = valor_total / total_parcelas
    except Exception:
        valor_parcela = None

    parcelas = parcelas_pagamento if isinstance(parcelas_pagamento, list) else []
    parcelas_por_numero = {}
    for item in parcelas:
        if not isinstance(item, dict):
            continue
        try:
            numero = int(item.get('numero'))
        except Exception:
            continue
        if numero < 1 or numero > total_parcelas:
            continue
        parcelas_por_numero[numero] = item

    numeros_ativos = []
    for numero in range(1, total_parcelas + 1):
        item = parcelas_por_numero.get(numero, {})
        data_vencimento = (item.get('data_vencimento') or '').strip()
        if not data_vencimento:
            data_vencimento = gerar_data_vencimento_parcela(numero, dia_vencimento)

        if not data_vencimento:
            continue

        paga = bool(item.get('paga'))
        status = 'Concluído' if paga else 'Agendado'
        valor_texto = f" - R$ {valor_parcela:.2f}" if valor_parcela is not None else ''
        referencia_texto = f" | Ref.: {referencia}" if referencia else ''
        doc = {
            'titulo': f"Recebimento - {cliente_nome} ({numero}ª parcela)",
            'tipo': 'Recebimento',
            'data': data_vencimento,
            'hora': '09:00',
            'status': status,
            'cliente_id': cliente_id_str,
            'cliente_nome': cliente_nome,
            'referencia_pagamento': referencia,
            'local': '',
            'observacoes': f"Pagamento via {forma}{valor_texto}{referencia_texto}",
            'forum_competencia': '',
            'numero_processo': '',
            'tipo_prazo': '',
            'data_publicacao': '',
            'dias_uteis_prazo': None,
            'tipo_audiencia': '',
            'formato_audiencia': '',
            'link_reuniao_virtual': '',
            'origem': 'cliente_pagamento',
            'parcela_numero': numero,
            'updated_at': datetime.utcnow()
        }

        colecao.update_one(
            {'origem': 'cliente_pagamento', 'cliente_id': cliente_id_str, 'parcela_numero': numero},
            {'$set': doc, '$setOnInsert': {'created_at': datetime.utcnow()}},
            upsert=True
        )
        numeros_ativos.append(numero)

    if numeros_ativos:
        colecao.delete_many({
            'origem': 'cliente_pagamento',
            'cliente_id': cliente_id_str,
            'parcela_numero': {'$nin': numeros_ativos}
        })
    else:
        colecao.delete_many({'origem': 'cliente_pagamento', 'cliente_id': cliente_id_str})


@main_bp.app_context_processor
def injetar_permissoes_menu():
    tipo_normalizado = normalizar_tipo_usuario(session.get('tipo_usuario'))
    dados_menu = permissoes_menu_por_tipo(tipo_normalizado)
    dados_menu['perfil_usuario_rotulo'] = rotulo_perfil_usuario(session.get('tipo_usuario'))
    dados_menu['csrf_token'] = obter_csrf_token()
    return dados_menu


@main_bp.before_app_request
def proteger_csrf_global():
    if request.method not in UNSAFE_HTTP_METHODS:
        return None

    if not validar_csrf_request():
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': 'Token CSRF inválido ou ausente'}), 403

        flash('Sessão expirada ou token inválido. Tente novamente.', 'warning')
        return redirect(url_for('main.login'))

    return None


# ============================================================================
# DECORATOR DE AUTENTICAÇÃO
# ============================================================================

def login_required(f):
    """
    Decorator para proteger rotas que requerem autenticação.
    
    Se usuário não está logado, redireciona para /login.
    Se está logado, permite acesso à rota.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_logado' not in session:
            flash('Por favor, faça login primeiro', 'warning')
            return redirect(url_for('main.login'))

        tipo_usuario = normalizar_tipo_usuario(session.get('tipo_usuario'))
        endpoint_atual = request.endpoint or ''

        if tipo_usuario == 'secretaria' and not endpoint_permitido_para_tipo(tipo_usuario, endpoint_atual):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Acesso restrito para Secretaria'}), 403
            flash('Acesso restrito: perfil Secretaria só pode acessar Agenda e Perfil', 'warning')
            return redirect(url_for('main.listar_agenda'))

        if tipo_usuario == 'estagiario' and not endpoint_permitido_para_tipo(tipo_usuario, endpoint_atual):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Acesso restrito para Estagiário'}), 403
            flash('Acesso restrito: perfil Estagiário só pode acessar Agenda, Clientes e Procuração', 'warning')
            return redirect(url_for('main.listar_agenda'))

        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ROTAS DE AUTENTICAÇÃO
# ============================================================================

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota: GET/POST /login
    
    GET: Exibe o formulário de login
    POST: Valida credenciais e inicia sessão
    
    Em produção, consulta usuários com senha hasheada.
    """
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        usuario_norm = usuario.lower()
        senha = request.form.get('senha', '')
        tentativa_chave = chave_login_attempt(usuario_norm)

        bloqueado, minutos_restantes = login_bloqueado(tentativa_chave)
        if bloqueado:
            return render_template('login.html', erro=f'Muitas tentativas inválidas. Tente novamente em {minutos_restantes} minuto(s).')

        try:
            db = get_db()
        except Exception:
            db = None

        # Usuários internos com senha hash (ex.: admin)
        usuario_sistema = db['usuarios_sistema'].find_one({'usuario': usuario_norm}) if db is not None else None
        if usuario_sistema:
            senha_hash_sistema = usuario_sistema.get('senha_hash', '')
            if senha_hash_sistema and check_password_hash(senha_hash_sistema, senha):
                limpar_falha_login(tentativa_chave)
                session['usuario_logado'] = usuario_sistema.get('usuario', usuario_norm)
                session['nome_usuario'] = usuario_sistema.get('nome', 'Usuário')
                session['tipo_usuario'] = 'Administrador'
                perfil_usuario = db['usuarios_perfil'].find_one({'usuario': session['usuario_logado']})
                session['foto_usuario'] = perfil_usuario.get('foto_path') if perfil_usuario else None
                session['checar_agenda_hoje'] = True
                get_flashed_messages(with_categories=True)
                flash('Login realizado com sucesso!', 'success_auto')
                return redirect(url_for('main.index'))

        # Bootstrap opcional de admin apenas no primeiro login (sem credencial fixa em código)
        admin_bootstrap_password = os.getenv('ADMIN_BOOTSTRAP_PASSWORD', '').strip()
        if (
            db is not None
            and usuario_norm == 'admin'
            and admin_bootstrap_password
            and not usuario_sistema
            and senha == admin_bootstrap_password
        ):
            db['usuarios_sistema'].update_one(
                {'usuario': 'admin'},
                {
                    '$set': {
                        'usuario': 'admin',
                        'nome': 'Administrador',
                        'senha_hash': generate_password_hash(admin_bootstrap_password),
                        'updated_at': datetime.utcnow()
                    }
                },
                upsert=True
            )

            limpar_falha_login(tentativa_chave)
            session['usuario_logado'] = 'admin'
            session['nome_usuario'] = 'Administrador'
            session['tipo_usuario'] = 'Administrador'
            perfil_usuario = db['usuarios_perfil'].find_one({'usuario': 'admin'})
            session['foto_usuario'] = perfil_usuario.get('foto_path') if perfil_usuario else None
            session['checar_agenda_hoje'] = True
            get_flashed_messages(with_categories=True)
            flash('Login realizado com sucesso! Admin inicial configurado.', 'success_auto')
            return redirect(url_for('main.index'))

        # Credenciais de advogados cadastrados no sistema
        advogado = db['advogados'].find_one({'usuario': usuario_norm}) if db is not None else None

        if advogado:
            senha_hash = advogado.get('senha_hash', '')
            senha_legada = advogado.get('senha', '')
            senha_ok = False
            if senha_hash:
                senha_ok = check_password_hash(senha_hash, senha)
            elif senha_legada:
                senha_ok = (senha_legada == senha)
                if senha_ok and db is not None:
                    db['advogados'].update_one(
                        {'_id': advogado['_id']},
                        {
                            '$set': {'senha_hash': generate_password_hash(senha)},
                            '$unset': {'senha': ''}
                        }
                    )

            if senha_ok:
                limpar_falha_login(tentativa_chave)
                session['usuario_logado'] = advogado.get('usuario', usuario)
                session['nome_usuario'] = advogado.get('nome', 'Advogado')
                session['tipo_usuario'] = (advogado.get('tipo') or 'Advogado').strip() or 'Advogado'
                perfil_usuario = db['usuarios_perfil'].find_one({'usuario': session['usuario_logado']})
                session['foto_usuario'] = perfil_usuario.get('foto_path') if perfil_usuario else None
                session['checar_agenda_hoje'] = True
                get_flashed_messages(with_categories=True)
                flash('Login realizado com sucesso!', 'success_auto')
                tipo_destino = normalizar_tipo_usuario(session.get('tipo_usuario'))
                destino = 'main.listar_agenda' if tipo_destino in {'secretaria', 'estagiario'} else 'main.index'
                return redirect(url_for(destino))

        registrar_falha_login(tentativa_chave)
        return render_template('login.html', erro='Usuário ou senha incorretos')
    
    # GET: Exibe formulário
    if 'usuario_logado' in session:
        return redirect(url_for('main.index'))
    
    return render_template('login.html')


@main_bp.route('/logout')
def logout():
    """
    Rota: GET /logout
    Remove a sessão e redireciona para login
    """
    session.clear()
    flash('Você foi desconectado com sucesso', 'info')
    return redirect(url_for('main.login'))


@main_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil_usuario():
    """Página de perfil para upload de foto do usuário logado."""
    db = get_db()
    usuario_logado = (session.get('usuario_logado') or '').strip().lower()

    if not usuario_logado:
        flash('Usuário não autenticado', 'warning')
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        acao = request.form.get('acao', '').strip()

        if acao == 'alterar_senha':
            senha_atual = request.form.get('senha_atual') or ''
            nova_senha = request.form.get('nova_senha') or ''
            confirmar_senha = request.form.get('confirmar_senha') or ''

            if not senha_atual or not nova_senha or not confirmar_senha:
                flash('Preencha todos os campos de senha', 'danger')
                return redirect(url_for('main.perfil_usuario'))

            if nova_senha != confirmar_senha:
                flash('A confirmação da nova senha não confere', 'danger')
                return redirect(url_for('main.perfil_usuario'))

            if len(nova_senha) < 6:
                flash('A nova senha deve ter pelo menos 6 caracteres', 'danger')
                return redirect(url_for('main.perfil_usuario'))

            if usuario_logado == 'admin':
                admin_doc = db['usuarios_sistema'].find_one({'usuario': 'admin'})
                senha_hash_admin = (admin_doc or {}).get('senha_hash', '')

                if not senha_hash_admin:
                    flash('Admin sem senha segura configurada. Defina ADMIN_BOOTSTRAP_PASSWORD no ambiente e faça novo login.', 'danger')
                    return redirect(url_for('main.perfil_usuario'))

                senha_valida = check_password_hash(senha_hash_admin, senha_atual)

                if not senha_valida:
                    flash('Senha antiga incorreta', 'danger')
                    return redirect(url_for('main.perfil_usuario'))

                db['usuarios_sistema'].update_one(
                    {'usuario': 'admin'},
                    {
                        '$set': {
                            'usuario': 'admin',
                            'nome': 'Administrador',
                            'senha_hash': generate_password_hash(nova_senha),
                            'updated_at': datetime.utcnow()
                        }
                    },
                    upsert=True
                )

                flash('Senha alterada com sucesso!', 'success')
                return redirect(url_for('main.perfil_usuario'))

            advogado = db['advogados'].find_one({'usuario': session.get('usuario_logado')}) or db['advogados'].find_one({'usuario': usuario_logado})
            if not advogado:
                flash('Usuário não encontrado para alterar senha', 'danger')
                return redirect(url_for('main.perfil_usuario'))

            senha_hash = advogado.get('senha_hash', '')
            senha_legada = advogado.get('senha', '')
            senha_ok = False
            if senha_hash:
                senha_ok = check_password_hash(senha_hash, senha_atual)
            elif senha_legada:
                senha_ok = (senha_legada == senha_atual)

            if not senha_ok:
                flash('Senha antiga incorreta', 'danger')
                return redirect(url_for('main.perfil_usuario'))

            db['advogados'].update_one(
                {'_id': advogado['_id']},
                {
                    '$set': {'senha_hash': generate_password_hash(nova_senha)},
                    '$unset': {'senha': ''}
                }
            )
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('main.perfil_usuario'))

        if 'foto' not in request.files:
            flash('Selecione uma foto para enviar', 'danger')
            return redirect(url_for('main.perfil_usuario'))

        arquivo = request.files['foto']
        if not arquivo or arquivo.filename == '':
            flash('Selecione uma foto para enviar', 'danger')
            return redirect(url_for('main.perfil_usuario'))

        extensoes_permitidas = {'.jpg', '.jpeg', '.png', '.webp'}
        mimes_permitidos = {'image/jpeg', 'image/png', 'image/webp'}
        tamanho_maximo_bytes = 5 * 1024 * 1024  # 5MB

        nome_seguro = secure_filename(arquivo.filename)
        if not nome_seguro:
            flash('Nome de arquivo inválido', 'danger')
            return redirect(url_for('main.perfil_usuario'))

        ext = os.path.splitext(nome_seguro)[1].lower()
        if ext not in extensoes_permitidas:
            flash('Formato inválido. Use JPG, JPEG, PNG ou WEBP', 'danger')
            return redirect(url_for('main.perfil_usuario'))

        if arquivo.mimetype and arquivo.mimetype.lower() not in mimes_permitidos:
            flash('Tipo MIME inválido. Envie uma imagem JPG, PNG ou WEBP', 'danger')
            return redirect(url_for('main.perfil_usuario'))

        try:
            arquivo.stream.seek(0, os.SEEK_END)
            tamanho_arquivo = arquivo.stream.tell()
            arquivo.stream.seek(0)
        except Exception:
            tamanho_arquivo = 0

        if tamanho_arquivo <= 0:
            flash('Arquivo inválido ou vazio', 'danger')
            return redirect(url_for('main.perfil_usuario'))

        if tamanho_arquivo > tamanho_maximo_bytes:
            flash('Arquivo muito grande. Tamanho máximo permitido: 5MB', 'danger')
            return redirect(url_for('main.perfil_usuario'))

        cabecalho = arquivo.stream.read(16)
        arquivo.stream.seek(0)

        formato_detectado = None
        if cabecalho.startswith(b'\xff\xd8\xff'):
            formato_detectado = '.jpg'
        elif cabecalho.startswith(b'\x89PNG\r\n\x1a\n'):
            formato_detectado = '.png'
        elif cabecalho.startswith(b'RIFF') and cabecalho[8:12] == b'WEBP':
            formato_detectado = '.webp'

        if not formato_detectado:
            flash('Conteúdo inválido. O arquivo enviado não é uma imagem suportada', 'danger')
            return redirect(url_for('main.perfil_usuario'))

        ext_esperada = '.jpg' if ext in {'.jpg', '.jpeg'} else ext
        if ext_esperada != formato_detectado:
            flash('Extensão e conteúdo do arquivo não conferem', 'danger')
            return redirect(url_for('main.perfil_usuario'))

        base_dir = os.path.dirname(os.path.dirname(__file__))
        pasta_upload = os.path.join(base_dir, 'static', 'uploads', 'usuarios')
        os.makedirs(pasta_upload, exist_ok=True)

        nome_arquivo = f"{usuario_logado}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{formato_detectado}"
        caminho_arquivo = os.path.join(pasta_upload, nome_arquivo)
        arquivo.save(caminho_arquivo)

        caminho_relativo = f"uploads/usuarios/{nome_arquivo}"
        db['usuarios_perfil'].update_one(
            {'usuario': usuario_logado},
            {
                '$set': {
                    'usuario': usuario_logado,
                    'nome_usuario': session.get('nome_usuario', ''),
                    'foto_path': caminho_relativo,
                    'updated_at': datetime.utcnow()
                }
            },
            upsert=True
        )

        session['foto_usuario'] = caminho_relativo
        flash('Foto atualizada com sucesso!', 'success')
        return redirect(url_for('main.perfil_usuario'))

    foto_path = None
    try:
        perfil = db['usuarios_perfil'].find_one({'usuario': usuario_logado})
        if perfil:
            foto_path = perfil.get('foto_path')
    except Exception:
        foto_path = None

    session['foto_usuario'] = foto_path

    return render_template('perfil.html', foto_path=foto_path)


# ============================================================================
# ROTAS PRINCIPAIS
# ============================================================================

@main_bp.route('/')
@login_required
def index():
    """
    Rota: GET /
    Exibe a página inicial (Dashboard)
    
    Lógica:
    1. Obtém total de clientes da coleção
    2. Obtém total de processos
    3. Conta processos por status para gráficos
    4. Renderiza template com dados para o frontend
    """
    db = get_db()

    if session.pop('checar_agenda_hoje', False):
        hoje_iso = datetime.now().strftime('%Y-%m-%d')
        compromissos_hoje = []
        try:
            if 'agenda' in db.list_collection_names():
                compromissos_hoje = list(db['agenda'].find({'data': hoje_iso}).sort('hora', 1))
        except Exception:
            compromissos_hoje = []

        if compromissos_hoje:
            prioridade_tipo = {
                'Prazo': 1,
                'Audiência': 2,
                'Pagamento': 3,
                'Recebimento': 4,
                'Consulta': 5
            }
            compromissos_hoje.sort(
                key=lambda c: (
                    prioridade_tipo.get(c.get('tipo', ''), 99),
                    c.get('hora', '99:99')
                )
            )

            resumo = ', '.join([
                f"{c.get('hora', '--:--')} [{c.get('tipo', 'Compromisso')}] {c.get('titulo', 'Compromisso')}"
                for c in compromissos_hoje[:3]
            ])
            if len(compromissos_hoje) > 3:
                resumo += f" e mais {len(compromissos_hoje) - 3}"
            flash(f"Você tem {len(compromissos_hoje)} compromisso(s) para hoje: {resumo}", 'success')
    
    # Contar total de clientes ativos
    total_clientes = db['clientes'].count_documents({'ativo': True})
    
    # Contar total de processos abertos
    total_processos = db['processos'].count_documents({'status': 'Aberto'})
    
    # Contar processos por status
    processos_abertos = db['processos'].count_documents({'status': 'Aberto'})
    processos_suspensos = db['processos'].count_documents({'status': 'Suspenso'})
    processos_julgados = db['processos'].count_documents({'status': 'Julgado'})
    
    # Últimos 5 processos para widget no dashboard
    ultimos_processos = list(db['processos'].find().sort('_id', -1).limit(5))
    for processo in ultimos_processos:
        Processo.converter_para_json(processo)  # Converte ObjectId para String
    
    # Dados para renderização no template
    metricas = {
        'total_clientes': total_clientes,
        'total_processos': total_processos,
        'processos_abertos': processos_abertos,
        'processos_suspensos': processos_suspensos,
        'processos_julgados': processos_julgados,
        'ultimos_processos': ultimos_processos
    }
    
    return render_template('index.html', metricas=metricas)


@main_bp.route('/clientes')
@login_required
def listar_clientes():
    """
    Rota: GET /clientes
    Exibe página com lista de todos os clientes
    
    Lógica:
    1. Busca todos os clientes da coleção
    2. Converte ObjectId para String (necessário para JavaScript)
    3. Passa dados para template Jinja2 renderizar
    """
    db = get_db()
    
    # Busca todos os clientes ativos, ordenados por nome
    clientes = list(db['clientes'].find({'ativo': True}).sort('nome', 1))
    
    # Converte cada ObjectId para String para transmissão JSON
    for cliente in clientes:
        Cliente.converter_para_json(cliente)
    
    return render_template('clientes.html', clientes=clientes)


# ============================================================================
# ROTAS AJAX PARA CLIENTES (Sem refresh de página)
# ============================================================================

@main_bp.route('/api/clientes/novo', methods=['POST'])
def adicionar_cliente():
    """
    Rota: POST /api/clientes/novo
    Adiciona um novo cliente ao banco de dados
    
    Recebe JSON do Frontend com dados do cliente.
    
    Processo:
    1. Valida dados obrigatórios com modelo.validar()
    2. Prepara dados para MongoDB (adiciona timestamps)
    3. Insere na coleção 'clientes'
    4. Retorna JSON com sucesso/erro
    
    Response (JSON):
        - success: true/false
        - message: Mensagem de feedback
        - cliente_id: ID do novo cliente (se criado)
    """
    try:
        # Obtém dados do formulário enviados via POST
        dados = request.get_json()
        
        # Valida dados usando o modelo
        valido, erros = Cliente.validar(dados)
        if not valido:
            return jsonify({'success': False, 'message': ', '.join(erros)}), 400
        
        db = get_db()
        
        # Verifica se email já existe (unicidade) entre clientes ativos
        if db['clientes'].find_one({'email': dados['email'].lower(), 'ativo': True}):
            return jsonify({'success': False, 'message': 'Email já cadastrado'}), 400

        # Verifica se CPF/CNPJ já existe (comparando apenas entre ativos)
        cnpj_digits = re.sub(r"\D", "", dados.get('cpf_cnpj', ''))
        if cnpj_digits:
            # Verifica existência direta por igualdade de string primeiro (ativos apenas)
            if db['clientes'].find_one({'cpf_cnpj': dados.get('cpf_cnpj'), 'ativo': True}):
                return jsonify({'success': False, 'message': 'CPF/CNPJ já cadastrado'}), 400
            # Fallback: itera registros ativos para comparar apenas dígitos (evita duplicidade por formatação)
            for existente in db['clientes'].find({'ativo': True}, {'cpf_cnpj': 1}):
                if re.sub(r"\D", "", existente.get('cpf_cnpj', '')) == cnpj_digits:
                    return jsonify({'success': False, 'message': 'CPF/CNPJ já cadastrado'}), 400
        
        parcelas_normalizadas = normalizar_parcelas_pagamento(
            dados.get('parcelas_pagamento', []),
            dados.get('numero_parcelas', None)
        )
        dados['parcelas_pagamento'] = parcelas_normalizadas
        dados['pagamentos_contratos'] = dados.get('pagamentos_contratos', []) if isinstance(dados.get('pagamentos_contratos', []), list) else []

        # Prepara dados para MongoDB (adiciona data_cadastro, etc)
        cliente_doc = Cliente.preparar_para_mongodb(dados)
        
        # Insere no banco e obtém ID gerado
        resultado = db['clientes'].insert_one(cliente_doc)

        sincronizar_recebimentos_agenda_cliente(
            db=db,
            cliente_id=resultado.inserted_id,
            cliente_nome=cliente_doc.get('nome', ''),
            forma_pagamento=cliente_doc.get('forma_pagamento', ''),
            valor_honorarios=cliente_doc.get('valor_honorarios', None),
            numero_parcelas=cliente_doc.get('numero_parcelas', None),
            parcelas_pagamento=cliente_doc.get('parcelas_pagamento', []),
            dia_vencimento=cliente_doc.get('dia_vencimento', None),
            referencia_pagamento=cliente_doc.get('referencia_pagamento', '')
        )
        
        return jsonify({
            'success': True,
            'message': 'Cliente cadastrado com sucesso!',
            'cliente_id': str(resultado.inserted_id)  # Converte ObjectId para String
        }), 201
        
    except Exception as e:
        erro_texto = str(e)
        if 'E11000' in erro_texto and 'oab' in erro_texto.lower():
            return jsonify({'success': False, 'message': 'OAB já cadastrado para outro usuário'}), 400
        if 'E11000' in erro_texto and 'usuario' in erro_texto.lower():
            return jsonify({'success': False, 'message': 'Usuário já cadastrado'}), 400
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@main_bp.route('/api/clientes/verificar_cnpj', methods=['POST'])
def verificar_cnpj():
    """
    Rota: POST /api/clientes/verificar_cnpj
    Recebe JSON: { cnpj: '00000000000000' }
    Retorna se já existe cliente com esse CNPJ (comparing only digits).
    """
    try:
        dados = request.get_json() or {}
        cnpj = dados.get('cnpj', '')
        cnpj_digits = re.sub(r"\D", "", cnpj)
        if not cnpj_digits:
            return jsonify({'exists': False}), 200

        db = get_db()
        for existente in db['clientes'].find({'ativo': True}, {'cpf_cnpj': 1}):
            if re.sub(r"\D", "", existente.get('cpf_cnpj', '')) == cnpj_digits:
                return jsonify({'exists': True}), 200

        return jsonify({'exists': False}), 200
    except Exception as e:
        return jsonify({'exists': False, 'error': str(e)}), 500


@main_bp.route('/api/clientes/lista', methods=['GET'])
def lista_clientes():
    """
    Rota: GET /api/clientes/lista
    Retorna lista de clientes ativos em JSON para uso em selects (ex.: criação de processo)
    """
    try:
        db = get_db()
        clientes = list(db['clientes'].find({'ativo': True}).sort('nome', 1)) if 'clientes' in db.list_collection_names() else []
        for c in clientes:
            Cliente.converter_para_json(c)
        return jsonify({'success': True, 'clientes': clientes}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/clientes/<cliente_id>/atualizar', methods=['PUT'])
def atualizar_cliente(cliente_id):
    """
    Rota: PUT /api/clientes/<cliente_id>/atualizar
    Atualiza dados de um cliente existente
    
    Argumentos:
        cliente_id: ID do cliente em formato String (vem do Frontend)
    
    Processo:
    1. Converte cliente_id de String para ObjectId (formato MongoDB)
    2. Busca o cliente no banco
    3. Valida dados novos
    4. Atualiza documento
    5. Retorna JSON com resultado
    """
    try:
        # IMPORTANTE: Converte String para ObjectId para buscar no MongoDB
        try:
            obj_id = ObjectId(cliente_id)
        except:
            return jsonify({'success': False, 'message': 'ID de cliente inválido'}), 400
        
        dados = request.get_json()
        
        # Valida dados
        valido, erros = Cliente.validar(dados)
        if not valido:
            return jsonify({'success': False, 'message': ', '.join(erros)}), 400
        
        db = get_db()
        
        # Busca cliente existente
        cliente = db['clientes'].find_one({'_id': obj_id})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        numero_parcelas_novo = dados.get('numero_parcelas', cliente.get('numero_parcelas', None))
        parcelas_origem = dados.get('parcelas_pagamento', cliente.get('parcelas_pagamento', []))
        parcelas_normalizadas = normalizar_parcelas_pagamento(parcelas_origem, numero_parcelas_novo)

        # Prepara dados atualizados
        atualizacoes = {
            'nome': dados.get('nome', cliente['nome']),
            'email': dados.get('email', cliente['email']),
            'telefone': dados.get('telefone', cliente.get('telefone', '')),
            'cpf_cnpj': dados.get('cpf_cnpj', cliente.get('cpf_cnpj', '')),
            'endereco': dados.get('endereco', cliente.get('endereco', '')),
            'cidade': dados.get('cidade', cliente.get('cidade', '')),
            'uf': dados.get('uf', cliente.get('uf', '')),
            'anotacoes': dados.get('anotacoes', cliente.get('anotacoes', '')),
            'forma_pagamento': dados.get('forma_pagamento', cliente.get('forma_pagamento', '')),
            'referencia_pagamento': dados.get('referencia_pagamento', cliente.get('referencia_pagamento', '')),
            'valor_honorarios': dados.get('valor_honorarios', cliente.get('valor_honorarios', None)),
            'dia_vencimento': dados.get('dia_vencimento', cliente.get('dia_vencimento', None)),
            'observacoes_pagamento': dados.get('observacoes_pagamento', cliente.get('observacoes_pagamento', '')),
            'numero_parcelas': numero_parcelas_novo,
            'parcelas_pagamento': parcelas_normalizadas,
            'pagamentos_contratos': dados.get('pagamentos_contratos', cliente.get('pagamentos_contratos', [])) if isinstance(dados.get('pagamentos_contratos', cliente.get('pagamentos_contratos', [])), list) else []
        }
        
        # Atualiza no MongoDB
        db['clientes'].update_one({'_id': obj_id}, {'$set': atualizacoes})

        sincronizar_recebimentos_agenda_cliente(
            db=db,
            cliente_id=obj_id,
            cliente_nome=atualizacoes.get('nome', cliente.get('nome', '')),
            forma_pagamento=atualizacoes.get('forma_pagamento', ''),
            valor_honorarios=atualizacoes.get('valor_honorarios', None),
            numero_parcelas=atualizacoes.get('numero_parcelas', None),
            parcelas_pagamento=atualizacoes.get('parcelas_pagamento', []),
            dia_vencimento=atualizacoes.get('dia_vencimento', None),
            referencia_pagamento=atualizacoes.get('referencia_pagamento', '')
        )
        
        return jsonify({'success': True, 'message': 'Cliente atualizado com sucesso!'}), 200
        
    except Exception as e:
        erro_texto = str(e)
        if 'E11000' in erro_texto and 'oab' in erro_texto.lower():
            return jsonify({'success': False, 'message': 'OAB já cadastrado para outro usuário'}), 400
        if 'E11000' in erro_texto and 'usuario' in erro_texto.lower():
            return jsonify({'success': False, 'message': 'Usuário já cadastrado'}), 400
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@main_bp.route('/api/clientes/<cliente_id>/anotacoes', methods=['GET', 'PUT'])
def cliente_anotacoes(cliente_id):
    """
    GET: retorna anotacoes do cliente
    PUT: atualiza anotacoes do cliente (JSON: { anotacoes: '...' })
    """
    try:
        try:
            obj_id = ObjectId(cliente_id)
        except:
            return jsonify({'success': False, 'message': 'ID de cliente inválido'}), 400

        db = get_db()
        cliente = db['clientes'].find_one({'_id': obj_id})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        if request.method == 'GET':
            return jsonify({'success': True, 'anotacoes': cliente.get('anotacoes', '')}), 200

        # PUT: atualiza anotacoes
        dados = request.get_json() or {}
        anotacoes = dados.get('anotacoes', '')
        db['clientes'].update_one({'_id': obj_id}, {'$set': {'anotacoes': anotacoes}})
        return jsonify({'success': True, 'message': 'Anotações atualizadas com sucesso!'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@main_bp.route('/api/clientes/<cliente_id>/deletar', methods=['DELETE'])
def deletar_cliente(cliente_id):
    """
    Rota: DELETE /api/clientes/<cliente_id>/deletar
    Deleta (inativa) um cliente do sistema
    
    Nota: Usa exclusão lógica (marca como inativo) em vez de físico
          Isso preserva histórico de dados e relacionamentos
    """
    try:
        # Converte String para ObjectId
        try:
            obj_id = ObjectId(cliente_id)
        except:
            return jsonify({'success': False, 'message': 'ID inválido'}), 400
        
        db = get_db()
        
        # Marca cliente como inativo (exclusão lógica)
        resultado = db['clientes'].update_one(
            {'_id': obj_id},
            {'$set': {'ativo': False}}
        )
        
        if resultado.matched_count == 0:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        return jsonify({'success': True, 'message': 'Cliente removido com sucesso!'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


# ============================================================================
# ROTAS PARA PROCESSOS JURÍDICOS
# ============================================================================

@main_bp.route('/processos')
@login_required
def listar_processos():
    """
    Rota: GET /processos
    Exibe página com lista de todos os processos
    
    Lógica:
    1. Busca todos os processos com informações do cliente
    2. Converte ObjectIds para Strings
    3. Renderiza template com dados
    """
    db = get_db()
    
    # Busca todos os processos, ordenados por data decrescente
    processos = list(db['processos'].find().sort('data_abertura', -1))
    
    # Converte cada processo para JSON (ObjectId -> String)
    for processo in processos:
        Processo.converter_para_json(processo)
    
    return render_template('processos.html', processos=processos)


def salvar_arquivos_processo(arquivos):
    """Salva uma lista de arquivos enviados e retorna caminhos relativos ao diretório static."""
    arquivos_salvos = []
    upload_dir = os.path.join('static', 'uploads', 'processos')
    os.makedirs(upload_dir, exist_ok=True)

    for indice, arquivo in enumerate(arquivos):
        if not arquivo or not arquivo.filename:
            continue

        filename_original = secure_filename(arquivo.filename)
        if not filename_original:
            continue

        prefix = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        filename = f"{prefix}_{indice}_{filename_original}"
        caminho = os.path.join(upload_dir, filename)
        arquivo.save(caminho)
        arquivos_salvos.append(f"uploads/processos/{filename}")

    return arquivos_salvos


@main_bp.route('/api/processos/novo', methods=['POST'])
def adicionar_processo():
    """
    Rota: POST /api/processos/novo
    Cria um novo processo jurídico
    
    Processo:
    1. Valida dados com modelo
    2. Busca cliente associado (verifica existência)
    3. Insere processo com referência ao cliente
    4. Retorna JSON com resultado
    """
    try:
        # Suporta JSON ou multipart/form-data (FormData com anexo)
        dados = None
        content_type = request.content_type or ''
        if 'multipart/form-data' in content_type:
            # Extrai campos do form e arquivos
            form = request.form
            dados = {
                'numero_processo': form.get('numero_processo', '').strip(),
                'cliente_id': form.get('cliente_id', '').strip(),
                'cliente_nome': form.get('cliente_nome', '').strip(),
                'tipo_acao': form.get('tipo_acao', '').strip(),
                'status': form.get('status', '').strip(),
                'tribunal': form.get('tribunal', '').strip(),
                'vara': form.get('vara', '').strip(),
                'juiz': form.get('juiz', '').strip(),
                'prazo_data': form.get('prazo_data', '').strip(),
                'descricao': form.get('descricao', '').strip()
            }
            # Trata arquivos anexos (opcional)
            arquivos_anexados = request.files.getlist('anexos')
            if not arquivos_anexados:
                arquivo_legado = request.files.get('anexo')
                if arquivo_legado and arquivo_legado.filename:
                    arquivos_anexados = [arquivo_legado]

            anexos_salvos = salvar_arquivos_processo(arquivos_anexados)
            if anexos_salvos:
                dados['anexos'] = anexos_salvos
                dados['anexo'] = anexos_salvos[0]
        else:
            dados = request.get_json()

        # Valida dados
        valido, erros = Processo.validar(dados)
        if not valido:
            return jsonify({'success': False, 'message': ', '.join(erros)}), 400
        
        db = get_db()
        
        # Verifica se cliente existe
        cliente_id_obj = ObjectId(dados['cliente_id'])
        cliente = db['clientes'].find_one({'_id': cliente_id_obj})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404
        
        # Verifica se número de processo já existe
        if db['processos'].find_one({'numero_processo': dados['numero_processo']}):
            return jsonify({'success': False, 'message': 'Número de processo já cadastrado'}), 400
        
        # Prepara dados (converte cliente_id String para ObjectId)
        dados['cliente_nome'] = cliente['nome']  # Cache do nome
        processo_doc = Processo.preparar_para_mongodb(dados)
        
        # Insere no banco
        resultado = db['processos'].insert_one(processo_doc)
        
        return jsonify({
            'success': True,
            'message': 'Processo cadastrado com sucesso!',
            'processo_id': str(resultado.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@main_bp.route('/api/processos/<processo_id>/atualizar', methods=['PUT'])
def atualizar_processo(processo_id):
    """
    Rota: PUT /api/processos/<processo_id>/atualizar
    Atualiza informações de um processo existente
    """
    try:
        try:
            obj_id = ObjectId(processo_id)
        except:
            return jsonify({'success': False, 'message': 'ID inválido'}), 400
        
        content_type = request.content_type or ''
        if 'multipart/form-data' in content_type:
            form = request.form
            dados = {
                'numero_processo': form.get('numero_processo', '').strip(),
                'cliente_id': form.get('cliente_id', '').strip(),
                'cliente_nome': form.get('cliente_nome', '').strip(),
                'tipo_acao': form.get('tipo_acao', '').strip(),
                'status': form.get('status', '').strip(),
                'tribunal': form.get('tribunal', '').strip(),
                'vara': form.get('vara', '').strip(),
                'juiz': form.get('juiz', '').strip(),
                'prazo_data': form.get('prazo_data', '').strip(),
                'descricao': form.get('descricao', '').strip()
            }
        else:
            dados = request.get_json()
        
        # Valida dados
        valido, erros = Processo.validar(dados)
        if not valido:
            return jsonify({'success': False, 'message': ', '.join(erros)}), 400
        
        db = get_db()
        
        # Busca processo
        processo = db['processos'].find_one({'_id': obj_id})
        if not processo:
            return jsonify({'success': False, 'message': 'Processo não encontrado'}), 404

        anexos_atuais = processo.get('anexos')
        if not isinstance(anexos_atuais, list):
            anexos_atuais = []
        if not anexos_atuais and processo.get('anexo'):
            anexos_atuais = [processo.get('anexo')]

        novos_anexos = []
        if 'multipart/form-data' in content_type:
            arquivos_anexados = request.files.getlist('anexos')
            if not arquivos_anexados:
                arquivo_legado = request.files.get('anexo')
                if arquivo_legado and arquivo_legado.filename:
                    arquivos_anexados = [arquivo_legado]
            novos_anexos = salvar_arquivos_processo(arquivos_anexados)

        anexos_finais = anexos_atuais + novos_anexos
        
        # Prepara atualizações (mantém cliente_id e data_abertura originais)
        atualizacoes = {
            'numero_processo': dados.get('numero_processo', processo['numero_processo']),
            'tipo_acao': dados.get('tipo_acao', processo['tipo_acao']),
            'tribunal': dados.get('tribunal', processo.get('tribunal', '')),
            'vara': dados.get('vara', processo.get('vara', '')),
            'juiz': dados.get('juiz', processo.get('juiz', '')),
            'status': dados.get('status', processo['status']),
            'descricao': dados.get('descricao', processo.get('descricao', '')),
            'anexos': anexos_finais,
            'anexo': anexos_finais[0] if anexos_finais else '',
            'data_ultima_movimentacao': datetime.utcnow()  # Registra atualização
        }
        
        db['processos'].update_one({'_id': obj_id}, {'$set': atualizacoes})
        
        return jsonify({'success': True, 'message': 'Processo atualizado com sucesso!'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@main_bp.route('/api/processos/<processo_id>/deletar', methods=['DELETE'])
def deletar_processo(processo_id):
    """
    Rota: DELETE /api/processos/<processo_id>/deletar
    Remove um processo do banco de dados
    """
    try:
        try:
            obj_id = ObjectId(processo_id)
        except:
            return jsonify({'success': False, 'message': 'ID inválido'}), 400
        
        db = get_db()
        
        resultado = db['processos'].delete_one({'_id': obj_id})
        
        if resultado.deleted_count == 0:
            return jsonify({'success': False, 'message': 'Processo não encontrado'}), 404
        
        return jsonify({'success': True, 'message': 'Processo removido com sucesso!'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@main_bp.route('/api/clientes/<cliente_id>/processos', methods=['GET'])
def obter_processos_cliente(cliente_id):
    """
    Rota: GET /api/clientes/<cliente_id>/processos
    Retorna todos os processos de um cliente específico (AJAX)
    
    Uso: Chamada JavaScript para popular modal de processos de um cliente
    """
    try:
        try:
            obj_id = ObjectId(cliente_id)
        except:
            return jsonify({'success': False, 'message': 'ID inválido'}), 400
        
        db = get_db()
        
        # Busca todos os processos do cliente
        processos = list(db['processos'].find({'cliente_id': obj_id}))
        
        # Converte para JSON
        for processo in processos:
            Processo.converter_para_json(processo)
        
        return jsonify({
            'success': True,
            'processos': processos,
            'total': len(processos)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@main_bp.route('/api/clientes/<cliente_id>/referencias-pagamento', methods=['GET'])
def obter_referencias_pagamento_cliente(cliente_id):
    """
    Rota: GET /api/clientes/<cliente_id>/referencias-pagamento
    Retorna contratos válidos para pagamento do cliente.
    """
    try:
        try:
            obj_id = ObjectId(cliente_id)
        except Exception:
            return jsonify({'success': False, 'message': 'ID inválido'}), 400

        db = get_db()

        referencias = []

        contratos = list(
            db['contratos'].find({'cliente_id': obj_id}).sort([('data', -1), ('created_at', -1)])
        ) if 'contratos' in db.list_collection_names() else []

        for contrato in contratos:
            contrato_id = str(contrato.get('_id', '')).strip()
            if not contrato_id:
                continue

            tipo = (contrato.get('tipo') or 'Contrato').strip()
            subtipo = (contrato.get('subtipo') or '').strip()
            subtipo_outros = (contrato.get('subtipo_outros') or '').strip()
            data = (contrato.get('data') or '').strip()

            if subtipo:
                subtipo_label = subtipo_outros if subtipo == 'Outros' and subtipo_outros else subtipo
                tipo_label = f"{tipo} - {subtipo_label}"
            else:
                tipo_label = tipo

            data_label = f" - {data}" if data else ''
            label = f"Contrato: {tipo_label}{data_label} ({contrato_id[:8]})"
            valor = contrato_id

            referencias.append({
                'tipo': 'contrato',
                'id': contrato_id,
                'label': label,
                'valor': valor
            })

        vistos = set()
        referencias_unicas = []
        for item in referencias:
            chave = (item.get('valor') or '').strip().lower()
            if not chave or chave in vistos:
                continue
            vistos.add(chave)
            referencias_unicas.append(item)

        referencias_unicas.sort(key=lambda x: (x.get('tipo', ''), x.get('label', '')))

        return jsonify({'success': True, 'referencias': referencias_unicas, 'total': len(referencias_unicas)}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


# ============================================================================
# ROTAS ADICIONAIS (Advogados e Procuração)
# ============================================================================


@main_bp.route('/advogados')
@main_bp.route('/usuarios')
@login_required
def pagina_usuarios():
    """
    Rota: GET /usuarios
    Exibe página com lista de usuários cadastrados
    """
    db = get_db()
    advogados = list(db['advogados'].find().sort('nome', 1)) if 'advogados' in db.list_collection_names() else []
    for usuario_doc in advogados:
        usuario_doc['tipo'] = tipo_usuario_canonico(usuario_doc.get('tipo'))
    return render_template('usuarios.html', advogados=advogados)


pagina_advogados = pagina_usuarios


@main_bp.route('/contratos')
@login_required
def listar_contratos():
    """
    Rota: GET /contratos
    Exibe a página de contratos (lista básica por enquanto)
    """
    db = get_db()
    contratos = list(db['contratos'].find().sort('data', -1)) if 'contratos' in db.list_collection_names() else []
    # converte ObjectId para string
    for c in contratos:
        if '_id' in c:
            c['_id'] = str(c['_id'])
    return render_template('contratos.html', contratos=contratos)


@main_bp.route('/financeiro')
@login_required
def pagina_financeiro():
    """Painel financeiro com visão completa de fluxo de caixa."""
    def parse_moeda(valor):
        texto = str(valor or '').strip()
        if not texto:
            return 0.0
        texto = texto.replace('R$', '').replace(' ', '')
        if ',' in texto and '.' in texto:
            texto = texto.replace('.', '').replace(',', '.')
        elif ',' in texto:
            texto = texto.replace(',', '.')
        try:
            return float(texto)
        except Exception:
            return 0.0

    def data_br(data_iso):
        if not data_iso:
            return '-'
        try:
            return datetime.strptime(data_iso, '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            return data_iso

    def cliente_esta_inadimplente(parcelas_validas):
        """
        Considera inadimplência apenas quando há evidência objetiva de atraso,
        com data de vencimento da parcela já expirada e sem pagamento.
        """
        hoje = datetime.now().date()
        for parcela in parcelas_validas:
            if not isinstance(parcela, dict):
                continue
            if parcela.get('paga'):
                continue
            data_venc = (parcela.get('data_vencimento') or '').strip()
            if not data_venc:
                continue
            try:
                data_venc_dt = datetime.strptime(data_venc, '%Y-%m-%d').date()
            except Exception:
                continue
            if data_venc_dt < hoje:
                return True
        return False

    db = get_db()
    clientes = list(db['clientes'].find({'ativo': True}).sort('nome', 1)) if 'clientes' in db.list_collection_names() else []
    lancamentos = list(db['fluxo_caixa'].find().sort([('data_vencimento', 1), ('criado_em', -1)])) if 'fluxo_caixa' in db.list_collection_names() else []

    total_faturado = 0.0
    total_recebido = 0.0
    total_a_receber = 0.0
    total_inadimplentes = 0
    detalhes_clientes = []

    entradas_realizadas = 0.0
    saidas_realizadas = 0.0
    entradas_previstas = 0.0
    saidas_previstas = 0.0

    hoje_iso = datetime.now().strftime('%Y-%m-%d')
    lancamentos_formatados = []

    for cliente in clientes:
        valor_honorarios = float(cliente.get('valor_honorarios') or 0)
        numero_parcelas = int(cliente.get('numero_parcelas') or 0)
        parcelas = cliente.get('parcelas_pagamento') or []
        parcelas_validas = [p for p in parcelas if isinstance(p, dict)]
        parcelas_pagas = len([p for p in parcelas_validas if p.get('paga')])

        if numero_parcelas > 0 and valor_honorarios > 0:
            valor_por_parcela = valor_honorarios / numero_parcelas
            valor_recebido = valor_por_parcela * min(parcelas_pagas, numero_parcelas)
            valor_a_receber = max(valor_honorarios - valor_recebido, 0)
            progresso = int((min(parcelas_pagas, numero_parcelas) / numero_parcelas) * 100)
        else:
            valor_recebido = 0.0
            valor_a_receber = valor_honorarios
            progresso = 0

        esta_inadimplente = cliente_esta_inadimplente(parcelas_validas)
        if esta_inadimplente:
            total_inadimplentes += 1

        if valor_honorarios <= 0:
            status_pagamento = ''
        elif valor_a_receber <= 0:
            status_pagamento = 'Pago'
        elif esta_inadimplente:
            status_pagamento = 'Atrasado'
        else:
            status_pagamento = 'Em dia'

        total_faturado += valor_honorarios
        total_recebido += valor_recebido
        total_a_receber += valor_a_receber

        if valor_honorarios > 0:
            detalhes_clientes.append({
                'nome': cliente.get('nome', '-'),
                'forma_pagamento': cliente.get('forma_pagamento', ''),
                'status_pagamento': status_pagamento,
                'valor_total': valor_honorarios,
                'valor_recebido': valor_recebido,
                'valor_a_receber': valor_a_receber,
                'parcelas_pagas': parcelas_pagas,
                'numero_parcelas': numero_parcelas,
                'progresso': progresso
            })

    detalhes_clientes.sort(key=lambda item: item.get('valor_a_receber', 0), reverse=True)

    for lanc in lancamentos:
        lanc_id = str(lanc.get('_id'))
        tipo = (lanc.get('tipo') or 'saida').strip().lower()
        status_original = (lanc.get('status') or 'pendente').strip().lower()
        data_vencimento = (lanc.get('data_vencimento') or '').strip()
        valor = parse_moeda(lanc.get('valor'))

        status = status_original
        if status == 'pendente' and data_vencimento and data_vencimento < hoje_iso:
            status = 'atrasado'

        if tipo == 'entrada':
            if status == 'pago':
                entradas_realizadas += valor
            else:
                entradas_previstas += valor
        else:
            if status == 'pago':
                saidas_realizadas += valor
            else:
                saidas_previstas += valor

        lancamentos_formatados.append({
            '_id': lanc_id,
            'tipo': tipo,
            'categoria': lanc.get('categoria', ''),
            'descricao': lanc.get('descricao', ''),
            'cliente_nome': lanc.get('cliente_nome', ''),
            'valor': valor,
            'data_vencimento': data_vencimento,
            'data_vencimento_br': data_br(data_vencimento),
            'data_pagamento': lanc.get('data_pagamento', ''),
            'data_pagamento_br': data_br(lanc.get('data_pagamento', '')),
            'status': status,
            'observacoes': lanc.get('observacoes', '')
        })

    resumo = {
        'total_faturado': total_faturado,
        'total_recebido': total_recebido,
        'total_a_receber': total_a_receber,
        'total_inadimplentes': total_inadimplentes,
        'total_clientes_financeiro': len(detalhes_clientes),
        'entradas_realizadas': entradas_realizadas,
        'saidas_realizadas': saidas_realizadas,
        'entradas_previstas': entradas_previstas,
        'saidas_previstas': saidas_previstas,
        'saldo_atual': entradas_realizadas - saidas_realizadas,
        'saldo_projetado': (entradas_realizadas + entradas_previstas) - (saidas_realizadas + saidas_previstas)
    }

    categorias_entrada = ['Honorários', 'Consulta', 'Acordo', 'Êxito', 'Reembolso', 'Outros']
    categorias_saida = ['Fornecedor', 'Tributos', 'Folha', 'Aluguel', 'Software', 'Custas', 'Outros']

    return render_template(
        'financeiro.html',
        resumo=resumo,
        detalhes_clientes=detalhes_clientes,
        lancamentos=lancamentos_formatados,
        categorias_entrada=categorias_entrada,
        categorias_saida=categorias_saida
    )


@main_bp.route('/financeiro/lancamentos', methods=['POST'])
@login_required
def adicionar_lancamento_financeiro():
    db = get_db()

    tipo = (request.form.get('tipo') or '').strip().lower()
    categoria = (request.form.get('categoria') or '').strip()
    descricao = (request.form.get('descricao') or '').strip()
    cliente_nome = (request.form.get('cliente_nome') or '').strip()
    data_vencimento = (request.form.get('data_vencimento') or '').strip()
    observacoes = (request.form.get('observacoes') or '').strip()
    valor_raw = (request.form.get('valor') or '').strip()

    if tipo not in ['entrada', 'saida']:
        flash('Tipo de lançamento inválido.', 'danger')
        return redirect(url_for('main.pagina_financeiro'))

    if not descricao:
        flash('Informe a descrição do lançamento.', 'warning')
        return redirect(url_for('main.pagina_financeiro'))

    if not data_vencimento:
        flash('Informe a data de vencimento.', 'warning')
        return redirect(url_for('main.pagina_financeiro'))

    valor_texto = valor_raw.replace('R$', '').replace(' ', '')
    if ',' in valor_texto and '.' in valor_texto:
        valor_texto = valor_texto.replace('.', '').replace(',', '.')
    elif ',' in valor_texto:
        valor_texto = valor_texto.replace(',', '.')

    try:
        valor = float(valor_texto)
    except Exception:
        flash('Valor inválido.', 'danger')
        return redirect(url_for('main.pagina_financeiro'))

    if valor <= 0:
        flash('O valor deve ser maior que zero.', 'warning')
        return redirect(url_for('main.pagina_financeiro'))

    documento = {
        'tipo': tipo,
        'categoria': categoria,
        'descricao': descricao,
        'cliente_nome': cliente_nome,
        'valor': valor,
        'data_vencimento': data_vencimento,
        'data_pagamento': '',
        'status': 'pendente',
        'observacoes': observacoes,
        'criado_em': datetime.utcnow(),
        'atualizado_em': datetime.utcnow()
    }

    db['fluxo_caixa'].insert_one(documento)
    flash('Lançamento financeiro adicionado com sucesso.', 'success')
    return redirect(url_for('main.pagina_financeiro'))


@main_bp.route('/financeiro/lancamentos/<lancamento_id>/status', methods=['POST'])
@login_required
def atualizar_status_lancamento_financeiro(lancamento_id):
    db = get_db()
    acao = (request.form.get('acao') or '').strip().lower()

    try:
        obj_id = ObjectId(lancamento_id)
    except Exception:
        flash('Lançamento inválido.', 'danger')
        return redirect(url_for('main.pagina_financeiro'))

    if acao not in ['pago', 'pendente']:
        flash('Ação inválida para o lançamento.', 'danger')
        return redirect(url_for('main.pagina_financeiro'))

    payload = {
        'status': acao,
        'atualizado_em': datetime.utcnow()
    }
    payload['data_pagamento'] = datetime.now().strftime('%Y-%m-%d') if acao == 'pago' else ''

    db['fluxo_caixa'].update_one({'_id': obj_id}, {'$set': payload})
    flash('Status do lançamento atualizado.', 'success')
    return redirect(url_for('main.pagina_financeiro'))


@main_bp.route('/financeiro/lancamentos/<lancamento_id>/excluir', methods=['POST'])
@login_required
def excluir_lancamento_financeiro(lancamento_id):
    db = get_db()

    try:
        obj_id = ObjectId(lancamento_id)
    except Exception:
        flash('Lançamento inválido.', 'danger')
        return redirect(url_for('main.pagina_financeiro'))

    db['fluxo_caixa'].delete_one({'_id': obj_id})
    flash('Lançamento removido com sucesso.', 'info')
    return redirect(url_for('main.pagina_financeiro'))


@main_bp.route('/agenda')
@login_required
def listar_agenda():
    """Página da agenda com calendário e lista de compromissos."""
    db = get_db()
    compromissos = list(db['agenda'].find().sort([('data', 1), ('hora', 1)])) if 'agenda' in db.list_collection_names() else []

    def serializar_item_agenda(item):
        doc = dict(item)
        for chave, valor in list(doc.items()):
            if isinstance(valor, ObjectId):
                doc[chave] = str(valor)
            elif isinstance(valor, datetime):
                doc[chave] = valor.isoformat()
        return doc

    compromissos = [serializar_item_agenda(item) for item in compromissos]
    return render_template('agenda.html', compromissos=compromissos)


@main_bp.route('/api/agenda/lista', methods=['GET'])
@login_required
def lista_agenda_api():
    try:
        db = get_db()
        compromissos = list(db['agenda'].find().sort([('data', 1), ('hora', 1)])) if 'agenda' in db.list_collection_names() else []

        def serializar_item_agenda(item):
            doc = dict(item)
            for chave, valor in list(doc.items()):
                if isinstance(valor, ObjectId):
                    doc[chave] = str(valor)
                elif isinstance(valor, datetime):
                    doc[chave] = valor.isoformat()
            return doc

        compromissos = [serializar_item_agenda(item) for item in compromissos]
        return jsonify({'success': True, 'compromissos': compromissos}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/agenda/nova', methods=['POST'])
@login_required
def adicionar_compromisso_agenda():
    try:
        dados = request.get_json() or {}
        titulo = (dados.get('titulo') or '').strip()
        tipo = (dados.get('tipo') or '').strip()
        data = (dados.get('data') or '').strip()
        hora = (dados.get('hora') or '').strip()
        status = (dados.get('status') or 'Agendado').strip()
        cliente_id = (dados.get('cliente_id') or '').strip()
        cliente_nome = (dados.get('cliente_nome') or '').strip()
        local = (dados.get('local') or '').strip()
        observacoes = (dados.get('observacoes') or '').strip()
        forum_competencia = (dados.get('forum_competencia') or '').strip()
        numero_processo = (dados.get('numero_processo') or '').strip()
        tipo_prazo = (dados.get('tipo_prazo') or '').strip()
        data_publicacao = (dados.get('data_publicacao') or '').strip()
        dias_uteis_prazo_raw = dados.get('dias_uteis_prazo')
        tipo_audiencia = (dados.get('tipo_audiencia') or '').strip()
        formato_audiencia = (dados.get('formato_audiencia') or '').strip()
        link_reuniao_virtual = (dados.get('link_reuniao_virtual') or '').strip()

        if not titulo or not tipo:
            return jsonify({'success': False, 'message': 'Título e tipo são obrigatórios'}), 400

        if tipo != 'Audiência' and not hora:
            return jsonify({'success': False, 'message': 'Hora é obrigatória para este tipo de compromisso'}), 400

        dias_uteis_prazo = None
        if tipo == 'Prazo':
            if not forum_competencia or not numero_processo or not tipo_prazo or not data_publicacao:
                return jsonify({'success': False, 'message': 'Para compromisso do tipo Prazo, informe fórum de competência, número do processo, tipo de prazo e data de publicação'}), 400
            try:
                dias_uteis_prazo = int(dias_uteis_prazo_raw)
            except Exception:
                return jsonify({'success': False, 'message': 'Dias úteis do prazo deve ser um número entre 1 e 25'}), 400
            if dias_uteis_prazo < 1 or dias_uteis_prazo > 25:
                return jsonify({'success': False, 'message': 'Dias úteis do prazo deve estar entre 1 e 25'}), 400

            try:
                data_base = datetime.strptime(data_publicacao, '%Y-%m-%d').date()
            except Exception:
                return jsonify({'success': False, 'message': 'Data de publicação inválida'}), 400

            dias_restantes = dias_uteis_prazo
            data_vencimento = data_base
            while dias_restantes > 0:
                data_vencimento += timedelta(days=1)
                if data_vencimento.weekday() < 5:
                    dias_restantes -= 1
            data = data_vencimento.isoformat()
        elif not data:
            return jsonify({'success': False, 'message': 'Data é obrigatória para este tipo de compromisso'}), 400

        if tipo == 'Audiência':
            if tipo_audiencia not in {'Instrução', 'Conciliação'}:
                return jsonify({'success': False, 'message': 'Para Audiência, selecione um tipo de audiência válido'}), 400
            if formato_audiencia not in {'Presencial', 'Virtual'}:
                return jsonify({'success': False, 'message': 'Para Audiência, selecione se será presencial ou virtual'}), 400
            if formato_audiencia == 'Presencial':
                if not hora or not local:
                    return jsonify({'success': False, 'message': 'Para audiência presencial, informe hora e local'}), 400
                link_reuniao_virtual = ''
            else:
                if not link_reuniao_virtual:
                    return jsonify({'success': False, 'message': 'Para audiência virtual, informe o link da reunião'}), 400
                hora = ''
                local = ''
        else:
            tipo_audiencia = ''
            formato_audiencia = ''
            link_reuniao_virtual = ''

        db = get_db()
        doc = {
            'titulo': titulo,
            'tipo': tipo,
            'data': data,
            'hora': hora,
            'status': status,
            'cliente_id': cliente_id,
            'cliente_nome': cliente_nome,
            'local': local,
            'observacoes': observacoes,
            'forum_competencia': forum_competencia,
            'numero_processo': numero_processo,
            'tipo_prazo': tipo_prazo if tipo == 'Prazo' else '',
            'data_publicacao': data_publicacao if tipo == 'Prazo' else '',
            'dias_uteis_prazo': dias_uteis_prazo if tipo == 'Prazo' else None,
            'tipo_audiencia': tipo_audiencia if tipo == 'Audiência' else '',
            'formato_audiencia': formato_audiencia if tipo == 'Audiência' else '',
            'link_reuniao_virtual': link_reuniao_virtual if (tipo == 'Audiência' and formato_audiencia == 'Virtual') else '',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        resultado = db['agenda'].insert_one(doc)
        return jsonify({'success': True, 'id': str(resultado.inserted_id), 'message': 'Compromisso cadastrado com sucesso!'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/agenda/<compromisso_id>/atualizar', methods=['PUT'])
@login_required
def atualizar_compromisso_agenda(compromisso_id):
    try:
        try:
            obj_id = ObjectId(compromisso_id)
        except Exception:
            return jsonify({'success': False, 'message': 'ID inválido'}), 400

        dados = request.get_json() or {}
        titulo = (dados.get('titulo') or '').strip()
        tipo = (dados.get('tipo') or '').strip()
        data = (dados.get('data') or '').strip()
        hora = (dados.get('hora') or '').strip()
        forum_competencia = (dados.get('forum_competencia') or '').strip()
        numero_processo = (dados.get('numero_processo') or '').strip()
        tipo_prazo = (dados.get('tipo_prazo') or '').strip()
        data_publicacao = (dados.get('data_publicacao') or '').strip()
        dias_uteis_prazo_raw = dados.get('dias_uteis_prazo')
        tipo_audiencia = (dados.get('tipo_audiencia') or '').strip()
        formato_audiencia = (dados.get('formato_audiencia') or '').strip()
        link_reuniao_virtual = (dados.get('link_reuniao_virtual') or '').strip()

        if not titulo or not tipo:
            return jsonify({'success': False, 'message': 'Título e tipo são obrigatórios'}), 400

        if tipo != 'Audiência' and not hora:
            return jsonify({'success': False, 'message': 'Hora é obrigatória para este tipo de compromisso'}), 400

        dias_uteis_prazo = None
        if tipo == 'Prazo':
            if not forum_competencia or not numero_processo or not tipo_prazo or not data_publicacao:
                return jsonify({'success': False, 'message': 'Para compromisso do tipo Prazo, informe fórum de competência, número do processo, tipo de prazo e data de publicação'}), 400
            try:
                dias_uteis_prazo = int(dias_uteis_prazo_raw)
            except Exception:
                return jsonify({'success': False, 'message': 'Dias úteis do prazo deve ser um número entre 1 e 25'}), 400
            if dias_uteis_prazo < 1 or dias_uteis_prazo > 25:
                return jsonify({'success': False, 'message': 'Dias úteis do prazo deve estar entre 1 e 25'}), 400

            try:
                data_base = datetime.strptime(data_publicacao, '%Y-%m-%d').date()
            except Exception:
                return jsonify({'success': False, 'message': 'Data de publicação inválida'}), 400

            dias_restantes = dias_uteis_prazo
            data_vencimento = data_base
            while dias_restantes > 0:
                data_vencimento += timedelta(days=1)
                if data_vencimento.weekday() < 5:
                    dias_restantes -= 1
            data = data_vencimento.isoformat()
        elif not data:
            return jsonify({'success': False, 'message': 'Data é obrigatória para este tipo de compromisso'}), 400

        if tipo == 'Audiência':
            if tipo_audiencia not in {'Instrução', 'Conciliação'}:
                return jsonify({'success': False, 'message': 'Para Audiência, selecione um tipo de audiência válido'}), 400
            if formato_audiencia not in {'Presencial', 'Virtual'}:
                return jsonify({'success': False, 'message': 'Para Audiência, selecione se será presencial ou virtual'}), 400
            if formato_audiencia == 'Presencial':
                if not hora or not (dados.get('local') or '').strip():
                    return jsonify({'success': False, 'message': 'Para audiência presencial, informe hora e local'}), 400
                link_reuniao_virtual = ''
            else:
                if not link_reuniao_virtual:
                    return jsonify({'success': False, 'message': 'Para audiência virtual, informe o link da reunião'}), 400
                hora = ''
                dados['local'] = ''
        else:
            tipo_audiencia = ''
            formato_audiencia = ''
            link_reuniao_virtual = ''

        db = get_db()
        atualizacoes = {
            'titulo': titulo,
            'tipo': tipo,
            'data': data,
            'hora': hora,
            'status': (dados.get('status') or 'Agendado').strip(),
            'cliente_id': (dados.get('cliente_id') or '').strip(),
            'cliente_nome': (dados.get('cliente_nome') or '').strip(),
            'local': (dados.get('local') or '').strip() if not (tipo == 'Audiência' and formato_audiencia == 'Virtual') else '',
            'observacoes': (dados.get('observacoes') or '').strip(),
            'forum_competencia': forum_competencia,
            'numero_processo': numero_processo,
            'tipo_prazo': tipo_prazo if tipo == 'Prazo' else '',
            'data_publicacao': data_publicacao if tipo == 'Prazo' else '',
            'dias_uteis_prazo': dias_uteis_prazo if tipo == 'Prazo' else None,
            'tipo_audiencia': tipo_audiencia if tipo == 'Audiência' else '',
            'formato_audiencia': formato_audiencia if tipo == 'Audiência' else '',
            'link_reuniao_virtual': link_reuniao_virtual if (tipo == 'Audiência' and formato_audiencia == 'Virtual') else '',
            'updated_at': datetime.utcnow()
        }

        resultado = db['agenda'].update_one({'_id': obj_id}, {'$set': atualizacoes})
        if resultado.matched_count == 0:
            return jsonify({'success': False, 'message': 'Compromisso não encontrado'}), 404

        return jsonify({'success': True, 'message': 'Compromisso atualizado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/agenda/<compromisso_id>/deletar', methods=['DELETE'])
@login_required
def deletar_compromisso_agenda(compromisso_id):
    try:
        try:
            obj_id = ObjectId(compromisso_id)
        except Exception:
            return jsonify({'success': False, 'message': 'ID inválido'}), 400

        db = get_db()
        resultado = db['agenda'].delete_one({'_id': obj_id})
        if resultado.deleted_count == 0:
            return jsonify({'success': False, 'message': 'Compromisso não encontrado'}), 404
        return jsonify({'success': True, 'message': 'Compromisso removido com sucesso!'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500




@main_bp.route('/api/advogados/novo', methods=['POST'])
@login_required
def adicionar_advogado():
    try:
        dados = request.get_json() or {}
        nome = dados.get('nome', '').strip()
        oab = dados.get('oab', '').strip().upper()
        tipo = tipo_usuario_canonico(dados.get('tipo', 'Advogado'))
        email = dados.get('email', '').strip()
        telefone = dados.get('telefone', '').strip()
        endereco_profissional = dados.get('endereco_profissional', '').strip()
        usuario = dados.get('usuario', '').strip().lower()
        senha = dados.get('senha', '').strip()

        if not nome or not usuario or not senha:
            return jsonify({'success': False, 'message': 'Nome, usuário e senha são obrigatórios'}), 400

        if tipo == 'Advogado' and not oab:
            return jsonify({'success': False, 'message': 'OAB é obrigatório para usuário do tipo Advogado'}), 400

        db = get_db()
        # Verifica duplicidade por OAB entre ativos
        if oab and db['advogados'].find_one({'oab': oab}):
            return jsonify({'success': False, 'message': 'OAB já cadastrado'}), 400
        if db['advogados'].find_one({'usuario': usuario}):
            return jsonify({'success': False, 'message': 'Usuário já cadastrado'}), 400

        doc = {
            'nome': nome,
            'tipo': tipo,
            'email': email,
            'telefone': telefone,
            'endereco': endereco_profissional,
            'endereco_profissional': endereco_profissional,
            'usuario': usuario,
            'senha_hash': generate_password_hash(senha),
            'created_at': datetime.utcnow()
        }
        if tipo == 'Advogado':
            doc['oab'] = oab

        resultado = db['advogados'].insert_one(doc)
        return jsonify({'success': True, 'message': 'Usuário cadastrado com sucesso!', 'advogado_id': str(resultado.inserted_id)}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@main_bp.route('/api/advogados/<advogado_id>/atualizar', methods=['PUT'])
@login_required
def atualizar_advogado(advogado_id):
    try:
        try:
            obj_id = ObjectId(advogado_id)
        except:
            return jsonify({'success': False, 'message': 'ID inválido'}), 400

        dados = request.get_json() or {}
        db = get_db()
        advogado = db['advogados'].find_one({'_id': obj_id})
        if not advogado:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404

        usuario_novo = (dados.get('usuario', advogado.get('usuario', '')) or '').strip().lower()
        if not usuario_novo:
            return jsonify({'success': False, 'message': 'Usuário é obrigatório'}), 400

        existente = db['advogados'].find_one({'usuario': usuario_novo, '_id': {'$ne': obj_id}})
        if existente:
            return jsonify({'success': False, 'message': 'Usuário já cadastrado'}), 400

        atualizacoes = {
            'nome': dados.get('nome', advogado.get('nome')),
            'tipo': tipo_usuario_canonico(dados.get('tipo', advogado.get('tipo', 'Advogado'))),
            'email': dados.get('email', advogado.get('email', '')),
            'telefone': dados.get('telefone', advogado.get('telefone', '')),
            'endereco': dados.get('endereco_profissional', advogado.get('endereco', '')),
            'endereco_profissional': dados.get('endereco_profissional', advogado.get('endereco_profissional', advogado.get('endereco', ''))),
            'usuario': usuario_novo
        }

        oab_novo = (dados.get('oab', advogado.get('oab', '')) or '').strip().upper()
        if atualizacoes['tipo'] == 'Advogado' and not oab_novo:
            return jsonify({'success': False, 'message': 'OAB é obrigatório para usuário do tipo Advogado'}), 400

        if oab_novo:
            existente_oab = db['advogados'].find_one({'oab': oab_novo, '_id': {'$ne': obj_id}})
            if existente_oab:
                return jsonify({'success': False, 'message': 'OAB já cadastrado'}), 400

        senha_nova = (dados.get('senha') or '').strip()
        if senha_nova:
            atualizacoes['senha_hash'] = generate_password_hash(senha_nova)

        if atualizacoes['tipo'] == 'Advogado':
            atualizacoes['oab'] = oab_novo
            db['advogados'].update_one({'_id': obj_id}, {'$set': atualizacoes})
        else:
            db['advogados'].update_one({'_id': obj_id}, {'$set': atualizacoes, '$unset': {'oab': ''}})

        return jsonify({'success': True, 'message': 'Usuário atualizado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


@main_bp.route('/api/advogados/<advogado_id>/deletar', methods=['DELETE'])
@login_required
def deletar_advogado_api(advogado_id):
    try:
        try:
            obj_id = ObjectId(advogado_id)
        except:
            return jsonify({'success': False, 'message': 'ID inválido'}), 400

        db = get_db()
        resultado = db['advogados'].delete_one({'_id': obj_id})
        if resultado.deleted_count == 0:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        return jsonify({'success': True, 'message': 'Usuário removido com sucesso!'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500



@main_bp.route('/api/contratos/lista', methods=['GET'])
@login_required
def lista_contratos():
    """Retorna lista de contratos em JSON para popular tabela"""
    try:
        db = get_db()
        contratos = list(db['contratos'].find().sort('data', -1)) if 'contratos' in db.list_collection_names() else []
        for c in contratos:
            if '_id' in c:
                c['_id'] = str(c['_id'])
            # converte cliente_id para string se for ObjectId
            if isinstance(c.get('cliente_id'), ObjectId):
                c['cliente_id'] = str(c['cliente_id'])
        return jsonify({'success': True, 'contratos': contratos}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/contratos/novo', methods=['POST'])
@login_required
def adicionar_contrato():
    """Cria um novo contrato (suporta multipart/form-data com arquivo)."""
    try:
        content_type = request.content_type or ''
        dados = {}
        arquivo = None
        if 'multipart/form-data' in content_type:
            form = request.form
            dados['cliente_id'] = form.get('cliente_id', '').strip()
            dados['tipo'] = form.get('tipo', '').strip()
            dados['subtipo'] = form.get('subtipo', '').strip()
            dados['subtipo_outros'] = form.get('subtipo_outros', '').strip()
            dados['data'] = form.get('data', '').strip()
            arquivo = request.files.get('arquivo')
            if arquivo and arquivo.filename:
                upload_dir = os.path.join('static', 'uploads', 'contratos')
                os.makedirs(upload_dir, exist_ok=True)
                filename = secure_filename(arquivo.filename)
                prefix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                filename = f"{prefix}_{filename}"
                caminho = os.path.join(upload_dir, filename)
                arquivo.save(caminho)
                dados['arquivo'] = f"uploads/contratos/{filename}"
        else:
            dados = request.get_json() or {}

        if not dados.get('cliente_id'):
            return jsonify({'success': False, 'message': 'cliente_id é obrigatório'}), 400

        db = get_db()
        try:
            cliente_obj = ObjectId(dados['cliente_id'])
        except Exception:
            return jsonify({'success': False, 'message': 'ID de cliente inválido'}), 400

        cliente = db['clientes'].find_one({'_id': cliente_obj})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        contrato_doc = {
            'cliente_id': cliente_obj,
            'cliente_nome': cliente.get('nome'),
            'tipo': dados.get('tipo', ''),
            'subtipo': dados.get('subtipo', ''),
            'subtipo_outros': dados.get('subtipo_outros', ''),
            'data': dados.get('data', ''),
            'arquivo': dados.get('arquivo', None),
            'created_at': datetime.utcnow()
        }

        resultado = db['contratos'].insert_one(contrato_doc)
        return jsonify({'success': True, 'message': 'Contrato criado', 'id': str(resultado.inserted_id)}), 201

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/contratos/<contrato_id>/atualizar', methods=['PUT'])
@login_required
def atualizar_contrato(contrato_id):
    """Atualiza um contrato existente (suporta multipart/form-data com arquivo)."""
    try:
        try:
            obj_id = ObjectId(contrato_id)
        except Exception:
            return jsonify({'success': False, 'message': 'ID de contrato inválido'}), 400

        db = get_db()
        contrato = db['contratos'].find_one({'_id': obj_id})
        if not contrato:
            return jsonify({'success': False, 'message': 'Contrato não encontrado'}), 404

        content_type = request.content_type or ''
        dados = {}

        if 'multipart/form-data' in content_type:
            form = request.form
            dados['cliente_id'] = form.get('cliente_id', '').strip()
            dados['tipo'] = form.get('tipo', '').strip()
            dados['subtipo'] = form.get('subtipo', '').strip()
            dados['subtipo_outros'] = form.get('subtipo_outros', '').strip()
            dados['data'] = form.get('data', '').strip()

            arquivo = request.files.get('arquivo')
            if arquivo and arquivo.filename:
                upload_dir = os.path.join('static', 'uploads', 'contratos')
                os.makedirs(upload_dir, exist_ok=True)
                filename = secure_filename(arquivo.filename)
                prefix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                filename = f"{prefix}_{filename}"
                caminho = os.path.join(upload_dir, filename)
                arquivo.save(caminho)
                dados['arquivo'] = f"uploads/contratos/{filename}"
        else:
            dados = request.get_json() or {}

        cliente_id_raw = (dados.get('cliente_id') or '').strip()
        if not cliente_id_raw:
            cliente_id_raw = str(contrato.get('cliente_id')) if contrato.get('cliente_id') else ''

        if not cliente_id_raw:
            return jsonify({'success': False, 'message': 'cliente_id é obrigatório'}), 400

        try:
            cliente_obj = ObjectId(cliente_id_raw)
        except Exception:
            return jsonify({'success': False, 'message': 'ID de cliente inválido'}), 400

        cliente = db['clientes'].find_one({'_id': cliente_obj})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        atualizacoes = {
            'cliente_id': cliente_obj,
            'cliente_nome': cliente.get('nome', ''),
            'tipo': (dados.get('tipo') or contrato.get('tipo') or '').strip(),
            'subtipo': (dados.get('subtipo') or contrato.get('subtipo') or '').strip(),
            'subtipo_outros': (dados.get('subtipo_outros') or contrato.get('subtipo_outros') or '').strip(),
            'data': (dados.get('data') or contrato.get('data') or '').strip(),
            'updated_at': datetime.utcnow()
        }

        if 'arquivo' in dados:
            atualizacoes['arquivo'] = dados.get('arquivo')

        db['contratos'].update_one({'_id': obj_id}, {'$set': atualizacoes, '$unset': {'referencia': ''}})
        return jsonify({'success': True, 'message': 'Contrato atualizado com sucesso!'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/contratos/<contrato_id>/deletar', methods=['DELETE'])
@login_required
def deletar_contrato(contrato_id):
    """Remove um contrato existente."""
    try:
        try:
            obj_id = ObjectId(contrato_id)
        except Exception:
            return jsonify({'success': False, 'message': 'ID de contrato inválido'}), 400

        db = get_db()
        resultado = db['contratos'].delete_one({'_id': obj_id})
        if resultado.deleted_count == 0:
            return jsonify({'success': False, 'message': 'Contrato não encontrado'}), 404

        return jsonify({'success': True, 'message': 'Contrato removido com sucesso!'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500



@main_bp.route('/procuracao')
@login_required
def procurar_procuracao():
    """
    Rota: GET /procuracao
    Página de procurações (template pode ser vazio por enquanto)
    """
    db = get_db()

    # Lista de clientes para select (ativos)
    clientes = list(db['clientes'].find({'ativo': True}).sort('nome', 1)) if 'clientes' in db.list_collection_names() else []
    for c in clientes:
        if '_id' in c:
            c['_id'] = str(c['_id'])

    # Tipos de procuração pré-definidos
    tipos = ['Geral', 'Específica', 'Judicial', 'Extrajudicial']

    # Lista de advogados para select (somente usuários do tipo Advogado)
    # Faz a filtragem em Python para cobrir variações antigas de capitalização/acentos.
    usuarios = list(db['advogados'].find().sort('nome', 1)) if 'advogados' in db.list_collection_names() else []
    advogados = []
    for usuario_doc in usuarios:
        tipo_canonico = tipo_usuario_canonico(usuario_doc.get('tipo'))
        if tipo_canonico == 'Advogado':
            advogados.append(usuario_doc)
    for a in advogados:
        if '_id' in a:
            a['_id'] = str(a['_id'])

    # Folhas timbradas: procura arquivos em static/folhas/
    import os
    base_dir = os.path.dirname(os.path.dirname(__file__))
    folhas_dir = os.path.join(base_dir, 'static', 'folhas')
    folhas = []
    try:
        if os.path.isdir(folhas_dir):
            for fn in os.listdir(folhas_dir):
                if fn.lower().endswith(('.pdf', '.jpg', '.png')):
                    folhas.append(fn)
    except Exception:
        folhas = []

    return render_template('procuracao.html', clientes=clientes, tipos=tipos, folhas=folhas, advogados=advogados)


def modelos_procuracao_padrao():
    return [
        {
            'id': 'padrao-geral-civel',
            'nome': 'Padrão - Geral Cível',
            'tipo': 'Geral',
            'fonte': 'Helvetica',
            'tamanho_fonte': 12,
            'texto': 'Concede poderes gerais para representação do outorgante perante órgãos públicos e privados, inclusive para assinar documentos, firmar acordos e praticar atos necessários ao cumprimento do mandato.'
        },
        {
            'id': 'padrao-judicial-completo',
            'nome': 'Padrão - Judicial Completo',
            'tipo': 'Judicial',
            'fonte': 'Helvetica',
            'tamanho_fonte': 12,
            'texto': 'Concede poderes para foro em geral, com cláusula ad judicia et extra, podendo propor ações, contestar, recorrer, transigir, receber e dar quitação, além de praticar todos os atos processuais cabíveis.'
        },
        {
            'id': 'padrao-extrajudicial-cartorio',
            'nome': 'Padrão - Extrajudicial/Cartório',
            'tipo': 'Extrajudicial',
            'fonte': 'Helvetica',
            'tamanho_fonte': 12,
            'texto': 'Concede poderes para representação em cartórios, bancos e repartições, inclusive para requerer certidões, reconhecer firmas, autenticar documentos, assinar termos e receber documentos em nome do outorgante.'
        }
    ]


@main_bp.route('/api/procuracoes/modelos', methods=['GET'])
@login_required
def listar_modelos_procuracao():
    try:
        db = get_db()
        modelos_custom = []
        if 'procuracao_modelos' in db.list_collection_names():
            docs = list(db['procuracao_modelos'].find().sort('nome', 1))
            for doc in docs:
                modelos_custom.append({
                    'id': str(doc.get('_id')),
                    'nome': doc.get('nome', 'Modelo sem nome'),
                    'tipo': doc.get('tipo', ''),
                    'fonte': doc.get('fonte', 'Helvetica'),
                    'tamanho_fonte': int(doc.get('tamanho_fonte', 12) or 12),
                    'texto': doc.get('texto', ''),
                    'padrao': False
                })

        modelos_padrao = []
        for item in modelos_procuracao_padrao():
            modelos_padrao.append({
                'id': item['id'],
                'nome': item['nome'],
                'tipo': item.get('tipo', ''),
                'fonte': item.get('fonte', 'Helvetica'),
                'tamanho_fonte': int(item.get('tamanho_fonte', 12) or 12),
                'texto': item.get('texto', ''),
                'padrao': True
            })

        return jsonify({'success': True, 'modelos': modelos_padrao + modelos_custom}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao listar modelos: {str(e)}'}), 500


@main_bp.route('/api/procuracoes/modelos', methods=['POST'])
@login_required
def salvar_modelo_procuracao():
    try:
        dados = request.get_json() or {}
        nome = (dados.get('nome') or '').strip()
        texto = (dados.get('texto') or '').strip()
        fonte = (dados.get('fonte') or 'Helvetica').strip()
        tamanho_fonte_raw = dados.get('tamanho_fonte', 12)
        try:
            tamanho_fonte = int(tamanho_fonte_raw)
        except Exception:
            tamanho_fonte = 12
        if tamanho_fonte < 8 or tamanho_fonte > 24:
            tamanho_fonte = 12
        fontes_permitidas = {
            'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique',
            'Times-Roman', 'Times-Bold', 'Times-Italic',
            'Courier', 'Courier-Bold', 'Courier-Oblique',
            'Georgia', 'Georgia-Bold', 'Georgia-Italic'
        }
        if fonte not in fontes_permitidas:
            fonte = 'Helvetica'

        if not nome:
            return jsonify({'success': False, 'message': 'Nome do modelo é obrigatório'}), 400

        if not texto:
            return jsonify({'success': False, 'message': 'Texto do modelo é obrigatório'}), 400

        db = get_db()

        existente = db['procuracao_modelos'].find_one({'nome': {'$regex': f'^{re.escape(nome)}$', '$options': 'i'}})
        if existente:
            return jsonify({'success': False, 'message': 'Já existe um modelo com esse nome'}), 400

        documento = {
            'nome': nome,
            'tipo': '',
            'fonte': fonte,
            'tamanho_fonte': tamanho_fonte,
            'texto': texto,
            'criado_por': session.get('usuario_logado', 'sistema'),
            'created_at': datetime.utcnow()
        }

        resultado = db['procuracao_modelos'].insert_one(documento)

        return jsonify({
            'success': True,
            'message': 'Modelo salvo com sucesso',
            'modelo': {
                'id': str(resultado.inserted_id),
                'nome': nome,
                'tipo': '',
                'fonte': fonte,
                'tamanho_fonte': tamanho_fonte,
                'texto': texto,
                'padrao': False
            }
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao salvar modelo: {str(e)}'}), 500


@main_bp.route('/api/procuracoes/modelos/<modelo_id>', methods=['PUT'])
@login_required
def atualizar_modelo_procuracao(modelo_id):
    try:
        try:
            obj_id = ObjectId(modelo_id)
        except Exception:
            return jsonify({'success': False, 'message': 'Somente modelos personalizados podem ser editados'}), 400

        dados = request.get_json() or {}
        nome = (dados.get('nome') or '').strip()
        texto = (dados.get('texto') or '').strip()
        fonte = (dados.get('fonte') or 'Helvetica').strip()
        tamanho_fonte_raw = dados.get('tamanho_fonte', 12)
        try:
            tamanho_fonte = int(tamanho_fonte_raw)
        except Exception:
            tamanho_fonte = 12
        if tamanho_fonte < 8 or tamanho_fonte > 24:
            tamanho_fonte = 12
        fontes_permitidas = {
            'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique',
            'Times-Roman', 'Times-Bold', 'Times-Italic',
            'Courier', 'Courier-Bold', 'Courier-Oblique',
            'Georgia', 'Georgia-Bold', 'Georgia-Italic'
        }
        if fonte not in fontes_permitidas:
            fonte = 'Helvetica'

        if not nome:
            return jsonify({'success': False, 'message': 'Nome do modelo é obrigatório'}), 400

        if not texto:
            return jsonify({'success': False, 'message': 'Texto do modelo é obrigatório'}), 400

        db = get_db()
        modelo = db['procuracao_modelos'].find_one({'_id': obj_id})
        if not modelo:
            return jsonify({'success': False, 'message': 'Modelo não encontrado'}), 404

        duplicado = db['procuracao_modelos'].find_one({
            '_id': {'$ne': obj_id},
            'nome': {'$regex': f'^{re.escape(nome)}$', '$options': 'i'}
        })
        if duplicado:
            return jsonify({'success': False, 'message': 'Já existe um modelo com esse nome'}), 400

        db['procuracao_modelos'].update_one(
            {'_id': obj_id},
            {'$set': {
                'nome': nome,
                'tipo': '',
                'fonte': fonte,
                'tamanho_fonte': tamanho_fonte,
                'texto': texto,
                'updated_at': datetime.utcnow(),
                'atualizado_por': session.get('usuario_logado', 'sistema')
            }}
        )

        return jsonify({'success': True, 'message': 'Modelo atualizado com sucesso'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao atualizar modelo: {str(e)}'}), 500


@main_bp.route('/api/procuracoes/modelos/<modelo_id>', methods=['DELETE'])
@login_required
def excluir_modelo_procuracao(modelo_id):
    try:
        try:
            obj_id = ObjectId(modelo_id)
        except Exception:
            return jsonify({'success': False, 'message': 'Somente modelos personalizados podem ser excluídos'}), 400

        db = get_db()
        resultado = db['procuracao_modelos'].delete_one({'_id': obj_id})
        if resultado.deleted_count == 0:
            return jsonify({'success': False, 'message': 'Modelo não encontrado'}), 404

        return jsonify({'success': True, 'message': 'Modelo excluído com sucesso'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao excluir modelo: {str(e)}'}), 500



@main_bp.route('/api/procuracoes/novo', methods=['POST'])
@login_required
def adicionar_procuracao():
    """
    Rota: POST /api/procuracoes/novo
    Insere uma nova procuração no banco (registro simples)
    """
    try:
        dados = request.get_json()
        titulo = dados.get('titulo')
        cliente_id = dados.get('cliente_id')
        tipo = dados.get('tipo')
        folha = dados.get('folha')
        cidade_procuracao = dados.get('cidade')
        advogado_id = dados.get('advogado_id')
        data_str = dados.get('data')

        if not titulo or not cliente_id or not tipo:
            return jsonify({'success': False, 'message': 'Campos obrigatórios faltando'}), 400

        db = get_db()

        # Converte cliente_id para ObjectId e valida
        try:
            cliente_obj_id = ObjectId(cliente_id)
        except Exception:
            return jsonify({'success': False, 'message': 'ID de cliente inválido'}), 400

        cliente = db['clientes'].find_one({'_id': cliente_obj_id})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        advogado_nome = None
        advogado_oab = None
        if advogado_id:
            try:
                adv_obj = ObjectId(advogado_id)
                advogado = db['advogados'].find_one({'_id': adv_obj})
                if advogado:
                    advogado_nome = advogado.get('nome')
                    advogado_oab = advogado.get('oab')
            except Exception:
                pass

        # Monta documento de procuração
        procuracao = {
            'titulo': titulo,
            'cliente_id': cliente_obj_id,
            'cliente_nome': cliente.get('nome'),
            'tipo': tipo,
            'folha': folha,
            'cidade': cidade_procuracao,
            'advogado_id': advogado_id,
            'advogado_nome': advogado_nome,
            'advogado_oab': advogado_oab,
            'data': data_str or datetime.utcnow().strftime('%Y-%m-%d'),
            'created_at': datetime.utcnow()
        }

        resultado = db['procuracoes'].insert_one(procuracao)

        return jsonify({'success': True, 'message': 'Procuração criada', 'id': str(resultado.inserted_id)}), 201

    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500



@main_bp.route('/api/folhas/upload', methods=['POST'])
@login_required
def upload_folha():
    """Upload de folha timbrada para static/folhas"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Arquivo não enviado'}), 400
        f = request.files['file']
        if f.filename == '':
            return jsonify({'success': False, 'message': 'Nome de arquivo inválido'}), 400

        extensoes_permitidas = {'.pdf', '.jpg', '.jpeg', '.png', '.webp', '.doc', '.docx'}
        mimes_permitidos = {
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/webp',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        tamanho_maximo_bytes = 10 * 1024 * 1024  # 10MB

        filename = secure_filename(f.filename)
        if not filename:
            return jsonify({'success': False, 'message': 'Nome de arquivo inválido'}), 400

        ext = os.path.splitext(filename)[1].lower()
        if ext not in extensoes_permitidas:
            return jsonify({'success': False, 'message': 'Extensão inválida. Use PDF, JPG, JPEG, PNG, WEBP, DOC ou DOCX'}), 400

        if f.mimetype and f.mimetype.lower() not in mimes_permitidos:
            return jsonify({'success': False, 'message': 'Tipo MIME inválido para upload'}), 400

        try:
            f.stream.seek(0, os.SEEK_END)
            tamanho_arquivo = f.stream.tell()
            f.stream.seek(0)
        except Exception:
            tamanho_arquivo = 0

        if tamanho_arquivo <= 0:
            return jsonify({'success': False, 'message': 'Arquivo inválido ou vazio'}), 400

        if tamanho_arquivo > tamanho_maximo_bytes:
            return jsonify({'success': False, 'message': 'Arquivo muito grande. Tamanho máximo: 10MB'}), 400

        cabecalho = f.stream.read(32)
        f.stream.seek(0)

        assinatura_valida = False
        if ext in {'.jpg', '.jpeg'}:
            assinatura_valida = cabecalho.startswith(b'\xff\xd8\xff')
        elif ext == '.png':
            assinatura_valida = cabecalho.startswith(b'\x89PNG\r\n\x1a\n')
        elif ext == '.webp':
            assinatura_valida = cabecalho.startswith(b'RIFF') and cabecalho[8:12] == b'WEBP'
        elif ext == '.pdf':
            assinatura_valida = cabecalho.startswith(b'%PDF-')
        elif ext == '.docx':
            assinatura_valida = cabecalho.startswith(b'PK\x03\x04') or cabecalho.startswith(b'PK\x05\x06') or cabecalho.startswith(b'PK\x07\x08')
        elif ext == '.doc':
            assinatura_valida = cabecalho.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1')

        if not assinatura_valida:
            return jsonify({'success': False, 'message': 'Conteúdo do arquivo não corresponde à extensão informada'}), 400

        base_dir = os.path.dirname(os.path.dirname(__file__))
        folhas_dir = os.path.join(base_dir, 'static', 'folhas')
        os.makedirs(folhas_dir, exist_ok=True)

        base_nome = os.path.splitext(filename)[0]
        filename = f"{base_nome}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{ext}"
        save_path = os.path.join(folhas_dir, filename)
        f.save(save_path)

        name_lower = filename.lower()
        # Se for .docx ou .doc, tentamos converter para PDF
        if name_lower.endswith('.docx') or name_lower.endswith('.doc'):
            pdf_filename = os.path.splitext(filename)[0] + '.pdf'
            pdf_path = os.path.join(folhas_dir, pdf_filename)

            # 1) Tenta docx2pdf (usa MS Word no Windows)
            try:
                from docx2pdf import convert as docx2pdf_convert
                try:
                    docx2pdf_convert(save_path, pdf_path)
                    filename = pdf_filename
                    # opcional: remove o .docx original? Mantemos ambos por segurança.
                except Exception:
                    # se a conversão falhar, seguimos para fallback
                    pass
            except Exception:
                pass

            # 2) Fallback: extrair texto com python-docx (ou por extração manual) e gerar PDF com reportlab
            if not os.path.isfile(pdf_path):
                try:
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.lib.pagesizes import A4
                    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
                    from reportlab.lib.units import mm
                    from io import BytesIO
                except Exception as e:
                    return jsonify({'success': False, 'message': f'Dependência ausente para geração de PDF: {e}'}), 500

                paragraphs = []
                # Tenta python-docx primeiro
                try:
                    from docx import Document
                    docx = Document(save_path)
                    paragraphs = [p.text for p in docx.paragraphs if p.text and p.text.strip()]
                except Exception:
                    # fallback manual: extrair document.xml do .docx (se possível)
                    try:
                        import zipfile, xml.etree.ElementTree as ET
                        with zipfile.ZipFile(save_path) as zf:
                            with zf.open('word/document.xml') as docxml:
                                tree = ET.parse(docxml)
                                root = tree.getroot()
                                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                                for para in root.findall('.//w:p', ns):
                                    texts = [t.text for t in para.findall('.//w:t', ns) if t.text]
                                    if texts:
                                        paragraphs.append(''.join(texts))
                    except Exception:
                        paragraphs = []

                # Gera PDF a partir dos parágrafos extraídos
                try:
                    pdf_io = BytesIO()
                    styles = getSampleStyleSheet()
                    body_style = ParagraphStyle('Body', parent=styles['Normal'], alignment=TA_JUSTIFY, fontSize=12, leading=18)
                    doc = SimpleDocTemplate(pdf_io, pagesize=A4, leftMargin=25*mm, rightMargin=25*mm, topMargin=25*mm, bottomMargin=25*mm)
                    flow = []
                    for p in paragraphs:
                        flow.append(Paragraph((p or '').replace('\t', ' '), body_style))
                        flow.append(Spacer(1, 4*mm))
                    # Se não houver parágrafos, cria um PDF simples com o nome do arquivo
                    if not flow:
                        flow = [Paragraph('Documento convertido', body_style), Spacer(1, 4*mm)]
                    doc.build(flow)
                    pdf_io.seek(0)
                    with open(pdf_path, 'wb') as outfh:
                        outfh.write(pdf_io.read())
                    filename = pdf_filename
                except Exception as e:
                    return jsonify({'success': False, 'message': f'Não foi possível converter .doc(x) para PDF: {e}'}), 500

        return jsonify({'success': True, 'filename': filename}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/api/procuracoes/gerar', methods=['POST'])
@login_required
def gerar_procuracao_automatica():
    """Gera uma procuração automaticamente usando dados do cliente e retorna o PDF sem salvar no banco."""
    try:
        dados = request.get_json() or {}
        cliente_id = dados.get('cliente_id')
        tipo = dados.get('tipo')
        folha = dados.get('folha')  # opcional
        advogado_id = dados.get('advogado_id')
        texto_adicional = (dados.get('texto_adicional') or '').strip()
        fonte_solicitada = (dados.get('fonte') or 'Helvetica').strip()
        tamanho_fonte_raw = dados.get('tamanho_fonte', 12)
        try:
            tamanho_fonte = int(tamanho_fonte_raw)
        except Exception:
            tamanho_fonte = 12
        if tamanho_fonte < 8 or tamanho_fonte > 24:
            tamanho_fonte = 12

        def registrar_fontes_georgia():
            try:
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                registradas = set(pdfmetrics.getRegisteredFontNames())
                if {'Georgia', 'Georgia-Bold', 'Georgia-Italic'}.issubset(registradas):
                    return True

                fontes_dir = os.path.join('C:\\', 'Windows', 'Fonts')
                arquivo_regular = os.path.join(fontes_dir, 'georgia.ttf')
                arquivo_bold = os.path.join(fontes_dir, 'georgiab.ttf')
                arquivo_italic = os.path.join(fontes_dir, 'georgiai.ttf')

                if not (os.path.isfile(arquivo_regular) and os.path.isfile(arquivo_bold) and os.path.isfile(arquivo_italic)):
                    return False

                if 'Georgia' not in registradas:
                    pdfmetrics.registerFont(TTFont('Georgia', arquivo_regular))
                if 'Georgia-Bold' not in registradas:
                    pdfmetrics.registerFont(TTFont('Georgia-Bold', arquivo_bold))
                if 'Georgia-Italic' not in registradas:
                    pdfmetrics.registerFont(TTFont('Georgia-Italic', arquivo_italic))
                return True
            except Exception:
                return False

        mapa_fontes = {
            'helvetica': ('Helvetica', 'Helvetica-Bold'),
            'helvetica-bold': ('Helvetica-Bold', 'Helvetica-Bold'),
            'helvetica-oblique': ('Helvetica-Oblique', 'Helvetica-Bold'),
            'times-roman': ('Times-Roman', 'Times-Bold'),
            'times-bold': ('Times-Bold', 'Times-Bold'),
            'times-italic': ('Times-Italic', 'Times-Bold'),
            'times': ('Times-Roman', 'Times-Bold'),
            'times new roman': ('Times-Roman', 'Times-Bold'),
            'courier': ('Courier', 'Courier-Bold'),
            'courier-bold': ('Courier-Bold', 'Courier-Bold'),
            'courier-oblique': ('Courier-Oblique', 'Courier-Bold'),
            'courier new': ('Courier', 'Courier-Bold'),
            'georgia': ('Georgia', 'Georgia-Bold'),
            'georgia-bold': ('Georgia-Bold', 'Georgia-Bold'),
            'georgia-italic': ('Georgia-Italic', 'Georgia-Bold')
        }
        fonte_normal, fonte_titulo = mapa_fontes.get(fonte_solicitada.lower(), ('Helvetica', 'Helvetica-Bold'))
        if fonte_normal.startswith('Georgia') and not registrar_fontes_georgia():
            fonte_normal, fonte_titulo = ('Times-Roman', 'Times-Bold')

        if not cliente_id or not tipo:
            return jsonify({'success': False, 'message': 'cliente_id e tipo são obrigatórios'}), 400

        try:
            cliente_obj_id = ObjectId(cliente_id)
        except Exception:
            return jsonify({'success': False, 'message': 'ID de cliente inválido'}), 400

        db = get_db()
        cliente = db['clientes'].find_one({'_id': cliente_obj_id})
        if not cliente:
            return jsonify({'success': False, 'message': 'Cliente não encontrado'}), 404

        # Dados para a procuração
        titulo = f'Procuração - {tipo}'
        cliente_nome = cliente.get('nome', '')
        advogado_nome = None
        advogado_oab = None
        if advogado_id:
            try:
                adv_obj = ObjectId(advogado_id)
                advogado = db['advogados'].find_one({'_id': adv_obj})
                if advogado:
                    advogado_nome = advogado.get('nome')
                    advogado_oab = advogado.get('oab')
            except Exception:
                advogado_nome = None
                advogado_oab = None
        data = dados.get('data')
        # Se não informou data, pega a data do sistema e formata em pt-BR
        if not data:
            def formatar_data_ptbr(dt):
                meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
                return f"{dt.day} de {meses[dt.month-1]} de {dt.year}"

            agora = datetime.now()
            data = formatar_data_ptbr(agora)

        # Gera PDF em memória com reportlab (texto em tom formal jurídico)
        try:
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
        except Exception as e:
            return jsonify({'success': False, 'message': f'Dependência ausente: {e}'}), 500

        from io import BytesIO
        overlay_io = BytesIO()

        # Estilos (ajustados para formato jurídico: mais espaçamento e recuo de primeira linha)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title', parent=styles['Heading1'], alignment=TA_CENTER,
            fontName=fonte_titulo, fontSize=min(max(tamanho_fonte + 6, 14), 28), leading=min(max(tamanho_fonte + 10, 18), 34), spaceAfter=12
        )
        body_style = ParagraphStyle(
            'Body', parent=styles['Normal'], alignment=TA_JUSTIFY,
            fontName=fonte_normal, fontSize=tamanho_fonte, leading=tamanho_fonte + 8, firstLineIndent=18, spaceBefore=6, spaceAfter=12
        )
        small_style = ParagraphStyle(
            'Small', parent=styles['Normal'], alignment=TA_JUSTIFY,
            fontName=fonte_normal, fontSize=max(tamanho_fonte - 1, 9), leading=max(tamanho_fonte + 4, 13), spaceBefore=6, spaceAfter=8
        )

        # Estilo para assinatura (centralizado)
        sig_style = ParagraphStyle('Signature', parent=small_style, alignment=TA_CENTER)

        # Informações do outorgante (cidade pode ser sobrescrita pelo parâmetro enviado)
        endereco = cliente.get('endereco', '')
        cidade = dados.get('cidade') or cliente.get('cidade', '')
        uf = cliente.get('uf', '')
        cpf_cnpj = cliente.get('cpf_cnpj', '')

        # Texto formal jurídico conforme tipo de procuração
        poderes_map = {
            'Geral': 'conferindo amplos, gerais e ilimitados poderes para me representar em juízo ou fora dele, ativa e passivamente, podendo receber citações e intimações, transigir, firmar compromissos e acordos, substabelecer, assinar quaisquer documentos, requerer certidões e praticar todos os atos necessários ao bom e fiel desempenho deste mandato.',
            'Específica': 'conferindo poderes específicos para a prática dos atos relacionados ao assunto indicado pelo outorgante, incluindo assinatura de documentos e representação perante órgãos públicos ou privados, e demais providências necessárias ao fiel cumprimento deste mandato.',
            'Judicial': 'conferindo poderes especiais para o foro judicial, para o ajuizamento, defesa, acompanhamento e solução de demandas, com poderes para receber citações, firmar compromissos, transigir, e praticar todos os atos processuais necessários.',
            'Extrajudicial': 'conferindo poderes para representação extrajudicial perante repartições públicas e privadas, empresas e cartórios, podendo requerer documentos, assinar termos, receber e dar quitação, e praticar os atos necessários no âmbito extrajudicial.'
        }

        texto_poderes = poderes_map.get(tipo, poderes_map['Geral'])

        titulo_paragraph = Paragraph('<b>PROCURAÇÃO</b>', title_style)

        if advogado_nome:
            procurautor_text = f"nomeio e constituo como meu bastante procurador o(a) advogado(a) <b>{advogado_nome}</b>"
            if advogado_oab:
                procurautor_text += f", inscrito(a) na OAB {advogado_oab}"
            procurautor_text += ", a quem confiro, em caráter irrevogável e irretratável, "
        else:
            procurautor_text = "nomeio e constituo como meu bastante procurador o(a) advogado(a) que este instrumento vier a indicar, "

        corpo = (
            f"Pelo presente instrumento particular de procuração, eu, <b>{cliente_nome}</b>, portador(a) do CPF/CNPJ nº <b>{cpf_cnpj}</b>, "
            f"residente e domiciliado(a) à {endereco}, {cidade} - {uf}, doravante designado(a) OUTORGANTE, "
            f"{procurautor_text}{texto_poderes}"
        )

        if texto_adicional:
            texto_adicional_safe = html.escape(texto_adicional).replace('\n', '<br/>')
            corpo += f"<br/><br/>{texto_adicional_safe}"

        corpo_paragraph = Paragraph(corpo, body_style)

        # Cláusula de foro
        clausula_forum = Paragraph(
            'Para dirimir quaisquer questões oriundas deste instrumento, fica eleito o foro da comarca do domicílio do OUTORGANTE, com renúncia a qualquer outro, por mais privilegiado que seja.',
            small_style
        )

        # Assinaturas (centralizada)
        assinatura = Paragraph('<br/>__________________________________<br/>Assinatura do Outorgante', sig_style)

        # Monta documento com espaçamentos compatíveis ao tom jurídico
        # Normaliza data: se vier no formato ISO YYYY-MM-DD, converte para DD/MM/YYYY
        try:
            parsed_dt = datetime.strptime(data, '%Y-%m-%d')
            data_short = parsed_dt.strftime('%d/%m/%Y')
        except Exception:
            data_short = data

        # Parágrafo com cidade + data formatada (centralizado)
        city_date_text = f"{cidade} - {data_short}" if cidade else f"{data_short}"
        city_date_style = ParagraphStyle('CityDate', parent=styles['Normal'], alignment=TA_CENTER, fontName=fonte_normal, fontSize=max(tamanho_fonte - 1, 9), leading=max(tamanho_fonte + 2, 12))
        city_date_paragraph = Paragraph(city_date_text, city_date_style)

        doc = SimpleDocTemplate(overlay_io, pagesize=A4, leftMargin=25*mm, rightMargin=25*mm, topMargin=30*mm, bottomMargin=25*mm)
        flowables = [
            Spacer(1, 20*mm),
            titulo_paragraph,
            Spacer(1, 8*mm),
            corpo_paragraph,
            Spacer(1, 8*mm),
            clausula_forum,
            Spacer(1, 4*mm),
            city_date_paragraph,
            Spacer(1, 12*mm),
            assinatura
        ]

        doc.build(flowables)
        overlay_io.seek(0)

        # Se não houver folha, retornamos apenas o overlay
        try:
            from PyPDF2 import PdfReader, PdfWriter
        except Exception as e:
                    return jsonify({'success': False, 'message': f'Dependência ausente: {e}'}), 500
        # Import adicional para desenho de imagens quando a folha for uma imagem
        try:
            from reportlab.pdfgen import canvas
            width, height = A4
        except Exception:
            # width/height serão definidos a partir de A4 já importado; se falhar, seguimos sem
            width = None
            height = None

        # Se folha informada e for PDF, mescla; se imagem, desenha imagem como fundo e mescla
        base_dir = os.path.dirname(os.path.dirname(__file__))
        folhas_dir = os.path.join(base_dir, 'static', 'folhas')

        final_io = BytesIO()

        # Se nenhuma folha informada, tenta usar a primeira folha disponível na pasta
        if not folha:
            try:
                available = [f for f in os.listdir(folhas_dir) if os.path.isfile(os.path.join(folhas_dir, f))]
                if available:
                    folha = available[0]
            except Exception:
                folha = None

        if folha:
            folha_path = os.path.join(folhas_dir, folha)
            if os.path.isfile(folha_path) and folha.lower().endswith('.pdf'):
                reader = PdfReader(folha_path)
                page = reader.pages[0]
                overlay_reader = PdfReader(overlay_io)
                overlay_page = overlay_reader.pages[0]
                page.merge_page(overlay_page)
                writer = PdfWriter()
                writer.add_page(page)
                writer.write(final_io)
                final_io.seek(0)
            else:
                # imagem como folha -> desenha com reportlab e mescla overlay
                try:
                    from reportlab.lib.utils import ImageReader
                    bg_io = BytesIO()
                    c2 = canvas.Canvas(bg_io, pagesize=A4)
                    img = ImageReader(folha_path)
                    # se width/height não definidos, usa A4
                    w = width or A4[0]
                    h = height or A4[1]
                    c2.drawImage(img, 0, 0, width=w, height=h)
                    c2.showPage()
                    c2.save()
                    bg_io.seek(0)
                    reader = PdfReader(bg_io)
                    page = reader.pages[0]
                    overlay_reader = PdfReader(overlay_io)
                    overlay_page = overlay_reader.pages[0]
                    page.merge_page(overlay_page)
                    writer = PdfWriter()
                    writer.add_page(page)
                    writer.write(final_io)
                    final_io.seek(0)
                except Exception:
                    # fallback: retorna overlay
                    final_io = overlay_io
        else:
            final_io = overlay_io

        from flask import send_file
        final_io.seek(0)
        return send_file(final_io, mimetype='application/pdf', as_attachment=True, download_name='procuracao_automatica.pdf')

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500



@main_bp.route('/procuracoes/<proc_id>/download')
@login_required
def download_procuracao(proc_id):
    """Gera PDF final da procuração usando folha timbrada (se selecionada) e retorna para download."""
    try:
        db = get_db()
        try:
            obj_id = ObjectId(proc_id)
        except:
            return "ID inválido", 400

        procuracao = db['procuracoes'].find_one({'_id': obj_id})
        if not procuracao:
            return "Procuração não encontrada", 404

        # Diretórios
        base_dir = os.path.dirname(os.path.dirname(__file__))
        folhas_dir = os.path.join(base_dir, 'static', 'folhas')
        out_dir = os.path.join(base_dir, 'static', 'procuracoes')
        os.makedirs(out_dir, exist_ok=True)

        folha = procuracao.get('folha')
        titulo = procuracao.get('titulo', '')
        cliente_nome = procuracao.get('cliente_nome', '')
        tipo = procuracao.get('tipo', '')
        data = procuracao.get('data', datetime.utcnow().strftime('%Y-%m-%d'))
        cidade_procuracao = procuracao.get('cidade')

        # Gera PDF temporário com texto (overlay)
        overlay_path = os.path.join(out_dir, f'overlay_{proc_id}.pdf')
        final_path = os.path.join(out_dir, f'proc_{proc_id}.pdf')

        # Cria overlay com reportlab
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
        except Exception as e:
            return f"Dependência ausente: {e}", 500

        c = canvas.Canvas(overlay_path, pagesize=A4)
        width, height = A4
        # Posiciona texto (ajuste simples) — deslocado mais para baixo para evitar sobreposição com cabeçalho
        c.setFont('Helvetica-Bold', 14)
        c.drawString(72, height - 210, f'Título: {titulo}')
        c.setFont('Helvetica', 12)
        c.drawString(72, height - 230, f'Cliente: {cliente_nome}')
        # formata data do sistema em pt-BR
        def formatar_data_ptbr(dt):
            meses = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']
            return f"{dt.day} de {meses[dt.month-1]} de {dt.year}"

        agora = datetime.now()
        data_formatada = formatar_data_ptbr(agora)
        city_date = f"{cidade_procuracao} - {data_formatada}" if cidade_procuracao else data_formatada
        c.drawString(72, height - 246, f'{city_date}')
        c.drawString(72, height - 266, f'Tipo: {tipo}')
        c.drawString(72, height - 286, f'Data gerada: {data_formatada}')
        # Assinatura posicionada logo abaixo da linha "Data gerada"
        # 'Data gerada' foi desenhada em y = height - 286; colocamos a linha de assinatura
        # alguns pontos abaixo para ficar imediatamente abaixo da data
        sig_y = height - 302
        center_x = width / 2
        line_len = 200
        c.line(center_x - line_len/2, sig_y, center_x + line_len/2, sig_y)
        c.setFont('Helvetica', 10)
        c.drawCentredString(center_x, sig_y - 14, 'Assinatura do Outorgante')
        c.showPage()
        c.save()

        # Se folha for PDF, mesclar overlay; se imagem, criar PDF com imagem como fundo e mesclar overlay
        try:
            from PyPDF2 import PdfReader, PdfWriter
        except Exception as e:
            return f"Dependência ausente: {e}", 500

        if folha:
            folha_path = os.path.join(folhas_dir, folha)
            if os.path.isfile(folha_path) and folha.lower().endswith('.pdf'):
                reader = PdfReader(folha_path)
                page = reader.pages[0]
                overlay_reader = PdfReader(overlay_path)
                overlay_page = overlay_reader.pages[0]
                page.merge_page(overlay_page)
                writer = PdfWriter()
                writer.add_page(page)
                with open(final_path, 'wb') as fh:
                    writer.write(fh)
            else:
                # Se não for PDF (imagem), usamos reportlab para compor imagem + overlay
                try:
                    from reportlab.lib.utils import ImageReader
                    c = canvas.Canvas(final_path, pagesize=A4)
                    img = ImageReader(folha_path)
                    c.drawImage(img, 0, 0, width=width, height=height)
                    # Adiciona texto sobre a imagem
                    c.setFont('Helvetica-Bold', 14)
                    c.drawString(72, height - 210, f'Título: {titulo}')
                    c.setFont('Helvetica', 12)
                    c.drawString(72, height - 230, f'Cliente: {cliente_nome}')
                    c.drawString(72, height - 250, f'Tipo: {tipo}')
                    # 'data' pode vir como YYYY-MM-DD; formatamos para DD/MM/YYYY
                    try:
                        parsed_saved = datetime.strptime(data, '%Y-%m-%d')
                        data_print = parsed_saved.strftime('%d/%m/%Y')
                    except Exception:
                        data_print = data
                    c.drawString(72, height - 270, f'Data: {data_print}')
                    # Assinatura centralizada logo abaixo da data
                    center_x = width / 2
                    line_len = 200
                    sig_y = height - 286
                    c.line(center_x - line_len/2, sig_y, center_x + line_len/2, sig_y)
                    c.setFont('Helvetica', 10)
                    c.drawCentredString(center_x, sig_y - 14, 'Assinatura do Outorgante')
                    c.showPage()
                    c.save()
                except Exception as e:
                    # fallback: retorna overlay
                    os.replace(overlay_path, final_path)
        else:
            # Sem folha, retorna apenas overlay
            os.replace(overlay_path, final_path)

        from flask import send_file
        return send_file(final_path, as_attachment=True)

    except Exception as e:
        return str(e), 500


# ============================================================================
# ROTAS DE ERRO
# ============================================================================

@main_bp.errorhandler(404)
def pagina_nao_encontrada(error):
    """Trata erros 404 (página não encontrada)"""
    return render_template('404.html'), 404


@main_bp.errorhandler(500)
def erro_servidor(error):
    """Trata erros 500 (erro interno do servidor)"""
    return render_template('500.html'), 500
