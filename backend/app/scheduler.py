# ============================================================================
# SCHEDULER - Tarefas agendadas
# ============================================================================
# Arquivo: app/scheduler.py
# Propósito: Executa tarefas em background (alertas de email)

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_DISPONIVEL = True
    ERRO_APSCHEDULER = None
except Exception as e:
    APSCHEDULER_DISPONIVEL = False
    ERRO_APSCHEDULER = e

from .email_service import EmailService
import atexit

scheduler = BackgroundScheduler() if APSCHEDULER_DISPONIVEL else None

def iniciar_scheduler():
    """
    Inicia o scheduler com tarefas agendadas
    """
    if not APSCHEDULER_DISPONIVEL or scheduler is None:
        print(f"[AVISO] APScheduler indisponivel: {ERRO_APSCHEDULER}")
        return False

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
        print("[OK] Scheduler iniciado com sucesso")
        
        # Garante que o scheduler termine ao desligar a app
        atexit.register(lambda: scheduler.shutdown())
        return True
        
    except Exception as e:
        print(f"[ERRO] Falha ao iniciar scheduler: {e}")
        return False

def enviar_alerta_prazos_diario():
    """
    Função chamada diariamente para enviar alertas de prazos
    """
    try:
        print("[INFO] Enviando alerta de prazos")
        email_service = EmailService()
        email_service.enviar_alerta_prazos()
    except Exception as e:
        print(f"[ERRO] Falha ao enviar alerta: {e}")

def parar_scheduler():
    """
    Para o scheduler
    """
    if scheduler is not None and scheduler.running:
        scheduler.shutdown()
        print("[OK] Scheduler parado")
