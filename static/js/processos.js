/* ============================================================================
   JAVASCRIPT - PÁGINA DE PROCESSOS JURÍDICOS
   ============================================================================
   Arquivo: static/js/processos.js
   Propósito: Funções AJAX para gestão de processos jurídicos
   
   Funcionalidades:
   - Salvar novo processo ou editar
   - Deletar processo
   - Filtrar processos por status/tipo
   - Carregar lista de clientes no select
   ============================================================================ */

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Script de processos carregado!');
    
    // Carrega lista de clientes ao abrir modal
    document.getElementById('modalProcesso').addEventListener('show.bs.modal', function(e) {
        const processoId = document.getElementById('processoId').value;
        const clienteSelecionado = processoId ? document.getElementById('cliente_id').value : '';
        carregarClientes(clienteSelecionado);
        
        // Se for novo processo, limpa formulário
        if (!document.getElementById('processoId').value) {
            document.getElementById('modalProcessoTitle').textContent = 'Novo Processo';
            limparFormulario('formProcesso');
            document.getElementById('anexoAtual').innerHTML = '';
        }
    });

    abrirProcessoPendenteEdicao();

});

async function abrirProcessoPendenteEdicao() {
    try {
        const flagEdicao = new URLSearchParams(window.location.search).get('editar');
        const processoRaw = sessionStorage.getItem('processoEdicaoPendente');

        if (!flagEdicao || !processoRaw) {
            return;
        }

        const processo = JSON.parse(processoRaw);
        sessionStorage.removeItem('processoEdicaoPendente');

        if (!processo || !processo._id) {
            return;
        }

        await editarProcesso(
            processo._id,
            processo.numero_processo || '',
            processo.cliente_id || '',
            processo.tipo_acao || '',
            processo.tribunal || '',
            processo.vara || '',
            processo.juiz || '',
            processo.status || '',
            processo.descricao || '',
            Array.isArray(processo.anexos) ? processo.anexos : []
        );

        const urlLimpa = `${window.location.origin}${window.location.pathname}`;
        window.history.replaceState({}, document.title, urlLimpa);
    } catch (erro) {
        console.error('Erro ao abrir processo pendente para edição:', erro);
    }
}

// ============================================================================
// CARREGAR CLIENTES - Popula select do formulário
// ============================================================================

async function carregarClientes(clienteSelecionado = '') {
    /*
    Carrega lista de clientes e popula o select do formulário.

    Observação: implementar endpoint `/api/clientes/lista` é recomendado
    para retorno JSON; aqui evitamos recarregar o select se já existir
    */
    
    const selectCliente = document.getElementById('cliente_id');
    
    try {
        const resposta = await fazRequisicao('/api/clientes/lista', 'GET');

        if (!resposta || resposta.status !== 200 || !resposta.dados?.success) {
            mostrarAlerta(resposta?.dados?.message || 'Não foi possível carregar clientes', 'danger');
            return;
        }

        // Limpa opções (mantém o placeholder)
        selectCliente.innerHTML = '<option value="">Selecionar cliente...</option>';

        const clientes = resposta.dados.clientes || [];
        if (clientes.length === 0) {
            selectCliente.innerHTML = '<option value="">Nenhum cliente cadastrado</option>';
            return;
        }

        clientes.forEach(cliente => {
            const option = document.createElement('option');
            option.value = cliente._id;
            option.textContent = cliente.nome;
            selectCliente.appendChild(option);
        });

        if (clienteSelecionado) {
            selectCliente.value = clienteSelecionado;
        }
        
    } catch (erro) {
        console.error('Erro ao carregar clientes:', erro);
    }
}

// ============================================================================
// SALVAR PROCESSO (Novo ou Edição)
// ============================================================================

