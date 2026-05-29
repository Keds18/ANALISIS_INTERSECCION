# ==========================================
# APP TRANSITO - VERSION 2
# Dashboard de análisis operacional
# ==========================================

import csv
import io
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from colas import calcular_cola
from nivelservicio import nivel_servicio
from webster import calcular_ciclo_webster


# ------------------------------------------
# CONFIG
# ------------------------------------------

st.set_page_config(
    page_title="TRANSITO 🚦",
    page_icon="🚦",
    layout="wide"
)


# ------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------

def cargar_flujos_texto():
    ruta = Path(__file__).with_name("flujos.txt")
    if ruta.exists():
        return ruta.read_text(encoding="utf-8")
    return ""


def parse_literal(valor):
    if valor is None:
        return None

    valor = str(valor).strip()

    if valor == "":
        return None

    try:
        if "." in valor:
            return float(valor)
        return int(valor)

    except ValueError:
        return valor


def cargar_escenarios_flujos(texto):

    texto = texto.strip()

    if not texto:
        return []

    lineas = [
        linea for linea in texto.splitlines()
        if linea.strip()
        and not linea.startswith("#")
    ]

    if not lineas:
        return []

    lector = csv.DictReader(io.StringIO("\n".join(lineas)))

    escenarios = []

    for fila in lector:

        escenario = {}

        for clave, valor in fila.items():
            escenario[clave.strip()] = parse_literal(valor)

        escenario["name"] = escenario.get(
            "scenario",
            f"Escenario {len(escenarios)+1}"
        )

        escenarios.append(escenario)

    return escenarios


# ------------------------------------------
# SESSION STATE
# ------------------------------------------

if "resultado_webster" not in st.session_state:
    st.session_state.resultado_webster = None

if "resultado_cola" not in st.session_state:
    st.session_state.resultado_cola = None


# ------------------------------------------
# TITULO
# ------------------------------------------

st.title("🚦 Sistema Integrado de Análisis de Tránsito")
st.caption(
    "Método de Webster + Teoría de Colas + Nivel de Servicio"
)


# ------------------------------------------
# CARGA DE ESCENARIOS
# ------------------------------------------

texto_flujos = cargar_flujos_texto()
escenarios = cargar_escenarios_flujos(texto_flujos)

escenario = {}

if escenarios:

    nombres = [e["name"] for e in escenarios]

    seleccion = st.selectbox(
        "Seleccionar escenario:",
        nombres
    )

    escenario = next(
        e for e in escenarios
        if e["name"] == seleccion
    )


# ------------------------------------------
# SIDEBAR
# ------------------------------------------

with st.sidebar:

    st.header("⚙ Parámetros de entrada")

    st.subheader("Flujos")

    q_norte = st.number_input(
        "Norte",
        value=float(escenario.get("q_norte", 450))
    )

    q_sur = st.number_input(
        "Sur",
        value=float(escenario.get("q_sur", 400))
    )

    q_este = st.number_input(
        "Este",
        value=float(escenario.get("q_este", 350))
    )

    q_oeste = st.number_input(
        "Oeste",
        value=float(escenario.get("q_oeste", 300))
    )

    st.subheader("Semaforización")

    s = st.number_input(
        "Saturación s (veh/h)",
        value=float(escenario.get("s", 1800))
    )

    L = st.number_input(
        "Tiempo perdido L (s)",
        value=float(escenario.get("L", 12))
    )

    st.subheader("Colas")

    lambda_llegadas = st.number_input(
        "λ llegadas",
        value=float(escenario.get("lambda", 300))
    )

    mu_servicio = st.number_input(
        "μ servicio",
        value=float(escenario.get("mu", 500))
    )


# ------------------------------------------
# BOTONES
# ------------------------------------------

col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("🚦 Calcular Webster"):
        st.session_state.resultado_webster = calcular_ciclo_webster(
            q_norte,
            q_sur,
            q_este,
            q_oeste,
            s=s,
            L=L
        )

with col_btn2:
    if st.button("🚗 Calcular Cola"):
        st.session_state.resultado_cola = calcular_cola(
            lambda_llegadas,
            mu_servicio
        )


# ------------------------------------------
# TABS
# ------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "🚦 Webster",
    "🚗 Colas",
    "📊 Dashboard",
    "📁 Exportar"
])


# ==========================================
# TAB 1 WEBSTER
# ==========================================

with tab1:

    resultado = st.session_state.resultado_webster

    if resultado and "error" not in resultado:

        st.subheader("Resultados del Método de Webster")

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "Relación crítica Y",
                round(resultado["Y"], 3)
            )

        with c2:
            st.metric(
                "Ciclo óptimo",
                f"{round(resultado['C'],1)} s"
            )

        st.write("### Verdes efectivos")

        st.dataframe(
            pd.DataFrame(
                resultado["verde"].items(),
                columns=["Acceso", "Verde (s)"]
            )
        )


# ==========================================
# TAB 2 COLAS
# ==========================================

with tab2:

    resultado = st.session_state.resultado_cola

    if resultado and "error" not in resultado:

        demora_min = resultado["Wq"] * 60
        longitud_cola = resultado["Lq"] * 6.5

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("ρ", round(resultado["rho"], 3))
        c2.metric("Lq", round(resultado["Lq"], 2))
        c3.metric("Demora", f"{demora_min:.2f} min")
        c4.metric("Cola estimada", f"{longitud_cola:.1f} m")

        st.success(
            f"Nivel de servicio: {nivel_servicio(demora_min)}"
        )


# ==========================================
# TAB 3 DASHBOARD
# ==========================================

with tab3:

    st.subheader("Dashboard de Flujos")

    df_flujos = pd.DataFrame({
        "Acceso": ["Norte", "Sur", "Este", "Oeste"],
        "Flujo": [
            q_norte,
            q_sur,
            q_este,
            q_oeste
        ]
    })

    st.bar_chart(
        df_flujos.set_index("Acceso")
    )

    st.subheader("Relación v/c")

    df_vc = pd.DataFrame({
        "Acceso": ["Norte", "Sur", "Este", "Oeste"],
        "v/c": [
            q_norte/s,
            q_sur/s,
            q_este/s,
            q_oeste/s
        ]
    })

    st.dataframe(df_vc)

    fig, ax = plt.subplots()

    ax.pie(
        df_flujos["Flujo"],
        labels=df_flujos["Acceso"],
        autopct="%1.1f%%"
    )

    st.pyplot(fig)


# ==========================================
# TAB 4 EXPORTAR
# ==========================================

with tab4:

    st.subheader("Exportación")

    df_export = pd.DataFrame([
        {"Campo": "q_norte", "Valor": q_norte},
        {"Campo": "q_sur", "Valor": q_sur},
        {"Campo": "q_este", "Valor": q_este},
        {"Campo": "q_oeste", "Valor": q_oeste},
        {"Campo": "s", "Valor": s},
        {"Campo": "L", "Valor": L},
        {"Campo": "lambda", "Valor": lambda_llegadas},
        {"Campo": "mu", "Valor": mu_servicio},
    ])

    csv_bytes = df_export.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Descargar CSV",
        csv_bytes,
        file_name="escenario_transito.csv"
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df_export.to_excel(
            writer,
            index=False
        )

    st.download_button(
        "Descargar Excel",
        output.getvalue(),
        file_name="escenario_transito.xlsx"
    )