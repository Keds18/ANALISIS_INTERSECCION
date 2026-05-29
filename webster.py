# ============================================
# CALCULO BASICO DE CICLO SEMAFORICO
# METODO SIMPLE TIPO WEBSTER
# ============================================


def calcular_ciclo_webster(q_norte, q_sur, q_este, q_oeste, s=1300, L=12):
    """Calcula ciclo semafórico y tiempos de verde con el método de Webster."""
    y_norte = q_norte / s
    y_sur = q_sur / s
    y_este = q_este / s
    y_oeste = q_oeste / s
    Y = y_norte + y_sur + y_este + y_oeste

    if Y >= 1:
        return {
            "error": "La demanda es demasiado alta para calcular un ciclo estable (Y >= 1)."
        }

    C = (1.5 * L + 5) / (1 - Y)

    if Y == 0:
        g_norte = g_sur = g_este = g_oeste = 0.0
    else:
        g_norte = (y_norte / Y) * (C - L)
        g_sur = (y_sur / Y) * (C - L)
        g_este = (y_este / Y) * (C - L)
        g_oeste = (y_oeste / Y) * (C - L)

    return {
        "Y": round(Y, 3),
        "C": round(C, 2),
        "verde": {
            "norte": round(g_norte, 2),
            "sur": round(g_sur, 2),
            "este": round(g_este, 2),
            "oeste": round(g_oeste, 2),
        },
    }


if __name__ == "__main__":
    q_norte = 250
    q_sur = 350
    q_este = 250
    q_oeste = 350

    resultado = calcular_ciclo_webster(q_norte, q_sur, q_este, q_oeste)
    if "error" in resultado:
        print("Error:", resultado["error"])
    else:
        print("================================")
        print("RESULTADOS DEL CICLO SEMAFORICO")
        print("================================")
        print(f"Relacion critica total Y = {resultado['Y']:.3f}")
        print(f"Ciclo semaforico optimo = {resultado['C']:.2f} segundos")
        print(f"Verde efectivo Norte = {resultado['verde']['norte']:.2f} segundos")
        print(f"Verde efectivo Sur = {resultado['verde']['sur']:.2f} segundos")
        print(f"Verde efectivo Este = {resultado['verde']['este']:.2f} segundos")
        print(f"Verde efectivo Oeste = {resultado['verde']['oeste']:.2f} segundos")
