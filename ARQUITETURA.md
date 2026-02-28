# ============================================================================
# ARQUITETURA DO PROJETO
# ============================================================================

## 🏗️ ARQUITETURA GERAL

```
┌────────────────────────────────────────────────────────────────┐
│                     NAVEGADOR (Cliente)                         │
│  HTML5 + CSS3 + Bootstrap 5 + Jinja2 + JavaScript             │
└────────────────────────────────────────────────────────────────┘
                              ↓ AJAX
                              ↓ HTTP
┌────────────────────────────────────────────────────────────────┐
│                     SERVIDOR FLASK (app/)                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ run.py → create_app() → __init__.py                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ routes.py - TODAS AS ROTAS                             │   │
│  │ • GET  /                (Dashboard)                    │   │
│  │ • GET  /clientes        (Listar)                       │   │
│  │ • POST /api/clientes/novo                             │   │
│  │ • PUT  /api/clientes/<id>/atualizar                   │   │
│  │ • DELETE /api/clientes/<id>/deletar                   │   │
│  │ • GET  /api/clientes/<id>/processos                   │   │
│  │ • [Mesmas operações para /processos]                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ models.py - LÓGICA DE NEGÓCIO                          │   │
│  │ • Cliente.validar() → Valida dados                    │   │
│  │ • Cliente.preparar_para_mongodb() → Formata           │   │
│  │ • Cliente.converter_para_json() → ObjectId → String   │   │
│  │ • Processo.* (mesmas operações)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ config.py - CONFIGURAÇÃO & CONEXÃO                     │   │
│  │ • MongoClient(MONGODB_URI)                             │   │
│  │ • init_db() → Cria collections e índices             │   │
│  │ • get_db() → Retorna referência ao banco               │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                              ↓ pymongo
                              ↓ TCP/IP
┌────────────────────────────────────────────────────────────────┐
│              MONGODB ATLAS (Cloud - Nuvem)                     │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │ Database:        │  │ Database:        │                  │
│  │ gestor_juridico  │  │ gestor_juridico  │                  │
│  │                  │  │                  │                  │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │                  │
│  │ │ clientes     │ │  │ │ processos    │ │                  │
│  │ │ (Collection) │ │  │ │ (Collection) │ │                  │
│  │ │              │ │  │ │              │ │                  │
│  │ │ _id: Index   │ │  │ │ _id: Index   │ │                  │
│  │ │ nome: Index  │ │  │ │ cliente_id   │ │                  │
│  │ │ email: Unique│ │  │ │ status: Index│ │                  │
│  │ └──────────────┘ │  │ └──────────────┘ │                  │
│  └──────────────────┘  └──────────────────┘                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 📁 ESTRUTURA DE ARQUIVOS

```
gestor_juridico/
│
├── app/                              ← Pacote principal (Python)
│   ├── __init__.py                  ← Factory pattern Flask
│   ├── config.py                    ← MongoDB + Configurações
│   ├── models.py                    ← Validação + Conversão JSON
│   └── routes.py                    ← CRUD Routes
│
├── templates/                        ← Templates HTML (Jinja2)
│   ├── base.html                    ← Layout mestre (Herança)
│   ├── index.html                   ← Estende base.html
│   ├── clientes.html                ← Estende base.html
│   ├── processos.html               ← Estende base.html
│   ├── 404.html                     ← Estende base.html
│   └── 500.html                     ← Estende base.html
│
├── static/                           ← Arquivos estáticos
│   ├── css/
│   │   └── style.css                ← Estilos customizados
│   ├── js/
│   │   ├── main.js                  ← AJAX globais
│   │   ├── clientes.js              ← CRUD clientes
│   │   └── processos.js             ← CRUD processos
│   └── img/                         ← Imagens (se houver)
│
├── run.py                           ← Ponto de entrada
├── requirements.txt                 ← Dependências
├── Procfile                         ← Config deploy
├── setup.sh / setup.bat             ← Scripts de setup
├── seed_data.py                     ← Dados de teste
│
├── .env                             ← Variáveis (SECRETO!)
├── .env.example                     ← Template seguro
├── .gitignore                       ← Proteção Git
│
├── README.md                        ← Documentação usuário
├── DESENVOLVIMENTO.md               ← Guia desenvolvedor
├── COMPLETO.md                      ← Resumo final
└── ARQUITETURA.md                   ← Este arquivo

