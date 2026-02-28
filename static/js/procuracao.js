// Funções relacionadas à geração e preview de procuração (limpas de handlers do modal removido)

let modelosProcuracaoCache = [];

function obterCssFontePreview(fonteSelecionada) {
    const mapa = {
        'Helvetica': 'Arial, Helvetica, sans-serif',
        'Helvetica-Bold': 'Arial, Helvetica, sans-serif',
        'Helvetica-Oblique': 'Arial, Helvetica, sans-serif',
        'Times-Roman': '"Times New Roman", Times, serif',
        'Times-Bold': '"Times New Roman", Times, serif',
        'Times-Italic': '"Times New Roman", Times, serif',
        'Courier': '"Courier New", Courier, monospace',
        'Courier-Bold': '"Courier New", Courier, monospace',
        'Courier-Oblique': '"Courier New", Courier, monospace',
        'Georgia': 'Georgia, "Times New Roman", serif',
        'Georgia-Bold': 'Georgia, "Times New Roman", serif',
        'Georgia-Italic': 'Georgia, "Times New Roman", serif'
    };
    return mapa[fonteSelecionada] || 'Arial, Helvetica, sans-serif';
}

function atualizarPreviewVisualFonte() {
    const preview = document.getElementById('anexoPreviewVisual');
    const fonteEl = document.getElementById('anexoFonte');
    const tamanhoEl = document.getElementById('anexoTamanhoFonte');
    const textoEl = document.getElementById('anexoTextoComplementar');
    if (!preview) return;

    const fonteSelecionada = (fonteEl?.value || 'Helvetica').trim();
    const tamanhoRaw = Number(tamanhoEl?.value || 12);
    const tamanho = Number.isFinite(tamanhoRaw) ? Math.min(Math.max(tamanhoRaw, 8), 24) : 12;
    const texto = (textoEl?.value || '').trim();

    preview.style.fontFamily = obterCssFontePreview(fonteSelecionada);
    preview.style.fontSize = `${tamanho}px`;
    preview.style.lineHeight = `${Math.max(tamanho + 7, 16)}px`;
    preview.style.fontWeight = fonteSelecionada.toLowerCase().includes('bold') ? '700' : '400';
    preview.style.fontStyle = fonteSelecionada.toLowerCase().includes('italic') || fonteSelecionada.toLowerCase().includes('oblique') ? 'italic' : 'normal';

    if (texto) {
        preview.textContent = texto;
    } else {
        preview.textContent = 'Pelo presente instrumento particular de procuração, o outorgante constitui procurador com os poderes necessários para representação legal.';
    }
}

function obterModeloSelecionado() {
    const sel = document.getElementById('anexoModelo');
    if (!sel) return null;
    const idSelecionado = sel.value;
    if (!idSelecionado) return null;
    return modelosProcuracaoCache.find((m) => String(m.id) === String(idSelecionado)) || null;
}

async function carregarModelosProcuracao() {
    try {
        const resp = await fetch('/api/procuracoes/modelos', { method: 'GET', credentials: 'same-origin' });
        const data = await resp.json().catch(() => null);
        if (!resp.ok || !data?.success) {
            return;
        }

        modelosProcuracaoCache = Array.isArray(data.modelos) ? data.modelos : [];
        const sel = document.getElementById('anexoModelo');
        if (!sel) return;

        sel.innerHTML = '<option value="">Selecionar modelo salvo</option>';
        modelosProcuracaoCache.forEach((modelo) => {
            const opt = document.createElement('option');
            opt.value = modelo.id;
            const sufixoTipo = modelo.tipo ? ` (${modelo.tipo})` : '';
            const sufixoPadrao = modelo.padrao ? ' [Padrão]' : '';
            opt.textContent = `${modelo.nome}${sufixoTipo}${sufixoPadrao}`;
            sel.appendChild(opt);
        });
    } catch (e) {
        console.error('Erro ao carregar modelos de procuração:', e);
    }
}