async function salvarProcesso() {
    /*
    Salva um processo no banco de dados (INSERT ou UPDATE).

    Processo:
    1. Obtém dados do formulário
    2. Valida dados obrigatórios
    3. Determina se é novo (POST) ou edição (PUT)
    4. Envia requisição AJAX
    5. Atualiza tabela ou exibe erro
    */
    
    // Obtém dados do formulário
    const processoId = document.getElementById('processoId').value;
    const numero_processo = document.getElementById('numero_processo').value;
    const cliente_id = document.getElementById('cliente_id').value;
    const tipo_acao = document.getElementById('tipo_acao').value;
    const status = document.getElementById('status').value;
    const tribunal = document.getElementById('tribunal').value;
    const vara = document.getElementById('vara').value;
    const juiz = document.getElementById('juiz').value;
    const descricao = document.getElementById('descricao').value;
    
    // Validações básicas
    if (!numero_processo || !cliente_id || !tipo_acao || !status) {
        mostrarAlerta('Preencha todos os campos obrigatórios (*)', 'warning');
        return;
    }
    
    // Dados a enviar ao backend (multipart/form-data)
    const clienteOption = document.getElementById('cliente_id').selectedOptions[0];
    const formData = new FormData();
    formData.append('numero_processo', numero_processo);
    formData.append('cliente_id', cliente_id);
    formData.append('cliente_nome', clienteOption ? clienteOption.textContent : '');
    formData.append('tipo_acao', tipo_acao);
    formData.append('status', status);
    formData.append('tribunal', tribunal);
    formData.append('vara', vara);
    formData.append('juiz', juiz);
    formData.append('descricao', descricao);

    const anexosSelecionados = document.getElementById('anexos').files;
    if (anexosSelecionados && anexosSelecionados.length > 0) {
        Array.from(anexosSelecionados).forEach(arquivo => {
            formData.append('anexos', arquivo);
        });
    }
    
    try {
        // Determina se é novo ou edição
        let url, metodo, mensagem;
        
        if (processoId) {
            // EDIÇÃO: PUT /api/processos/<id>/atualizar
            url = `/api/processos/${processoId}/atualizar`;
            metodo = 'PUT';
            mensagem = 'Processo atualizado com sucesso!';
        } else {
            // NOVO: POST /api/processos/novo
            url = '/api/processos/novo';
            metodo = 'POST';
            mensagem = 'Processo cadastrado com sucesso!';
        }
        
        // Envia requisição AJAX
        const respostaFetch = await fetch(url, {
            method: metodo,
            body: formData
        });
        const respostaJson = await respostaFetch.json();
        const resposta = { status: respostaFetch.status, dados: respostaJson };
        
        if (resposta && (resposta.status === 200 || resposta.status === 201)) {
            mostrarAlerta(mensagem, 'success');
            
            // Fecha o modal
            fecharModal('modalProcesso');
            
            // Limpa o formulário
            limparFormulario('formProcesso');
            document.getElementById('processoId').value = '';
            document.getElementById('anexoAtual').innerHTML = '';
            
            // Recarrega a página para atualizar tabela
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            mostrarAlerta(resposta.dados.message || 'Erro ao salvar processo', 'danger');
        }
    } catch (erro) {
        console.error('Erro:', erro);
        mostrarAlerta('Erro ao salvar processo', 'danger');
    }
}

// ============================================================================
// EDITAR PROCESSO
// ============================================================================

