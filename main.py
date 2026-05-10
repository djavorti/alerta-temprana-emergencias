import traceback
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
from src.notion_client import buscar_poliza, buscar_por_cedula, registrar_notificacion, obtener_notificaciones, obtener_estadisticas, obtener_polizas
from src.gemini_agent import analizar_ingreso
from src.notifications import enviar_notificaciones

app = FastAPI(title="Sistema de Alerta Temprana de Emergencias")

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sistema de Alerta Temprana - Emergencias</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @keyframes pulse-red { 0%,100%{opacity:1} 50%{opacity:.5} }
    .pulse-red { animation: pulse-red 2s cubic-bezier(.4,0,.6,1) infinite; }
    .card-hover { transition: all .3s ease; }
    .card-hover:hover { transform: translateY(-4px); box-shadow: 0 20px 25px -5px rgba(0,0,0,.1); }
    .fade-in { animation: fadeIn .5s ease-in; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
  </style>
</head>
<body class="bg-gray-50">
  <div class="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold">&#127973; Sistema de Alerta Temprana</h1>
          <p class="text-blue-100 mt-1">Monitoreo en tiempo real de ingresos a emergencias &middot; Powered by LLaMA 3.3 + Notion</p>
        </div>
        <div class="text-right">
          <div class="text-2xl font-bold" id="clock"></div>
          <div class="text-sm text-blue-100">&#218;ltima alerta: <span id="lastUpdate">-</span></div>
        </div>
      </div>
    </div>
  </div>

  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-lg shadow card-hover p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-blue-100 rounded-md p-3">
            <svg class="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600">Total Alertas</p>
            <p class="text-2xl font-semibold text-gray-900" id="totalAlertas">-</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-lg shadow card-hover p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-green-100 rounded-md p-3">
            <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600">P&#243;lizas Cubiertas</p>
            <p class="text-2xl font-semibold text-gray-900" id="cubiertas">-</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-lg shadow card-hover p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-yellow-100 rounded-md p-3">
            <svg class="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600">Parciales/No cubiertas</p>
            <p class="text-2xl font-semibold text-gray-900" id="noCubiertas">-</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-lg shadow card-hover p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0 bg-red-100 rounded-md p-3 pulse-red">
            <svg class="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600">Nivel ALTA</p>
            <p class="text-2xl font-semibold text-gray-900" id="criticos">-</p>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
      <div class="bg-white rounded-lg shadow-lg overflow-hidden">
        <div class="bg-blue-700 px-6 py-4">
          <h2 class="text-xl font-bold text-white">&#127973; Registrar Ingreso a Emergencias</h2>
          <p class="text-blue-200 text-sm mt-1">Al registrar, el Agente IA se activa autom&#225;ticamente y notifica a admisiones y al seguro</p>
        </div>
        <div class="p-6 space-y-4">

          <!-- Chips de cedulas -->
          <div>
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">&#128073; C&#233;dulas registradas &mdash; haz clic para usar</p>
            <div class="flex gap-2 flex-wrap">
              <button onclick="usarCedula('0999999999')" class="px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-800 text-sm font-medium rounded-lg border border-blue-200 flex items-center gap-2">&#129456; <span><strong>0999999999</strong> &middot; Carlos Mendoza</span></button>
              <button onclick="usarCedula('0111111111')" class="px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-800 text-sm font-medium rounded-lg border border-blue-200 flex items-center gap-2">&#129456; <span><strong>0111111111</strong> &middot; Mar&#237;a Garc&#237;a</span></button>
              <button onclick="usarCedula('0222222222')" class="px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-800 text-sm font-medium rounded-lg border border-blue-200 flex items-center gap-2">&#129456; <span><strong>0222222222</strong> &middot; Juan P&#233;rez</span></button>
            </div>
          </div>

          <!-- Campo cedula -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">N&#250;mero de C&#233;dula <span class="text-red-500">*</span></label>
            <div class="relative">
              <input id="f_cedula" type="text" placeholder="Ej: 0999999999" maxlength="13"
                class="w-full border border-gray-300 rounded-lg px-3 py-2 pr-10 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors" />
              <div id="cedula_icon" class="absolute right-3 top-2 text-xl hidden"></div>
            </div>
            <p id="cedula_error" class="text-xs text-red-500 mt-1 hidden">&#10060; C&#233;dula no encontrada en el sistema</p>
            <p id="cedula_loading" class="text-xs text-gray-400 mt-1 hidden">&#128269; Buscando...</p>
          </div>

          <!-- Info auto-rellenada -->
          <div id="poliza_info" class="hidden bg-green-50 border border-green-200 rounded-lg p-4 fade-in">
            <div class="flex items-center gap-2 mb-3">
              <span class="text-green-600 text-lg">&#9989;</span>
              <span class="text-sm font-semibold text-green-800">Paciente encontrado</span>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs font-medium text-gray-500 mb-1">Nombre del Paciente</p>
                <p class="text-sm font-bold text-gray-900" id="f_nombre_display">-</p>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 mb-1">ID P&#243;liza</p>
                <p class="text-sm font-bold text-gray-900" id="f_poliza_display">-</p>
              </div>
            </div>
          </div>

          <!-- Hidden inputs -->
          <input type="hidden" id="f_nombre" />
          <input type="hidden" id="f_poliza" />

          <!-- Hospital y motivo -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Hospital</label>
              <input id="f_hospital" type="text" value="Hospital Central" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Motivo de Ingreso</label>
              <input id="f_motivo" type="text" value="Dolor en el pecho" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <!-- Dos campos de email -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">&#127973; Email &mdash; Admisiones del Hospital</label>
            <input id="f_email_admisiones" type="email" placeholder="admisiones@hospital.com"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">&#128203; Email &mdash; Gestor de Casos del Seguro</label>
            <input id="f_email_gestor" type="email" placeholder="gestor@seguro.com"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
            <p class="text-xs text-gray-500 mt-1">Las notificaciones de alerta se enviar&#225;n a ambas direcciones</p>
          </div>

          <button onclick="simularIngreso()" id="btnSimular"
            class="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105">
            &#127973; Registrar Ingreso a Emergencias
          </button>
        </div>
        <div id="resultado" class="hidden px-6 pb-6">
          <div id="resultadoContent"></div>
        </div>
      </div>

      <div class="bg-white rounded-lg shadow-lg overflow-hidden">
        <div class="bg-gray-800 px-6 py-4">
          <h2 class="text-xl font-bold text-white">&#128225; Webhook de Integraci&#243;n</h2>
          <p class="text-gray-400 text-sm mt-1">Endpoint para sistemas hospitalarios</p>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <p class="text-sm font-medium text-gray-700 mb-2">URL del Webhook</p>
            <div class="bg-gray-100 rounded-lg p-3 font-mono text-sm break-all text-blue-700">
              POST https://alerta-temprana-emergencias.vercel.app/webhook/ingreso-emergencia
            </div>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-700 mb-2">Body (JSON)</p>
            <pre class="bg-gray-900 text-green-400 rounded-lg p-4 text-xs overflow-auto">{
  "nombre": "Carlos Mendoza",
  "id_poliza": "POL-2026-001",
  "hospital": "Hospital Central",
  "motivo": "Dolor en el pecho",
  "email_admisiones": "admisiones@hospital.com",
  "email_gestor": "gestor@seguro.com"
}</pre>
          </div>
          <div class="bg-blue-50 rounded-lg p-4">
            <p class="text-sm font-semibold text-blue-800 mb-2">&#129504; Flujo del Agente IA</p>
            <div class="space-y-1 text-sm text-blue-700">
              <div>&#128203; Consulta p&#243;liza en Notion</div>
              <div>&#129504; Analiza con LLaMA 3.3 (Groq)</div>
              <div>&#128231; Notifica a hospital y gestor simult&#225;neamente</div>
            </div>
          </div>
          <div class="bg-green-50 rounded-lg p-4">
            <p class="text-sm font-semibold text-green-800 mb-2">&#9989; P&#243;lizas disponibles en Notion</p>
            <div id="polizasInfoPanel" class="space-y-1 text-sm text-green-700">
              <div>&#128203; POL-2026-001 &mdash; Carlos Mendoza</div>
              <div>&#128203; POL-2026-002 &mdash; Mar&#237;a Garc&#237;a</div>
              <div>&#128203; POL-2026-003 &mdash; Juan P&#233;rez</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-lg shadow-lg overflow-hidden">
      <div class="bg-gray-800 px-6 py-4 flex items-center justify-between">
        <h2 class="text-xl font-bold text-white">&#128203; Alertas Recientes</h2>
        <button onclick="cargarDatos()" class="text-sm bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded-lg transition-colors">
          &#128260; Actualizar
        </button>
      </div>
      <div id="alertasContainer" class="divide-y divide-gray-200">
        <div class="p-8 text-center text-gray-400">Cargando alertas...</div>
      </div>
    </div>
  </div>

  <script>
    var polizaActual = null;
    var debounceTimer = null;

    function updateClock() {
      document.getElementById('clock').textContent = new Date().toLocaleTimeString('es-EC');
    }
    setInterval(updateClock, 1000);
    updateClock();

    function usarCedula(cedula) {
      document.getElementById('f_cedula').value = cedula;
      buscarPorCedula(cedula);
    }

    document.getElementById('f_cedula').addEventListener('input', function() {
      clearTimeout(debounceTimer);
      var val = this.value.trim();
      resetPolizaUI();
      if (val.length >= 8) {
        document.getElementById('cedula_loading').classList.remove('hidden');
        debounceTimer = setTimeout(function() { buscarPorCedula(val); }, 600);
      }
    });

    function resetPolizaUI() {
      polizaActual = null;
      document.getElementById('poliza_info').classList.add('hidden');
      document.getElementById('cedula_error').classList.add('hidden');
      document.getElementById('cedula_loading').classList.add('hidden');
      document.getElementById('cedula_icon').classList.add('hidden');
      document.getElementById('f_nombre').value = '';
      document.getElementById('f_poliza').value = '';
    }

    function buscarPorCedula(cedula) {
      document.getElementById('cedula_loading').classList.remove('hidden');
      document.getElementById('cedula_error').classList.add('hidden');
      fetch('/api/poliza/cedula/' + encodeURIComponent(cedula))
        .then(function(res) {
          document.getElementById('cedula_loading').classList.add('hidden');
          if (!res.ok) {
            document.getElementById('cedula_error').classList.remove('hidden');
            document.getElementById('cedula_icon').innerHTML = '&#10060;';
            document.getElementById('cedula_icon').classList.remove('hidden');
            polizaActual = null;
            return;
          }
          res.json().then(function(data) {
            polizaActual = data;
            document.getElementById('f_nombre').value = data.nombre;
            document.getElementById('f_poliza').value = data.id_poliza;
            document.getElementById('f_nombre_display').textContent = data.nombre;
            document.getElementById('f_poliza_display').textContent = data.id_poliza;
            document.getElementById('poliza_info').classList.remove('hidden');
            document.getElementById('cedula_icon').innerHTML = '&#9989;';
            document.getElementById('cedula_icon').classList.remove('hidden');
          });
        })
        .catch(function() {
          document.getElementById('cedula_loading').classList.add('hidden');
          document.getElementById('cedula_error').classList.remove('hidden');
          polizaActual = null;
        });
    }

    function cargarDatos() {
      fetch('/api/dashboard')
        .then(function(r) { return r.json(); })
        .then(function(data) {
          var s = data.estadisticas || {};
          document.getElementById('totalAlertas').textContent = s.total || 0;
          document.getElementById('cubiertas').textContent = s.cubiertas || 0;
          document.getElementById('noCubiertas').textContent = s.no_cubiertas || 0;
          document.getElementById('criticos').textContent = s.nivel_alta || 0;
          if (s.ultima_alerta) {
            document.getElementById('lastUpdate').textContent = new Date(s.ultima_alerta).toLocaleTimeString('es-EC');
          }
          renderizarAlertas(data.notificaciones || []);
        })
        .catch(function() {
          document.getElementById('alertasContainer').innerHTML =
            '<div class="p-6 text-center text-gray-400">Sin datos. <button onclick="cargarDatos()" class="underline">Reintentar</button></div>';
        });
    }

    function renderizarAlertas(notificaciones) {
      var container = document.getElementById('alertasContainer');
      if (!notificaciones.length) {
        container.innerHTML = '<div class="p-8 text-center text-gray-400">No hay alertas registradas.</div>';
        return;
      }
      var nivelColor = {ALTA:'red', MEDIA:'yellow', BAJA:'green'};
      var nivelEmoji = {ALTA:'&#128308;', MEDIA:'&#128993;', BAJA:'&#128994;'};
      var coberturaEmoji = {CUBIERTO:'&#9989;', PARCIAL:'&#9888;&#65039;', NO_CUBIERTO:'&#10060;', POLIZA_INVALIDA:'&#128683;'};
      container.innerHTML = notificaciones.map(function(n) {
        var color = nivelColor[n.nivel_alerta] || 'gray';
        return '<div class="p-6 hover:bg-gray-50 fade-in">' +
          '<div class="flex items-center gap-3 mb-2 flex-wrap">' +
          '<h3 class="text-lg font-semibold text-gray-900">' + (n.nombre || 'Paciente') + '</h3>' +
          '<span class="px-3 py-1 text-xs font-semibold rounded-full bg-' + color + '-100 text-' + color + '-800">' + (nivelEmoji[n.nivel_alerta] || '') + ' ' + (n.nivel_alerta || '') + '</span>' +
          '<span class="text-sm text-gray-600">' + (coberturaEmoji[n.estado_cobertura] || '') + ' ' + (n.estado_cobertura || '') + '</span></div>' +
          '<p class="text-sm text-gray-600 mb-2"><strong>P&#243;liza:</strong> ' + n.id_poliza + ' &middot; <strong>Hospital:</strong> ' + (n.hospital || '') + '</p>' +
          '<div class="bg-blue-50 border-l-4 border-blue-500 p-3"><p class="text-sm text-blue-900">' + (n.resumen || '') + '</p></div>' +
          '<p class="text-xs text-gray-400 mt-2">&#9200; ' + (n.timestamp ? new Date(n.timestamp).toLocaleString('es-EC') : '') + '</p>' +
          '</div>';
      }).join('');
    }

    function simularIngreso() {
      if (!polizaActual) { alert('Primero ingresa una cedula valida'); return; }
      var emailAdm = document.getElementById('f_email_admisiones').value.trim();
      var emailGes = document.getElementById('f_email_gestor').value.trim();
      if (!emailAdm || !emailGes) { alert('Ingresa ambos correos'); return; }
      var btn = document.getElementById('btnSimular');
      btn.disabled = true;
      btn.innerHTML = '&#9203; Activando agente IA...';
      document.getElementById('resultado').classList.add('hidden');
      var body = {
        nombre: document.getElementById('f_nombre').value,
        id_poliza: document.getElementById('f_poliza').value,
        hospital: document.getElementById('f_hospital').value,
        motivo: document.getElementById('f_motivo').value,
        email_admisiones: emailAdm,
        email_gestor: emailGes
      };
      fetch('/webhook/ingreso-emergencia', {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)
      })
        .then(function(res) {
          return res.json().then(function(data) { return {ok: res.ok, data: data}; });
        })
        .then(function(r) {
          var data = r.data;
          if (!r.ok) {
            document.getElementById('resultadoContent').innerHTML =
              '<div class="bg-red-50 border border-red-200 rounded-lg p-4"><p class="text-red-800 font-semibold">&#10060; ' + (data.error || 'Error') + '</p></div>';
          } else {
            var an = data.analisis || {};
            var nivelColor = {ALTA:'red', MEDIA:'yellow', BAJA:'green'};
            var color = nivelColor[an.nivel_alerta] || 'blue';
            var emailBadge = data.email_enviado
              ? '<span class="text-green-700">&#9989; Emails enviados</span>'
              : '<span class="text-yellow-700">&#9888; ' + (data.email_error || 'Email no enviado') + '</span>';
            document.getElementById('resultadoContent').innerHTML =
              '<div class="bg-' + color + '-50 border border-' + color + '-200 rounded-lg p-4 space-y-2">' +
              '<p class="font-semibold text-' + color + '-800">&#127973; Ingreso registrado &mdash; Agente IA activado</p>' +
              '<p class="text-sm text-' + color + '-700">' + emailBadge + '</p>' +
              '<p class="text-sm text-' + color + '-700"><strong>Cobertura:</strong> ' + (an.estado_cobertura || '-') + '</p>' +
              '<p class="text-sm text-' + color + '-700"><strong>Nivel:</strong> ' + (an.nivel_alerta || '-') + '</p>' +
              '<p class="text-sm text-' + color + '-700 mt-1">' + (an.resumen || '') + '</p>' +
              '<ul class="list-disc list-inside text-sm text-' + color + '-700">' +
              (an.recomendaciones || []).map(function(r) { return '<li>' + r + '</li>'; }).join('') +
              '</ul></div>';
            cargarDatos();
          }
          document.getElementById('resultado').classList.remove('hidden');
          btn.disabled = false;
          btn.innerHTML = '&#127973; Registrar Ingreso a Emergencias';
        })
        .catch(function(e) {
          document.getElementById('resultadoContent').innerHTML =
            '<div class="bg-red-50 border border-red-200 rounded-lg p-4"><p class="text-red-700">&#10060; ' + e.message + '</p></div>';
          document.getElementById('resultado').classList.remove('hidden');
          btn.disabled = false;
          btn.innerHTML = '&#127973; Registrar Ingreso a Emergencias';
        });
    }

    cargarDatos();
    setInterval(cargarDatos, 30000);
  </script>
