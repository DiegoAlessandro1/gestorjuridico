/* ============================================================================
   JAVASCRIPT - AGENDA DE COMPROMISSOS
   ============================================================================
   Arquivo: static/js/agenda.js
   Propósito: Funções AJAX para gestão de compromissos
   ============================================================================ */

let compromissosAgenda = [];
let calendarioMesAtual = new Date();
let dataFiltroSelecionada = '';
let filtroRecebimentosAutomaticos = false;
let filtroRecebimentoCliente = '';

function formatarIsoData(ano, mes, dia) {
    return `${ano}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`;
}

function calcularPascoa(ano) {
    const a = ano % 19;
    const b = Math.floor(ano / 100);
    const c = ano % 100;
    const d = Math.floor(b / 4);
    const e = b % 4;
    const f = Math.floor((b + 8) / 25);
    const g = Math.floor((b - f + 1) / 3);
    const h = (19 * a + b - d - g + 15) % 30;
    const i = Math.floor(c / 4);
    const k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7;
    const m = Math.floor((a + 11 * h + 22 * l) / 451);
    const mes = Math.floor((h + l - 7 * m + 114) / 31);
    const dia = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(ano, mes - 1, dia);
}

function adicionarDias(dataBase, dias) {
    const data = new Date(dataBase.getFullYear(), dataBase.getMonth(), dataBase.getDate());
    data.setDate(data.getDate() + dias);
    return data;
}

function mapaFeriadosBrasil(ano) {
    const feriados = {};
    const adicionar = (data, nome) => {
        feriados[formatarIsoData(data.getFullYear(), data.getMonth() + 1, data.getDate())] = nome;
    };

    adicionar(new Date(ano, 0, 1), 'Confraternização Universal');
    adicionar(new Date(ano, 3, 21), 'Tiradentes');
    adicionar(new Date(ano, 4, 1), 'Dia do Trabalhador');
    adicionar(new Date(ano, 8, 7), 'Independência do Brasil');
    adicionar(new Date(ano, 9, 12), 'Nossa Senhora Aparecida');
    adicionar(new Date(ano, 10, 2), 'Finados');
    adicionar(new Date(ano, 10, 15), 'Proclamação da República');
    adicionar(new Date(ano, 11, 25), 'Natal');

    const pascoa = calcularPascoa(ano);
    adicionar(adicionarDias(pascoa, -47), 'Carnaval');
    adicionar(adicionarDias(pascoa, -2), 'Sexta-feira Santa');
    adicionar(adicionarDias(pascoa, 60), 'Corpus Christi');

    return feriados;
}

function classeTipo(tipo) {
    if (tipo === 'Audiência') return 'bg-primary';
    if (tipo === 'Prazo') return 'bg-warning text-dark';
    if (tipo === 'Pagamento') return 'bg-danger';
    if (tipo === 'Recebimento') return 'bg-success';
    if (tipo === 'Consulta') return 'bg-info text-dark';
    return 'bg-secondary';
}

