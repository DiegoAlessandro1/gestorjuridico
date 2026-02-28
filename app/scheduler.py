# ============================================================================
# SCHEDULER - Tarefas agendadas
# ============================================================================
# Arquivo: app/scheduler.py
# Propósito: Executa tarefas em background (alertas de email)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.email_service import EmailService
import atexit

scheduler = BackgroundScheduler()

def iniciar_scheduler():
    """
    Inicia o scheduler com tarefas agendadas
    """
    try:
        # Tarefa diária às 08:00 para enviar alertas de prazos
        scheduler.add_job(
            func=enviar_alerta_prazos_diario,
            trigger=CronTrigger(hour=8, minute=0),
            id='alerta_prazos',
            name='Alerta de Prazos Vencendo',
            replace_existing=True
        )
        
        scheduler.start()
        print("✅ Scheduler iniciado com sucesso!")
        
        # Garante que o scheduler termine ao desligar a app
        atexit.register(lambda: scheduler.shutdown())
        
    except Exception as e:
        print(f"❌ Erro ao iniciar scheduler: {e}")

def enviar_alerta_prazos_diario():
    """
    Função chamada diariamente para enviar alertas de prazos
    """
    try:
        print("📧 Enviando alerta de prazos...")
        email_service = EmailService()
        email_service.enviar_alerta_prazos()
    except Exception as e:
        print(f"❌ Erro ao enviar alerta: {e}")

def parar_scheduler():
    """
    Para o scheduler
    """
    if scheduler.running:
        scheduler.shutdown()
        print("✅ Scheduler parado")
