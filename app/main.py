# ==========================================
# TRANSITO v3 — Dashboard de Análisis
# Operacional de Intersecciones con 1 acceso
# Huancayo, Perú
#
# Mejoras v3:
# · Módulos tipados con dataclasses
# · Validaciones robustas con advertencias
# · Parámetro s=1800 veh/h (HCM estándar)
# · Gráficos Plotly interactivos
# · Exportación a CSV y Excel multisheet
# · Soporte para flujos.txt (CSV externo)
# · Indicadores LOS con color dinámico
# ==========================================

import csv
import io
import importlib.util
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.colas import calcular_cola
from webster import calcular_ciclo_webster

# Cargar el módulo local nivelservicio.py desde la misma carpeta que este script.
# Esto evita conflictos si existe otro paquete `nivelservicio` en el entorno.
_nivelservicio_path = Path(__file__).with_name("nivelservicio.py")
_spec = importlib.util.spec_from_file_location("nivelservicio_local", _nivelservicio_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"No se pudo cargar el módulo local nivelservicio desde {_nivelservicio_path}")
nivelservicio = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nivelservicio)


# ------------------------------------------
# CONFIG DE PÁGINA
# ------------------------------------------

st.set_page_config(
    page_title="Analisis de Tránsito de una interseccion semaforizada de 1 carril por acceso",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS mínimo para KPI cards
st.markdown(
    """
    <style>
    .kpi-card {
        background: #1e2130;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #4f8ef7;
    }
    .kpi-label { color: #aab0c2; font-size: 0.78rem; text-transform: uppercase; letter-spacing: .06em; }
    .kpi-value { color: #e8ecf4; font-size: 1.6rem; font-weight: 700; }
    .kpi-unit  { color: #7b82a0; font-size: 0.78rem; margin-left: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------

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
            return resultado.get("demora_minutos", resultado.get("Wq", 0) * 60)
        if nombre == "longitud_cola_metros":
            return resultado.get("longitud_cola_metros", resultado.get("Lq", 0) * 6.5)
        return resultado.get(nombre, valor_predeterminado)
    return getattr(resultado, nombre, valor_predeterminado)


# ------------------------------------------
# SESSION STATE
# ------------------------------------------

defaults = {
    "resultado_webster": None,
    "resultado_cola": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ------------------------------------------
# ENCABEZADO
# ------------------------------------------

st.title("🚦 Sistema Integrado de Análisis de Tránsito")
st.caption(
    "Método de Webster (1958) · Teoría de Colas M/M/1 · Nivel de Servicio (HCM 2010)"
)
st.divider()


# ------------------------------------------
# CARGA DE ESCENARIOS
# ------------------------------------------

texto_flujos = cargar_flujos_texto()
escenarios = cargar_escenarios_flujos(texto_flujos)
escenario = {}

if escenarios:
    nombres = [e["name"] for e in escenarios]
    seleccion = st.selectbox("📂 Seleccionar escenario predefinido:", nombres)
    escenario = next(e for e in escenarios if e["name"] == seleccion)
    st.divider()


# ------------------------------------------
# SIDEBAR — PARÁMETROS DE ENTRADA
# ------------------------------------------

with st.sidebar:
    st.header("⚙️ Parámetros de entrada")
    st.caption("Intersección semaforizada con 1 carril por acceso · Análisis de desempeño")

    # ── Flujos vehiculares ──────────────────
    st.subheader("Flujos por acceso (veh/h)")
    q_norte = st.number_input("Norte ↑", value=float(escenario.get("q_norte", 450)), min_value=0.0, step=10.0)
    q_sur   = st.number_input("Sur ↓",   value=float(escenario.get("q_sur",   400)), min_value=0.0, step=10.0)
    q_este  = st.number_input("Este →",  value=float(escenario.get("q_este",  350)), min_value=0.0, step=10.0)
    q_oeste = st.number_input("Oeste ←", value=float(escenario.get("q_oeste", 300)), min_value=0.0, step=10.0)

    # ── Semaforización ──────────────────────
    st.subheader("Semaforización")
    s = st.number_input(
        "Flujo de saturación S (veh/h)",
        value=float(escenario.get("s", 1800)),
        min_value=500.0, max_value=2400.0, step=50.0,
        help="Valor típico HCM: 1800 veh/h por carril."
    )
    L = st.number_input(
        "Tiempo perdido por ciclo L (s)",
        value=float(escenario.get("L", 8)),
        min_value=0.0, max_value=60.0, step=1.0,
        help="Estimado como 4s(3s(ambar)+1s(rojo)) × n° de fases (2 fases → 8s)."
    )

    # ── Teoría de colas ─────────────────────
    st.subheader("Teoría de Colas M/M/1")
    lambda_llegadas = st.number_input(
        "λ — Tasa de llegadas (veh/h)  = flujos",
        value=float(escenario.get("lambda", 300)),
        min_value=0.0, step=10.0,
    )
    mu_servicio = st.number_input(
        "μ — Tasa de servicio (veh/h) = Q(v.S/C)",
        value=float(escenario.get("mu", 800)),
        min_value=1.0, step=10.0,
    )

    st.divider()

    # ── Botones de cálculo ──────────────────
    calc_web = st.button("🚦 Calcular Webster",   use_container_width=True)
    calc_cola = st.button("🚗 Calcular Cola M/M/1", use_container_width=True)
    calc_todo = st.button("⚡ Calcular todo",       use_container_width=True, type="primary")

if calc_web or calc_todo:
    st.session_state.resultado_webster = calcular_ciclo_webster(
        q_norte, q_sur, q_este, q_oeste, s=s, L=L
    )

if calc_cola or calc_todo:
    st.session_state.resultado_cola = calcular_cola(lambda_llegadas, mu_servicio)


# ------------------------------------------
# TABS PRINCIPALES
# ------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "🚦 Webster",
    "🚗 Colas M/M/1",
    "📊 Dashboard",
    "📁 Exportar",
])


# ==========================================
# TAB 1 — WEBSTER
# ==========================================

with tab1:
    st.subheader("Método de Webster (1958)")
    st.markdown(
        "Calcula el ciclo semafórico óptimo distribuyendo el verde efectivo "
        "proporcional a la relación de flujo por fase."
    )

    res_w = st.session_state.resultado_webster

    if res_w is None:
        st.info("Presione **🚦 Calcular Webster** o **⚡ Calcular todo** en la barra lateral.")
    elif not obtener_atributo(res_w, "es_valido", False):
        st.error(f"❌ {obtener_atributo(res_w, 'error', 'Error desconocido en cálculo de Webster.')}")
    else:
        # Advertencias
        for adv in obtener_atributo(res_w, "advertencias", []):
            st.warning(adv)

        # KPIs principales
        col1, col2, col3 = st.columns(3)
        with col1:
            kpi_card("Relación crítica Y", f"{obtener_atributo(res_w, 'Y', 0):.3f}", color="#f7a44f")
        with col2:
            estado_y = "✅ Estable" if obtener_atributo(res_w, 'Y', 0) < 0.90 else "⚠ Carga alta"
            kpi_card("Estado de la intersección", estado_y, color="#4fcef7")
        with col3:
            kpi_card("Ciclo óptimo C", f"{obtener_atributo(res_w, 'C', 0):.1f}", "s", color="#4ff79e")

        st.divider()

        # Tabla de verdes
        st.markdown("#### Verdes efectivos por acceso")
        ciclo_optimo = obtener_atributo(res_w, 'C', 0)
        df_v = pd.DataFrame(
            [{
                "Acceso": acc.capitalize(),
                "Verde efectivo (s)": g,
                "% del ciclo efectivo": round(g / (ciclo_optimo - L) * 100, 1) if (ciclo_optimo - L) > 0 else 0,
                "Capacidad teórica Q (veh/h)": round(g * s / ciclo_optimo, 1) if ciclo_optimo > 0 else 0,
            }
             for acc, g in obtener_atributo(res_w, 'verde', {}).items()]
        )
        st.dataframe(df_v, use_container_width=True, hide_index=True)

        # Gráfico de barras — verdes
        fig_v = px.bar(
            df_v, x="Acceso", y="Verde efectivo (s)",
            color="Verde efectivo (s)",
            color_continuous_scale="Teal",
            title="Distribución de verdes efectivos",
            labels={"Verde efectivo (s)": "Verde (s)"},
            text_auto=".1f",
        )
        fig_v.update_layout(coloraxis_showscale=False, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_v, use_container_width=True)

        # Diagrama de torta del ciclo
        labels_ciclo = list(obtener_atributo(res_w, 'verde', {}).keys()) + ["Tiempo perdido L"]
        values_ciclo = list(obtener_atributo(res_w, 'verde', {}).values()) + [L]
        fig_pie = go.Figure(data=[go.Pie(
            labels=[l.capitalize() for l in labels_ciclo],
            values=values_ciclo,
            hole=0.8,
            textinfo="label+percent",
        )])
        fig_pie.update_layout(title="Composición del ciclo semafórico")
        st.plotly_chart(fig_pie, use_container_width=True)


# ==========================================
# TAB 2 — COLAS M/M/1
# ==========================================

with tab2:
    st.subheader("Modelo de Cola M/M/1")
    st.markdown(
        "Llegadas Poisson · Servicio exponencial · Un servidor · "
        "Capacidad infinita (modelo de Kendall: M/M/1/∞)."
    )

    res_c = st.session_state.resultado_cola

    if res_c is None:
        st.info("Presione **🚗 Calcular Cola M/M/1** o **⚡ Calcular todo** en la barra lateral.")
    elif not obtener_atributo(res_c, "es_valido", False):
        st.error(f"❌ {obtener_atributo(res_c, 'error', 'Error desconocido en cálculo de cola.')}")
    else:
        for adv in obtener_atributo(res_c, "advertencias", []):
            st.warning(adv)

        demora_min     = obtener_atributo(res_c, "demora_minutos", 0)
        longitud_m     = obtener_atributo(res_c, "longitud_cola_metros", 0)
        los_resultado  = nivelservicio.nivel_servicio_desde_minutos(demora_min)

        # KPIs
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: kpi_card("Utilización ρ", f"{obtener_atributo(res_c, 'rho', 0):.3f}", color="#f7a44f")
        with c2: kpi_card("Veh. en cola Lq", f"{obtener_atributo(res_c, 'Lq', 0):.2f}", "veh", color="#4fcef7")
        with c3: kpi_card("Demora Wq", f"{demora_min:.2f}", "min", color="#a44ff7")
        with c4: kpi_card("Cola estimada", f"{longitud_m:.1f}", "m", color="#f74f4f")
        with c5: kpi_card("LOS", los_resultado.los, los_resultado.descripcion[:18], color=los_resultado.color_hex)

        st.divider()

        # Sensibilidad: variación del ρ
        st.markdown("#### Análisis de sensibilidad — ρ vs. métricas")
        rhos    = [i / 100 for i in range(10, 96, 5)]
        lqs     = [(r**2) / (1 - r) for r in rhos]
        wqs_min = [(lq / (rhos[i] * mu_servicio)) * 60 for i, lq in enumerate(lqs)]

        df_sens = pd.DataFrame({"ρ": rhos, "Lq (veh)": lqs, "Wq (min)": wqs_min})

        fig_sens = px.line(
            df_sens, x="ρ", y=["Lq (veh)", "Wq (min)"],
            title="Comportamiento de la cola ante variaciones de utilización",
            markers=True,
        )
        fig_sens.add_vline(
            x=obtener_atributo(res_c, 'rho', 0), line_dash="dash", line_color="red",
            annotation_text=f"ρ actual = {obtener_atributo(res_c, 'rho', 0):.3f}",
        )
        fig_sens.update_layout(plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_sens, use_container_width=True)


# ==========================================
# TAB 3 — DASHBOARD
# ==========================================

with tab3:
    st.subheader("Dashboard de Flujos Vehiculares")
    st.caption("Interseccion semafoizada - Distribución por acceso")

    # ── Flujos por acceso ───────────────────
    df_flujos = pd.DataFrame({
        "Acceso": ["Norte", "Sur", "Este", "Oeste"],
        "Flujo (veh/h)": [q_norte, q_sur, q_este, q_oeste],
        "v/c": [round(q / s, 3) for q in [q_norte, q_sur, q_este, q_oeste]],
    })

    col_a, col_b = st.columns(2)

    with col_a:
        fig_bar = px.bar(
            df_flujos, x="Acceso", y="Flujo (veh/h)",
            color="Acceso",
            color_discrete_sequence=px.colors.qualitative.Safe,
            title="Flujo vehicular por acceso",
            text_auto=True,
        )
        fig_bar.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_b:
        fig_pie2 = px.pie(
            df_flujos, names="Acceso", values="Flujo (veh/h)",
            title="Distribución porcentual de flujos",
            color_discrete_sequence=px.colors.qualitative.Safe,
            hole=0.35,
        )
        st.plotly_chart(fig_pie2, use_container_width=True)

    # ── Relación v/c ────────────────────────
    st.markdown("#### Relación volumen/capacidad (v/c) por acceso")

    # Colores semafóricos según v/c
    def color_vc(vc):
        if vc < 0.60: return "#1a9850"
        if vc < 0.85: return "#fee08b"
        return "#d73027"

    df_flujos["Color"] = df_flujos["v/c"].apply(color_vc)
    fig_vc = px.bar(
        df_flujos, x="Acceso", y="v/c",
        color="v/c",
        color_continuous_scale=["#1a9850", "#fee08b", "#d73027"],
        range_color=[0, 1],
        title="Relación v/c por acceso (0 = libre · 1 = capacidad)",
        text_auto=".3f",
    )
    fig_vc.add_hline(y=0.90, line_dash="dash", line_color="orange",
                     annotation_text="Umbral crítico (v/c = 0.90)")
    fig_vc.add_hline(y=1.00, line_dash="dash", line_color="red",
                     annotation_text="Capacidad máxima (v/c = 1.00)")
    fig_vc.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_vc, use_container_width=True)

    st.dataframe(df_flujos[["Acceso", "Flujo (veh/h)", "v/c"]],
                 use_container_width=True, hide_index=True)


# ==========================================
# TAB 4 — EXPORTAR
# ==========================================

with tab4:
    st.subheader("Exportación de resultados")

    # ── Parámetros de entrada ───────────────
    df_params = pd.DataFrame([
        {"Parámetro": "q Norte (veh/h)",           "Valor": q_norte},
        {"Parámetro": "q Sur (veh/h)",             "Valor": q_sur},
        {"Parámetro": "q Este (veh/h)",            "Valor": q_este},
        {"Parámetro": "q Oeste (veh/h)",           "Valor": q_oeste},
        {"Parámetro": "s — Saturación (veh/h)",    "Valor": s},
        {"Parámetro": "L — T. perdido (s)",        "Valor": L},
        {"Parámetro": "λ — Llegadas (veh/h)",      "Valor": lambda_llegadas},
        {"Parámetro": "μ — Servicio (veh/h)",      "Valor": mu_servicio},
    ])

    # ── Resultados Webster ──────────────────
    res_w = st.session_state.resultado_webster
    if res_w and obtener_atributo(res_w, "es_valido", False):
        filas_w = [
            {"Indicador": "Relación crítica Y",    "Valor": obtener_atributo(res_w, 'Y', 0)},
            {"Indicador": "Ciclo óptimo C (s)",    "Valor": obtener_atributo(res_w, 'C', 0)},
        ]
        for acc, g in obtener_atributo(res_w, 'verde', {}).items():
            filas_w.append({"Indicador": f"Verde {acc.capitalize()} (s)", "Valor": g})
        df_webster = pd.DataFrame(filas_w)
    else:
        df_webster = pd.DataFrame(columns=["Indicador", "Valor"])

    # ── Resultados Cola ─────────────────────
    res_c = st.session_state.resultado_cola
    if res_c and obtener_atributo(res_c, "es_valido", False):
        los_r = nivelservicio.nivel_servicio_desde_minutos(obtener_atributo(res_c, 'demora_minutos', 0))
        df_cola = pd.DataFrame([
            {"Indicador": "Utilización ρ",          "Valor": obtener_atributo(res_c, 'rho', 0)},
            {"Indicador": "Veh. en cola Lq",        "Valor": obtener_atributo(res_c, 'Lq', 0)},
            {"Indicador": "Demora Wq (min)",         "Valor": round(obtener_atributo(res_c, 'demora_minutos', 0), 3)},
            {"Indicador": "Cola estimada (m)",       "Valor": round(obtener_atributo(res_c, 'longitud_cola_metros', 0), 1)},
            {"Indicador": "Nivel de Servicio (LOS)", "Valor": los_r.los},
        ])
    else:
        df_cola = pd.DataFrame(columns=["Indicador", "Valor"])

    # ── Vista previa ────────────────────────
    st.markdown("**Vista previa — Parámetros de entrada**")
    st.dataframe(df_params, use_container_width=True, hide_index=True)

    col_exp1, col_exp2 = st.columns(2)

    # Exportar CSV
    with col_exp1:
        csv_bytes = df_params.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar CSV (parámetros)",
            csv_bytes,
            file_name="transito_parametros.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Exportar Excel multi-hoja
    with col_exp2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_params.to_excel(writer,   sheet_name="Parámetros", index=False)
            df_webster.to_excel(writer,  sheet_name="Webster",    index=False)
            df_cola.to_excel(writer,     sheet_name="Colas",      index=False)

        st.download_button(
            "⬇️ Descargar Excel (multisheet)",
            output.getvalue(),
            file_name="transito_resultados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.info(
        "El archivo Excel contiene tres hojas: **Parámetros**, **Webster** y **Colas**. "
        "Asegúrese de ejecutar ambos cálculos antes de exportar."
    )