document.addEventListener('DOMContentLoaded', function() {
    compromissosAgenda = Array.isArray(window.__agendaCompromissos) ? window.__agendaCompromissos : [];

    const modal = document.getElementById('modalAgenda');
    if (modal) {
        modal.addEventListener('show.bs.modal', function() {
            carregarClientesAgenda();

            if (!document.getElementById('compromissoId').value) {
                document.getElementById('modalAgendaTitle').textContent = 'Novo Compromisso';
                limparFormulario('formAgenda');
                document.getElementById('forum_competencia').value = '';
                document.getElementById('numero_processo').value = '';
                document.getElementById('tipo_prazo').value = '';
                document.getElementById('data_publicacao').value = '';
                document.getElementById('dias_uteis_prazo').value = '';
                document.getElementById('tipo_audiencia').value = '';
                document.getElementById('formato_audiencia').value = '';
                document.getElementById('link_reuniao_virtual').value = '';
                togglePrazoFields();
            }
        });
    }

    const tipoSelect = document.getElementById('tipo');
    const formatoAudienciaSelect = document.getElementById('formato_audiencia');
    if (tipoSelect) {
        tipoSelect.addEventListener('change', togglePrazoFields);
    }
    if (formatoAudienciaSelect) {
        formatoAudienciaSelect.addEventListener('change', togglePrazoFields);
    }

    const prevBtn = document.getElementById('calPrevMonth');
    const nextBtn = document.getElementById('calNextMonth');
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            calendarioMesAtual.setMonth(calendarioMesAtual.getMonth() - 1);
            renderAgendaCalendar();
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            calendarioMesAtual.setMonth(calendarioMesAtual.getMonth() + 1);
            renderAgendaCalendar();
        });
    }

    const filtroAuto = document.getElementById('filtroRecebimentosAuto');
    const filtroCliente = document.getElementById('filtroRecebimentoCliente');
    const limparFiltros = document.getElementById('limparFiltroRecebimento');

    if (filtroAuto) {
        filtroAuto.addEventListener('change', function() {
            filtroRecebimentosAutomaticos = !!filtroAuto.checked;
            if (filtroCliente) {
                filtroCliente.disabled = !filtroRecebimentosAutomaticos;
                if (!filtroRecebimentosAutomaticos) {
                    filtroCliente.value = '';
                    filtroRecebimentoCliente = '';
                }
            }
            renderTabelaAgenda();
        });
    }

    if (filtroCliente) {
        filtroCliente.addEventListener('change', function() {
            filtroRecebimentoCliente = filtroCliente.value || '';
            renderTabelaAgenda();
        });
    }

    if (limparFiltros) {
        limparFiltros.addEventListener('click', function() {
            dataFiltroSelecionada = '';
            filtroRecebimentosAutomaticos = false;
            filtroRecebimentoCliente = '';
            if (filtroAuto) filtroAuto.checked = false;
            if (filtroCliente) {
                filtroCliente.value = '';
                filtroCliente.disabled = true;
            }
            renderAgendaCalendar();
            renderTabelaAgenda();
        });
    }

    atualizarFiltroClientesRecebimento();

    renderAgendaCalendar();
    renderTabelaAgenda();
    renderAvisoPrazos();
    togglePrazoFields();
});

function parseDataLocal(dataIso) {
    if (!dataIso || typeof dataIso !== 'string' || dataIso.length < 10) return null;
    const partes = dataIso.split('-');
    if (partes.length < 3) return null;
    const ano = Number(partes[0]);
    const mes = Number(partes[1]);
    const dia = Number(partes[2]);
    if (!ano || !mes || !dia) return null;
    return new Date(ano, mes - 1, dia);
}

function atualizarFiltroClientesRecebimento() {
    const filtroCliente = document.getElementById('filtroRecebimentoCliente');
    if (!filtroCliente) return;

    const valorAtual = filtroCliente.value || '';
    const mapaClientes = new Map();

    compromissosAgenda.forEach((item) => {
        if (item?.tipo !== 'Recebimento' || item?.origem !== 'cliente_pagamento') return;
        const id = (item.cliente_id || '').trim();
        if (!id) return;
        mapaClientes.set(id, (item.cliente_nome || 'Cliente').trim() || 'Cliente');
    });

    filtroCliente.innerHTML = '<option value="">Todos os clientes</option>';
    Array.from(mapaClientes.entries())
        .sort((a, b) => a[1].localeCompare(b[1], 'pt-BR'))
        .forEach(([id, nome]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = nome;
            filtroCliente.appendChild(option);
        });

    if (valorAtual && mapaClientes.has(valorAtual)) {
        filtroCliente.value = valorAtual;
    } else {
        filtroCliente.value = '';
        filtroRecebimentoCliente = '';
    }
}

function adicionarDiasUteis(dataIso, diasUteis) {
    const base = parseDataLocal(dataIso);
    if (!base || !Number.isInteger(diasUteis) || diasUteis < 1) return '';

    const data = new Date(base.getFullYear(), base.getMonth(), base.getDate());
    let restantes = diasUteis;

    while (restantes > 0) {
        data.setDate(data.getDate() + 1);
        const diaSemana = data.getDay();
        if (diaSemana !== 0 && diaSemana !== 6) {
            restantes -= 1;
        }
    }

    const ano = data.getFullYear();
    const mes = String(data.getMonth() + 1).padStart(2, '0');
    const dia = String(data.getDate()).padStart(2, '0');
    return `${ano}-${mes}-${dia}`;
}

