# ============================================
# NIVEL DE SERVICIO (LOS) — HCM 2010/2016
# Para intersecciones semaforizadas
# ============================================

from dataclasses import dataclass
from typing import Optional


@dataclass
class ResultadoLOS:
    """Nivel de servicio con descripción operacional y color asociado."""
    los: str
    demora_min: float
    descripcion: str
    color_hex: str   # Útil para visualizaciones

    def __str__(self) -> str:
        return f"LOS {self.los} — {self.descripcion} (demora: {self.demora_min:.1f} min)"


# Tabla LOS para intersecciones semaforizadas según HCM 2010 (Tabla 18-4)
# Umbrales de demora de control por vehículo en segundos, convertidos a horas.
_TABLA_LOS = [
    ("A", 10/3600,  "Demora muy baja. Operación libre.",                    "#1a9850"),
    ("B", 20/3600,  "Demora baja. Conductores no perciben restricciones.",  "#91cf60"),
    ("C", 35/3600,  "Demora moderada. Colas cortas.",                       "#d9ef8b"),
    ("D", 55/3600,  "Demora notable. Colas significativas.",                "#fee08b"),
    ("E", 80/3600,  "Demora alta. Operación cercana a capacidad.",          "#fc8d59"),
]
_LOS_F_COLOR = "#d73027"


def nivel_servicio(demora_horas: float) -> ResultadoLOS:
    """
    Determina el Nivel de Servicio (LOS) de una intersección semaforizada
    según el HCM 2010/2016.

    Parámetros
    ----------
    demora_horas : float
        Demora de control por vehículo en HORAS (s/3600 o min/60).
        NOTA: la función acepta horas para coherencia con el modelo M/M/1.

    Retorna
    -------
    ResultadoLOS
        Objeto con los, descripción y color para visualización.

    Referencias
    -----------
    Transportation Research Board. (2010). Highway Capacity Manual (HCM 2010).
        National Academies of Sciences. Capítulo 18.
    Transportation Research Board. (2016). Highway Capacity Manual (HCM 6th ed.).
        National Academies of Sciences.
    """
    if demora_horas < 0:
        demora_horas = 0.0

    for los, umbral_h, descripcion, color in _TABLA_LOS:
        if demora_horas <= umbral_h:
            return ResultadoLOS(
                los=los,
                demora_min=demora_horas * 60,
                descripcion=descripcion,
                color_hex=color,
            )

    return ResultadoLOS(
        los="F",
        demora_min=demora_horas * 60,
        descripcion="Demora inaceptable. Colapso operacional. Colas crecientes.",
        color_hex=_LOS_F_COLOR,
    )


def nivel_servicio_desde_minutos(demora_min: float) -> ResultadoLOS:
    """
    Wrapper conveniente: recibe demora en minutos (como genera calcular_cola).
    """
    return nivel_servicio(demora_min / 60)


if __name__ == "__main__":
    ejemplos = [0.05, 0.15, 0.30, 0.50, 0.70, 1.20]   # horas
    print(f"{'Demora (min)':>14} | {'LOS':>4} | Descripción")
    print("-" * 70)
    for d in ejemplos:
        r = nivel_servicio(d)
        print(f"{d*60:>14.2f} | {r.los:>4} | {r.descripcion}")