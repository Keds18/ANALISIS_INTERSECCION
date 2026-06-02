# 🚦 PROY_SEMAFOROS

Proyecto de análisis de tráfico para una intersección semaforizada con un carril por acceso.

---

## 📌 Descripción

Este proyecto ofrece un panel interactivo desarrollado en **Streamlit** para calcular, analizar y visualizar el comportamiento operacional de una intersección semaforizada usando:

- 🚥 **Método de Webster (1958)** para diseño del ciclo semafórico óptimo.
- 🚗 **Modelo de colas M/M/1** para estimación de retrasos y longitud de filas.
- 📊 **Nivel de Servicio (LOS)** según metodología **HCM**.

La aplicación permite ingresar flujos vehiculares por acceso, parámetros de semaforización y evaluar indicadores clave de desempeño operacional.

---

## 🗂️ Estructura del proyecto

```bash
PROY_SEMAFOROS/
│
├── main.py               # Interfaz principal en Streamlit
├── webster.py            # Cálculo del ciclo semafórico óptimo
├── colas.py              # Modelo de colas M/M/1
├── nivelservicio.py      # Cálculo de Nivel de Servicio (LOS)
├── requirements.txt      # Dependencias del proyecto
│
└── datos/
    └── flujos.txt        # Escenarios predefinidos
```

### Archivos principales

- 🖥️ `main.py` → Interfaz Streamlit y visualización de resultados.
- 🚦 `webster.py` → Diseño de tiempos semafóricos mediante Webster.
- 🚗 `colas.py` → Análisis de colas vehiculares y métricas de desempeño.
- 📈 `nivelservicio.py` → Evaluación del Nivel de Servicio según HCM.
- 📦 `requirements.txt` → Librerías necesarias para ejecutar el proyecto.
- 📄 `datos/flujos.txt` → Casos de entrada de ejemplo.

---

## ⚙️ Requisitos

Antes de ejecutar el proyecto necesitas:

- 🐍 Python **3.11 o superior**
- 📦 `pip`

Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

---

## ▶️ Ejecución

Desde la carpeta raíz del proyecto ejecutar:

```bash
streamlit run main.py
```

Luego abrir en el navegador la URL que Streamlit mostrará en el terminal, normalmente:

```bash
http://localhost:8501
```

---

## 📂 Uso de escenarios predefinidos

Si existe un archivo llamado `flujos.txt` en el mismo directorio que `main.py`, la aplicación cargará automáticamente los escenarios definidos.

El proyecto incluye un ejemplo en:

```bash
datos/flujos.txt
```

Para utilizarlo:

- copiar el archivo a la raíz del proyecto, o
- moverlo junto a `main.py`

como:

```bash
PROY_SEMAFOROS/flujos.txt
```

---

## 📐 Notas técnicas

- ⚙️ El flujo de saturación por carril `s` puede ajustarse manualmente desde la aplicación.
- ⏱️ La pérdida de tiempo `L` también es configurable.
- 📊 El método de Webster es válido siempre que:

```math
Y < 1
```

donde `Y` representa la relación flujo/capacidad total crítica de la intersección.

---

## 🛠️ Tecnologías utilizadas

- 🐍 Python
- 🎈 Streamlit
- 🔢 NumPy
- 📊 Pandas
- 📉 Matplotlib

---

## 👨‍💻 Autor

Proyecto desarrollado por **Kevin Galindo Antezana**  
Ingeniería de Transporte · Tránsito · Semaforización · Movilidad Urbana
