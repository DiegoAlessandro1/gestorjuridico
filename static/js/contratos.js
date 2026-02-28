document.addEventListener('DOMContentLoaded', function() {
  console.log('Contratos script carregado');

  const btnNovo = document.getElementById('btnNovoContrato');
  const modalEl = document.getElementById('modalContrato');
  const btnSalvar = document.getElementById('btnSalvarContrato');
  const tipoEl = document.getElementById('contrato_tipo');
  const subtipoContainer = document.getElementById('contrato_subtipo_container');
  const subtipoEl = document.getElementById('contrato_subtipo');
  const subtipoOutros = document.getElementById('contrato_subtipo_outros');

  let contratoModal = null;
  let contratoEditandoId = '';
  let contratosCache = [];

  if (modalEl) contratoModal = new bootstrap.Modal(modalEl);

  function alternarCamposSubtipo() {
    if (!tipoEl || !subtipoContainer) return;

    if (tipoEl.value === 'Civis') {
      subtipoContainer.classList.remove('d-none');
    } else {
      subtipoContainer.classList.add('d-none');
      if (subtipoEl) subtipoEl.value = '';
      if (subtipoOutros) {
        subtipoOutros.value = '';
        subtipoOutros.classList.add('d-none');
      }
    }
  }

  function alternarCampoSubtipoOutros() {
    if (!subtipoEl || !subtipoOutros) return;
    if (subtipoEl.value === 'Outros') {
      subtipoOutros.classList.remove('d-none');
    } else {
      subtipoOutros.classList.add('d-none');
      subtipoOutros.value = '';
    }
  }

  async function carregarClientes(clienteSelecionado = '') {
    try {
      const res = await fetch('/api/clientes/lista');
      const json = await res.json();
      const sel = document.getElementById('contrato_cliente');
      if (!sel) return;

      sel.innerHTML = '';
      if (json.success) {
        json.clientes.forEach(c => {
          const opt = document.createElement('option');
          opt.value = c._id;
          opt.textContent = c.nome;
          sel.appendChild(opt);
        });
      }

      if (clienteSelecionado) {
        sel.value = clienteSelecionado;
      }
    } catch (e) {
      console.error('Erro ao carregar clientes', e);
    }
  }

  function resetarFormularioContrato() {
    const form = document.getElementById('formContrato');
    if (!form) return;
    form.reset();
    contratoEditandoId = '';
    alternarCamposSubtipo();
    alternarCampoSubtipoOutros();
    if (btnSalvar) btnSalvar.textContent = 'Salvar';
    const tituloModal = modalEl?.querySelector('.modal-title');
    if (tituloModal) tituloModal.textContent = 'Novo Contrato';
  }

  function preencherFormularioEdicao(contrato) {
    document.getElementById('contrato_cliente').value = contrato.cliente_id || '';
    document.getElementById('contrato_tipo').value = contrato.tipo || '';
    document.getElementById('contrato_subtipo').value = contrato.subtipo || '';
    document.getElementById('contrato_subtipo_outros').value = contrato.subtipo_outros || '';
    document.getElementById('contrato_data').value = contrato.data || '';
    document.getElementById('contrato_arquivo').value = '';

    alternarCamposSubtipo();
    alternarCampoSubtipoOutros();

    if (btnSalvar) btnSalvar.textContent = 'Atualizar';
    const tituloModal = modalEl?.querySelector('.modal-title');
    if (tituloModal) tituloModal.textContent = 'Editar Contrato';
  }

  async function abrirNovoContrato() {
    await carregarClientes();
    resetarFormularioContrato();
    contratoModal && contratoModal.show();
  }

  async function abrirEdicaoContrato(contratoId) {
    const contrato = contratosCache.find((item) => item._id === contratoId);
    if (!contrato) {
      alert('Contrato não encontrado para edição.');
      return;
    }

    await carregarClientes(contrato.cliente_id || '');
    contratoEditandoId = contratoId;
    preencherFormularioEdicao(contrato);
    contratoModal && contratoModal.show();
  }

  async function salvarContrato() {
    const fd = new FormData();
    fd.append('cliente_id', document.getElementById('contrato_cliente').value || '');
    fd.append('tipo', document.getElementById('contrato_tipo').value || '');

    const subtipoVal = subtipoEl ? (subtipoEl.value || '') : '';
    fd.append('subtipo', subtipoVal);
    if (subtipoVal === 'Outros') {
      fd.append('subtipo_outros', document.getElementById('contrato_subtipo_outros').value || '');
    }

    fd.append('data', document.getElementById('contrato_data').value || '');
    const arquivo = document.getElementById('contrato_arquivo').files[0];
    if (arquivo) fd.append('arquivo', arquivo);

    const isEdicao = !!contratoEditandoId;
    const url = isEdicao
      ? `/api/contratos/${contratoEditandoId}/atualizar`
      : '/api/contratos/novo';
    const metodo = isEdicao ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, { method: metodo, body: fd });
      const json = await res.json();

      if (!res.ok) {
        alert(json.message || 'Erro ao salvar contrato');
        return;
      }

      contratoModal && contratoModal.hide();
      await carregarContratos();
      resetarFormularioContrato();
    } catch (e) {
      console.error(e);
      alert('Erro ao salvar contrato');
    }
  }

  async function deletarContrato(contratoId) {
    const contrato = contratosCache.find((item) => item._id === contratoId);
    const descricao = `${contrato?.tipo || 'Contrato'}${contrato?.data ? ` (${contrato.data})` : ''}`;

    if (!confirm(`Tem certeza que deseja deletar o contrato "${descricao}"?`)) {
      return;
    }

    try {
      const res = await fetch(`/api/contratos/${contratoId}/deletar`, { method: 'DELETE' });
      const json = await res.json();

      if (!res.ok) {
        alert(json.message || 'Erro ao deletar contrato');
        return;
      }

      await carregarContratos();
    } catch (e) {
      console.error('Erro ao deletar contrato', e);
      alert('Erro ao deletar contrato');
    }
  }

  async function carregarContratos() {
    try {
      const res = await fetch('/api/contratos/lista');
      const json = await res.json();
      if (!json.success) return;

      contratosCache = Array.isArray(json.contratos) ? json.contratos : [];

      const tbody = document.querySelector('#contratosLista tbody');
      if (!tbody) return;
      tbody.innerHTML = '';

      contratosCache.forEach(ct => {
        const tr = document.createElement('tr');
        const tipoTexto = ct.tipo === 'Civis' && ct.subtipo
          ? `${ct.tipo} - ${ct.subtipo === 'Outros' ? (ct.subtipo_outros || 'Outros') : ct.subtipo}`
          : (ct.tipo || '');

        tr.innerHTML = `
          <td>${ct.cliente_nome || ''}</td>
          <td>${tipoTexto}</td>
          <td>${ct.data || ''}</td>
          <td class="text-end">
            <button class="btn btn-sm btn-outline-secondary me-1" data-acao="editar" data-id="${ct._id}">Editar</button>
            <button class="btn btn-sm btn-outline-danger" data-acao="deletar" data-id="${ct._id}">Deletar</button>
          </td>
        `;
        tbody.appendChild(tr);
      });

      tbody.querySelectorAll('button[data-acao="editar"]').forEach((btn) => {
        btn.addEventListener('click', () => abrirEdicaoContrato(btn.dataset.id));
      });
      tbody.querySelectorAll('button[data-acao="deletar"]').forEach((btn) => {
        btn.addEventListener('click', () => deletarContrato(btn.dataset.id));
      });
    } catch (e) {
      console.error('Erro ao carregar contratos', e);
    }
  }

  btnNovo && btnNovo.addEventListener('click', abrirNovoContrato);
  btnSalvar && btnSalvar.addEventListener('click', salvarContrato);
  if (tipoEl) tipoEl.addEventListener('change', alternarCamposSubtipo);
  if (subtipoEl) subtipoEl.addEventListener('change', alternarCampoSubtipoOutros);

  carregarContratos();
  alternarCamposSubtipo();
  alternarCampoSubtipoOutros();
});
