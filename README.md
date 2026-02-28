# ============================================================================
# GESTOR JURÍDICO MVP - GUIA COMPLETO DE USO E DEPLOY
# ============================================================================

## 📋 Visão Geral

**Gestor Jurídico MVP** é uma aplicação web para gestão de clientes e processos 
jurídicos com foco em simplicidade, segurança e baixo custo de manutenção.

**Stack Tecnológica:**
- Backend: Python + Flask
- Banco de Dados: MongoDB (NoSQL)
- Frontend: HTML5 + CSS3 + Bootstrap 5 + Jinja2
- Servidor: Gunicorn (produção)

---

## 🚀 INÍCIO RÁPIDO (LOCAL)

### 1️⃣ PRÉ-REQUISITOS

Certifique-se de que você tem instalado:
- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/))
- **Conta MongoDB Atlas** (gratuita em [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas))

### 2️⃣ CONFIGURAR MONGODB ATLAS

#### Passo 1: Criar Conta no MongoDB Atlas
1. Acesse https://www.mongodb.com/cloud/atlas
2. Clique em "Start Free" (ou faça login se já tem conta)
3. Preencha os dados e confirme o email

#### Passo 2: Criar Cluster Gratuito
1. Na dashboard, clique em "Create" > "Build a cluster"
2. Selecione **M0 (Shared)** - GRATUITO
3. Escolha um provedor (AWS/Google/Azure)
4. Escolha região mais próxima (ex: São Paulo para Brasil)
5. Clique em "Create Deployment"
6. Espere a criação (2-3 minutos)

#### Passo 3: Obter String de Conexão (CONNECTION STRING)
1. Na página do cluster, clique em "Connect"
2. Selecione "Connect your application"
3. Escolha "Python 3.6 or later"
4. Copie a connection string (exemplo abaixo):

```
mongodb+srv://seu_usuario:sua_senha@cluster0.mongodb.net/gestor_juridico?retryWrites=true&w=majority
```

⚠️ **IMPORTANTE:** 
- Substitua `seu_usuario` pelo seu username
- Substitua `sua_senha` pela sua senha
- Se a senha tem caracteres especiais (@, %, &), use URL encoding

### 3️⃣ CLONAR E CONFIGURAR O PROJETO

```bash
# Clonar o repositório
git clone https://github.com/seu_usuario/gestor_juridico.git
cd gestor_juridico

# Criar ambiente virtual (isolado)
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 4️⃣ CONFIGURAR O ARQUIVO .env

1. Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env  # macOS/Linux
copy .env.example .env  # Windows
```

2. Abra o arquivo `.env` e configure:

```plaintext
# Cole aqui a connection string do MongoDB
MONGODB_URI=mongodb+srv://seu_usuario:sua_senha@cluster0.mongodb.net/gestor_juridico?retryWrites=true&w=majority

# Nome do banco de dados
MONGODB_DB_NAME=gestor_juridico

# Chave secreta (mude isso em produção!)
SECRET_KEY=chave_super_segura_desenvolvimento_2026

# Modo de desenvolvimento
FLASK_ENV=development
FLASK_DEBUG=True

# Porta
PORT=5000
```

### 5️⃣ EXECUTAR A APLICAÇÃO

```bash
# Ativar venv novamente (se não estiver)
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Executar aplicação
python run.py
```

Você verá uma mensagem assim:

```
╔════════════════════════════════════════════════════════════╗
║           GESTOR JURÍDICO MVP - SERVIDOR INICIADO          ║
╠════════════════════════════════════════════════════════════╣
║ 🚀 Servidor rodando em: http://localhost:5000            ║
║ 🔧 Modo: DESENVOLVIMENTO                                  ║
╚════════════════════════════════════════════════════════════╝
```

### 6️⃣ ACESSAR A APLICAÇÃO

Abra seu navegador e acesse:

```
http://localhost:5000
```

Pronto! 🎉 Você está rodando o Gestor Jurídico MVP!

---

## 📁 ESTRUTURA DO PROJETO

