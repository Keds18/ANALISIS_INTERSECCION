# Aplicativo principal para análisis de tránsito con Streamlit
import csv
from io import BytesIO
from pathlib import Path
import io

import pandas as pd
import streamlit as st

from colas import calcular_cola
from nivelservicio import nivel_servicio
from semaforo import calcular_ciclo_webster


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
    if valor.lower() in {"none", "na", "nan"}:
        return None
    try:
        if "." in valor:
            return float(valor)
        return int(valor)
    except ValueError:
        try:
            return float(valor)
        except ValueError:
            return valor


def cargar_escenarios_flujos(texto):
    texto = texto.strip()
    if not texto:
        return []

    lineas = [linea for linea in texto.splitlines() if linea.strip() and not linea.strip().startswith("#")]
    if not lineas:
        return []

    if "," in lineas[0]:
        lector = csv.DictReader(io.StringIO("\n".join(lineas)))
        escenarios = []
        for fila in lector:
            if not any(fila.values()):
                continue
            escenario = {}
            for clave, valor in fila.items():
                if clave is None:
                    continue
                nombre = clave.strip()
                escenario[nombre] = parse_literal(valor)
            escenario["name"] = escenario.get("scenario") or escenario.get("name") or f"escenario_{len(escenarios)+1}"
            escenarios.append(escenario)
        return escenarios

    # Formato clave=valor simple
    escenario = {}
    for linea in lineas:
        if "=" in linea:
            clave, valor = linea.split("=", 1)
            escenario[clave.strip()] = parse_literal(valor)
    if escenario:
        escenario["name"] = escenario.get("scenario") or escenario.get("name") or "default"
        return [escenario]
    return []


