#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

print('🔍 Testando credenciais Gmail SMTP...')
print(f'Host: {os.getenv("MAIL_SERVER")}')
print(f'Porta: {os.getenv("MAIL_PORT")}')
print(f'Usuário: {os.getenv("MAIL_USERNAME")}')
print()

try:
    server = smtplib.SMTP(os.getenv('MAIL_SERVER'), int(os.getenv('MAIL_PORT', 587)))
    print('✅ Conexão ao servidor SMTP estabelecida')
    
    server.starttls()
    print('✅ TLS iniciado')
    
    server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
    print('✅ Login realizado com sucesso')
    
    # Envia email de teste
    msg = MIMEMultipart()
    msg['Subject'] = '🧪 TESTE - Sistema de Alertas Gestor Jurídico'
    msg['From'] = os.getenv('MAIL_FROM')
    msg['To'] = os.getenv('MAIL_ALERT_TO')
    
    corpo_html = '<h1>✅ Email de Teste</h1><p>Se você recebeu este email, o sistema está funcionando corretamente!</p>'
    msg.attach(MIMEText(corpo_html, 'html'))
    
    server.sendmail(os.getenv('MAIL_FROM'), os.getenv('MAIL_ALERT_TO'), msg.as_string())
    print('✅ Email de teste enviado com sucesso!')
    print(f'📧 Destinatário: {os.getenv("MAIL_ALERT_TO")}')
    
    server.quit()
    
except smtplib.SMTPAuthenticationError as e:
    print(f'❌ Erro de autenticação: {e}')
    print('   Verifique a senha de app do Gmail')
except smtplib.SMTPException as e:
    print(f'❌ Erro SMTP: {e}')
except Exception as e:
    print(f'❌ Erro geral: {e}')
    import traceback
    traceback.print_exc()