```
gestor_juridico/
├── app/                         # Código da aplicação
│   ├── __init__.py             # Inicialização Flask
│   ├── config.py               # Configuração e MongoDB
│   ├── models.py               # Modelos (Cliente, Processo)
│   └── routes.py               # Rotas (CRUD APIs)
│
├── templates/                   # Templates HTML (Jinja2)
│   ├── base.html               # Layout mestre (sidebar, navbar)
│   ├── index.html              # Dashboard
│   ├── clientes.html           # Gestão de clientes
│   ├── processos.html          # Gestão de processos
│   ├── 404.html                # Página não encontrada
│   └── 500.html                # Erro do servidor
│
├── static/                      # Arquivos estáticos
│   ├── css/
│   │   └── style.css           # Estilos customizados
│   ├── js/
│   │   ├── main.js             # Funções JavaScript globais
│   │   ├── clientes.js         # Funções de clientes (AJAX)
│   │   └── processos.js        # Funções de processos (AJAX)
│   └── img/                     # Imagens (se houver)
│
├── run.py                       # Arquivo de inicialização
├── requirements.txt             # Dependências Python
├── Procfile                     # Configuração para deploy
├── .env                         # Variáveis de ambiente (SECRETO!)
├── .env.example                 # Exemplo de .env (seguro)
└── README.md                    # Este arquivo

```

---

## 🗄️ BANCO DE DADOS - MongoDB

### Collections (Tabelas)

#### 1. Collection: `clientes`

Armazena dados dos clientes jurídicos.

**Schema:**
```javascript
{
    _id: ObjectId,                // ID único (gerado automaticamente)
    nome: String,                 // Nome do cliente
    email: String,                // Email (único)
    telefone: String,             // Telefone de contato
    cpf_cnpj: String,            // CPF/CNPJ (identificação)
    endereco: String,             // Endereço completo
    cidade: String,               // Cidade
    uf: String,                   // Estado (sigla)
    data_cadastro: DateTime,      // Data de criação
    ativo: Boolean                // Status (true = ativo)
}
```

#### 2. Collection: `processos`

Armazena dados dos processos jurídicos.

**Schema:**
```javascript
{
    _id: ObjectId,                // ID único
    numero_processo: String,      // Número único do processo
    cliente_id: ObjectId,         // Referência ao cliente
    cliente_nome: String,         // Cache do nome do cliente
    tipo_acao: String,            // Tipo (Cível, Penal, etc)
    tribunal: String,             // Tribunal responsável
    vara: String,                 // Vara do tribunal
    juiz: String,                 // Juiz responsável
    status: String,               // Status (Aberto, Suspenso, etc)
    data_abertura: DateTime,      // Data de abertura
    data_ultima_movimentacao: DateTime,  // Última atualização
    descricao: String             // Descrição do caso
}
```

### Índices Criados

Para melhor performance:
- `clientes.email` - Índice único (garante email único)
- `clientes.nome` - Índice de busca rápida
- `processos.numero_processo` - Índice único
- `processos.cliente_id` - Índice para relacionamento
- `processos.status` - Índice para filtros

---

## 🔐 SEGURANÇA E VARIÁVEIS DE AMBIENTE

### ⚠️ O arquivo `.env` NUNCA deve ser commitado!

**Por quê?** Contém credenciais secretas:
- Senha do MongoDB
- Chave secreta da aplicação
- Dados sensíveis

### Como proteger:

1. O arquivo `.env` já está no `.gitignore` (não será enviado para GitHub)
2. Compartilhe apenas `.env.example` com colegas
3. Cada desenvolvedor cria seu próprio `.env` localmente
4. Em produção, configure variáveis de ambiente na plataforma

---

## 📡 ROTAS DA APLICAÇÃO

### Rotas Web (Frontend)

```
GET  /                                # Dashboard
GET  /clientes                        # Página de clientes
GET  /processos                       # Página de processos
```

### Rotas API (AJAX/Backend)

#### Clientes

```
POST   /api/clientes/novo             # Criar novo cliente
PUT    /api/clientes/<id>/atualizar   # Atualizar cliente
DELETE /api/clientes/<id>/deletar     # Deletar cliente
GET    /api/clientes/<id>/processos   # Obter processos do cliente
```

#### Processos

```
POST   /api/processos/novo            # Criar novo processo
PUT    /api/processos/<id>/atualizar  # Atualizar processo
DELETE /api/processos/<id>/deletar    # Deletar processo
```

---

## 🚀 FAZER DEPLOY NO RENDER.COM

### Passo 1: Preparar Repositório GitHub

```bash
# Confirme que .env está em .gitignore
cat .gitignore  # Deve incluir ".env"

# Faça commit e push
git add .
git commit -m "Initial commit - Gestor Jurídico MVP"
git push origin main
```

### Passo 2: Criar Conta no Render

1. Acesse https://render.com
2. Clique em "Sign up" (pode usar GitHub)
3. Autorize o Render a acessar seus repositórios

### Passo 3: Criar Novo Web Service

1. Na dashboard, clique em "New +" > "Web Service"
2. Selecione seu repositório `gestor_juridico`
3. Configure:

