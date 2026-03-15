/* ============================================================================
   JAVASCRIPT - PÁGINA DE CLIENTES
   ============================================================================
   Arquivo: static/js/clientes.js
   Propósito: Funções AJAX específicas para gestão de clientes
   
   Funcionalidades:
   - Adicionar novo cliente via modal
   - Editar cliente existente
   - Deletar cliente
   - Visualizar processos do cliente
   ============================================================================ */

// ============================================================================
// SALVAR CLIENTE (Novo ou Edição)
// ============================================================================

// Marca que o script de clientes foi carregado
try { window.__clientes_loaded = true; } catch(e) { /* noop if no window */ }

let pagamentosPorContratoAtual = [];

function ativarAbaClienteDados() {
    const tabBtn = document.getElementById('cliente-dados-tab');
    if (tabBtn && typeof bootstrap !== 'undefined' && bootstrap.Tab) {
        bootstrap.Tab.getOrCreateInstance(tabBtn).show();
    }
}

function formatCurrencyBRL(valor) {
    const numero = Number(valor);
    if (!Number.isFinite(numero)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numero);
}

function atualizarResumoPagamento() {
    const totalEl = document.getElementById('pagamentoResumoTotal');
    const pagoEl = document.getElementById('pagamentoResumoPago');
    const restanteEl = document.getElementById('pagamentoResumoRestante');
    if (!totalEl || !pagoEl || !restanteEl) return;

    const valorHonorariosRaw = (document.getElementById('valor_honorarios')?.value || '').trim();
    const numeroParcelasRaw = (document.getElementById('numero_parcelas')?.value || '').trim();
    const valorTotal = valorHonorariosRaw ? Number(valorHonorariosRaw) : 0;
    const totalParcelas = numeroParcelasRaw ? Number(numeroParcelasRaw) : 0;

    const parcelas = coletarParcelasPagamentoAtual();
    const pagas = parcelas.filter((p) => p.paga).length;

    let valorPago = 0;
    let valorRestante = valorTotal;
    if (Number.isFinite(valorTotal) && valorTotal > 0 && Number.isInteger(totalParcelas) && totalParcelas > 0) {
        const valorParcela = valorTotal / totalParcelas;
        valorPago = valorParcela * pagas;
        valorRestante = valorTotal - valorPago;
        if (valorRestante < 0) valorRestante = 0;
    }

    totalEl.textContent = `Valor total: ${formatCurrencyBRL(valorTotal > 0 ? valorTotal : 0)}`;
    pagoEl.textContent = `Valor pago: ${formatCurrencyBRL(valorPago > 0 ? valorPago : 0)}`;
    restanteEl.textContent = `Valor restante: ${formatCurrencyBRL(valorRestante > 0 ? valorRestante : 0)}`;
}

function obterContratoIdDaReferencia(valorReferencia = '') {
    const valor = (valorReferencia || '').trim();
    if (!valor) return '';

    const match = valor.match(/^Contrato\s*ID:\s*(.+)$/i);
    if (match && match[1]) return match[1].trim();
    return valor;
}

function atualizarAvisoContratoSemConfiguracao(exibir = false) {
    const aviso = document.getElementById('avisoContratoSemFinanceiro');
    if (!aviso) return;

    if (exibir) {
        aviso.classList.remove('d-none');
    } else {
        aviso.classList.add('d-none');
    }
}

function limparCamposPagamentoContrato(mostrarAviso = false) {
    const formaEl = document.getElementById('forma_pagamento');
    const valorEl = document.getElementById('valor_honorarios');
    const diaEl = document.getElementById('dia_vencimento');
    const obsEl = document.getElementById('observacoes_pagamento');
    const parcelasEl = document.getElementById('numero_parcelas');

    if (formaEl) formaEl.value = '';
    if (valorEl) valorEl.value = '';
    if (diaEl) diaEl.value = '';
    if (obsEl) obsEl.value = '';
    if (parcelasEl) parcelasEl.value = '';

    renderParcelasPagamento('');
    atualizarResumoPagamento();
    atualizarAvisoContratoSemConfiguracao(mostrarAviso);
}

function aplicarPagamentoDoContratoSelecionado() {
    const select = document.getElementById('referencia_pagamento');
    if (!select) return;

    const contratoId = obterContratoIdDaReferencia(select.value || '');
    if (!contratoId) {
        limparCamposPagamentoContrato(false);
        return;
    }

    const registro = Array.isArray(pagamentosPorContratoAtual)
        ? pagamentosPorContratoAtual.find((item) => (item?.contrato_id || '').trim() === contratoId)
        : null;

    if (!registro) {
        limparCamposPagamentoContrato(true);
        return;
    }

    document.getElementById('forma_pagamento').value = registro.forma_pagamento || '';
    document.getElementById('valor_honorarios').value = (registro.valor_honorarios ?? '') === null ? '' : (registro.valor_honorarios ?? '');
    document.getElementById('dia_vencimento').value = (registro.dia_vencimento ?? '') === null ? '' : (registro.dia_vencimento ?? '');
    document.getElementById('observacoes_pagamento').value = registro.observacoes_pagamento || '';
    document.getElementById('numero_parcelas').value = (registro.numero_parcelas ?? '') === null ? '' : (registro.numero_parcelas ?? '');

    renderParcelasPagamento(registro.numero_parcelas || '', registro.parcelas_pagamento || []);
    atualizarResumoPagamento();
    atualizarAvisoContratoSemConfiguracao(false);
}

function definirSelectReferenciaPagamentoPadrao(mensagem) {
    const select = document.getElementById('referencia_pagamento');
    if (!select) return;

    select.innerHTML = `<option value="">${mensagem}</option>`;
    select.value = '';
    select.disabled = true;
    atualizarAvisoContratoSemConfiguracao(false);
}