function aplicarModeloSelecionado() {
    const textoEl = document.getElementById('anexoTextoComplementar');
    const tipoEl = document.getElementById('anexoTipo');
    const nomeEl = document.getElementById('novoModeloNome');
    const fonteEl = document.getElementById('anexoFonte');
    const tamanhoEl = document.getElementById('anexoTamanhoFonte');

    if (!textoEl) return;

    const modelo = obterModeloSelecionado();
    if (!modelo) {
        mostrarAlerta('Selecione um modelo para aplicar', 'warning');
        return;
    }

    textoEl.value = modelo.texto || '';
    if (tipoEl && modelo.tipo) {
        tipoEl.value = modelo.tipo;
    }
    if (nomeEl) {
        nomeEl.value = modelo.nome || '';
    }
    if (fonteEl && modelo.fonte) {
        fonteEl.value = modelo.fonte;
    }
    if (tamanhoEl && modelo.tamanho_fonte) {
        tamanhoEl.value = modelo.tamanho_fonte;
    }
    atualizarPreviewVisualFonte();
    mostrarAlerta('Modelo aplicado no texto complementar', 'success');
}

async function editarModeloSelecionado() {
    const modelo = obterModeloSelecionado();
    if (!modelo) {
        mostrarAlerta('Selecione um modelo para editar', 'warning');
        return;
    }
    if (modelo.padrao) {
        mostrarAlerta('Modelos padrão não podem ser editados', 'warning');
        return;
    }

    const nomeEl = document.getElementById('novoModeloNome');
    const textoEl = document.getElementById('anexoTextoComplementar');
    const fonteEl = document.getElementById('anexoFonte');
    const tamanhoEl = document.getElementById('anexoTamanhoFonte');

    const nome = (nomeEl?.value || modelo.nome || '').trim();
    const texto = (textoEl?.value || '').trim();
    const fonte = (fonteEl?.value || 'Helvetica').trim();
    const tamanho_fonte = Number(tamanhoEl?.value || 12);

    if (!nome) {
        mostrarAlerta('Informe um nome para o modelo', 'warning');
        return;
    }
    if (!texto) {
        mostrarAlerta('Informe o texto do modelo', 'warning');
        return;
    }

    try {
        const resp = await fetch(`/api/procuracoes/modelos/${modelo.id}`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, texto, fonte, tamanho_fonte })
        });
        const data = await resp.json().catch(() => null);
        if (!resp.ok || !data?.success) {
            mostrarAlerta(data?.message || 'Não foi possível editar o modelo', 'danger');
            return;
        }

        mostrarAlerta('Modelo atualizado com sucesso', 'success');
        await carregarModelosProcuracao();
        const sel = document.getElementById('anexoModelo');
        if (sel) sel.value = modelo.id;
    } catch (e) {
        console.error(e);
        mostrarAlerta('Erro ao editar modelo', 'danger');
    }
}

