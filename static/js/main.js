/* ============================================================================
   JAVASCRIPT PRINCIPAL - FUNÇÕES GLOBAIS
   ============================================================================
   Arquivo: static/js/main.js
   Propósito: Funções JavaScript reutilizáveis em toda aplicação
   
   Funções:
   - Requisições AJAX com fetch()
   - Validações de formulário
   - Manipulação de alertas
   - Utilitários gerais
   ============================================================================ */

// ============================================================================
// REQUISIÇÕES AJAX - Utilitários para comunicação com Backend
// ============================================================================

function obterCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? (meta.getAttribute('content') || '') : '';
}

if (!window.__csrf_fetch_patched) {
    const _fetchOriginal = window.fetch.bind(window);
    window.fetch = function(input, init = {}) {
        const options = init || {};
        const metodo = String(options.method || 'GET').toUpperCase();
        const metodosEscrita = ['POST', 'PUT', 'PATCH', 'DELETE'];

        if (metodosEscrita.includes(metodo)) {
            const token = obterCsrfToken();
            if (token) {
                const headers = new Headers(options.headers || {});
                if (!headers.has('X-CSRF-Token')) {
                    headers.set('X-CSRF-Token', token);
                }
                options.headers = headers;
            }
        }

        return _fetchOriginal(input, options);
    };
    window.__csrf_fetch_patched = true;
}

/**
 * Função genérica para fazer requisições AJAX
 * 
 * Argumentos:
 *   url: URL do endpoint
 *   metodo: GET, POST, PUT, DELETE
 *   dados: Objeto com dados a enviar (opcional)
 * 
 * Retorna: Promise com resultado da requisição
 * 
 * Exemplo:
 *   fazRequisicao('/api/clientes/novo', 'POST', { nome: 'João' })
 */
async function fazRequisicao(url, metodo = 'GET', dados = null) {
    try {
        const tokenCsrf = obterCsrfToken();
        const opcoes = {
            method: metodo,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const metodoUpper = String(metodo || 'GET').toUpperCase();
        if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(metodoUpper) && tokenCsrf) {
            opcoes.headers['X-CSRF-Token'] = tokenCsrf;
        }
        
        // Adiciona corpo se houver dados
        if (dados) {
            opcoes.body = JSON.stringify(dados);
        }
        
        // Faz a requisição
        const resposta = await fetch(url, opcoes);
        const resultado = await resposta.json();
        
        return {
            status: resposta.status,
            dados: resultado
        };
        
    } catch (erro) {
        console.error('Erro na requisição:', erro);
        mostrarAlerta('Erro ao comunicar com o servidor', 'danger');
        return null;
    }
}

// ============================================================================
// ALERTAS - Sistema de Notificações
// ============================================================================

/**
 * Mostra um alerta tipo Toast (Bootstrap)
 * 
 * Argumentos:
 *   mensagem: Texto a exibir
 *   tipo: 'success', 'danger', 'warning', 'info'
 */
