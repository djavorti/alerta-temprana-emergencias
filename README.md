# Sistema de Alerta Temprana de Ingresos a Emergencias

Sistema automatizado que se activa cuando un asegurado ingresa a emergencias. Al registrar el ingreso, un agente de IA analiza la validez de la póliza y las pre-existencias, y envía notificaciones simultáneas al hospital y al gestor de casos del seguro.

## Características

- **Webhook en tiempo real** para recibir ingresos a emergencia
- **Agente IA (LLaMA 3.3 via Groq)** que analiza automáticamente:
  - Validez y vigencia de la póliza
  - Relación clínica entre pre-existencias y el motivo de ingreso
  - Nivel de alerta (ALTA / MEDIA / BAJA)
  - Estado de cobertura (CUBIERTO / PARCIAL / NO_CUBIERTO)
  - Recomendaciones específicas para el caso
- **Notificaciones HTML** simultáneas vía Gmail SMTP a dos destinatarios:
  - Admisiones del hospital
  - Gestor de casos del seguro
- **Registro por cédula** — al ingresar el número de cédula, nombre e ID de póliza se auto-rellenan desde Notion
- **Dashboard en tiempo real** con estadísticas y alertas recientes
- **Base de datos en Notion** — pólizas y registro de alertas

## Demo en vivo

| Recurso | URL |
|---------|-----|
| **Dashboard** | https://alerta-temprana-emergencias.vercel.app |
| **Webhook** | `POST https://alerta-temprana-emergencias.vercel.app/webhook/ingreso-emergencia` |

## Cómo probar el agente desde el dashboard

### Paso 1 — Abrir el dashboard
Ve a **https://alerta-temprana-emergencias.vercel.app**

### Paso 2 — Seleccionar un paciente
En la sección **"Registrar Ingreso a Emergencias"**, haz clic en uno de los chips de cédula disponibles:

| Cédula | Paciente | Póliza |
|--------|----------|--------|
| `0999999999` | Carlos Mendoza | POL-2026-001 |
| `0111111111` | María García | POL-2026-002 |
| `0222222222` | Juan Pérez | POL-2026-003 |

Al hacer clic, el nombre y el ID de póliza se llenan automáticamente desde Notion. También puedes escribir la cédula manualmente en el campo de texto.

### Paso 3 — Completar los datos del ingreso
- **Hospital**: viene pre-llenado con "Hospital Central" (puedes cambiarlo)
- **Motivo de ingreso**: viene pre-llenado con "Dolor en el pecho" — **cámbialo** para ver cómo el agente IA relaciona el motivo con las pre-existencias del paciente. Ejemplos:
  - `Dolor en el pecho`
  - `Fractura de tobillo`
  - `Crisis hipertensiva`
  - `Dificultad para respirar`

### Paso 4 — Ingresar correos de notificación
- **Email de admisiones del hospital**: cualquier correo al que quieras recibir la alerta
- **Email del gestor de casos**: cualquier correo (puede ser el mismo u otro)

### Paso 5 — Registrar el ingreso
Haz clic en **"Registrar Ingreso a Emergencias"**. El agente tardará unos segundos (~10–20 seg) mientras:
1. Consulta la póliza y pre-existencias en Notion
2. Analiza con LLaMA 3.3 la relación clínica entre pre-existencias y motivo
3. Envía las notificaciones por email a ambos destinatarios
4. Registra la alerta en Notion

### Paso 6 — Ver el resultado
Verás directamente en el dashboard:
- **Estado de cobertura**: `CUBIERTO` / `PARCIAL` / `NO_CUBIERTO`
- **Nivel de alerta**: `ALTA` / `MEDIA` / `BAJA`
- **Análisis clínico** con la relación entre pre-existencias y el motivo de ingreso
- **Recomendaciones** específicas para el caso
- La alerta quedará registrada en la sección **"Alertas Recientes"** al fondo de la página

## Stack Tecnológico

| Componente | Tecnología |
|-----------|------------|
| Backend | Python · FastAPI |
| Agente IA | LLaMA 3.3 70B (Groq) |
| Base de datos | Notion API |
| Notificaciones | Gmail SMTP |
| Deploy | Vercel |