async function carregarReferenciasPagamentoCliente(clienteId, referenciaSelecionada = '') {
    const select = document.getElementById('referencia_pagamento');
    if (!select) return;

    if (!clienteId) {
        definirSelectReferenciaPagamentoPadrao('Selecione um cliente salvo para carregar os contratos...');
        return;
    }

    select.disabled = true;
    select.innerHTML = '<option value="">Carregando contratos...</option>';

    try {
        const resposta = await fazRequisicao(`/api/clientes/${clienteId}/referencias-pagamento`, 'GET');

        if (!(resposta && resposta.status === 200 && resposta.dados?.success)) {
            definirSelectReferenciaPagamentoPadrao('Não foi possível carregar contratos do cliente');
            return;
        }

        const referencias = Array.isArray(resposta.dados.referencias) ? resposta.dados.referencias : [];

        if (referencias.length === 0) {
            definirSelectReferenciaPagamentoPadrao('Sem contratos cadastrados para este cliente');
            return;
        }

        select.innerHTML = '<option value="">Selecionar contrato...</option>';

        referencias.forEach((item) => {
            const option = document.createElement('option');
            option.value = item.valor || '';
            option.textContent = item.label || item.valor || '';
            option.dataset.contratoId = item.id || '';
            select.appendChild(option);
        });

        if (referenciaSelecionada) {
            const existe = referencias.some((item) => (item.valor || '') === referenciaSelecionada);
            if (existe) {
                select.value = referenciaSelecionada;
            } else {
                const legacy = document.createElement('option');
                legacy.value = referenciaSelecionada;
                const contratoIdLegado = obterContratoIdDaReferencia(referenciaSelecionada);
                const contratoResumo = contratoIdLegado ? contratoIdLegado.slice(0, 8) : 'sem identificação';
                legacy.textContent = `Contrato atual (legado): ${contratoResumo}`;
                select.appendChild(legacy);
                select.value = referenciaSelecionada;
            }
        }

        select.disabled = false;
        aplicarPagamentoDoContratoSelecionado();
    } catch (erro) {
        console.error('Erro ao carregar contratos do cliente:', erro);
        definirSelectReferenciaPagamentoPadrao('Erro ao carregar contratos do cliente');
    }
}

function coletarParcelasPagamentoAtual() {
    const checks = document.querySelectorAll('#parcelasPagamentoContainer input[type="checkbox"][data-parcela-num]');
    return Array.from(checks).map((chk) => {
        const numero = Number(chk.dataset.parcelaNum);
        const vencimentoInput = document.querySelector(`#parcelasPagamentoContainer input[type="date"][data-parcela-venc="${numero}"]`);
        return {
            numero: numero,
            paga: !!chk.checked,
            data_vencimento: (vencimentoInput?.value || '').trim()
        };
    });
}

function gerarDataParcela(numeroParcela, diaVencimento) {
    const dia = Number(diaVencimento);
    if (!Number.isInteger(dia) || dia < 1 || dia > 31) {
        return '';
    }

    const hoje = new Date();
    const dataParcela = new Date(hoje.getFullYear(), hoje.getMonth() + (numeroParcela - 1), 1);
    const ultimoDiaMes = new Date(dataParcela.getFullYear(), dataParcela.getMonth() + 1, 0).getDate();
    dataParcela.setDate(Math.min(dia, ultimoDiaMes));

    const ano = dataParcela.getFullYear();
    const mes = String(dataParcela.getMonth() + 1).padStart(2, '0');
    const diaTexto = String(dataParcela.getDate()).padStart(2, '0');
    return `${ano}-${mes}-${diaTexto}`;
}

function renderParcelasPagamento(quantidade, parcelasExistentes = []) {
    const container = document.getElementById('parcelasPagamentoContainer');
    if (!container) return;

    container.innerHTML = '';
    const total = Number(quantidade);
    if (!Number.isInteger(total) || total < 1) return;

    const mapaPagas = new Map();
    const mapaVencimentos = new Map();
    (Array.isArray(parcelasExistentes) ? parcelasExistentes : []).forEach((item) => {
        if (item && Number.isInteger(Number(item.numero))) {
            mapaPagas.set(Number(item.numero), !!item.paga);
            mapaVencimentos.set(Number(item.numero), (item.data_vencimento || '').trim());
        }
    });

    const diaVencimento = Number((document.getElementById('dia_vencimento')?.value || '').trim());

    for (let i = 1; i <= total; i++) {
        const wrapper = document.createElement('div');
        wrapper.className = 'border rounded px-2 py-2 d-flex flex-column gap-1';

        const linhaCheck = document.createElement('div');
        linhaCheck.className = 'form-check';

        const input = document.createElement('input');
        input.className = 'form-check-input';
        input.type = 'checkbox';
        input.id = `parcela_${i}`;
        input.dataset.parcelaNum = String(i);
        input.checked = mapaPagas.get(i) === true;
        input.addEventListener('change', atualizarResumoPagamento);

        const label = document.createElement('label');
        label.className = 'form-check-label small';
        label.htmlFor = `parcela_${i}`;
        label.textContent = `${i}ª paga`;

        linhaCheck.appendChild(input);
        linhaCheck.appendChild(label);

        const labelData = document.createElement('small');
        labelData.className = 'text-muted';
        labelData.textContent = `${i}ª vencimento`;

        const inputData = document.createElement('input');
        inputData.type = 'date';
        inputData.className = 'form-control form-control-sm';
        inputData.dataset.parcelaVenc = String(i);
        inputData.value = mapaVencimentos.get(i) || gerarDataParcela(i, diaVencimento);

        wrapper.appendChild(linhaCheck);
        wrapper.appendChild(labelData);
        wrapper.appendChild(inputData);
        container.appendChild(wrapper);
    }

    atualizarResumoPagamento();
}

function limparSubabaProcessosCliente(mensagem = 'Selecione um cliente salvo para listar os processos.') {
    const container = document.getElementById('clienteProcessosContainer');
    const totalEl = document.getElementById('clienteProcessosTotal');

    if (totalEl) {
        totalEl.textContent = 'Total: 0';
    }

    if (container) {
        container.innerHTML = `<div class="text-muted">${mensagem}</div>`;
        container.dataset.loadedClienteId = '';
    }
}

