import os
import json
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"), timeout_ms=10000)
POLIZAS_DB = os.getenv("NOTION_POLIZAS_DB")
NOTIF_DB = os.getenv("NOTION_NOTIF_DB")


def _texto(prop): return prop["rich_text"][0]["plain_text"] if prop.get("rich_text") else ""
def _titulo(prop): return prop["title"][0]["plain_text"] if prop.get("title") else ""
def _select(prop): return prop["select"]["name"] if prop.get("select") else ""
def _email(prop): return prop.get("email") or ""
def _fecha(prop): return prop["date"]["start"] if prop.get("date") else ""


def buscar_por_cedula(cedula: str) -> dict | None:
    try:
        response = notion.databases.query(
            database_id=POLIZAS_DB,
            filter={"property": "Cedula", "rich_text": {"equals": cedula}},
        )
        if not response["results"]:
            return None
        props = response["results"][0]["properties"]
        return {
            "id_poliza": _titulo(props.get("ID Poliza", {})),
            "nombre": _texto(props.get("Nombre Asegurado", {})),
            "email": _email(props.get("Email Asegurado ", {})),
            "estado": _select(props.get("Estado Poliza", {})),
            "preexistencias": _texto(props.get("Pre-existencias", {})) or "Sin información",
            "fecha_vigencia": _fecha(props.get("Fecha Vigencia ", {})),
            "cedula": cedula,
        }
    except Exception:
        return None


def buscar_poliza(id_poliza: str) -> dict | None:
    try:
        response = notion.databases.query(
            database_id=POLIZAS_DB,
            filter={"property": "ID Poliza", "title": {"equals": id_poliza}},
        )
        if not response["results"]:
            return None
        props = response["results"][0]["properties"]
        return {
            "id_poliza": _titulo(props.get("ID Poliza", {})),
            "nombre": _texto(props.get("Nombre Asegurado", {})),
            "email": _email(props.get("Email Asegurado ", {})),
            "estado": _select(props.get("Estado Poliza", {})),
            "preexistencias": _texto(props.get("Pre-existencias", {})) or "Sin información",
            "fecha_vigencia": _fecha(props.get("Fecha Vigencia ", {})),
        }
    except Exception:
        return None


def registrar_notificacion(paciente: dict, analisis: dict, email_hospital: str):
    resumen = json.dumps({
        "nombre": paciente["nombre"],
        "hospital": paciente["hospital"],
        "estado_cobertura": analisis["estado_cobertura"],
        "nivel_alerta": analisis["nivel_alerta"],
        "resumen": analisis["resumen"][:800],
    }, ensure_ascii=False)

    try:
        notion.pages.create(
            parent={"database_id": NOTIF_DB},
            properties={
                "ID Poliza": {"title": [{"text": {"content": paciente["id_poliza"]}}]},
                "Timestamp": {"date": {"start": datetime.utcnow().isoformat()}},
                "Estado Alerta": {"rich_text": [{"text": {"content": resumen}}]},
                "Email Hospital": {"email": email_hospital},
            },
        )
    except Exception:
        pass


def obtener_notificaciones(limit: int = 20) -> list:
    try:
        response = notion.databases.query(
            database_id=NOTIF_DB,
            sorts=[{"property": "Timestamp", "direction": "descending"}],
            page_size=limit,
        )
        results = []
        for page in response["results"]:
            props = page["properties"]
            raw = _texto(props.get("Estado Alerta", {}))
            try:
                data = json.loads(raw)
            except Exception:
                data = {"resumen": raw}
            results.append({
                "id_poliza": _titulo(props.get("ID Poliza", {})),
                "timestamp": _fecha(props.get("Timestamp", {})),
                "email_hospital": _email(props.get("Email Hospital", {})),
                "nombre": data.get("nombre", ""),
                "hospital": data.get("hospital", ""),
                "estado_cobertura": data.get("estado_cobertura", ""),
                "nivel_alerta": data.get("nivel_alerta", ""),
                "resumen": data.get("resumen", ""),
            })
        return results
    except Exception:
        return []


def obtener_polizas(limit: int = 5) -> list:
    try:
        response = notion.databases.query(
            database_id=POLIZAS_DB,
            page_size=limit,
        )
        results = []
        for page in response["results"]:
            props = page["properties"]
            cedula = _texto(props.get("Cedula", {}))
            nombre = _texto(props.get("Nombre Asegurado", {}))
            id_poliza = _titulo(props.get("ID Poliza", {}))
            if cedula and nombre:
                results.append({"cedula": cedula, "nombre": nombre, "id_poliza": id_poliza})
        return results
    except Exception:
        return []


def obtener_estadisticas() -> dict:
    notifs = obtener_notificaciones(limit=100)
    total = len(notifs)
    cubiertas = sum(1 for n in notifs if n["estado_cobertura"] == "CUBIERTO")
    nivel_alta = sum(1 for n in notifs if n["nivel_alerta"] == "ALTA")
    ultima = notifs[0]["timestamp"] if notifs else None
    return {
        "total": total,
        "cubiertas": cubiertas,
        "no_cubiertas": total - cubiertas,
        "nivel_alta": nivel_alta,
        "ultima_alerta": ultima,
    }