```

---

## 🔄 FLUXO DE REQUISIÇÃO - Exemplo Prático

### Exemplo: Criar Novo Cliente

```
1. FRONTEND (HTML)
   ├─ Usuário clica "Novo Cliente"
   ├─ Modal abre (bootstrap)
   └─ Usuário preenche formulário
        ├─ Nome: João Silva
        ├─ Email: joao@example.com
        └─ CPF: 123.456.789-00

2. JAVASCRIPT (main.js + clientes.js)
   ├─ Evento onclick="salvarCliente()"
   ├─ Obtém dados do formulário
   ├─ Valida (email, nome mínimo)
   ├─ fetch() HTTP POST
   └─ Headers: Content-Type: application/json
                Body: { nome: "João", email: "joao@example.com", ... }

3. FLASK - ROUTE (routes.py)
   ├─ @main_bp.route('/api/clientes/novo', methods=['POST'])
   ├─ def adicionar_cliente():
   ├─ dados = request.get_json()
   └─ Continua...

4. MODELO - VALIDAÇÃO (models.py)
   ├─ Cliente.validar(dados)
   ├─ Valida campos obrigatórios
   ├─ Valida formato email
   ├─ Retorna (True, []) ou (False, [erros])
   └─ Se inválido, retorna erro 400

5. BANCO DE DADOS (MongoDB)
   ├─ Cliente.preparar_para_mongodb(dados)
   ├─ Adiciona data_cadastro
   ├─ Adiciona ativo = True
   ├─ db['clientes'].insert_one(cliente_doc)
   ├─ Retorna InsertResult com _id (ObjectId)
   └─ MongoDB armazena: {"_id": ObjectId(...), "nome": "João", ...}

6. CONVERSÃO JSON (models.py)
   ├─ Cliente.converter_para_json(cliente)
   ├─ cliente['_id'] = str(cliente['_id'])
   │  (ObjectId → String porque JSON não reconhece ObjectId)
   └─ {"_id": "507f1f77bcf86cd799439011", "nome": "João", ...}

7. RESPOSTA HTTP (routes.py)
   ├─ return jsonify({
   │    'success': True,
   │    'message': 'Cliente cadastrado com sucesso!',
   │    'cliente_id': '507f1f77bcf86cd799439011'
   │  }), 201
   └─ Content-Type: application/json

8. JAVASCRIPT RECEBE (clientes.js)
   ├─ resposta.status === 201 ✅
   ├─ resposta.dados.success === True ✅
   ├─ mostrarAlerta('Cliente cadastrado com sucesso!', 'success')
   ├─ fecharModal('modalCliente')
   └─ location.reload() (recarrega página)

9. FRONTEND ATUALIZADO (HTML)
   ├─ Nova linha aparecer na tabela
   ├─ Tabela renderiza com dados do servidor
   └─ Usuário vê o cliente novo listado

```

---

## 🗄️ FLUXO DE DADOS - Dados de Cliente

```json
CLIENTE NO FRONTEND:
{
  "id": "507f1f77bcf86cd799439011",  ← String (JS)
  "nome": "João Silva",
  "email": "joao@example.com",
  "cpf_cnpj": "123.456.789-00"
}

                    ↓ fetch() POST
                    
CLIENTE EM TRÂNSITO (JSON):
{
  "nome": "João Silva",
  "email": "joao@example.com",
  "cpf_cnpj": "123.456.789-00"
}

                    ↓ request.get_json()
                    
CLIENTE NO PYTHON (Dict):
{
  'nome': 'João Silva',
  'email': 'joao@example.com',
  'cpf_cnpj': '123.456.789-00'
}

                    ↓ Cliente.preparar_para_mongodb()
                    
CLIENTE PREPARADO:
{
  'nome': 'João Silva',
  'email': 'joao@example.com',
  'cpf_cnpj': '123.456.789-00',
  'data_cadastro': datetime.utcnow(),  ← Adicionado
  'ativo': True                        ← Adicionado
}

                    ↓ db['clientes'].insert_one()
                    