function abrirProcessoClienteSubaba(processoEncoded) {
    try {
        const processo = JSON.parse(decodeURIComponent(processoEncoded));
        if (!processo || !processo._id) {
            mostrarAlerta('Processo inválido para edição.', 'warning');
            return;
        }

        document.getElementById('clienteProcessoEditId').value = processo._id || '';
        document.getElementById('clienteProcessoClienteId').value = processo.cliente_id || '';
        document.getElementById('clienteProcessoNumero').value = processo.numero_processo || '';
        document.getElementById('clienteProcessoTipo').value = processo.tipo_acao || '';
        document.getElementById('clienteProcessoStatus').value = processo.status || '';
        document.getElementById('clienteProcessoTribunal').value = processo.tribunal || '';
        document.getElementById('clienteProcessoVara').value = processo.vara || '';
        document.getElementById('clienteProcessoJuiz').value = processo.juiz || '';
        document.getElementById('clienteProcessoDescricao').value = processo.descricao || '';

        const inputAnexos = document.getElementById('clienteProcessoAnexos');
        if (inputAnexos) {
            inputAnexos.value = '';
        }

        const anexosAtuaisEl = document.getElementById('clienteProcessoAnexosAtuais');
        const anexosAtuais = Array.isArray(processo.anexos)
            ? processo.anexos.filter(item => !!item)
            : [];

        if (anexosAtuaisEl) {
            if (anexosAtuais.length > 0) {
                anexosAtuaisEl.innerHTML = anexosAtuais
                    .map((anexo, index) => `<div><a href="/static/${encodeURI(anexo)}" target="_blank"><i class="bi bi-paperclip"></i> Ver anexo ${index + 1}</a></div>`)
                    .join('');
            } else {
                anexosAtuaisEl.innerHTML = '<span class="text-muted">Nenhum anexo atual.</span>';
            }
        }

        abrirModal('modalEditarProcessoCliente');
    } catch (erro) {
        console.error('Erro ao abrir processo para edição:', erro);
        mostrarAlerta('Não foi possível abrir o processo para edição.', 'danger');
    }
}