function renderAvisoPrazos() {
    const container = document.getElementById('agendaPrazoAlert');
    if (!container) return;

    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    const msDia = 24 * 60 * 60 * 1000;

    const compromissosAte3DiasPorTipo = (tipo) => compromissosAgenda.filter(item => {
        if (item.tipo !== tipo) return false;
        const dataItem = parseDataLocal(item.data);
        if (!dataItem) return false;
        dataItem.setHours(0, 0, 0, 0);
        const diffDias = Math.round((dataItem.getTime() - hoje.getTime()) / msDia);
        return diffDias >= 0 && diffDias <= 3;
    });

    const prazos3dias = compromissosAte3DiasPorTipo('Prazo');
    const audiencias3dias = compromissosAte3DiasPorTipo('Audiência');
    const pagamentos3dias = compromissosAte3DiasPorTipo('Pagamento');
    const recebimentos3dias = compromissosAte3DiasPorTipo('Recebimento');
    const consultas3dias = compromissosAte3DiasPorTipo('Consulta');

    const ordenarPorDataHora = (a, b) => {
        const chaveA = `${a.data || ''} ${a.hora || ''}`;
        const chaveB = `${b.data || ''} ${b.hora || ''}`;
        return chaveA.localeCompare(chaveB);
    };

    const diasRestantes = (dataIso) => {
        const dataItem = parseDataLocal(dataIso);
        if (!dataItem) return null;
        dataItem.setHours(0, 0, 0, 0);
        return Math.round((dataItem.getTime() - hoje.getTime()) / msDia);
    };

    const textoPrazoRestante = (dataIso) => {
        const dias = diasRestantes(dataIso);
        if (dias === null) return 'prazo indefinido';
        if (dias <= 0) return 'vence hoje';
        if (dias === 1) return 'falta 1 dia';
        return `faltam ${dias} dias`;
    };

    const montarResumoComPrazo = (lista, tituloPadrao) => lista
        .slice(0, 3)
        .map(item => `${item.data || '--/--/----'} ${item.titulo || tituloPadrao} (${textoPrazoRestante(item.data)})`)
        .join(' • ');

    prazos3dias.sort(ordenarPorDataHora);
    audiencias3dias.sort(ordenarPorDataHora);
    pagamentos3dias.sort(ordenarPorDataHora);
    recebimentos3dias.sort(ordenarPorDataHora);
    consultas3dias.sort(ordenarPorDataHora);

    if (!prazos3dias.length && !audiencias3dias.length && !pagamentos3dias.length && !recebimentos3dias.length && !consultas3dias.length) {
        container.innerHTML = '';
        return;
    }

    const blocos = [];

    if (prazos3dias.length) {
        const resumoPrazos = montarResumoComPrazo(prazos3dias, 'Prazo');
        const extraPrazos = prazos3dias.length > 3 ? ` e mais ${prazos3dias.length - 3}` : '';

        blocos.push(`
            <div class="alert alert-warning shadow-sm mb-2" role="alert">
                <strong>Aviso de prazo:</strong> você tem ${prazos3dias.length} prazo(s) próximos. ${resumoPrazos}${extraPrazos}
            </div>
        `);
    }

    if (audiencias3dias.length) {
        const resumoAudiencias = montarResumoComPrazo(audiencias3dias, 'Audiência');
        const extraAudiencias = audiencias3dias.length > 3 ? ` e mais ${audiencias3dias.length - 3}` : '';

        blocos.push(`
            <div class="alert alert-primary shadow-sm mb-0" role="alert">
                <strong>Aviso de audiência:</strong> você tem ${audiencias3dias.length} audiência(s) próximas. ${resumoAudiencias}${extraAudiencias}
            </div>
        `);
    }

    if (pagamentos3dias.length) {
        const resumoPagamentos = montarResumoComPrazo(pagamentos3dias, 'Pagamento');
        const extraPagamentos = pagamentos3dias.length > 3 ? ` e mais ${pagamentos3dias.length - 3}` : '';

        blocos.push(`
            <div class="alert alert-danger shadow-sm mb-2" role="alert">
                <strong>Aviso de pagamento:</strong> você tem ${pagamentos3dias.length} pagamento(s) próximos. ${resumoPagamentos}${extraPagamentos}
            </div>
        `);
    }

    if (recebimentos3dias.length) {
        const resumoRecebimentos = montarResumoComPrazo(recebimentos3dias, 'Recebimento');
        const extraRecebimentos = recebimentos3dias.length > 3 ? ` e mais ${recebimentos3dias.length - 3}` : '';

        blocos.push(`
            <div class="alert alert-success shadow-sm mb-2" role="alert">
                <strong>Aviso de recebimento:</strong> você tem ${recebimentos3dias.length} recebimento(s) próximos. ${resumoRecebimentos}${extraRecebimentos}
            </div>
        `);
    }

    if (consultas3dias.length) {
        const resumoConsultas = montarResumoComPrazo(consultas3dias, 'Consulta');
        const extraConsultas = consultas3dias.length > 3 ? ` e mais ${consultas3dias.length - 3}` : '';

        blocos.push(`
            <div class="alert alert-info shadow-sm mb-0" role="alert">
                <strong>Aviso de consulta:</strong> você tem ${consultas3dias.length} consulta(s) próximas. ${resumoConsultas}${extraConsultas}
            </div>
        `);
    }

    container.innerHTML = blocos.join('');
}