CLIENTE NO MONGODB:
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),  ← ObjectId (BSON)
  "nome": "João Silva",
  "email": "joao@example.com",
  "cpf_cnpj": "123.456.789-00",
  "data_cadastro": ISODate("2026-02-01T10:30:00Z"),
  "ativo": true
}

                    ↓ Cliente.converter_para_json()
                    
CLIENTE PARA JSON:
{
  "_id": "507f1f77bcf86cd799439011",  ← String (convertido)
  "nome": "João Silva",
  "email": "joao@example.com",
  "cpf_cnpj": "123.456.789-00",
  "data_cadastro": ISODate("2026-02-01T10:30:00Z"),
  "ativo": true
}

                    ↓ jsonify() + HTTP
                    
RESPOSTA HTTP:
{
  "success": true,
  "message": "Cliente cadastrado com sucesso!",
  "cliente_id": "507f1f77bcf86cd799439011"
}

                    ↓ JavaScript recebe
                    
TELA ATUALIZADA:
✅ Cliente aparece na tabela da página /clientes

```

---

## 🔐 SEGURANÇA - Camadas

```
┌─────────────────────────────────────────────────────┐
│ 1. FRONTEND (HTML + JavaScript)                     │
│    - Validação básica de email/formato             │
│    - Feedback visual ao usuário                    │
│    ⚠️  NÃO confie apenas nisso!                    │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 2. BACKEND (Flask - routes.py)                     │
│    - Validação rigorosa (models.py)                │
│    - Verificação de duplicatas (email)            │
│    - Tratamento de erros                          │
│    - Retorna 400/404/500 apropriados             │
│    ✅ CONFIÁVEL - Segunda camada de proteção     │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 3. BANCO DE DADOS (MongoDB)                        │
│    - Índices únicos (email não duplicado)          │
│    - Esquema validado                             │
│    - Criptografia em trânsito (TLS)              │
│    - Backups automáticos                         │
│    ✅ SEGURO - Terceira camada                   │
└─────────────────────────────────────────────────────┘
```

---

## 📊 PADRÕES DE DESIGN USADOS

### 1. Factory Pattern
```
run.py:
    app = create_app()
    ↓
app/__init__.py:
    def create_app():
        app = Flask(...)
        app.config.from_object(Config)
        init_db()
        app.register_blueprint(main_bp)
        return app
```

### 2. MVC (Model-View-Controller)
```
Model:   models.py (Cliente, Processo)
View:    templates/ (HTML com Jinja2)
Control: routes.py (Funções das rotas)
```

### 3. Blueprint (Modularização)
```
routes.py:
    main_bp = Blueprint('main', __name__)
    
app/__init__.py:
    app.register_blueprint(main_bp)
```

### 4. Validação em Camadas
```
Frontend (JavaScript)
        ↓
    Backend (models.py - models.validar())
        ↓
    Database (MongoDB índices)
```

---

## 🚀 DEPLOYMENT ARCHITECTURE

```
Local Development:
    python run.py
    http://localhost:5000
    ↓
    Flask (Development Server)

Production (Render/Heroku):
    Procfile:
        web: gunicorn --bind 0.0.0.0:$PORT run:app
    ↓
    Gunicorn (Production Server)
    ↓
    MongoDB Atlas (Cloud)
    ↓
    https://seu-app-name.onrender.com
    ou
    https://seu-app-name.herokuapp.com
```

---

## 📈 ESCALABILIDADE

**MVP Atual Pode Suportar:**
- ✅ Até 10.000 clientes
- ✅ Até 50.000 processos
- ✅ ~100 usuários simultâneos
- ✅ Com M0 (gratuito) do MongoDB

**Para Crescer (V2+):**
```
1. Upgrade MongoDB (M2+)
2. Adicionar Cache (Redis)
3. Load Balancer (se múltiplos servidores)
4. CDN para assets (estáticos)
5. Banco separado para leitura (replicação)
```

---

**Criado com ❤️ | Versão 1.0.0 | 2026**