</body>
</html>"""


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc), "tipo": type(exc).__name__, "detalle": traceback.format_exc().splitlines()[-3:]})


class IngresoEmergencia(BaseModel):
    nombre: str
    id_poliza: str
    hospital: str
    email_admisiones: EmailStr
    email_gestor: EmailStr
    motivo: str | None = None
    timestamp: str | None = None


@app.get("/")
def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML, headers={"Cache-Control": "no-store"})


@app.get("/api/dashboard")
def dashboard_data():
    notificaciones = obtener_notificaciones(limit=10)
    total = len(notificaciones)
    cubiertas = sum(1 for n in notificaciones if n["estado_cobertura"] == "CUBIERTO")
    nivel_alta = sum(1 for n in notificaciones if n["nivel_alerta"] == "ALTA")
    ultima = notificaciones[0]["timestamp"] if notificaciones else None
    return {
        "notificaciones": notificaciones,
        "estadisticas": {
            "total": total,
            "cubiertas": cubiertas,
            "no_cubiertas": total - cubiertas,
            "nivel_alta": nivel_alta,
            "ultima_alerta": ultima,
        },
    }


@app.get("/api/polizas")
def listar_polizas():
    return obtener_polizas(limit=5)


@app.get("/api/poliza/cedula/{cedula}")
def poliza_por_cedula(cedula: str):
    poliza = buscar_por_cedula(cedula)
    if not poliza:
        raise HTTPException(status_code=404, detail="Cédula no encontrada en el sistema")
    return poliza


@app.get("/api/estadisticas")
def estadisticas():
    return obtener_estadisticas()


@app.get("/api/notificaciones")
def notificaciones():
    return obtener_notificaciones()


@app.post("/webhook/ingreso-emergencia")
def webhook_ingreso(ingreso: IngresoEmergencia):
    ts = ingreso.timestamp or datetime.utcnow().isoformat()

    poliza = buscar_poliza(ingreso.id_poliza)
    if not poliza:
        raise HTTPException(status_code=404, detail="Póliza no encontrada en el sistema")

    paciente = {
        "nombre": ingreso.nombre,
        "id_poliza": ingreso.id_poliza,
        "hospital": ingreso.hospital,
        "motivo": ingreso.motivo,
        "timestamp": ts,
    }

    analisis = analizar_ingreso(paciente, poliza)

    email_ok = True
    email_error = None
    try:
        enviar_notificaciones(paciente, poliza, analisis, ingreso.email_admisiones, ingreso.email_gestor)
    except Exception as e:
        email_ok = False
        email_error = f"Email no enviado (restricción de dominio gratuito): usa el email verificado en Resend"

    registrar_notificacion(paciente, analisis, ingreso.email_admisiones)

    return {
        "mensaje": "Alerta procesada",
        "email_enviado": email_ok,
        "email_error": email_error,
        "analisis": {
            "estado_cobertura": analisis["estado_cobertura"],
            "nivel_alerta": analisis["nivel_alerta"],
            "resumen": analisis["resumen"],
            "recomendaciones": analisis["recomendaciones"],
            "preexistencias_relevantes": analisis.get("preexistencias_relevantes", ""),
        },
    }
