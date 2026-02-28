# ============================================================================
# GUIA DE DESENVOLVIMENTO - DICAS E BOAS PRÁTICAS
# ============================================================================
# Arquivo: DESENVOLVIMENTO.md
# Propósito: Ajudar desenvolvedores a entender e estender o projeto
# ============================================================================

## 📚 Estrutura de Arquivos - Explicada

```
gestor_juridico/
├── app/                              # Pacote principal Python
│   ├── __init__.py                  # Factory pattern - cria Flask app
│   ├── config.py                    # Conexão MongoDB + configurações
│   ├── models.py                    # Validação de dados + conversão JSON
│   └── routes.py                    # Todas as rotas HTTP (CRUD)
│
├── templates/                        # Templates HTML (Jinja2)
│   ├── base.html                    # Layout mestre + sidebar
│   ├── index.html                   # Dashboard com métricas
│   ├── clientes.html                # CRUD de clientes
│   ├── processos.html               # CRUD de processos
│   └── 404.html / 500.html          # Páginas de erro
│
├── static/                           # Arquivos estáticos (CSS/JS)
│   ├── css/style.css                # Estilos customizados
│   ├── js/main.js                   # Funções globais AJAX
│   ├── js/clientes.js               # Funções específicas de clientes
│   └── js/processos.js              # Funções específicas de processos
│
└── Raiz:
    ├── run.py                       # Inicializa a aplicação
    ├── seed_data.py                 # Insere dados de teste
    ├── requirements.txt             # Dependências Python
    ├── Procfile                     # Config para deploy
    ├── .env                         # Variáveis (SECRETO)
    └── README.md                    # Documentação
```

---

## 🔄 FLUXO DE DADOS - Como Tudo Funciona

### Exemplo: Adicionar Novo Cliente

```
[Frontend HTML]
    ↓
[Formulário modal + JavaScript]
    ↓
[fetch('/api/clientes/novo', 'POST', dados)]
    ↓
[Flask Route: @main_bp.route('/api/clientes/novo', methods=['POST'])]
    ↓
[Models: Cliente.validar(dados)]
    ↓
[Models: Cliente.preparar_para_mongodb(dados)]
    ↓
[MongoDB: db['clientes'].insert_one(dados)]
    ↓
[Python: Cliente.converter_para_json() → String ObjectId]
    ↓
[Response JSON: {'success': True, 'cliente_id': '507f1f77bcf86cd799439011'}]
    ↓
[JavaScript: mostrarAlerta() + recarrega página]
    ↓
[Frontend: Tabela atualizada]
```

---

## 🔐 SEGURANÇA - Pontos Críticos

### 1. ObjectId ↔ String Conversion

⚠️ **IMPORTANTE:** MongoDB usa ObjectId, JavaScript/JSON usa String

```python
# ❌ ERRADO - Enviaria objeto BSON (não funciona em JSON)
return jsonify({'cliente_id': cliente['_id']})

# ✅ CORRETO - Converte para String
cliente['_id'] = str(cliente['_id'])
return jsonify({'cliente_id': cliente['_id']})
```

Veja no código:
- `app/models.py` - Funções `converter_para_json()`
- `app/routes.py` - Usa conversão antes de retornar

### 2. Validação de Entrada

**Sempre valide dados do usuário!**

```python
# Em app/models.py:
Cliente.validar(dados)  # Retorna (é_válido, erros)
```

Validações incluem:
- Campos obrigatórios não vazios
- Formato de email
- Comprimento mínimo de nome
- Status/tipo válidos

### 3. Variáveis de Ambiente

**NUNCA commite .env!** Contém:
- Senha do MongoDB
- Chave secreta da app
- Credenciais

Protegido em `.gitignore`

### 4. CORS (Cross-Origin)

Configurado em `config.py`:
```python
SESSION_COOKIE_HTTPONLY = True  # Protege contra XSS
SESSION_COOKIE_SAMESITE = 'Lax' # Proteção CSRF
```

---

## 🚀 COMO ADICIONAR NOVA FUNCIONALIDADE

### Exemplo: Adicionar Campo "Especialidade" aos Processos

#### Passo 1: Atualizar Modelo (app/models.py)

```python
class Processo:
    # ... código existente ...
    
    @staticmethod
    def preparar_para_mongodb(dados):
        return {
            # ... campos existentes ...
            'especialidade': dados.get('especialidade', 'Geral'),  # NOVO
        }
```

#### Passo 2: Atualizar Rota (app/routes.py)

```python
@main_bp.route('/api/processos/novo', methods=['POST'])
def adicionar_processo():
    dados = request.get_json()
    
    # Validação: adicione se necessário
    if not dados.get('especialidade'):
        return jsonify({'success': False, 'message': 'Especialidade obrigatória'}), 400
    
    # ... resto do código ...
```

#### Passo 3: Atualizar Template (templates/processos.html)