function togglePrazoFields() {
    const tipo = document.getElementById('tipo')?.value || '';
    const campoDataCompromisso = document.getElementById('campoDataCompromisso');
    const dataInput = document.getElementById('data');
    const campoHoraCompromisso = document.getElementById('campoHoraCompromisso');
    const horaInput = document.getElementById('hora');
    const campoLocalCompromisso = document.getElementById('campoLocalCompromisso');
    const localInput = document.getElementById('local');
    const prazoFields = document.getElementById('prazoFields');
    const audienciaFields = document.getElementById('audienciaFields');
    const audienciaVirtualFields = document.getElementById('audienciaVirtualFields');
    const forumInput = document.getElementById('forum_competencia');
    const numeroInput = document.getElementById('numero_processo');
    const tipoPrazoInput = document.getElementById('tipo_prazo');
    const dataPublicacaoInput = document.getElementById('data_publicacao');
    const diasUteisInput = document.getElementById('dias_uteis_prazo');
    const tipoAudienciaInput = document.getElementById('tipo_audiencia');
    const formatoAudienciaInput = document.getElementById('formato_audiencia');
    const linkVirtualInput = document.getElementById('link_reuniao_virtual');

    if (!campoDataCompromisso || !dataInput || !campoHoraCompromisso || !horaInput || !campoLocalCompromisso || !localInput || !prazoFields || !audienciaFields || !audienciaVirtualFields || !forumInput || !numeroInput || !tipoPrazoInput || !dataPublicacaoInput || !diasUteisInput || !tipoAudienciaInput || !formatoAudienciaInput || !linkVirtualInput) return;

    const isPrazo = tipo === 'Prazo';
    const isAudiencia = tipo === 'Audiência';
    const isAudienciaPresencial = isAudiencia && formatoAudienciaInput.value === 'Presencial';
    const isAudienciaVirtual = isAudiencia && formatoAudienciaInput.value === 'Virtual';

    campoDataCompromisso.style.display = isPrazo ? 'none' : '';
    dataInput.required = !isPrazo;
    if (isPrazo) {
        dataInput.value = '';
    }

    const mostrarHora = !isAudiencia || isAudienciaPresencial;
    campoHoraCompromisso.style.display = mostrarHora ? '' : 'none';
    horaInput.required = mostrarHora;
    if (!mostrarHora) {
        horaInput.value = '';
    }

    const mostrarLocal = !isAudiencia || isAudienciaPresencial;
    campoLocalCompromisso.style.display = mostrarLocal ? '' : 'none';
    if (isAudienciaVirtual) {
        localInput.value = '';
    }

    prazoFields.style.display = isPrazo ? '' : 'none';
    audienciaFields.style.display = isAudiencia ? '' : 'none';
    audienciaVirtualFields.style.display = isAudienciaVirtual ? '' : 'none';
    forumInput.required = isPrazo;
    numeroInput.required = isPrazo;
    tipoPrazoInput.required = isPrazo;
    dataPublicacaoInput.required = isPrazo;
    diasUteisInput.required = isPrazo;
    tipoAudienciaInput.required = isAudiencia;
    formatoAudienciaInput.required = isAudiencia;
    linkVirtualInput.required = isAudienciaVirtual;

    if (!isPrazo) {
        forumInput.value = '';
        numeroInput.value = '';
        tipoPrazoInput.value = '';
        dataPublicacaoInput.value = '';
        diasUteisInput.value = '';
    }

    if (!isAudiencia) {
        tipoAudienciaInput.value = '';
        formatoAudienciaInput.value = '';
        linkVirtualInput.value = '';
    }

    if (isAudiencia && !isAudienciaVirtual) {
        linkVirtualInput.value = '';
    }
}