async function editarProcesso(id, numero, clienteId, tipo, tribunal, vara, juiz, status, descricao, anexos = []) {
   /*
    Abre o modal com dados do processo para edição
   */
    
    // Preenche os campos com dados do processo
    document.getElementById('processoId').value = id;
    document.getElementById('numero_processo').value = numero;
    await carregarClientes(clienteId);
    document.getElementById('tipo_acao').value = tipo;
    document.getElementById('tribunal').value = tribunal;
    document.getElementById('vara').value = vara;
    document.getElementById('juiz').value = juiz;
    document.getElementById('status').value = status;
    document.getElementById('descricao').value = descricao;

    const anexoAtual = document.getElementById('anexoAtual');
    if (anexoAtual) {
        const anexosAtuais = Array.isArray(anexos) ? anexos.filter(item => item) : [];

        if (anexosAtuais.length > 0) {
            anexoAtual.innerHTML = anexosAtuais
                .map((anexo, index) => {
                    const href = `/static/${encodeURI(anexo)}`;
                    return `<div><a href="${href}" target="_blank"><i class="bi bi-paperclip"></i> Ver anexo ${index + 1}</a></div>`;
                })
                .join('') + '<small class="text-muted d-block mt-1">Novos arquivos serão adicionados aos anexos atuais.</small>';
        } else {
            anexoAtual.innerHTML = '<span class="text-muted">Nenhum anexo atual</span>';
        }
    }
    
    // Muda título do modal
    document.getElementById('modalProcessoTitle').textContent = 'Editar Processo';
    
    // Abre o modal
    abrirModal('modalProcesso');
}

// ============================================================================
// DELETAR PROCESSO
// ============================================================================

async function deletarProcesso(id, numero) {
    /*
    Deleta um processo do sistema
    */
    
    // Pede confirmação
    if (!confirm(`Tem certeza que deseja remover o processo "${numero}"?\n\nEsta ação não pode ser desfeita!`)) {
        return;
    }
    
    try {
        // Envia DELETE request
        const resposta = await fazRequisicao(
            `/api/processos/${id}/deletar`,
            'DELETE'
        );
        
        if (resposta && resposta.status === 200) {
            mostrarAlerta('Processo removido com sucesso!', 'success');
            
            // Recarrega a página
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            mostrarAlerta(resposta.dados.message || 'Erro ao remover processo', 'danger');
        }
    } catch (erro) {
        console.error('Erro:', erro);
        mostrarAlerta('Erro ao remover processo', 'danger');
    }
}

// ============================================================================
// FILTROS DE PROCESSOS
// ============================================================================

function filtrarProcessos() {
    /*
    Filtra a tabela de processos conforme critérios selecionados.

    Critérios:
    - Status
    - Tipo de Ação
    - Número do processo (busca)
    */
    
    // Obtém valores dos filtros
    const status = document.getElementById('filtroStatus').value;
    const tipo = document.getElementById('filtroTipo').value;
    const numero = document.getElementById('buscaNumero').value.toLowerCase();
    
    // Obtém todas as linhas da tabela
    const linhas = document.querySelectorAll('.processo-row');
    
    // Itera sobre cada linha
    linhas.forEach(linha => {
        let mostrar = true;
        
        // Filtra por status
        if (status && linha.getAttribute('data-status') !== status) {
            mostrar = false;
        }
        
        // Filtra por tipo
        if (tipo && linha.getAttribute('data-tipo') !== tipo) {
            mostrar = false;
        }
        
        // Filtra por número (busca)
        if (numero && !linha.getAttribute('data-numero').toLowerCase().includes(numero)) {
            mostrar = false;
        }
        
        // Mostra ou esconde a linha
        linha.style.display = mostrar ? '' : 'none';
    });
}

function limparFiltros() {
    /*
    Limpa todos os filtros e mostra todos os processos
    */
    
    document.getElementById('filtroStatus').value = '';
    document.getElementById('filtroTipo').value = '';
    document.getElementById('buscaNumero').value = '';
    
    // Mostra todas as linhas
    const linhas = document.querySelectorAll('.processo-row');
    linhas.forEach(linha => {
        linha.style.display = '';
    });
}

// ============================================================================
// VER DETALHES DO PROCESSO
// ============================================================================

function verDetalhesProcesso(processoId) {
    /*
    Abre detalhes de um processo específico.
    Pode ser expandido para mostrar modal com informações completas.
    */
    
    console.log('📋 Detalhes do processo:', processoId);
    // TODO: Implementar visualização detalhada do processo
}
