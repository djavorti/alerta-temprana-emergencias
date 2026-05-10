import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def analizar_ingreso(paciente: dict, poliza: dict) -> dict:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    prompt = f"""
Eres un auditor médico especializado en seguros de salud de emergencias. Analiza el siguiente caso con criterio clínico y de cobertura.

CASO DE EMERGENCIA:
- Paciente: {paciente['nombre']}
- Motivo de ingreso: {paciente.get('motivo', 'No especificado')}
- Hospital: {paciente['hospital']}
- Timestamp: {paciente['timestamp']}

PÓLIZA:
- ID: {paciente['id_poliza']}
- Estado: {poliza['estado']}
- Vigencia hasta: {poliza['fecha_vigencia']}
- Pre-existencias registradas: {poliza['preexistencias']}

INSTRUCCIONES DE ANÁLISIS OBLIGATORIAS:
1. RELACIÓN CLÍNICA: Determina si la pre-existencia "{poliza['preexistencias']}" tiene relación médica directa o indirecta con el motivo de ingreso "{paciente.get('motivo', 'No especificado')}". Sé explícito: indica "SÍ está relacionado" o "NO está relacionado" con justificación clínica concreta.
2. COBERTURA: Basándote en la relación o no-relación, determina el nivel de cobertura real. Si la pre-existencia complica el ingreso, aplica PARCIAL.
3. RECOMENDACIONES ESPECÍFICAS: Da recomendaciones concretas para ESTE caso puntual: qué exámenes solicitar, qué protocolos activar, qué documentar para el seguro. Nada genérico.

Responde ÚNICAMENTE en formato JSON con esta estructura exacta, sin texto adicional:
{{
  "estado_cobertura": "CUBIERTO | PARCIAL | NO_CUBIERTO | POLIZA_INVALIDA",
  "nivel_alerta": "ALTA | MEDIA | BAJA",
  "resumen": "2-3 oraciones que indiquen EXPLÍCITAMENTE si la pre-existencia se relaciona con el motivo y cómo impacta la cobertura",
  "recomendaciones": ["recomendación específica 1", "recomendación específica 2", "recomendación específica 3"],
  "preexistencias_relevantes": "SÍ/NO está relacionado + explicación clínica en 1 oración"
}}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    text = response.choices[0].message.content
    json_match = re.search(r'\{[\s\S]*\}', text)
    if not json_match:
        raise ValueError("El agente no retornó JSON válido")

    return json.loads(json_match.group())