async function salvarEdicaoProcessoClienteSubaba() {
    const processoId = (document.getElementById('clienteProcessoEditId')?.value || '').trim();
    const clienteId = (document.getElementById('clienteProcessoClienteId')?.value || '').trim();
    const numeroProcesso = (document.getElementById('clienteProcessoNumero')?.value || '').trim();
    const tipoAcao = (document.getElementById('clienteProcessoTipo')?.value || '').trim();
    const status = (document.getElementById('clienteProcessoStatus')?.value || '').trim();
    const tribunal = (document.getElementById('clienteProcessoTribunal')?.value || '').trim();
    const vara = (document.getElementById('clienteProcessoVara')?.value || '').trim();
    const juiz = (document.getElementById('clienteProcessoJuiz')?.value || '').trim();
    const descricao = (document.getElementById('clienteProcessoDescricao')?.value || '').trim();
    const anexosInput = document.getElementById('clienteProcessoAnexos');

    if (!processoId || !clienteId) {
        mostrarAlerta('Processo inválido para atualização.', 'warning');
        return;
    }

    if (!numeroProcesso || !tipoAcao || !status) {
        mostrarAlerta('Preencha os campos obrigatórios: Número, Tipo e Status.', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('numero_processo', numeroProcesso);
    formData.append('cliente_id', clienteId);
    formData.append('tipo_acao', tipoAcao);
    formData.append('status', status);
    formData.append('tribunal', tribunal);
    formData.append('vara', vara);
    formData.append('juiz', juiz);
    formData.append('descricao', descricao);

    if (anexosInput && anexosInput.files && anexosInput.files.length > 0) {
        Array.from(anexosInput.files).forEach((arquivo) => {
            formData.append('anexos', arquivo);
        });
    }

    try {
        const respostaFetch = await fetch(`/api/processos/${processoId}/atualizar`, {
            method: 'PUT',
            body: formData
        });
        const respostaJson = await respostaFetch.json();

        if (respostaFetch.status === 200 && respostaJson?.success) {
            mostrarAlerta('Processo atualizado com sucesso!', 'success');
            fecharModal('modalEditarProcessoCliente');

            const container = document.getElementById('clienteProcessosContainer');
            if (container) {
                container.dataset.loadedClienteId = '';
            }
            await carregarProcessosClienteSubaba(clienteId);
        } else {
            mostrarAlerta(respostaJson?.message || 'Erro ao atualizar processo.', 'danger');
        }
    } catch (erro) {
        console.error('Erro ao atualizar processo pela subaba de clientes:', erro);
        mostrarAlerta('Erro ao atualizar processo.', 'danger');
    }
}

async function carregarProcessosClienteSubaba(clienteId) {
    const container = document.getElementById('clienteProcessosContainer');
    const totalEl = document.getElementById('clienteProcessosTotal');

    if (!container || !totalEl) return;

    if (!clienteId) {
        limparSubabaProcessosCliente('Salve o cliente para visualizar os processos vinculados.');
        return;
    }

    if (container.dataset.loadedClienteId === clienteId) {
        return;
    }

    container.innerHTML = `
        <div class="text-center py-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Carregando...</span>
            </div>
        </div>
    `;

    try {
        const resposta = await fazRequisicao(`/api/clientes/${clienteId}/processos`, 'GET');

        if (!(resposta && resposta.status === 200)) {
            limparSubabaProcessosCliente('Não foi possível carregar os processos deste cliente.');
            return;
        }

        const processos = resposta.dados?.processos || [];
        totalEl.textContent = `Total: ${processos.length}`;

        if (processos.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-3">
                    <i class="bi bi-inbox" style="font-size: 1.5rem;"></i>
                    <p class="mt-2 mb-0">Este cliente ainda não possui processos.</p>
                </div>
            `;
            container.dataset.loadedClienteId = clienteId;
            return;
        }

        let html = `
            <table class="table table-sm table-hover align-middle">
                <thead class="table-light">
                    <tr>
                        <th>Número</th>
                        <th>Tipo</th>
                        <th>Status</th>
                        <th>Tribunal</th>
                        <th class="text-end">Ação</th>
                    </tr>
                </thead>
                <tbody>
        `;

        processos.forEach((processo) => {
            const processoParaEdicao = {
                _id: processo._id,
                numero_processo: processo.numero_processo || '',
                cliente_id: processo.cliente_id || '',
                tipo_acao: processo.tipo_acao || '',
                tribunal: processo.tribunal || '',
                vara: processo.vara || '',
                juiz: processo.juiz || '',
                status: processo.status || '',
                descricao: processo.descricao || '',
                anexos: Array.isArray(processo.anexos)
                    ? processo.anexos
                    : (processo.anexo ? [processo.anexo] : [])
            };
            const processoEncoded = encodeURIComponent(JSON.stringify(processoParaEdicao));

            html += `
                <tr>
                    <td>
                        <strong>${processo.numero_processo || '-'}</strong>
                    </td>
                    <td>${processo.tipo_acao || '-'}</td>
                    <td><span class="badge bg-info">${processo.status || '-'}</span></td>
                    <td>${processo.tribunal || '-'}</td>
                    <td class="text-end">
                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); abrirProcessoClienteSubaba('${processoEncoded}')">
                            <i class="bi bi-pencil"></i> Editar
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
        container.dataset.loadedClienteId = clienteId;
    } catch (erro) {
        console.error('Erro ao carregar processos na subaba:', erro);
        limparSubabaProcessosCliente('Erro ao carregar processos deste cliente.');
    }
}

async function salvarCliente() {
    /*
    Salva um cliente no banco de dados (INSERT ou UPDATE)

    Processo:
    1. Obtém dados do formulário
    2. Valida dados obrigatórios
    3. Determina se é novo (POST) ou edição (PUT)
    4. Envia requisição AJAX
    5. Atualiza a tabela ou exibe erro
    */
    
    // Obtém dados do formulário
    const clienteId = document.getElementById('clienteId').value;
    const tipo = (document.getElementById('tipo_cliente')?.value || 'PF');
    const nome = (document.getElementById('nome')?.value || '').trim();
    const nacionalidade = (document.getElementById('nacionalidade')?.value || '').trim();
    const estado_civil = (document.getElementById('estado_civil')?.value || '').trim();
    const profissao = (document.getElementById('profissao')?.value || '').trim();
    const rg = (document.getElementById('rg')?.value || '').trim();
    const orgao_expedidor = (document.getElementById('orgao_expedidor')?.value || '').trim();
    const conjuge_nome = (document.getElementById('conjuge_nome')?.value || '').trim();
    const regime_bens = (document.getElementById('regime_bens')?.value || '').trim();
    const email = (document.getElementById('email')?.value || '').trim();
    const telefone = (document.getElementById('telefone')?.value || '').trim();
    // CPF (PF) field is 'cpf_cnpj'; CNPJ (PJ) field is 'cnpj_pj'
    const cpf_cnpj = (document.getElementById('cpf_cnpj')?.value || '').trim();
    const cnpj_pj = (document.getElementById('cnpj_pj')?.value || '').trim();
    const endereco = (document.getElementById('endereco')?.value || '').trim();
    const cidade = (document.getElementById('cidade')?.value || '').trim();
    const uf = (document.getElementById('uf')?.value || '').trim();
    // Campos PJ
    const razao_social = (document.getElementById('razao_social')?.value || '').trim();
    const nome_fantasia = (document.getElementById('nome_fantasia')?.value || '').trim();
    const inscricao_estadual = (document.getElementById('inscricao_estadual')?.value || '').trim();
    const inscricao_municipal = (document.getElementById('inscricao_municipal')?.value || '').trim();
    const socio_nome = (document.getElementById('socio_nome')?.value || '').trim();
    const socio_cpf = (document.getElementById('socio_cpf')?.value || '').trim();
    const socio_rg = (document.getElementById('socio_rg')?.value || '').trim();
    const cargo = (document.getElementById('cargo')?.value || '').trim();
    // Campos de Pagamento
    const forma_pagamento = (document.getElementById('forma_pagamento')?.value || '').trim();
    const referencia_pagamento = (document.getElementById('referencia_pagamento')?.value || '').trim();
    const contratoIdSelecionado = obterContratoIdDaReferencia(referencia_pagamento);
    const referenciaSelect = document.getElementById('referencia_pagamento');
    const valor_honorarios_raw = (document.getElementById('valor_honorarios')?.value || '').trim();
    const dia_vencimento_raw = (document.getElementById('dia_vencimento')?.value || '').trim();
    const observacoes_pagamento = (document.getElementById('observacoes_pagamento')?.value || '').trim();
    const numero_parcelas_raw = (document.getElementById('numero_parcelas')?.value || '').trim();

    const valor_honorarios = valor_honorarios_raw ? Number(valor_honorarios_raw) : null;
    const dia_vencimento = dia_vencimento_raw ? Number(dia_vencimento_raw) : null;
    const numero_parcelas = numero_parcelas_raw ? Number(numero_parcelas_raw) : null;
    const parcelas_pagamento = coletarParcelasPagamentoAtual();

    if (valor_honorarios_raw && (Number.isNaN(valor_honorarios) || valor_honorarios < 0)) {
        mostrarAlerta('Valor dos honorários inválido', 'warning');
        return;
    }

    if (dia_vencimento_raw && (!Number.isInteger(dia_vencimento) || dia_vencimento < 1 || dia_vencimento > 31)) {
        mostrarAlerta('Dia de vencimento deve estar entre 1 e 31', 'warning');
        return;
    }

    if (numero_parcelas_raw && (!Number.isInteger(numero_parcelas) || numero_parcelas < 1 || numero_parcelas > 60)) {
        mostrarAlerta('Número de parcelas deve estar entre 1 e 60', 'warning');
        return;
    }

    if (forma_pagamento && referenciaSelect && !referenciaSelect.disabled && !referencia_pagamento) {
        mostrarAlerta('Selecione o contrato referente ao pagamento.', 'warning');
        return;
    }

    const pagamentosPorContratoPayload = Array.isArray(pagamentosPorContratoAtual)
        ? pagamentosPorContratoAtual.filter((item) => item && item.contrato_id)
        : [];

    if (contratoIdSelecionado) {
        const dadosContratoSelecionado = {
            contrato_id: contratoIdSelecionado,
            referencia_pagamento: referencia_pagamento,
            forma_pagamento: forma_pagamento,
            valor_honorarios: valor_honorarios,
            dia_vencimento: dia_vencimento,
            observacoes_pagamento: observacoes_pagamento,
            numero_parcelas: numero_parcelas,
            parcelas_pagamento: numero_parcelas ? parcelas_pagamento : []
        };

        const indiceExistente = pagamentosPorContratoPayload.findIndex(
            (item) => (item?.contrato_id || '').trim() === contratoIdSelecionado
        );

        const temDadosPagamento = !!(
            dadosContratoSelecionado.forma_pagamento ||
            (dadosContratoSelecionado.valor_honorarios !== null && dadosContratoSelecionado.valor_honorarios !== undefined && dadosContratoSelecionado.valor_honorarios !== '') ||
            (dadosContratoSelecionado.dia_vencimento !== null && dadosContratoSelecionado.dia_vencimento !== undefined && dadosContratoSelecionado.dia_vencimento !== '') ||
            dadosContratoSelecionado.observacoes_pagamento ||
            (dadosContratoSelecionado.numero_parcelas !== null && dadosContratoSelecionado.numero_parcelas !== undefined && dadosContratoSelecionado.numero_parcelas !== '')
        );

        if (temDadosPagamento) {
            if (indiceExistente >= 0) {
                pagamentosPorContratoPayload[indiceExistente] = dadosContratoSelecionado;
            } else {
                pagamentosPorContratoPayload.push(dadosContratoSelecionado);
            }
        } else if (indiceExistente >= 0) {
            pagamentosPorContratoPayload.splice(indiceExistente, 1);
        }
    }

    pagamentosPorContratoAtual = pagamentosPorContratoPayload;
    
    // Validações básicas
    console.log('salvarCliente - valores coletados:', {
        tipo, nome, email, cpf_cnpj, endereco, estado_civil
    });
    // Diagnóstico adicional
    const elCpf = document.getElementById('cpf_cnpj');
    const elCnpj = document.getElementById('cnpj_pj');
    console.log('diagnostico elementos:', {
        elCpf_exists: !!elCpf,
        elCpf_value: elCpf ? elCpf.value : null,
        elCpf_length: elCpf ? elCpf.value.replace(/\D/g,'').length : 0,
        elCpf_visible: elCpf ? (elCpf.offsetParent !== null) : false,
        elCnpj_exists: !!elCnpj,
        elCnpj_value: elCnpj ? elCnpj.value : null,
        elCnpj_length: elCnpj ? elCnpj.value.replace(/\D/g,'').length : 0,
        elCnpj_visible: elCnpj ? (elCnpj.offsetParent !== null) : false
    });

    // detalhar quais campos faltam para diagnóstico
    const faltando = [];
    if (tipo === 'PF') {
        if (!nome) faltando.push('Nome');
        if (!email) faltando.push('Email');
        if (!cpf_cnpj) faltando.push('CPF');
        if (!endereco) faltando.push('Endereço residencial');
        if (faltando.length) {
            mostrarAlerta('Preencha: ' + faltando.join(', '), 'warning');
            return;
        }
        // se casado, exige nome do cônjuge e regime
        if (estado_civil === 'Casado' && (!conjuge_nome || !regime_bens)) {
            mostrarAlerta('Informe nome do cônjuge e regime de bens', 'warning');
            return;
        }
    } else {
        // PJ: exigir razão social e CNPJ
        if (!razao_social || !email || !cpf_cnpj) {
            mostrarAlerta('Preencha Razão Social, Email e CNPJ', 'warning');
            return;
        }
    }
    
    // Valida email
    if (!emailValido(email)) {
        mostrarAlerta('Email inválido', 'warning');
        return;
    }

    // Valida CPF (PF) ou CNPJ (PJ)
    let valorDocumento = cpf_cnpj;
    if (tipo === 'PJ') valorDocumento = cnpj_pj || cpf_cnpj;
    const somenteDigitos = (valorDocumento || '').replace(/\D/g, '');
    if (somenteDigitos.length === 11 && tipo === 'PF') {
        if (!cpfValido(somenteDigitos)) {
            mostrarAlerta('CPF inválido', 'warning');
            return;
        }
    } else if (somenteDigitos.length === 14 && tipo === 'PJ') {
        if (!validarCNPJ(somenteDigitos)) {
            mostrarAlerta('CNPJ inválido', 'warning');
            return;
        }
        // Verifica existência do CNPJ no backend (apenas para novo cadastro)
        if (!clienteId) {
            const existe = await verificarCNPJ(somenteDigitos);
            if (existe) {
                mostrarAlerta('CNPJ já cadastrado', 'warning');
                return;
            }
        }
    }
    
    // Dados a enviar ao backend
    const dados = {
        tipo: tipo,
        nome: tipo === 'PJ' ? (razao_social || nome) : nome,
        nacionalidade: nacionalidade,
        estado_civil: estado_civil,
        profissao: profissao,
        rg: rg,
        orgao_expedidor: orgao_expedidor,
        conjuge_nome: conjuge_nome,
        regime_bens: regime_bens,
        razao_social: razao_social,
        nome_fantasia: nome_fantasia,
        email: email,
        telefone: telefone,
        cpf_cnpj: tipo === 'PJ' ? (cnpj_pj || cpf_cnpj) : cpf_cnpj,
        endereco: endereco,
        cidade: cidade,
        uf: uf,
        inscricao_estadual: inscricao_estadual,
        inscricao_municipal: inscricao_municipal,
        socio_nome: socio_nome,
        socio_cpf: socio_cpf,
        socio_rg: socio_rg,
        cargo: cargo,
        forma_pagamento: forma_pagamento,
        referencia_pagamento: referencia_pagamento,
        valor_honorarios: valor_honorarios,
        dia_vencimento: dia_vencimento,
        observacoes_pagamento: observacoes_pagamento,
        numero_parcelas: numero_parcelas,
        parcelas_pagamento: numero_parcelas ? parcelas_pagamento : [],
        pagamentos_contratos: pagamentosPorContratoPayload
    };
    
    try {
        // Determina se é novo ou edição
        let url, metodo, mensagem;
        
        if (clienteId) {
            // EDIÇÃO: PUT /api/clientes/<id>/atualizar
            url = `/api/clientes/${clienteId}/atualizar`;
            metodo = 'PUT';
            mensagem = 'Cliente atualizado com sucesso!';
        } else {
            // NOVO: POST /api/clientes/novo
            url = '/api/clientes/novo';
            metodo = 'POST';
            mensagem = 'Cliente cadastrado com sucesso!';
        }
        
        // Envia requisição AJAX
        console.log('salvarCliente - payload enviado:', dados);
        const resposta = await fazRequisicao(url, metodo, dados);
        console.log('salvarCliente - resposta recebida:', resposta);
        
        if (resposta && (resposta.status === 200 || resposta.status === 201)) {
            mostrarAlerta(mensagem, 'success');
            
            // Fecha o modal
            fecharModal('modalCliente');
            
            // Limpa o formulário
            limparFormulario('formCliente');
            document.getElementById('clienteId').value = '';
            
            // Recarrega a página para atualizar tabela
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            mostrarAlerta(resposta.dados.message || 'Erro ao salvar cliente', 'danger');
        }
    } catch (erro) {
        console.error('Erro:', erro);
        mostrarAlerta('Erro ao salvar cliente', 'danger');
    }
}

// Validação de CNPJ em JavaScript
function validarCNPJ(cnpj) {
    if (!cnpj) return false;
    cnpj = cnpj.replace(/\D/g, '');
    if (cnpj.length !== 14) return false;
    if (/^(\d)\1+$/.test(cnpj)) return false;

    const t = cnpj.length - 2;
    const d = cnpj.substring(t);
    const d1 = parseInt(d.charAt(0));
    const d2 = parseInt(d.charAt(1));
    const calc = (x) => {
        let n = cnpj.substring(0, x);
        let y = x - 7;
        let s = 0;
        for (let i = x; i >= 1; i--) {
            s += n.charAt(x - i) * y--;
            if (y < 2) y = 9;
        }
        let r = s % 11;
        return r < 2 ? 0 : 11 - r;
    };
    return calc(12) === d1 && calc(13) === d2;
}

// Verifica no backend se CNPJ já existe
async function verificarCNPJ(cnpj) {
    try {
        const resp = await fazRequisicao('/api/clientes/verificar_cnpj', 'POST', { cnpj });
        if (resp && resp.status === 200) return resp.dados.exists === true;
    } catch (e) {
        console.error('Erro ao verificar CNPJ', e);
    }
    return false;
}

// Validação de CPF em JavaScript
function cpfValido(cpf) {
    if (!cpf || cpf.length !== 11) return false;
    if (/^(\d)\1{10}$/.test(cpf)) return false; // todos iguais

    const nums = cpf.split('').map(d => parseInt(d, 10));

    // Primeiro dígito
    let sum = 0;
    for (let i = 0; i < 9; i++) sum += nums[i] * (10 - i);
    let r = (sum * 10) % 11;
    if (r === 10) r = 0;
    if (r !== nums[9]) return false;

    // Segundo dígito
    sum = 0;
    for (let i = 0; i < 10; i++) sum += nums[i] * (11 - i);
    r = (sum * 10) % 11;
    if (r === 10) r = 0;
    if (r !== nums[10]) return false;

    return true;
}

// ============================================================================
// EDITAR CLIENTE
// ============================================================================

function editarCliente(id, nome, email, telefone, cpf_cnpj, endereco, cidade, uf) {
    // Abre o modal com dados do cliente buscando o JSON embutido na linha
    try {
        const jsonEl = document.getElementById(`cliente-${id}`);
        const dados = jsonEl ? JSON.parse(jsonEl.textContent) : null;

        pagamentosPorContratoAtual = Array.isArray(dados?.pagamentos_contratos)
            ? dados.pagamentos_contratos
            : [];

        document.getElementById('clienteId').value = id;
        if (dados) {
            const tipo = dados.tipo || (dados.cpf_cnpj && dados.cpf_cnpj.replace(/\D/g,'').length===14 ? 'PJ' : 'PF');
            document.getElementById('tipo_cliente').value = tipo;
            // Trigger change to show/hide blocks
            document.getElementById('tipo_cliente').dispatchEvent(new Event('change'));

            document.getElementById('nome').value = dados.nome || '';
            document.getElementById('email').value = dados.email || '';
            document.getElementById('telefone').value = dados.telefone || '';
            document.getElementById('cpf_cnpj').value = dados.cpf_cnpj || '';
            document.getElementById('endereco').value = dados.endereco || '';
            document.getElementById('cidade').value = dados.cidade || '';
            document.getElementById('uf').value = dados.uf || '';

            // PJ fields
            document.getElementById('razao_social').value = dados.razao_social || '';
            document.getElementById('nome_fantasia').value = dados.nome_fantasia || '';
            document.getElementById('inscricao_estadual').value = dados.inscricao_estadual || '';
            document.getElementById('inscricao_municipal').value = dados.inscricao_municipal || '';
            document.getElementById('socio_nome').value = dados.socio_nome || '';
            document.getElementById('socio_cpf').value = dados.socio_cpf || '';
            document.getElementById('socio_rg').value = dados.socio_rg || '';
            document.getElementById('cargo').value = dados.cargo || '';

            // Pagamento
            document.getElementById('forma_pagamento').value = dados.forma_pagamento || '';
            document.getElementById('referencia_pagamento').value = dados.referencia_pagamento || '';
            document.getElementById('valor_honorarios').value = (dados.valor_honorarios ?? '') === null ? '' : (dados.valor_honorarios ?? '');
            document.getElementById('dia_vencimento').value = (dados.dia_vencimento ?? '') === null ? '' : (dados.dia_vencimento ?? '');
            document.getElementById('observacoes_pagamento').value = dados.observacoes_pagamento || '';
            document.getElementById('numero_parcelas').value = (dados.numero_parcelas ?? '') === null ? '' : (dados.numero_parcelas ?? '');
            renderParcelasPagamento(dados.numero_parcelas || '', dados.parcelas_pagamento || []);
            atualizarResumoPagamento();

            // PF fields
            document.getElementById('nacionalidade').value = dados.nacionalidade || '';
            document.getElementById('estado_civil').value = dados.estado_civil || '';
            document.getElementById('profissao').value = dados.profissao || '';
            document.getElementById('rg').value = dados.rg || '';
            document.getElementById('orgao_expedidor').value = dados.orgao_expedidor || '';
            document.getElementById('conjuge_nome').value = dados.conjuge_nome || '';
            document.getElementById('regime_bens').value = dados.regime_bens || '';

            // Show spouse block if needed
            if ((dados.estado_civil || '') === 'Casado') {
                document.getElementById('conjugeBlock').style.display = '';
            } else {
                document.getElementById('conjugeBlock').style.display = 'none';
            }
        }

        document.getElementById('modalTitle').textContent = 'Editar Cliente';
        carregarReferenciasPagamentoCliente(id, dados?.referencia_pagamento || '');
        limparSubabaProcessosCliente('Abra a aba Processos para visualizar os processos deste cliente.');
        ativarAbaClienteDados();
        abrirModal('modalCliente');
    } catch (e) {
        console.error('Erro ao abrir modal de edição:', e);
        mostrarAlerta('Erro ao carregar dados do cliente', 'danger');
    }
}

// ============================================================================
// DELETAR CLIENTE
// ============================================================================

async function deletarCliente(id, nome) {
    /*
    Deleta (inativa) um cliente do sistema

    Processo:
    1. Pede confirmação ao usuário
    2. Se confirmado, envia DELETE request
    3. Remove linha da tabela ou recarrega página
    */
    
    // Pede confirmação
    if (!confirm(`Tem certeza que deseja remover o cliente "${nome}"?\n\nEsta ação não pode ser desfeita!`)) {
        return;
    }
    
    try {
        // Envia DELETE request
        const resposta = await fazRequisicao(
            `/api/clientes/${id}/deletar`,
            'DELETE'
        );
        
        if (resposta && resposta.status === 200) {
            mostrarAlerta('Cliente removido com sucesso!', 'success');
            
            // Remove a linha da tabela
            const tabela = document.getElementById('tabelaClientes');
            if (tabela) {
                const linhas = tabela.querySelectorAll('tbody tr');
                linhas.forEach(linha => {
                    if (linha.innerHTML.includes(id)) {
                        linha.remove();
                    }
                });
            }
            
            // Ou recarrega a página
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            mostrarAlerta(resposta.dados.message || 'Erro ao remover cliente', 'danger');
        }
    } catch (erro) {
        console.error('Erro:', erro);
        mostrarAlerta('Erro ao remover cliente', 'danger');
    }
}

// ============================================================================
// VER PROCESSOS DO CLIENTE
// ============================================================================

async function verProcessosCliente(clienteId) {
    /*
    Carrega e exibe os processos de um cliente em um modal

    Faz requisição AJAX para /api/clientes/<id>/processos
    */
    
    try {
        // Abre o modal (vazio, depois carrega dados)
        abrirModal('modalProcessosCliente');
        
        // Exibe spinner de carregamento
        document.getElementById('processosClienteBody').innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
            </div>
        `;
        
        // Requisição AJAX para obter processos
        const resposta = await fazRequisicao(
            `/api/clientes/${clienteId}/processos`,
            'GET'
        );
        
        if (resposta && resposta.status === 200) {
            const processos = resposta.dados.processos;
            
            if (processos.length > 0) {
                // Monta tabela com processos
                let html = `
                    <table class="table table-sm">
                        <thead class="table-light">
                            <tr>
                                <th>Número</th>
                                <th>Tipo</th>
                                <th>Status</th>
                                <th>Tribunal</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                processos.forEach(processo => {
                    html += `
                        <tr>
                            <td><strong>${processo.numero_processo}</strong></td>
                            <td>${processo.tipo_acao}</td>
                            <td><span class="badge bg-info">${processo.status}</span></td>
                            <td>${processo.tribunal}</td>
                        </tr>
                    `;
                });
                
                html += `
                        </tbody>
                    </table>
                `;
                
                document.getElementById('processosClienteBody').innerHTML = html;
            } else {
                document.getElementById('processosClienteBody').innerHTML = `
                    <div class="text-center text-muted py-4">
                        <i class="bi bi-inbox" style="font-size: 2rem;"></i>
                        <p class="mt-2">Nenhum processo encontrado para este cliente</p>
                    </div>
                `;
            }
        } else {
            mostrarAlerta('Erro ao carregar processos', 'danger');
        }
    } catch (erro) {
        console.error('Erro:', erro);
        mostrarAlerta('Erro ao carregar processos', 'danger');
    }
}

