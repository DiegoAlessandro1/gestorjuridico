/* ============================================================================
   JAVASCRIPT - PÁGINA DE USUÁRIOS
   ============================================================================ */

async function salvarAdvogado() {
    const advogadoId = document.getElementById('advogadoId').value;
    const nome = document.getElementById('advogadoNome').value.trim();
    const oab = document.getElementById('advogadoOab').value.trim().toUpperCase();
    const tipo = document.getElementById('advogadoTipo').value;
    const email = document.getElementById('advogadoEmail').value.trim();
    const telefone = document.getElementById('advogadoTelefone').value.trim();
    const endereco_profissional = document.getElementById('advogadoEndereco').value.trim();
    const usuario = document.getElementById('advogadoUsuario').value.trim().toLowerCase();
    const senha = document.getElementById('advogadoSenha').value;

    const requerOab = tipo === 'Advogado';

    if (!nome || !tipo || !usuario || (requerOab && !oab)) {
        mostrarAlerta('Preencha os campos obrigatórios (*)', 'warning');
        return;
    }

    if (!advogadoId && !senha) {
        mostrarAlerta('Senha é obrigatória para novo usuário', 'warning');
        return;
    }

    if (email && !emailValido(email)) {
        mostrarAlerta('Email inválido', 'warning');
        return;
    }

    const dados = {
        nome,
        oab,
        tipo,
        email,
        telefone,
        endereco_profissional,
        usuario,
        senha
    };

    try {
        let url;
        let metodo;
        let mensagem;

        if (advogadoId) {
            url = `/api/advogados/${advogadoId}/atualizar`;
            metodo = 'PUT';
            mensagem = 'Usuário atualizado com sucesso!';
        } else {
            url = '/api/advogados/novo';
            metodo = 'POST';
            mensagem = 'Usuário cadastrado com sucesso!';
        }

        const resposta = await fazRequisicao(url, metodo, dados);

        if (resposta && (resposta.status === 200 || resposta.status === 201)) {
            mostrarAlerta(mensagem, 'success');
            fecharModal('modalAdvogado');
            limparFormulario('formAdvogado');
            document.getElementById('advogadoId').value = '';

            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            mostrarAlerta((resposta && resposta.dados && resposta.dados.message) ? resposta.dados.message : 'Erro ao salvar usuário', 'danger');
        }
    } catch (erro) {
        console.error('Erro:', erro);
        mostrarAlerta('Erro ao salvar usuário', 'danger');
    }
}

function editarAdvogado(id, nome, oab, tipo, email, telefone, endereco, usuario) {
    document.getElementById('advogadoId').value = id;
    document.getElementById('advogadoNome').value = nome;
    document.getElementById('advogadoOab').value = oab;
    document.getElementById('advogadoTipo').value = tipo || 'Advogado';
    document.getElementById('advogadoEmail').value = email || '';
    document.getElementById('advogadoTelefone').value = telefone || '';
    document.getElementById('advogadoEndereco').value = endereco || '';
    document.getElementById('advogadoUsuario').value = usuario || '';
    document.getElementById('advogadoSenha').value = '';

    document.getElementById('modalAdvogadoTitle').textContent = 'Editar Usuário';
    toggleOabRequirement();
    abrirModal('modalAdvogado');
}

function editarAdvogadoFromButton(botao) {
    if (!botao) return;

    editarAdvogado(
        botao.dataset.id || '',
        botao.dataset.nome || '',
        botao.dataset.oab || '',
        botao.dataset.tipo || 'Advogado',
        botao.dataset.email || '',
        botao.dataset.telefone || '',
        botao.dataset.endereco || '',
        botao.dataset.usuario || ''
    );
}

async function deletarAdvogado(id, nome) {
    if (!confirm(`Tem certeza que deseja remover o usuário "${nome}"?\n\nEsta ação não pode ser desfeita!`)) {
        return;
    }

    try {
        const resposta = await fazRequisicao(`/api/advogados/${id}/deletar`, 'DELETE');

        if (resposta && resposta.status === 200) {
            mostrarAlerta('Usuário removido com sucesso!', 'success');
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            mostrarAlerta((resposta && resposta.dados && resposta.dados.message) ? resposta.dados.message : 'Erro ao remover usuário', 'danger');
        }
    } catch (erro) {
        console.error('Erro:', erro);
        mostrarAlerta('Erro ao remover usuário', 'danger');
    }
}

function toggleOabRequirement() {
    const tipoEl = document.getElementById('advogadoTipo');
    const oabEl = document.getElementById('advogadoOab');
    if (!tipoEl || !oabEl) return;

    const isAdvogado = tipoEl.value === 'Advogado';
    oabEl.required = isAdvogado;
    oabEl.placeholder = isAdvogado ? 'UF 000000' : 'Opcional para este tipo';
    if (!isAdvogado) {
        oabEl.value = '';
    }
}

function deletarAdvogadoFromButton(botao) {
    if (!botao) return;
    deletarAdvogado(botao.dataset.id || '', botao.dataset.nome || '');
}

document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('modalAdvogado');
    const tipoEl = document.getElementById('advogadoTipo');
    if (tipoEl) {
        tipoEl.addEventListener('change', toggleOabRequirement);
    }
    if (modal) {
        modal.addEventListener('show.bs.modal', function () {
            if (!document.getElementById('advogadoId').value) {
                document.getElementById('modalAdvogadoTitle').textContent = 'Novo Usuário';
                limparFormulario('formAdvogado');
                document.getElementById('advogadoSenha').value = '';
                const tipo = document.getElementById('advogadoTipo');
                if (tipo) tipo.value = 'Advogado';
                toggleOabRequirement();
            }
        });
    }
    toggleOabRequirement();
});