function renderAgendaCalendar() {
    const meses = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
    const monthLabel = document.getElementById('calendarMonthLabel');
    const body = document.getElementById('agendaCalendarBody');
    if (!monthLabel || !body) return;

    const ano = calendarioMesAtual.getFullYear();
    const mes = calendarioMesAtual.getMonth();
    const feriadosAno = mapaFeriadosBrasil(ano);
    monthLabel.textContent = `${meses[mes]} de ${ano}`;

    const primeiroDia = new Date(ano, mes, 1).getDay();
    const totalDias = new Date(ano, mes + 1, 0).getDate();

    const eventosPorDia = {};
    compromissosAgenda
        .filter(item => typeof item.data === 'string' && item.data.length >= 10)
        .forEach(item => {
            if (!eventosPorDia[item.data]) {
                eventosPorDia[item.data] = { total: 0, tipos: new Set() };
            }
            eventosPorDia[item.data].total += 1;
            if (item.tipo) {
                eventosPorDia[item.data].tipos.add(item.tipo);
            }
        });

    body.innerHTML = '';
    let dia = 1;

    for (let linha = 0; linha < 6; linha++) {
        const tr = document.createElement('tr');
        for (let col = 0; col < 7; col++) {
            const td = document.createElement('td');
            td.style.height = '74px';
            td.style.verticalAlign = 'top';

            if ((linha === 0 && col < primeiroDia) || dia > totalDias) {
                td.className = 'bg-light';
            } else {
                const diaStr = String(dia).padStart(2, '0');
                const mesStr = String(mes + 1).padStart(2, '0');
                const dataIso = `${ano}-${mesStr}-${diaStr}`;
                const infoDia = eventosPorDia[dataIso];
                const nomeFeriado = feriadosAno[dataIso] || '';

                const selos = [];
                if (infoDia && infoDia.total > 0) {
                    const tipos = Array.from(infoDia.tipos);
                    if (tipos.length === 1) {
                        selos.push(`<span class="badge ${classeTipo(tipos[0])} mt-1">${tipos[0]}</span>`);
                    } else {
                        selos.push(`<span class="badge bg-dark mt-1">${infoDia.total} eventos</span>`);
                    }
                }

                if (nomeFeriado) {
                    selos.push('<span class="badge bg-light text-danger border border-danger-subtle mt-1">Feriado</span>');
                    td.classList.add('table-danger');
                    td.title = nomeFeriado;
                }

                td.innerHTML = `<div class="fw-semibold">${dia}</div>${selos.join('<br>')}`;
                td.style.cursor = 'pointer';
                if (dataFiltroSelecionada === dataIso) {
                    td.classList.add('table-primary');
                }
                td.addEventListener('click', function() {
                    dataFiltroSelecionada = (dataFiltroSelecionada === dataIso) ? '' : dataIso;
                    renderAgendaCalendar();
                    renderTabelaAgenda();
                });
                dia++;
            }
            tr.appendChild(td);
        }
        body.appendChild(tr);
        if (dia > totalDias) break;
    }
}

