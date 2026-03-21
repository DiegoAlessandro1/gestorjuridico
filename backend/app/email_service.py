# ============================================================================
# UTILITÁRIO DE EMAIL - Envio de alertas
# ============================================================================
# Arquivo: app/email_service.py
# Propósito: Funcionalidades para envio de email

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from .config import get_db
from .models import Processo

class EmailService:
    """
    Serviço de envio de emails
    """
    
    def __init__(self):
        self.server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        self.port = int(os.getenv('MAIL_PORT', 587))
        self.username = os.getenv('MAIL_USERNAME')
        self.password = os.getenv('MAIL_PASSWORD')
        self.from_addr = os.getenv('MAIL_FROM')
        self.use_tls = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    
    def enviar_email(self, destinatario, assunto, corpo_html):
        """
        Envia um email
        
        Argumentos:
            destinatario: Email do destinatário
            assunto: Assunto do email
            corpo_html: Corpo em HTML
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = assunto
            msg['From'] = self.from_addr
            msg['To'] = destinatario
            
            # Corpo em texto puro (fallback)
            corpo_texto = corpo_html.replace('<br>', '\n').replace('<p>', '').replace('</p>', '\n')
            
            msg.attach(MIMEText(corpo_texto, 'plain'))
            msg.attach(MIMEText(corpo_html, 'html'))
            
            # Conecta ao servidor SMTP do Gmail
            server = smtplib.SMTP(self.server, self.port)
            if self.use_tls:
                server.starttls()
            
            server.login(self.username, self.password)
            server.sendmail(self.from_addr, destinatario, msg.as_string())
            server.quit()
            
            print(f"✅ Email enviado para {destinatario}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar email: {e}")
            return False
    
    def enviar_alerta_prazos(self):
        """
        Envia alerta dos prazos que vencem nos próximos 3 dias (inclusive hoje)
        
        Lógica:
        1. Busca todos os processos com prazo entre hoje e 3 dias
        2. Monta HTML com tabela dos processos
        3. Envia email
        """
        try:
            db = get_db()
            email_destino = os.getenv('MAIL_ALERT_TO')
            
            if not email_destino:
                print("⚠️  MAIL_ALERT_TO não configurado no .env")
                return False
            
            # Calcula datas
            hoje = datetime.now()
            data_hoje = hoje.strftime('%Y-%m-%d')
            data_3dias = (hoje + timedelta(days=3)).strftime('%Y-%m-%d')
            
            # Busca processos com prazo entre hoje e 3 dias
            processos_alerta = list(db['processos'].find({
                'prazo_data': {'$gte': data_hoje, '$lte': data_3dias},
                'status': {'$in': ['Aberto', 'Suspenso']}
            }).sort('prazo_data', 1))
            
            # Busca compromissos com data entre hoje e 3 dias
            compromissos_alerta = list(db['agenda'].find({
                'data': {'$gte': data_hoje, '$lte': data_3dias},
                'status': 'Agendado'
            }).sort('data', 1))
            
            if not processos_alerta and not compromissos_alerta:
                print("ℹ️  Nenhum alerta para enviar hoje")
                return True
            
            # Monta HTML
            html = self._montar_html_alerta(processos_alerta, compromissos_alerta, data_hoje, data_3dias)
            
            # Envia email
            assunto = f"⚠️ Alerta de Prazos - Próximos 3 dias ({data_hoje} a {data_3dias})"
            return self.enviar_email(email_destino, assunto, html)
            
        except Exception as e:
            print(f"❌ Erro ao enviar alerta de prazos: {e}")
            return False
    
    def _montar_html_alerta(self, processos, compromissos, data_hoje, data_3dias):
        """
        Monta HTML do email de alerta
        """
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 15px; border-radius: 5px; text-align: center; }}
                .content {{ margin-top: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th {{ background: #f8f9fa; padding: 10px; border: 1px solid #dee2e6; text-align: left; }}
                td {{ padding: 10px; border: 1px solid #dee2e6; }}
                .section {{ margin: 20px 0; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>⚠️ ALERTA DE PRAZOS</h2>
                    <p>Prazos vencendo nos próximos 3 dias</p>
                    <p><strong>De {data_hoje} até {data_3dias}</strong></p>
                </div>
                
                <div class="content">
        """
        
        # Processos
        if processos:
            html += """
                    <div class="section">
                        <h3>📋 Processos com Prazo</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Número</th>
                                    <th>Cliente</th>
                                    <th>Tipo</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            for p in processos:
                html += f"""
                                <tr>
                                    <td>{p.get('numero_processo', '')}</td>
                                    <td>{p.get('cliente_nome', '')}</td>
                                    <td>{p.get('tipo_acao', '')}</td>
                                    <td>{p.get('status', '')}</td>
                                </tr>
                """
            html += """
                            </tbody>
                        </table>
                    </div>
            """
        
        # Compromissos
        if compromissos:
            html += """
                    <div class="section">
                        <h3>📅 Compromissos Agendados</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Hora</th>
                                    <th>Título</th>
                                    <th>Tipo</th>
                                    <th>Local</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            for c in compromissos:
                html += f"""
                                <tr>
                                    <td>{c.get('hora', '')}</td>
                                    <td>{c.get('titulo', '')}</td>
                                    <td>{c.get('tipo', '')}</td>
                                    <td>{c.get('local', '')}</td>
                                </tr>
                """
            html += """
                            </tbody>
                        </table>
                    </div>
            """
        
        html += """
                    <div class="footer">
                        <p>Este é um email automático. Não responda diretamente.</p>
                        <p>Gestor Jurídico MVP © 2026</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