## Instalación Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/djavorti/alerta-temprana-emergencias.git
cd alerta-temprana-emergencias
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crea un archivo `.env`:
```env
NOTION_TOKEN=tu_notion_integration_token
NOTION_POLIZAS_DB=id_de_tu_base_polizas
NOTION_NOTIF_DB=id_de_tu_base_notificaciones
GROQ_API_KEY=tu_groq_api_key
GMAIL_USER=tucorreo@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

#### Cómo obtener las credenciales:

**Groq (gratis):**
1. Ve a https://console.groq.com/keys
2. Crea una cuenta y genera una API Key

**Notion:**
1. Ve a https://www.notion.com/my-integrations
2. Crea una integración y copia el Internal Integration Token
3. Comparte las bases de datos con la integración

**Gmail App Password:**
1. Activa verificación en 2 pasos en tu cuenta Google
2. Ve a Cuenta de Google → Seguridad → Contraseñas de aplicaciones
3. Genera una contraseña de 16 caracteres

### 4. Iniciar el servidor
```bash
uvicorn main:app --port 3000 --reload
```

El dashboard estará disponible en: **http://localhost:3000**

## Uso del Webhook

### Endpoint principal

**POST** `/webhook/ingreso-emergencia`

```json
{
  "nombre": "Carlos Mendoza",
  "id_poliza": "POL-2026-001",
  "hospital": "Hospital Central",
  "motivo": "Dolor en el pecho",
  "email_admisiones": "admisiones@hospital.com",
  "email_gestor": "gestor@seguro.com"
}
```

### Ejemplo con cURL
```bash
curl -X POST https://alerta-temprana-emergencias.vercel.app/webhook/ingreso-emergencia \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Carlos Mendoza",
    "id_poliza": "POL-2026-001",
    "hospital": "Hospital Central",
    "motivo": "Dolor en el pecho",
    "email_admisiones": "admisiones@hospital.com",
    "email_gestor": "gestor@seguro.com"
  }'
```

### Respuesta
```json
{
  "mensaje": "Alerta procesada",
  "email_enviado": true,
  "analisis": {
    "estado_cobertura": "CUBIERTO",
    "nivel_alerta": "ALTA",
    "resumen": "El paciente Carlos Mendoza ingresó con dolor en el pecho. La pre-existencia de diabetes tipo 2 NO está directamente relacionada con el motivo de ingreso cardiovascular.",
    "recomendaciones": ["Realizar ECG inmediato", "Solicitar troponinas", "Notificar cardiólogo de guardia"],
    "preexistencias_relevantes": "NO está relacionado — la diabetes es metabólica, el dolor en el pecho sugiere evento cardiovascular independiente"
  }
}
```

## Endpoints disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Dashboard principal |
| GET | `/api/polizas` | Lista de pólizas registradas (máx. 5) |
| GET | `/api/poliza/cedula/{cedula}` | Buscar póliza por número de cédula |
| POST | `/webhook/ingreso-emergencia` | Registrar ingreso a emergencias |
| GET | `/api/estadisticas` | Estadísticas del sistema |
| GET | `/api/notificaciones` | Historial de alertas |

## Estructura del Proyecto

```
alerta-temprana-emergencias/
├── main.py                  # Servidor FastAPI + Dashboard HTML embebido
├── requirements.txt         # Dependencias Python
├── vercel.json              # Configuración Vercel
└── src/
    ├── notion_client.py    # Integración con Notion
    ├── gemini_agent.py     # Agente IA (Groq/LLaMA 3.3)
    └── notifications.py    # Notificaciones email (Gmail SMTP)
```

## Flujo del Sistema

```
1. Hospital registra ingreso → POST /webhook/ingreso-emergencia
         ↓
2. Sistema busca póliza en Notion por ID
         ↓
3. Agente LLaMA 3.3 analiza:
   · Validez de la póliza
   · Relación clínica entre pre-existencias y motivo de ingreso
   · Nivel de alerta y cobertura
   · Recomendaciones específicas para el caso
         ↓
4. Notificaciones HTML simultáneas vía Gmail SMTP:
   · Email a admisiones del hospital
   · Email al gestor de casos del seguro
         ↓
5. Registro en Notion + actualización del dashboard
```

---

Desarrollado por los pybes para el **Reto 4 — HackIAthon Viamatica 2026**
