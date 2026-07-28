"""
email_utils.py
Utilitário de envio de e-mail usado para 2ª via de boletos, comprovantes de
pagamento e alertas de vencimento.

Se as variáveis SMTP_* estiverem configuradas (via variáveis de ambiente),
o e-mail é enviado de verdade. Caso contrário, o envio é SIMULADO — retorna
sucesso e mostra no log o que seria enviado, sem precisar de credenciais
reais para testar.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", "cobranca@petromazxquimica.com")

def smtp_configurado() -> bool:
    return all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD])

def enviar_email(destinatario: str, assunto: str, corpo: str) -> dict:
    """Envia um e-mail. Usa SMTP real se configurado no .env; caso
    contrário, simula o envio (não falha o fluxo do agente)."""

    if not destinatario:
        return {"sucesso": False, "mensagem": "E-mail de destino não informado."}
    
    if not smtp_configurado():
        return {
            "sucesso": True,
            "modo": "simulado",
            "mensagem": f"[SIMULADO] E-mail enviado para {destinatario} com assunto '{assunto}'.",
        }
    
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_FROM
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        return {"sucesso": True, "modo": "real", "mensagem": f"E-mail enviado para {destinatario}."}
    except Exception as e:
        return {"sucesso": False, "modo": "real", "mensagem": f"Falha ao enviar e-mail: {e}"}