function renderTabelaAgenda() {
    const tbody = document.getElementById('agendaTableBody');
    if (!tbody) return;

    const lista = compromissosAgenda
        .filter(item => !dataFiltroSelecionada || item.data === dataFiltroSelecionada)
        .filter(item => {
            if (!filtroRecebimentosAutomaticos) return true;
            return item.tipo === 'Recebimento' && item.origem === 'cliente_pagamento';
        })
        .filter(item => {
            if (!filtroRecebimentosAutomaticos || !filtroRecebimentoCliente) return true;
            return (item.cliente_id || '') === filtroRecebimentoCliente;
        })
        .sort((a, b) => `${a.data || ''} ${a.hora || ''}`.localeCompare(`${b.data || ''} ${b.hora || ''}`));

    if (!lista.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-muted py-5">
                    <i class="bi bi-calendar-x" style="font-size: 2rem;"></i>
                    <p class="mt-2 mb-0">Nenhum compromisso encontrado com os filtros atuais</p>
                </td>
            </tr>
        `;
        return;
    }

    const statusBadge = (status) => {
        if (status === 'Agendado') return 'bg-success';
        if (status === 'Concluído') return 'bg-info';
        return 'bg-secondary';
    };

    const extrairReferencia = (item) => {
        const refCampo = (item?.referencia_pagamento || '').trim();
        if (refCampo) return refCampo;

        const observacoes = (item?.observacoes || '').trim();
        const match = observacoes.match(/Ref\.:\s*(.+)$/i);
        if (match && match[1]) {
            return match[1].trim();
        }

        return '-';
    };

    tbody.innerHTML = '';
    lista.forEach(item => {
        const tr = document.createElement('tr');

        const cData = document.createElement('td');
        cData.textContent = item.data || '-';
        tr.appendChild(cData);

        const cHora = document.createElement('td');
        cHora.textContent = item.hora || '-';
        tr.appendChild(cHora);

        const cTipo = document.createElement('td');
        cTipo.innerHTML = `<span class="badge ${classeTipo(item.tipo)}">${item.tipo || '-'}</span>`;
        tr.appendChild(cTipo);

        const cModalidade = document.createElement('td');
        if (item.tipo === 'Audiência' && item.formato_audiencia) {
            const classeModalidade = item.formato_audiencia === 'Virtual' ? 'bg-info text-dark' : 'bg-secondary';
            cModalidade.innerHTML = `<span class="badge ${classeModalidade}">${item.formato_audiencia}</span>`;
        } else {
            cModalidade.textContent = '-';
        }
        tr.appendChild(cModalidade);

        const cTitulo = document.createElement('td');
        cTitulo.textContent = item.titulo || '-';
        tr.appendChild(cTitulo);

        const cCliente = document.createElement('td');
        cCliente.textContent = item.cliente_nome || '-';
        tr.appendChild(cCliente);

        const cReferencia = document.createElement('td');
        cReferencia.textContent = extrairReferencia(item);
        tr.appendChild(cReferencia);

        const cStatus = document.createElement('td');
        cStatus.innerHTML = `<span class="badge ${statusBadge(item.status)}">${item.status || 'Agendado'}</span>`;
        tr.appendChild(cStatus);

        const cLocal = document.createElement('td');
        if (item.tipo === 'Audiência' && item.formato_audiencia === 'Virtual') {
            const link = (item.link_reuniao_virtual || '').trim();
            if (link) {
                cLocal.innerHTML = `<a href="${link}" target="_blank" rel="noopener noreferrer">Abrir link</a>`;
            } else {
                cLocal.textContent = '-';
            }
        } else if (item.tipo === 'Audiência' && item.formato_audiencia === 'Presencial') {
            cLocal.textContent = item.local || '-';
        } else {
            cLocal.textContent = item.local || '-';
        }
        tr.appendChild(cLocal);

        const cAcoes = document.createElement('td');
        cAcoes.className = 'text-end';

        const btnEditar = document.createElement('button');
        btnEditar.className = 'btn btn-sm btn-primary';
        btnEditar.innerHTML = '<i class="bi bi-pencil"></i> Editar';
        btnEditar.addEventListener('click', function() {
            editarCompromisso(
                item._id,
                item.titulo || '',
                item.tipo || '',
                item.data || '',
                item.hora || '',
                item.cliente_id || '',
                item.status || 'Agendado',
                item.local || '',
                item.observacoes || '',
                item.forum_competencia || '',
                item.numero_processo || '',
                item.tipo_prazo || '',
                item.data_publicacao || '',
                item.dias_uteis_prazo || '',
                item.tipo_audiencia || '',
                item.formato_audiencia || '',
                item.link_reuniao_virtual || ''
            );
        });

        const btnDeletar = document.createElement('button');
        btnDeletar.className = 'btn btn-sm btn-danger ms-1';
        btnDeletar.innerHTML = '<i class="bi bi-trash"></i> Deletar';
        btnDeletar.addEventListener('click', function() {
            deletarCompromisso(item._id, item.titulo || '');
        });

        cAcoes.appendChild(btnEditar);
        cAcoes.appendChild(btnDeletar);
        tr.appendChild(cAcoes);

        tbody.appendChild(tr);
    });
}

// ============================================================================
// CARREGAR CLIENTES
// ============================================================================

async function carregarClientesAgenda(clienteSelecionado = '') {
    const selectCliente = document.getElementById('cliente_id');

    try {
        const resposta = await fazRequisicao('/api/clientes/lista', 'GET');

        if (!resposta || resposta.status !== 200 || !resposta.dados?.success) {
            mostrarAlerta(resposta?.dados?.message || 'Não foi possível carregar clientes', 'danger');
            return;
        }

        selectCliente.innerHTML = '<option value="">Selecionar cliente...</option>';

        const clientes = resposta.dados.clientes || [];
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
// SALVAR COMPROMISSO
// ============================================================================

async function salvarCompromisso() {
    const compromissoId = document.getElementById('compromissoId').value;
    const titulo = document.getElementById('titulo').value;
    const tipo = document.getElementById('tipo').value;
    const data = document.getElementById('data').value;
    const hora = document.getElementById('hora').value;
    const status = document.getElementById('status').value;
    const cliente_id = document.getElementById('cliente_id').value;
    const local = document.getElementById('local').value;
    const observacoes = document.getElementById('observacoes').value;
    const forum_competencia = document.getElementById('forum_competencia').value;
    const numero_processo = document.getElementById('numero_processo').value;
    const tipo_prazo = document.getElementById('tipo_prazo').value;
    const data_publicacao = document.getElementById('data_publicacao').value;
    const dias_uteis_prazo = document.getElementById('dias_uteis_prazo').value;
    const tipo_audiencia = document.getElementById('tipo_audiencia').value;
    const formato_audiencia = document.getElementById('formato_audiencia').value;
    const link_reuniao_virtual = document.getElementById('link_reuniao_virtual').value.trim();

    if (!titulo || !tipo) {
        mostrarAlerta('Preencha todos os campos obrigatórios (*)', 'warning');
        return;
    }

    const exigeHora = tipo !== 'Audiência' || formato_audiencia === 'Presencial';
    if (exigeHora && !hora) {
        mostrarAlerta('Preencha o campo Hora para este compromisso', 'warning');
        return;
    }

    if (tipo !== 'Prazo' && !data) {
        mostrarAlerta('Preencha o campo Data para este tipo de compromisso', 'warning');
        return;
    }

    if (tipo === 'Prazo' && (!forum_competencia || !numero_processo || !tipo_prazo || !data_publicacao || !dias_uteis_prazo)) {
        mostrarAlerta('Para compromisso do tipo Prazo, preencha Fórum, Número do processo, Tipo de prazo, Data de publicação e Dias úteis', 'warning');
        return;
    }

    if (tipo === 'Audiência' && !tipo_audiencia) {
        mostrarAlerta('Para compromisso do tipo Audiência, selecione o tipo de audiência', 'warning');
        return;
    }

    if (tipo === 'Audiência' && !formato_audiencia) {
        mostrarAlerta('Para compromisso do tipo Audiência, selecione se será presencial ou virtual', 'warning');
        return;
    }

    if (tipo === 'Audiência' && formato_audiencia === 'Presencial' && !local.trim()) {
        mostrarAlerta('Para audiência presencial, informe o local', 'warning');
        return;
    }

    if (tipo === 'Audiência' && formato_audiencia === 'Virtual' && !link_reuniao_virtual) {
        mostrarAlerta('Para audiência virtual, informe o link da reunião', 'warning');
        return;
    }

    const diasUteisNumero = Number(dias_uteis_prazo);
    if (tipo === 'Prazo' && (!Number.isInteger(diasUteisNumero) || diasUteisNumero < 1 || diasUteisNumero > 25)) {
        mostrarAlerta('Dias úteis do prazo deve estar entre 1 e 25', 'warning');
        return;
    }

    const dataCalculadaPrazo = tipo === 'Prazo' ? adicionarDiasUteis(data_publicacao, diasUteisNumero) : '';
    if (tipo === 'Prazo' && !dataCalculadaPrazo) {
        mostrarAlerta('Não foi possível calcular a data do prazo a partir da data de publicação e dias úteis', 'danger');
        return;
    }

    const clienteOption = document.getElementById('cliente_id').selectedOptions[0];
    const dados = {
        titulo,
        tipo,
        data: tipo === 'Prazo' ? dataCalculadaPrazo : data,
        hora: exigeHora ? hora : '',
        status,
        cliente_id,
        cliente_nome: clienteOption ? clienteOption.textContent : '',
        local: (tipo === 'Audiência' && formato_audiencia === 'Virtual') ? '' : local,
        observacoes,
        forum_competencia,
        numero_processo,
        tipo_prazo,
        data_publicacao,
        dias_uteis_prazo: tipo === 'Prazo' ? diasUteisNumero : '',
        tipo_audiencia: tipo === 'Audiência' ? tipo_audiencia : '',
        formato_audiencia: tipo === 'Audiência' ? formato_audiencia : '',
        link_reuniao_virtual: (tipo === 'Audiência' && formato_audiencia === 'Virtual') ? link_reuniao_virtual : ''
    };

    try {
        let url, metodo, mensagem;

        if (compromissoId) {
            url = `/api/agenda/${compromissoId}/atualizar`;
            metodo = 'PUT';
            mensagem = 'Compromisso atualizado com sucesso!';
        } else {
            url = '/api/agenda/nova';
            metodo = 'POST';
            mensagem = 'Compromisso cadastrado com sucesso!';
        }

        const resposta = await fazRequisicao(url, metodo, dados);

        if (resposta && (resposta.status === 200 || resposta.status === 201)) {
            mostrarAlerta(mensagem, 'success');
            fecharModal('modalAgenda');
            limparFormulario('formAgenda');
            document.getElementById('compromissoId').value = '';
            await carregarAgenda();
        } else {
            mostrarAlerta(resposta.dados.message || 'Erro ao salvar compromisso', 'danger');
        }
    } catch (erro) {
        console.error('Erro:', erro);
        mostrarAlerta('Erro ao salvar compromisso', 'danger');
    }
}

// ============================================================================
// EDITAR COMPROMISSO
// ============================================================================

async function editarCompromisso(id, titulo, tipo, data, hora, clienteId, status, local, observacoes, forumCompetencia, numeroProcesso, tipoPrazo, dataPublicacao, diasUteisPrazo, tipoAudiencia, formatoAudiencia, linkReuniaoVirtual) {
    document.getElementById('compromissoId').value = id;
    document.getElementById('titulo').value = titulo;
    document.getElementById('tipo').value = tipo;
    document.getElementById('data').value = data;
    document.getElementById('hora').value = hora;
    document.getElementById('status').value = status;
    document.getElementById('local').value = local;
    document.getElementById('observacoes').value = observacoes;
    document.getElementById('forum_competencia').value = forumCompetencia || '';
    document.getElementById('numero_processo').value = numeroProcesso || '';
    document.getElementById('tipo_prazo').value = tipoPrazo || '';
    document.getElementById('data_publicacao').value = dataPublicacao || '';
    document.getElementById('dias_uteis_prazo').value = diasUteisPrazo ? String(diasUteisPrazo) : '';
    document.getElementById('tipo_audiencia').value = tipoAudiencia || '';
    document.getElementById('formato_audiencia').value = formatoAudiencia || '';
    document.getElementById('link_reuniao_virtual').value = linkReuniaoVirtual || '';
    togglePrazoFields();

    await carregarClientesAgenda(clienteId);

    document.getElementById('modalAgendaTitle').textContent = 'Editar Compromisso';
    abrirModal('modalAgenda');
}

// ============================================================================
// DELETAR COMPROMISSO
// ============================================================================

async function deletarCompromisso(id, titulo) {
    if (!confirm(`Tem certeza que deseja remover o compromisso "${titulo}"?`)) {
        return;
    }

    try {
        const resposta = await fazRequisicao(`/api/agenda/${id}/deletar`, 'DELETE');

        if (resposta && resposta.status === 200) {
            mostrarAlerta('Compromisso removido com sucesso!', 'success');
            await carregarAgenda();
        } else {
            mostrarAlerta(resposta.dados.message || 'Erro ao remover compromisso', 'danger');
        }
    } catch (erro) {
        console.error('Erro:', erro);
        mostrarAlerta('Erro ao remover compromisso', 'danger');
    }
}

async function carregarAgenda() {
    const resposta = await fazRequisicao('/api/agenda/lista', 'GET');
    if (resposta && resposta.status === 200 && resposta.dados?.success) {
        compromissosAgenda = resposta.dados.compromissos || [];
        atualizarFiltroClientesRecebimento();
        renderAgendaCalendar();
        renderTabelaAgenda();
        renderAvisoPrazos();
    }
}