def main():
    st.set_page_config(page_title="App de Tránsito", page_icon="🚦", layout="wide")
    st.title("Análisis de Tránsito Integrado")
    st.write(
        "Esta aplicación combina cálculo de ciclo semafórico, teoría de colas M/M/1 y nivel de servicio."
    )

    with st.expander("Información teórica"):
        st.markdown(
            """
            **Modelo M/M/1 (Teoría de colas)**

            - Llegadas: proceso de Poisson (tasa λ).
            - Servicio: tiempo de servicio exponencial (tasa μ).
            - Sistema de un único servidor.
            - Métricas útiles: utilización ρ = λ/μ, Lq (vehículos en cola), Wq (tiempo en cola).

            **Método de Webster (cálculo de ciclo semafórico)**

            - Calcula el ciclo óptimo C en segundos con base en la relación crítica Y y el tiempo perdido L:
              $$C = \\frac{1.5L + 5}{1 - Y}$$
            - Y es la suma de las fracciones de flujo por carril; si $Y \\ge 1$ el sistema no es estable.

            Estas fórmulas son aproximaciones usadas en diseño preliminar de control semafórico y análisis de servicio.
            """
        )

    texto_flujos = cargar_flujos_texto()
    escenarios = cargar_escenarios_flujos(texto_flujos)

    with st.expander("Ver contenido de flujos.txt"):
        if texto_flujos:
            st.code(texto_flujos, language="text")
        else:
            st.write("No se encontró `flujos.txt`. Puedes crearlo en la carpeta del proyecto con formato CSV o clave=valor.")

    if escenarios:
        nombres = [escenario["name"] for escenario in escenarios]
        seleccion = st.selectbox("Escenario cargado desde flujos.txt", nombres)
        escenario = next(esc for esc in escenarios if esc["name"] == seleccion)
        if escenario.get("notes"):
            st.caption(f"Notas: {escenario['notes']}")
    else:
        escenario = {}

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.header("Semáforo - Método de Webster")
        q_norte = st.number_input(
            "Flujo Norte (veh/h)",
            min_value=0.0,
            value=float(escenario.get("q_norte", 450.0)),
            step=10.0,
        )
        q_sur = st.number_input(
            "Flujo Sur (veh/h)",
            min_value=0.0,
            value=float(escenario.get("q_sur", 400.0)),
            step=10.0,
        )
        q_este = st.number_input(
            "Flujo Este (veh/h)",
            min_value=0.0,
            value=float(escenario.get("q_este", 350.0)),
            step=10.0,
        )
        q_oeste = st.number_input(
            "Flujo Oeste (veh/h)",
            min_value=0.0,
            value=float(escenario.get("q_oeste", 300.0)),
            step=10.0,
        )
        s = st.number_input(
            "Saturación por carril (veh/h)",
            min_value=100.0,
            value=float(escenario.get("s", 1300.0)),
            step=50.0,
        )
        L = st.number_input(
            "Tiempo perdido total L (segundos)",
            min_value=0.0,
            value=float(escenario.get("L", 12.0)),
            step=1.0,
        )

        if st.button("Calcular ciclo semafórico", key="btn_semaforo"):
            resultado = calcular_ciclo_webster(q_norte, q_sur, q_este, q_oeste, s=s, L=L)
            if "error" in resultado:
                st.error(resultado["error"])
            else:
                st.metric("Relación crítica total Y", resultado["Y"])
                st.metric("Ciclo semafórico C (s)", resultado["C"])
                st.write("### Tiempos de verde efectivos")
                st.write(
                    {
                        "Norte": f"{resultado['verde']['norte']} s",
                        "Sur": f"{resultado['verde']['sur']} s",
                        "Este": f"{resultado['verde']['este']} s",
                        "Oeste": f"{resultado['verde']['oeste']} s",
                    }
                )

    with col2:
        st.header("Teoría de Colas M/M/1")
        lambda_llegadas = st.number_input(
            "Llegadas λ (veh/h)",
            min_value=0.0,
            value=float(escenario.get("lambda", 300.0)),
            step=10.0,
        )
        mu_servicio = st.number_input(
            "Servicio μ (veh/h)",
            min_value=1.0,
            value=float(escenario.get("mu", 500.0)),
            step=10.0,
        )

        if st.button("Calcular cola", key="btn_colas"):
            resultado = calcular_cola(lambda_llegadas, mu_servicio)
            if "error" in resultado:
                st.error(resultado["error"])
            else:
                st.write("### Resultados de la cola")
                st.write(f"Utilización (ρ): {resultado['rho']}")
                st.write(f"Vehículos promedio en cola (Lq): {resultado['Lq']}")
                st.write(f"Tiempo promedio en cola (Wq): {resultado['Wq']:.4f} horas")
                demora_min = round(resultado['Wq'] * 60, 2)
                st.write(f"Tiempo en cola en minutos: {demora_min} min")
                st.write(f"Nivel de servicio: {nivel_servicio(demora_min)}")

    st.markdown("---")
    st.header("Exportar escenario actual")

    df_export = pd.DataFrame(
        [
            {"Campo": "q_norte", "Valor": q_norte},
            {"Campo": "q_sur", "Valor": q_sur},
            {"Campo": "q_este", "Valor": q_este},
            {"Campo": "q_oeste", "Valor": q_oeste},
            {"Campo": "s", "Valor": s},
            {"Campo": "L", "Valor": L},
            {"Campo": "lambda", "Valor": lambda_llegadas},
            {"Campo": "mu", "Valor": mu_servicio},
        ]
    )

    csv_bytes = df_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar CSV para Excel",
        data=csv_bytes,
        file_name="escenario_transito.csv",
        mime="text/csv",
    )

    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False, sheet_name="escenario")

        output.seek(0)
        st.download_button(
            "Descargar Excel",
            data=output.getvalue(),
            file_name="escenario_transito.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except ImportError:
        st.warning("Para descargar Excel, instala la dependencia openpyxl: pip install openpyxl")
    except Exception as e:
        st.error(f"Error al generar el archivo Excel: {e}")
    st.markdown("---")
    st.header("Nivel de servicio por demora")
    demora = st.number_input("Demora en minutos", min_value=0.0, value=15.0, step=1.0)
    st.write(f"Categoría de nivel de servicio: {nivel_servicio(demora)}")

    st.markdown(
        "---\n" "**Instrucciones:** Ejecuta `streamlit run main.py` en la carpeta del proyecto para abrir la app." 
    )


if __name__ == "__main__":
    main()
