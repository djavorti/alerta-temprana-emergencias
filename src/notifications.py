import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

NIVEL_COLOR = {"ALTA": "#d32f2f", "MEDIA": "#f57c00", "BAJA": "#388e3c"}
SENDER_NAME = "Agente IA · Alerta Temprana"


def _build_html(paciente: dict, poliza: dict, analisis: dict) -> str:
    color = NIVEL_COLOR.get(analisis["nivel_alerta"], "#1565c0")
    recomendaciones = "".join(f"<li>{r}</li>" for r in analisis["recomendaciones"])

    return f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
  <div style="background:{color};color:white;padding:20px">
    <h2 style="margin:0">&#127973; Alerta de Ingreso a Emergencias</h2>
    <p style="margin:4px 0 0">Nivel: <strong>{analisis['nivel_alerta']}</strong> &nbsp;|&nbsp; Cobertura: <strong>{analisis['estado_cobertura']}</strong></p>
  </div>
  <div style="padding:24px">
    <h3 style="margin-top:0;color:#1a1a1a">Datos del Paciente</h3>
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      <tr style="background:#f9f9f9"><td style="padding:8px 12px;color:#666;width:40%">Nombre</td><td style="padding:8px 12px"><strong>{paciente['nombre']}</strong></td></tr>
      <tr><td style="padding:8px 12px;color:#666">ID P&oacute;liza</td><td style="padding:8px 12px">{paciente['id_poliza']}</td></tr>
      <tr style="background:#f9f9f9"><td style="padding:8px 12px;color:#666">Hospital</td><td style="padding:8px 12px">{paciente['hospital']}</td></tr>
      <tr><td style="padding:8px 12px;color:#666">Motivo de ingreso</td><td style="padding:8px 12px">{paciente.get('motivo', 'No especificado')}</td></tr>
      <tr style="background:#f9f9f9"><td style="padding:8px 12px;color:#666">Estado P&oacute;liza</td><td style="padding:8px 12px">{poliza['estado']}</td></tr>
      <tr><td style="padding:8px 12px;color:#666">Vigencia</td><td style="padding:8px 12px">{poliza['fecha_vigencia']}</td></tr>
      <tr style="background:#f9f9f9"><td style="padding:8px 12px;color:#666">Timestamp</td><td style="padding:8px 12px">{paciente['timestamp']}</td></tr>
    </table>

    <h3 style="color:#1a1a1a;margin-top:24px">&#129504; An&aacute;lisis del Agente IA</h3>
    <div style="background:#f0f4ff;border-left:4px solid #3b82f6;padding:12px 16px;border-radius:0 6px 6px 0;font-size:14px;line-height:1.6">
      {analisis['resumen']}
    </div>

    <h3 style="color:#1a1a1a;margin-top:20px">Pre-existencias</h3>
    <p style="font-size:14px;color:#444;margin:0">{analisis.get('preexistencias_relevantes', 'No evaluado')}</p>

    <h3 style="color:#1a1a1a;margin-top:20px">Recomendaciones</h3>
    <ul style="font-size:14px;color:#444;line-height:1.8;padding-left:20px">{recomendaciones}</ul>
  </div>
  <div style="background:#f5f5f5;padding:12px 24px;font-size:11px;color:#999;text-align:center">
    Generado autom&aacute;ticamente por el Agente IA &middot; Sistema de Alerta Temprana de Emergencias
  </div>
</div>"""


def _send(to: str, subject: str, html: str):
    gmail_user = os.environ["GMAIL_USER"]
    gmail_pass = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{gmail_user}>"
    msg["To"] = to
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, to, msg.as_string())


def enviar_notificaciones(paciente: dict, poliza: dict, analisis: dict, email_hospital: str, email_gestor: str):
    html = _build_html(paciente, poliza, analisis)
    subject = f"[ALERTA {analisis['nivel_alerta']}] Ingreso a Emergencias — {paciente['nombre']}"
    _send(email_hospital, subject, html)
    _send(email_gestor, subject, html)