// ============================================================================
// ANOTAÇÕES DO CLIENTE
// ============================================================================

function abrirAnotacoesCliente(id) {
    try {
        const jsonEl = document.getElementById(`cliente-${id}`);
        const dados = jsonEl ? JSON.parse(jsonEl.textContent) : {};
        document.getElementById('anotacoesClienteId').value = id;
        document.getElementById('anotacoes_text').value = dados.anotacoes || '';
        abrirModal('modalAnotacoes');
    } catch (e) {
        console.error('Erro ao abrir anotacoes:', e);
        mostrarAlerta('Erro ao abrir anotações', 'danger');
    }
}

async function salvarAnotacoesCliente() {
    const id = document.getElementById('anotacoesClienteId').value;
    const texto = document.getElementById('anotacoes_text').value || '';
    if (!id) {
        mostrarAlerta('ID de cliente inválido', 'warning');
        return;
    }
    try {
        console.log('salvarAnotacoesCliente - payload:', { id, anotacoes: texto });
        const resposta = await fazRequisicao(`/api/clientes/${id}/anotacoes`, 'PUT', { anotacoes: texto });
        console.log('salvarAnotacoesCliente - resposta:', resposta);
        if (resposta && resposta.status === 200) {
            mostrarAlerta('Anotações salvas', 'success');
            fecharModal('modalAnotacoes');
            // Atualiza JSON embutido para futuras edições sem reload
            const jsonEl = document.getElementById(`cliente-${id}`);
            if (jsonEl) {
                try {
                    const obj = JSON.parse(jsonEl.textContent);
                    obj.anotacoes = texto;
                    jsonEl.textContent = JSON.stringify(obj);
                } catch (e) { /* ignore */ }
            }
        } else {
            mostrarAlerta(resposta.dados?.message || 'Erro ao salvar anotações', 'danger');
        }
    } catch (e) {
        console.error('Erro ao salvar anotações:', e);
        mostrarAlerta('Erro ao salvar anotações', 'danger');
    }
}

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Script de clientes carregado!');
    
    // Validação de CPF ao perder o foco (blur)
    const cpfInput = document.getElementById('cpf_cnpj');
    if (cpfInput) {
        cpfInput.addEventListener('blur', function () {
            const val = cpfInput.value.replace(/\D/g, '');
            if (val.length === 11) {
                if (!cpfValido(val)) {
                    mostrarAlerta('CPF inválido', 'warning');
                    cpfInput.classList.add('is-invalid');
                    cpfInput.classList.remove('is-valid');
                } else {
                    cpfInput.classList.remove('is-invalid');
                    cpfInput.classList.add('is-valid');
                }
            } else {
                // Remove estado visual se não parecer CPF
                cpfInput.classList.remove('is-valid');
                cpfInput.classList.remove('is-invalid');
            }
        });
    }

    // Limpa o formulário ao abrir modal novo
    document.getElementById('modalCliente').addEventListener('show.bs.modal', function (e) {
        // Se for novo (não edição), limpa formulário
        if (!document.getElementById('clienteId').value) {
            document.getElementById('modalTitle').textContent = 'Novo Cliente';
            limparFormulario('formCliente');
            pagamentosPorContratoAtual = [];
            definirSelectReferenciaPagamentoPadrao('Salve o cliente para habilitar a seleção de contrato');
            ativarAbaClienteDados();
            renderParcelasPagamento('');
            atualizarResumoPagamento();
            limparSubabaProcessosCliente('Salve o cliente para visualizar os processos vinculados.');
            // Remove classes de validação do CPF
            if (cpfInput) {
                cpfInput.classList.remove('is-valid');
                cpfInput.classList.remove('is-invalid');
            }
        }
    });

    const clienteProcessosTab = document.getElementById('cliente-processos-tab');
    if (clienteProcessosTab) {
        clienteProcessosTab.addEventListener('shown.bs.tab', function () {
            const clienteId = document.getElementById('clienteId')?.value || '';
            carregarProcessosClienteSubaba(clienteId);
        });
    }

    const clientePagamentoTab = document.getElementById('cliente-pagamento-tab');
    if (clientePagamentoTab) {
        clientePagamentoTab.addEventListener('shown.bs.tab', function () {
            const clienteId = document.getElementById('clienteId')?.value || '';
            const referenciaAtual = (document.getElementById('referencia_pagamento')?.value || '').trim();
            carregarReferenciasPagamentoCliente(clienteId, referenciaAtual);
        });
    }

    const referenciaPagamentoSelect = document.getElementById('referencia_pagamento');
    if (referenciaPagamentoSelect) {
        referenciaPagamentoSelect.addEventListener('change', function () {
            aplicarPagamentoDoContratoSelecionado();
        });
    }

    const numeroParcelasInput = document.getElementById('numero_parcelas');
    if (numeroParcelasInput) {
        numeroParcelasInput.addEventListener('change', function () {
            const atual = coletarParcelasPagamentoAtual();
            renderParcelasPagamento(numeroParcelasInput.value, atual);
        });
    }

    const diaVencimentoInput = document.getElementById('dia_vencimento');
    if (diaVencimentoInput) {
        diaVencimentoInput.addEventListener('change', function () {
            const atual = coletarParcelasPagamentoAtual();
            const numeroParcelasAtual = document.getElementById('numero_parcelas')?.value || '';
            renderParcelasPagamento(numeroParcelasAtual, atual);
        });
    }

    const valorHonorariosInput = document.getElementById('valor_honorarios');
    if (valorHonorariosInput) {
        valorHonorariosInput.addEventListener('input', atualizarResumoPagamento);
    }

    atualizarResumoPagamento();

    // Toggle PF / PJ
    const tipoSel = document.getElementById('tipo_cliente');
    if (tipoSel) {
        tipoSel.addEventListener('change', function () {
            const val = tipoSel.value;
            document.querySelectorAll('.pfFields').forEach(el => el.style.display = val === 'PF' ? '' : 'none');
            document.querySelectorAll('.pjFields').forEach(el => el.style.display = val === 'PJ' ? '' : 'none');
        });
    }

    // Estado civil -> mostrar bloco de cônjuge quando casado
    const estadoSel = document.getElementById('estado_civil');
    if (estadoSel) {
        estadoSel.addEventListener('change', function () {
            const val = estadoSel.value;
            const block = document.getElementById('conjugeBlock');
            if (block) block.style.display = val === 'Casado' ? '' : 'none';
        });
    }



    const cnpjInput = document.getElementById('cnpj_pj');
    if (cnpjInput) {
        cnpjInput.addEventListener('blur', async function () {
            const val = cnpjInput.value.replace(/\D/g, '');
            if (val.length === 14) {
                if (!validarCNPJ(val)) {
                    mostrarAlerta('CNPJ inválido', 'warning');
                    cnpjInput.classList.add('is-invalid');
                    cnpjInput.classList.remove('is-valid');
                } else {
                    const existe = await verificarCNPJ(val);
                    if (existe) {
                        mostrarAlerta('CNPJ já cadastrado', 'warning');
                        cnpjInput.classList.add('is-invalid');
                        cnpjInput.classList.remove('is-valid');
                    } else {
                        cnpjInput.classList.remove('is-invalid');
                        cnpjInput.classList.add('is-valid');
                    }
                }
            } else {
                cnpjInput.classList.remove('is-valid');
                cnpjInput.classList.remove('is-invalid');
            }
        });
    }
});