```html
<!-- Adicione campo no formulário do modal -->
<div class="col-md-6 mb-3">
    <label class="form-label">Especialidade *</label>
    <select class="form-select" id="especialidade" required>
        <option value="Cível">Cível</option>
        <option value="Penal">Penal</option>
        <option value="Geral">Geral</option>
    </select>
</div>
```

#### Passo 4: Atualizar JavaScript (static/js/processos.js)

```javascript
async function salvarProcesso() {
    const especialidade = document.getElementById('especialidade').value;
    
    const dados = {
        // ... dados existentes ...
        especialidade: especialidade,  // NOVO
    };
    
    // ... resto do código ...
}
```

#### Passo 5: Atualizar Tabela (templates/processos.html)

```html
<td>{{ processo.especialidade }}</td>  <!-- Adicione coluna -->
```

---

## 🧪 TESTES - Como Testar Localmente

### Teste 1: Criar Cliente

```bash
# Assumindo que app está rodando em localhost:5000
curl -X POST http://localhost:5000/api/clientes/novo \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Teste",
    "email": "joao@teste.com",
    "cpf_cnpj": "123.456.789-00"
  }'
```

### Teste 2: Carregar Clientes

Abra no navegador:
```
http://localhost:5000/clientes
```

Verifique console do navegador (F12) para erros.

### Teste 3: Inserir Dados de Teste

```bash
# Ativa venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows

# Executa script de seed
python seed_data.py
```

---

## 🐛 DEBUG - Ferramentas Úteis

### 1. Console Python

```python
# Em routes.py:
print("DEBUG:", dados)  # Exibe no terminal
```

### 2. Console Navegador (DevTools)

Pressione `F12` e vá em "Console". Execute:

```javascript
// Teste a função AJAX
fazRequisicao('/api/clientes/novo', 'POST', {
    nome: 'Teste',
    email: 'teste@test.com',
    cpf_cnpj: '123.456.789-00'
}).then(r => console.log(r))
```

### 3. Logs do MongoDB

```python
# Em config.py:
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📦 ADICIONAR NOVA DEPENDÊNCIA

```bash
# Ativar venv
source venv/bin/activate  # macOS/Linux

# Instalar pacote
pip install novo-pacote

# Atualizar requirements.txt
pip freeze > requirements.txt

# Commit
git add requirements.txt
git commit -m "Add novo-pacote"
```

---

## 🚀 OTIMIZAÇÕES - Performance

### 1. Índices MongoDB

Já foram criados em `config.py`:

```python
db['clientes'].create_index('nome')  # Para buscas rápidas
db['processos'].create_index('cliente_id')  # Para JOINs
```

Para adicionar mais:

```python
db['processos'].create_index('status')
```

### 2. Paginação (Futuro)

```python
# Em routes.py:
processos = list(db['processos']
    .find()
    .skip(10)  # Pula 10 primeiros
    .limit(20) # Retorna 20
)
```

### 3. Caching (Futuro)

```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=60)  # Cache por 60 segundos
def get_dashboard():
    # ...
```

---

## 🔧 VARIÁVEIS DE AMBIENTE

Adicione novas variáveis em `.env`:

```
MEU_NOVO_CONFIG=valor
```

Acesse em Python:

```python
import os
meu_config = os.getenv('MEU_NOVO_CONFIG', 'padrão')
```

---

## 📝 PADRÕES DE CÓDIGO

### Nomes de Variáveis

```python
# ✅ BOM
cliente_nome = "João"
processos_abertos = 10

# ❌ RUIM
cn = "João"
pa = 10
```

### Funções

```python
# ✅ BOM
def validar_email(email):
    """Valida formato de email"""
    return '@' in email

# ❌ RUIM
def ve(e):
    return '@' in e
```

### Comentários

```python
# ✅ BOM - Explica POR QUÊ
# Converte ObjectId para String porque JSON não suporta ObjectId
cliente['_id'] = str(cliente['_id'])

# ❌ RUIM - Obvio demais
# Converte _id
cliente['_id'] = str(cliente['_id'])
```

---

## 🔗 LINKS ÚTEIS

- **Flask**: https://flask.palletsprojects.com/
- **MongoDB**: https://docs.mongodb.com/
- **Bootstrap 5**: https://getbootstrap.com/docs/5.0/
- **Jinja2**: https://jinja.palletsprojects.com/
- **Python**: https://docs.python.org/3/

---

## ❓ FAQ - Perguntas Frequentes

### P: Como resetar o banco de dados?

**R:** Acesse MongoDB Atlas > Collections > Delete Collection. Ou execute:

```python
db['clientes'].delete_many({})
db['processos'].delete_many({})
```

### P: Como debugar AJAX?

**R:** No Console do Navegador (F12):

```javascript
// Veja a requisição sendo enviada
fetch('/api/clientes/novo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({...})
}).then(r => r.json()).then(d => console.log(d))
```

### P: Como adicionar autenticação?

**R:** Use Flask-Login:

```bash
pip install flask-login
```

Veja documentação oficial.

---

**Última Atualização:** 1 de Fevereiro de 2026