function mostrarAlerta(mensagem, tipo = 'info') {
    // Cria elemento de alerta dinamicamente
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo} alert-dismissible fade show`;
    alerta.setAttribute('role', 'alert');
    alerta.innerHTML = `
        <div class="mb-2">${mensagem}</div>
        <div class="d-flex justify-content-end">
            <button type="button" class="btn btn-sm btn-primary">OK</button>
        </div>
    `;
    
    // Insere no centro da tela
    let container = document.getElementById('globalAlertCenter');
    let overlay = document.getElementById('globalAlertOverlay');
    if (!container) {
        container = document.createElement('div');
        container.id = 'globalAlertCenter';
        container.style.position = 'fixed';
        container.style.top = '50%';
        container.style.left = '50%';
        container.style.transform = 'translate(-50%, -46%)';
        container.style.zIndex = '2000';
        container.style.width = 'min(92vw, 520px)';
        container.style.pointerEvents = 'none';
        container.style.opacity = '0';
        container.style.visibility = 'hidden';
        container.style.transition = 'opacity .25s ease, transform .25s ease, visibility .25s ease';
        document.body.appendChild(container);
    }

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'globalAlertOverlay';
        overlay.style.position = 'fixed';
        overlay.style.inset = '0';
        overlay.style.background = 'rgba(0,0,0,0.35)';
        overlay.style.zIndex = '1999';
        overlay.style.pointerEvents = 'none';
        overlay.style.opacity = '0';
        overlay.style.visibility = 'hidden';
        overlay.style.transition = 'opacity .25s ease, visibility .25s ease';
        document.body.appendChild(overlay);
    }

    alerta.style.pointerEvents = 'auto';
    container.appendChild(alerta);

    const atualizarOverlay = () => {
        const temAlertas = container.querySelectorAll('.alert.show').length > 0;
        overlay.style.opacity = temAlertas ? '1' : '0';
        overlay.style.visibility = temAlertas ? 'visible' : 'hidden';
        container.style.opacity = temAlertas ? '1' : '0';
        container.style.visibility = temAlertas ? 'visible' : 'hidden';
        container.style.transform = temAlertas ? 'translate(-50%, -50%)' : 'translate(-50%, -46%)';
    };
    atualizarOverlay();
    alerta.addEventListener('closed.bs.alert', atualizarOverlay);

    const okBtn = alerta.querySelector('button.btn-primary');
    if (okBtn) {
        okBtn.addEventListener('click', () => {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alerta);
                bsAlert.close();
            } catch (e) {
                alerta.remove();
            }
            setTimeout(atualizarOverlay, 180);
        });
    }
}

// ============================================================================
// VALIDAÇÕES - Funções de validação de dados
// ============================================================================

/**
 * Valida um email
 */
function emailValido(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Valida telefone brasileiro
 */
function telefoneValido(telefone) {
    const regex = /^\(\d{2}\) \d{4,5}-\d{4}$/;
    return regex.test(telefone) || telefone === '';
}

/**
 * Formata um telefone para padrão brasileiro
 */
function formatarTelefone(telefone) {
    const numeros = telefone.replace(/\D/g, '');
    if (numeros.length === 11) {
        return `(${numeros.slice(0, 2)}) ${numeros.slice(2, 7)}-${numeros.slice(7)}`;
    }
    return telefone;
}

// ============================================================================
// UTILIDADES DOM
// ============================================================================

/**
 * Limpa todos os campos de um formulário
 */
function limparFormulario(idFormulario) {
    const formulario = document.getElementById(idFormulario);
    if (formulario) {
        formulario.reset();
    }
}

/**
 * Obtém valores de um formulário como objeto
 */
function obterDadosFormulario(idFormulario) {
    const formulario = document.getElementById(idFormulario);
    const dados = new FormData(formulario);
    return Object.fromEntries(dados);
}

/**
 * Desabilita um botão temporariamente
 */
function desabilitarBotao(idBotao, tempo = 3000) {
    const botao = document.getElementById(idBotao);
    if (botao) {
        botao.disabled = true;
        setTimeout(() => {
            botao.disabled = false;
        }, tempo);
    }
}

// ============================================================================
// MANIPULAÇÃO DE MODAIS
// ============================================================================

/**
 * Abre um modal pelo ID
 */
function abrirModal(idModal) {
    const modal = new bootstrap.Modal(document.getElementById(idModal));
    modal.show();
}

/**
 * Fecha um modal pelo ID
 */
function fecharModal(idModal) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(idModal));
    if (modal) {
        modal.hide();
    }
}

// ============================================================================
// CONFIRMAÇÕES
// ============================================================================

/**
 * Mostra uma confirmação antes de executar ação
 */
function confirmar(mensagem) {
    return confirm(mensagem);
}

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Aplicação carregada com sucesso!');
    console.log('diagnóstico: __clientes_loaded=', window.__clientes_loaded, 'typeof salvarCliente=', typeof window.salvarCliente);
    // Fallback: garante que o botão Salvar Cliente acione a função salvarCliente
    const btnSalvar = document.getElementById('btnSalvarCliente');
    if (btnSalvar) {
        btnSalvar.addEventListener('click', function (e) {
            if (typeof salvarCliente === 'function') {
                try { salvarCliente(); } catch (err) { console.error('Erro em salvarCliente:', err); mostrarAlerta('Erro ao salvar cliente', 'danger'); }
            } else {
                console.error('salvarCliente não está definido');
                mostrarAlerta('Erro: função salvarCliente não carregada', 'danger');
            }
        });
    }
});
