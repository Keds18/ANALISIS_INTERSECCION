from pathlib import Path
import csv
import io
import streamlit as st


def cargar_flujos_texto() -> str:
    """Lee el archivo flujos.txt si existe en el mismo directorio."""
    ruta = Path(__file__).with_name("flujos.txt")
    return ruta.read_text(encoding="utf-8") if ruta.exists() else ""


def parse_literal(valor):
    """Convierte cadenas a int, float o None de forma segura."""
    if valor is None:
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    try:
        return float(valor) if "." in valor else int(valor)

    except ValueError:
        return valor


def cargar_escenarios_flujos(texto: str) -> list[dict]:
    """Parsea el contenido CSV de flujos.txt en una lista de escenarios."""

    texto = texto.strip()

    if not texto:
        return []

    lineas = [
        l for l in texto.splitlines()
        if l.strip() and not l.startswith("#")
    ]

    if not lineas:
        return []

    lector = csv.DictReader(io.StringIO("\n".join(lineas)))

    escenarios = []

    for idx, fila in enumerate(lector, start=1):
        esc = {k.strip(): parse_literal(v) for k, v in fila.items()}
        esc["name"] = esc.get("scenario", f"Escenario {idx}")
        escenarios.append(esc)

    return escenarios


def kpi_card(label: str, value: str, unit: str = "", color: str = "#4f8ef7"):
    """Renderiza una tarjeta KPI con HTML."""
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left-color:{color}">
          <div class="kpi-label">{label}</div>
          <div>
            <span class="kpi-value">{value}</span>
            <span class="kpi-unit">{unit}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def obtener_atributo(resultado, nombre, valor_predeterminado=None):
    """Retorna un atributo de resultado que puede ser dict o un objeto."""

    if resultado is None:
        return valor_predeterminado

    if isinstance(resultado, dict):

        if nombre == "es_valido":
            return resultado.get("error") is None

        if nombre == "demora_minutos":
            return resultado.get(
                "demora_minutos",
                resultado.get("Wq", 0) * 60
            )

        if nombre == "longitud_cola_metros":
            return resultado.get(
                "longitud_cola_metros",
                resultado.get("Lq", 0) * 6.5
            )

        return resultado.get(nombre, valor_predeterminado)

    return getattr(resultado, nombre, valor_predeterminado)