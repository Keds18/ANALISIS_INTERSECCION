# ============================================
# CALCULO DE CICLO SEMAFORICO
# METODO DE WEBSTER (1958)
# Versión mejorada con validaciones robustas
# ============================================

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResultadoWebster:
    """Contenedor tipado para resultados del método de Webster."""
    Y: float
    C: float
    verde: dict[str, float]
    error: Optional[str] = None
    advertencias: list[str] = field(default_factory=list)

    @property
    def es_valido(self) -> bool:
        return self.error is None

    def como_dict(self) -> dict:
        return {
            "Y": self.Y,
            "C": self.C,
            "verde": self.verde,
            "error": self.error,
            "advertencias": self.advertencias,
        }


def calcular_ciclo_webster(
    q_norte: float,
    q_sur: float,
    q_este: float,
    q_oeste: float,
    s: float = 1800,
    L: float = 12,
    n_fases: int = 4,
) -> ResultadoWebster:
    """
    Calcula el ciclo semafórico óptimo y los verdes efectivos
    mediante el método de Webster (1958).

    Parámetros
    ----------
    q_norte, q_sur, q_este, q_oeste : float
        Flujos vehiculares por acceso (veh/h).
    s : float
        Flujo de saturación por carril (veh/h). Default: 1800.
    L : float
        Tiempo total perdido por ciclo (s). Default: 12.
    n_fases : int
        Número de fases semafóricas. Default: 4.

    Retorna
    -------
    ResultadoWebster
        Objeto con Y, C, verdes por acceso, errores y advertencias.

    Referencias
    -----------
    Webster, F. V. (1958). Traffic signal settings. Road Research
        Technical Paper No. 39. HMSO, London.
    HCM (2010). Highway Capacity Manual. Transportation Research Board.
    """
    advertencias = []

    # --- Validaciones de entrada ---
    flujos = {
        "norte": q_norte,
        "sur": q_sur,
        "este": q_este,
        "oeste": q_oeste,
    }

    for acceso, q in flujos.items():
        if q < 0:
            return ResultadoWebster(
                Y=0, C=0, verde={},
                error=f"El flujo en el acceso {acceso} no puede ser negativo ({q} veh/h)."
            )

    if s <= 0:
        return ResultadoWebster(
            Y=0, C=0, verde={},
            error=f"El flujo de saturación s debe ser mayor a cero. Valor recibido: {s}."
        )

    if L < 0:
        return ResultadoWebster(
            Y=0, C=0, verde={},
            error=f"El tiempo perdido L no puede ser negativo. Valor recibido: {L}."
        )

    # --- Relaciones de flujo por fase ---
    y = {acc: q / s for acc, q in flujos.items()}
    Y = sum(y.values())

    # Advertencias por capacidad
    if Y >= 0.90:
        advertencias.append(
            f"Y = {Y:.3f} ≥ 0.90: intersección operando cerca de capacidad. "
            "El ciclo resultante puede ser muy largo o inestable."
        )

    if Y >= 1.0:
        return ResultadoWebster(
            Y=round(Y, 3), C=0, verde={},
            error=(
                f"La demanda supera la capacidad (Y = {Y:.3f} ≥ 1.0). "
                "No es posible calcular un ciclo estable. "
                "Considere incrementar el flujo de saturación o reducir la demanda."
            )
        )

    # --- Ciclo óptimo de Webster ---
    C_optimo = (1.5 * L + 5) / (1 - Y)

    # Límites prácticos del ciclo (HCM recomendaciones)
    C_min, C_max = 30, 180
    C = max(C_min, min(C_max, C_optimo))

    if C_optimo < C_min:
        advertencias.append(
            f"El ciclo calculado ({C_optimo:.1f} s) es menor al mínimo práctico "
            f"({C_min} s). Se ajustó a {C_min} s."
        )
    elif C_optimo > C_max:
        advertencias.append(
            f"El ciclo calculado ({C_optimo:.1f} s) supera el máximo práctico "
            f"({C_max} s). Se limitó a {C_max} s."
        )

    # --- Verdes efectivos proporcionales ---
    tiempo_efectivo = C - L
    if tiempo_efectivo <= 0:
        return ResultadoWebster(
            Y=round(Y, 3), C=round(C, 2), verde={},
            error=(
                f"El tiempo efectivo disponible (C - L = {tiempo_efectivo:.1f} s) "
                "es no positivo. Revise el tiempo perdido L."
            )
        )

    verde = {
        acc: round((yi / Y) * tiempo_efectivo, 2) if Y > 0 else 0.0
        for acc, yi in y.items()
    }

    # Verificar verde mínimo por acceso (≥ 5 s recomendado)
    for acc, g in verde.items():
        if g < 5:
            advertencias.append(
                f"Verde efectivo en acceso {acc} = {g:.1f} s < 5 s (mínimo recomendado)."
            )

    return ResultadoWebster(
        Y=round(Y, 3),
        C=round(C, 2),
        verde=verde,
        advertencias=advertencias,
    )


if __name__ == "__main__":
    # Ejemplo de uso con flujos representativos
    resultado = calcular_ciclo_webster(
        q_norte=450,
        q_sur=400,
        q_este=350,
        q_oeste=300,
        s=1800,
        L=12,
    )

    if not resultado.es_valido:
        print("❌ Error:", resultado.error)
    else:
        print("=" * 45)
        print("  RESULTADOS — MÉTODO DE WEBSTER (1958)  ")
        print("=" * 45)
        print(f"  Relación crítica total   Y = {resultado.Y:.3f}")
        print(f"  Ciclo semafórico óptimo  C = {resultado.C:.1f} s")
        print()
        print("  Verdes efectivos por acceso:")
        for acceso, g in resultado.verde.items():
            print(f"    {acceso.capitalize():6s} : {g:6.1f} s")
        if resultado.advertencias:
            print()
            print("  ⚠ Advertencias:")
            for adv in resultado.advertencias:
                print(f"    · {adv}")
        print("=" * 45)
        