# ============================================================================
# PROCFILE - CONFIGURAÇÃO PARA DEPLOY
# ============================================================================
# Arquivo: Procfile
# Propósito: Instrui plataformas de deploy (Render, Heroku) como iniciar a app
#
# Quando você faz deploy para Render/Heroku, a plataforma lê este arquivo
# e executa o comando especificado para iniciar a aplicação
#
# Formato: <processo>: <comando>
# - web: Processo que escuta conexões HTTP
# - worker: Tarefas em background (opcional)
# 
# Processo de Deploy:
# 1. Conecte seu repositório GitHub ao Render/Heroku
# 2. Este arquivo será detectado automaticamente
# 3. A plataforma instala requirements.txt
# 4. Executa este Procfile para iniciar a app
# ============================================================================

# PROCESSO WEB - Inicia servidor Flask com Gunicorn
# 
# Explicação:
# - gunicorn: Servidor WSGI robusto para produção
# - run:app: Executa a app do arquivo run.py (função create_app)
# - --bind: Define porta (0.0.0.0 = aceita conexões externas, :5000 ou $PORT)
# - --workers: Número de processos (máquinas pequenas = 1-2)
# - --worker-class: Tipo de worker
# - --timeout: Tempo máximo para requisição (segundos)
#
# OBS: Variável $PORT é injetada automaticamente pelo Render/Heroku

web: gunicorn --bind 0.0.0.0:$PORT --workers 1 --worker-class sync --timeout 60 run:app
