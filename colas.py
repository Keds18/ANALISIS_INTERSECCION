# ============================================
# TEORIA DE COLAS M/M/1
# Modelo de cola para intersecciones
# Versión mejorada con validaciones y métricas
# ============================================

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class ResultadoCola:
    """Contenedor tipado para resultados del modelo M/M/1."""
    rho: float
    Lq: float
    Wq: float
    L: float          # Número promedio total en sistema
    W: float          # Tiempo promedio total en sistema
    error: Optional[str] = None
    advertencias: list = None

    def __post_init__(self):
        if self.advertencias is None:
            self.advertencias = []

    @property
    def es_valido(self) -> bool:
        return self.error is None

    @property
    def demora_minutos(self) -> float:
        """Demora en cola expresada en minutos."""
        return self.Wq * 60

    @property
    def longitud_cola_metros(self, longitud_vehiculo: float = 6.5) -> float:
        """Longitud estimada de cola en metros (vehículo promedio = 6.5 m)."""
        return self.Lq * longitud_vehiculo


def calcular_cola(
    lambda_llegadas: float,
    mu_servicio: float,
) -> ResultadoCola:
    """
    Calcula las métricas de desempeño de una cola M/M/1
    (llegadas Poisson, servicio exponencial, un servidor).

    Parámetros
    ----------
    lambda_llegadas : float
        Tasa media de llegadas (veh/h).
    mu_servicio : float
        Tasa media de servicio (veh/h).

    Retorna
    -------
    ResultadoCola
        Objeto con ρ, Lq, Wq, L, W, errores y advertencias.

    Referencias
    -----------
    May, A. D. (1990). Fundamentals of Traffic Flow. Prentice-Hall.
    Newell, G. F. (1982). Applications of Queueing Theory.
        Chapman and Hall, London.
    HCM (2010). Highway Capacity Manual. Transportation Research Board.
    """
    advertencias = []

    # --- Validaciones ---
    if lambda_llegadas < 0:
        return ResultadoCola(
            rho=0, Lq=0, Wq=0, L=0, W=0,
            error="La tasa de llegadas λ no puede ser negativa."
        )

    if mu_servicio <= 0:
        return ResultadoCola(
            rho=0, Lq=0, Wq=0, L=0, W=0,
            error="La tasa de servicio μ debe ser estrictamente positiva."
        )

    if lambda_llegadas == 0:
        return ResultadoCola(
            rho=0.0, Lq=0.0, Wq=0.0, L=0.0, W=1.0 / mu_servicio,
            advertencias=["λ = 0: no hay vehículos en llegada. Sistema vacío."]
        )

    rho = lambda_llegadas / mu_servicio

    if rho >= 1.0:
        return ResultadoCola(
            rho=round(rho, 3), Lq=0, Wq=0, L=0, W=0,
            error=(
                f"Sistema inestable: ρ = λ/μ = {rho:.3f} ≥ 1.0. "
                "La demanda supera la capacidad de servicio. "
                "Considere aumentar μ o reducir λ."
            )
        )

    if rho >= 0.85:
        advertencias.append(
            f"Utilización ρ = {rho:.3f} ≥ 0.85: sistema con alta carga. "
            "Las colas pueden ser muy sensibles a variaciones en la demanda."
        )

    # --- Métricas M/M/1 ---
    Lq = (rho ** 2) / (1 - rho)          # Número en cola
    L  = rho / (1 - rho)                  # Número en sistema
    Wq = Lq / lambda_llegadas             # Tiempo en cola (h)
    W  = L  / lambda_llegadas             # Tiempo en sistema (h)

    return ResultadoCola(
        rho=round(rho, 4),
        Lq=round(Lq, 4),
        Wq=round(Wq, 6),
        L=round(L, 4),
        W=round(W, 6),
        advertencias=advertencias,
    )


if __name__ == "__main__":
    r = calcular_cola(lambda_llegadas=300, mu_servicio=450)
    if r.es_valido:
        print(f"ρ  = {r.rho:.3f}")
        print(f"Lq = {r.Lq:.3f} veh")
        print(f"Wq = {r.demora_minutos:.2f} min")
        print(f"Cola≈ {r.longitud_cola_metros:.1f} m")
    else:
        print("Error:", r.error)