| Campo | Valor |
|-------|-------|
| **Name** | gestor-juridico |
| **Environment** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn run:app` |
| **Plan** | Free (ou pagos conforme necessário) |

### Passo 4: Adicionar Variáveis de Ambiente

Na página de configuração do Web Service, clique em "Environment" e adicione:

```
MONGODB_URI = mongodb+srv://seu_usuario:sua_senha@cluster0.mongodb.net/gestor_juridico?retryWrites=true&w=majority
MONGODB_DB_NAME = gestor_juridico
SECRET_KEY = gere_uma_chave_segura_aqui_2026
FLASK_ENV = production
PORT = 5000
```

### Passo 5: Deploy!

Render fará o deploy automaticamente quando você faz push para GitHub.

Você verá a URL:
```
https://gestor-juridico.onrender.com
```

---

## 🚀 FAZER DEPLOY NO HEROKU

### Passo 1: Instalar Heroku CLI

[Download Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

### Passo 2: Login e Criar App

```bash
# Fazer login
heroku login

# Criar app (substitua "seu-app-name")
heroku create seu-app-name

# Verá URL: https://seu-app-name.herokuapp.com
```

### Passo 3: Adicionar Variáveis de Ambiente

```bash
heroku config:set MONGODB_URI="mongodb+srv://seu_usuario:sua_senha@cluster0.mongodb.net/gestor_juridico?retryWrites=true&w=majority"
heroku config:set MONGODB_DB_NAME="gestor_juridico"
heroku config:set SECRET_KEY="gere_uma_chave_segura"
heroku config:set FLASK_ENV="production"
```

### Passo 4: Deploy

```bash
# Push para Heroku
git push heroku main  # ou master, conforme seu branch

# Ver logs
heroku logs --tail
```

---

## 🐛 TROUBLESHOOTING

### Erro: "Connection refused MongoDB"

**Solução:**
1. Verifique se a URI está correta no `.env`
2. Verifique IP whitelist no MongoDB Atlas:
   - MongoDB Atlas Dashboard > Security > Network Access
   - Adicione IP `0.0.0.0/0` (aceita qualquer IP)

### Erro: "Module not found"

**Solução:**
```bash
# Certifique-se que o ambiente virtual está ativo
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Reinstale dependências
pip install -r requirements.txt
```

### Aplicação lenta/timeouts

**Solução:**
- MongoDB Atlas gratuito tem limitações
- Considere upgrade de cluster
- Otimize índices no banco
- Reduza número de workers no Procfile

---

## 📊 EXEMPLO DE USO

### Criar Cliente

1. Acesse http://localhost:5000/clientes
2. Clique em "Novo Cliente"
3. Preencha:
   - Nome: João Silva
   - Email: joao@example.com
   - CPF: 123.456.789-00
4. Clique em "Salvar Cliente"

### Criar Processo

1. Acesse http://localhost:5000/processos
2. Clique em "Novo Processo"
3. Preencha:
   - Número: 0000001-23.2024.8.26.0100
   - Cliente: Selecione João Silva
   - Tipo: Cível
   - Status: Aberto
4. Clique em "Salvar Processo"

### Visualizar Dashboard

- Dashboard mostra total de clientes e processos
- Gráficos com status dos processos
- Últimos processos registrados

---

## 🔧 COMANDOS ÚTEIS

```bash
# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar nova dependência
pip install nome-pacote

# Atualizar requirements.txt
pip freeze > requirements.txt

# Desativar ambiente virtual
deactivate

# Ver versão do Python
python --version

# Executar testes (futuro)
pytest
```

---

## 📝 PRÓXIMAS MELHORIAS (V2)

- [ ] Autenticação de usuários
- [ ] Controle de permissões (admin/usuário)
- [ ] Relatórios em PDF
- [ ] Agendamentos de audiências
- [ ] Notificações por email
- [ ] Upload de documentos
- [ ] Integração com APIs externas
- [ ] Testes automatizados
- [ ] Dashboard avançado com gráficos

---

## 📞 SUPORTE

Para dúvidas ou problemas:

1. Verifique a seção "Troubleshooting"
2. Consulte comentários no código (altamente documentado)
3. Abra uma issue no GitHub

---

## 📄 LICENÇA

Este projeto é fornecido como MVP para fins educacionais e de prototipagem.

---

## 👨‍💻 DESENVOLVIDO POR

**Engenheiro de Software Sênior**
2026 - Gestor Jurídico MVP

---

**Última Atualização:** 1 de Fevereiro de 2026
**Versão:** 1.0.0 - MVP