async function excluirModeloSelecionado() {
    const modelo = obterModeloSelecionado();
    if (!modelo) {
        mostrarAlerta('Selecione um modelo para excluir', 'warning');
        return;
    }
    if (modelo.padrao) {
        mostrarAlerta('Modelos padrão não podem ser excluídos', 'warning');
        return;
    }

    const confirmou = window.confirm(`Deseja excluir o modelo "${modelo.nome}"?`);
    if (!confirmou) return;

    try {
        const resp = await fetch(`/api/procuracoes/modelos/${modelo.id}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });
        const data = await resp.json().catch(() => null);
        if (!resp.ok || !data?.success) {
            mostrarAlerta(data?.message || 'Não foi possível excluir o modelo', 'danger');
            return;
        }

        mostrarAlerta('Modelo excluído com sucesso', 'success');
        const nomeEl = document.getElementById('novoModeloNome');
        const textoEl = document.getElementById('anexoTextoComplementar');
        const sel = document.getElementById('anexoModelo');
        if (nomeEl) nomeEl.value = '';
        if (textoEl) textoEl.value = '';
        if (sel) sel.value = '';
        atualizarPreviewVisualFonte();
        await carregarModelosProcuracao();
    } catch (e) {
        console.error(e);
        mostrarAlerta('Erro ao excluir modelo', 'danger');
    }
}

async function salvarModeloAtual() {
    const nomeEl = document.getElementById('novoModeloNome');
    const textoEl = document.getElementById('anexoTextoComplementar');
    const fonteEl = document.getElementById('anexoFonte');
    const tamanhoEl = document.getElementById('anexoTamanhoFonte');

    const nome = (nomeEl?.value || '').trim();
    const texto = (textoEl?.value || '').trim();
    const fonte = (fonteEl?.value || 'Helvetica').trim();
    const tamanho_fonte = Number(tamanhoEl?.value || 12);

    if (!nome) {
        mostrarAlerta('Informe um nome para o modelo', 'warning');
        return;
    }
    if (!texto) {
        mostrarAlerta('Escreva o texto complementar para salvar como modelo', 'warning');
        return;
    }

    try {
        const resp = await fetch('/api/procuracoes/modelos', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, texto, fonte, tamanho_fonte })
        });

        const data = await resp.json().catch(() => null);
        if (!resp.ok || !data?.success) {
            mostrarAlerta(data?.message || 'Não foi possível salvar o modelo', 'danger');
            return;
        }

        mostrarAlerta('Modelo salvo com sucesso', 'success');
        if (nomeEl) nomeEl.value = '';
        await carregarModelosProcuracao();

        const sel = document.getElementById('anexoModelo');
        if (sel && data?.modelo?.id) {
            sel.value = data.modelo.id;
        }
    } catch (e) {
        console.error(e);
        mostrarAlerta('Erro ao salvar modelo', 'danger');
    }
}

// Gera procuração automaticamente sem salvar no servidor
async function gerarProcuracaoAutomatica() {
    const cliente_id = document.getElementById('autoCliente')?.value;
    const tipo = document.getElementById('autoTipo')?.value;
    const folha = document.getElementById('procuracaoFolha') ? document.getElementById('procuracaoFolha').value : '';
    const advogado_id = document.getElementById('autoAdvogado') ? document.getElementById('autoAdvogado').value : '';
    const cidade = document.getElementById('autoCidade') ? document.getElementById('autoCidade').value : '';
    const fonte = document.getElementById('anexoFonte') ? document.getElementById('anexoFonte').value : 'Helvetica';
    const tamanho_fonte = Number(document.getElementById('anexoTamanhoFonte')?.value || 12);

    if (!cliente_id || !tipo) {
        mostrarAlerta('Selecione Cliente e Tipo para gerar a procuração', 'warning');
        return;
    }

    try {
        const resp = await fetch('/api/procuracoes/gerar', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cliente_id, tipo, folha, advogado_id, cidade, fonte, tamanho_fonte })
        });

        if (!resp.ok) {
            const err = await resp.json().catch(()=>null);
            mostrarAlerta(err?.message || 'Falha ao gerar procuração', 'danger');
            return;
        }

        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
        setTimeout(()=> window.URL.revokeObjectURL(url), 60000);
    } catch (e) {
        console.error(e);
        mostrarAlerta('Erro ao gerar procuração', 'danger');
    }
}


// Upload usado pelo card de Anexo
async function uploadAnexoFolha() {
    const input = document.getElementById('anexoFile');
    if (!input || !input.files || input.files.length === 0) {
        mostrarAlerta('Selecione um arquivo para enviar', 'warning');
        return;
    }

    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/folhas/upload', { method: 'POST', credentials: 'same-origin', body: formData });
        const data = await resp.json().catch(()=>null);
        if (resp.status === 201 && data && data.success) {
            mostrarAlerta('Folha enviada com sucesso', 'success');
            const sel = document.getElementById('anexoFolha');
            if (sel) {
                const opt = document.createElement('option');
                opt.value = data.filename;
                opt.textContent = data.filename;
                sel.appendChild(opt);
                sel.value = data.filename;
            }
        } else {
            mostrarAlerta(data?.message || 'Erro ao enviar folha', 'danger');
        }
    } catch (e) {
        console.error(e);
        mostrarAlerta('Erro ao enviar folha', 'danger');
    } finally {
        input.value = '';
    }
}

// Aplica as informações selecionadas diretamente na folha timbrada e mostra preview
async function aplicarEmFolha() {
    const cliente_id = document.getElementById('anexoCliente')?.value;
    const tipo = document.getElementById('anexoTipo')?.value;
    const folha = document.getElementById('anexoFolha')?.value || '';
    const advogado_id = document.getElementById('anexoAdvogado')?.value || '';
    const cidade = document.getElementById('anexoCidade')?.value || '';
    const fonte = document.getElementById('anexoFonte')?.value || 'Helvetica';
    const tamanho_fonte = Number(document.getElementById('anexoTamanhoFonte')?.value || 12);
    const texto_adicional = document.getElementById('anexoTextoComplementar')?.value || '';

    if (!cliente_id || !tipo) {
        mostrarAlerta('Selecione Cliente e Tipo para aplicar na folha', 'warning');
        return;
    }

    try {
        const resp = await fetch('/api/procuracoes/gerar', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cliente_id, tipo, folha, advogado_id, cidade, texto_adicional, fonte, tamanho_fonte })
        });

        if (!resp.ok) {
            const err = await resp.json().catch(()=>null);
            mostrarAlerta(err?.message || 'Falha ao aplicar na folha', 'danger');
            return;
        }

        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const iframe = document.getElementById('anexoPreviewFrame');
        if (iframe) iframe.src = url;
        setTimeout(()=> window.URL.revokeObjectURL(url), 60000);
    } catch (e) {
        console.error(e);
        mostrarAlerta('Erro ao aplicar na folha', 'danger');
    }
}

// Atualiza o preview HTML com os campos selecionados
function updateProcuracaoPreview(){
    const clienteSel = document.getElementById('procuracaoCliente');
    const advogadoSel = document.getElementById('procuracaoAdvogado');
    const tipoSel = document.getElementById('procuracaoTipo');
    const dataEl = document.getElementById('procuracaoData');

    const clienteNome = clienteSel ? (clienteSel.options[clienteSel.selectedIndex]?.text || '') : '';
    const clienteCpf = clienteSel ? (clienteSel.options[clienteSel.selectedIndex]?.dataset?.cpf || '') : '';
    const clienteEndereco = clienteSel ? (clienteSel.options[clienteSel.selectedIndex]?.dataset?.endereco || '') : '';
    const clienteCidade = clienteSel ? (clienteSel.options[clienteSel.selectedIndex]?.dataset?.cidade || '') : '';
    const clienteUf = clienteSel ? (clienteSel.options[clienteSel.selectedIndex]?.dataset?.uf || '') : '';

    const advogadoNomeRaw = advogadoSel ? (advogadoSel.options[advogadoSel.selectedIndex]?.text || '') : '';
    const advogadoNome = advogadoNomeRaw.split(' - OAB')[0];
    const advogadoOab = advogadoSel ? (advogadoSel.options[advogadoSel.selectedIndex]?.dataset?.oab || '') : '';
    const tipo = tipoSel ? tipoSel.value : '';
    const data = dataEl ? dataEl.value : '';

    const poderes_map = {
        'Geral': 'conferindo amplos, gerais e ilimitados poderes para me representar em juízo ou fora dele, ativa e passivamente, podendo receber citações e intimações, transigir, firmar compromissos e acordos, substabelecer, assinar quaisquer documentos, requerer certidões e praticar todos os atos necessários ao bom e fiel desempenho deste mandato.',
        'Específica': 'conferindo poderes específicos para a prática dos atos relacionados ao assunto indicado pelo outorgante, incluindo assinatura de documentos e representação perante órgãos públicos ou privados, e demais providências necessárias ao fiel cumprimento deste mandato.',
        'Judicial': 'conferindo poderes especiais para o foro judicial, para o ajuizamento, defesa, acompanhamento e solução de demandas, com poderes para receber citações, firmar compromissos, transigir, e praticar todos os atos processuais necessários.',
        'Extrajudicial': 'conferindo poderes para representação extrajudicial perante repartições públicas e privadas, empresas e cartórios, podendo requerer documentos, assinar termos, receber e dar quitação, e praticar os atos necessários no âmbito extrajudicial.'
    };
    const texto_poderes = poderes_map[tipo] || poderes_map['Geral'];

    let procurador_text = '';
    if (advogadoNome) {
        procurador_text = `nomeio e constituo como meu bastante procurador o(a) ${advogadoNome}, `;
    } else {
        procurador_text = 'nomeio e constituo como meu bastante procurador o(a) advogado(a) que este instrumento vier a indicar, ';
    }

    const corpo = `Pelo presente instrumento particular de procuração, eu, ${clienteNome} ${clienteCpf ? ' - CPF/CNPJ: ' + clienteCpf : ''}, ${clienteEndereco ? 'residente e domiciliado(a) à ' + clienteEndereco + (clienteCidade ? ', ' + clienteCidade : '') + (clienteUf ? ' - ' + clienteUf : '') + ',' : ''} ${procurador_text}${texto_poderes}`;

    const preview = document.getElementById('procuracaoPreview');
    if (preview) {
        preview.innerHTML = '';
        const title = document.createElement('div');
        title.innerHTML = '<strong>PROCURAÇÃO</strong>';
        title.style.textAlign = 'center';
        title.style.marginBottom = '8px';
        preview.appendChild(title);

        const body = document.createElement('div');
        body.innerHTML = corpo.replace(/\n/g,'<br/>');
        if (advogadoOab) {
            const oabLine = document.createElement('div');
            oabLine.style.marginTop = '8px';
            oabLine.innerHTML = `<small class="text-muted">OAB: ${advogadoOab}</small>`;
            preview.appendChild(oabLine);
        }
        preview.appendChild(body);

        const footer = document.createElement('div');
        footer.style.marginTop = '16px';
        footer.innerHTML = (data ? `<small class="text-muted">Data: ${data}</small>` : '');
        preview.appendChild(footer);
    }
}

// Inicialização de listeners
document.addEventListener('DOMContentLoaded', function() {
    // keep preview listeners (elements may or may not exist)
    const modalInputs = ['procuracaoCliente','procuracaoAdvogado','procuracaoTipo','procuracaoData'];
    modalInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', updateProcuracaoPreview);
    });

    // Anexo: upload/preview de folha timbrada (card de anexo)
    const anexoFile = document.getElementById('anexoFile');
    if (anexoFile) {
        anexoFile.addEventListener('change', function () {
            if (anexoFile.files && anexoFile.files.length > 0) {
                uploadAnexoFolha();
            }
        });
    }

    carregarModelosProcuracao();

    const modeloSel = document.getElementById('anexoModelo');
    if (modeloSel) {
        modeloSel.addEventListener('change', function () {
            const modelo = obterModeloSelecionado();
            const nomeEl = document.getElementById('novoModeloNome');
            if (nomeEl) {
                nomeEl.value = modelo?.nome || '';
            }
        });
    }

    const fonteEl = document.getElementById('anexoFonte');
    const tamanhoEl = document.getElementById('anexoTamanhoFonte');
    const textoEl = document.getElementById('anexoTextoComplementar');

    if (fonteEl) fonteEl.addEventListener('change', atualizarPreviewVisualFonte);
    if (tamanhoEl) tamanhoEl.addEventListener('input', atualizarPreviewVisualFonte);
    if (textoEl) textoEl.addEventListener('input', atualizarPreviewVisualFonte);

    atualizarPreviewVisualFonte();
});
