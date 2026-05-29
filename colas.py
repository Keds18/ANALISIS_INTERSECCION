# ============================================

def calcular_cola(lambda_llegadas, mu_servicio):

    # Verificacion de estabilidad
    if lambda_llegadas >= mu_servicio:

        return {
            "error": "El sistema es inestable"
        }

    # Factor de utilizacion
    rho = lambda_llegadas / mu_servicio

    # Numero promedio de vehiculos en cola
    Lq = (rho ** 2) / (1 - rho)

    # Tiempo promedio en cola
    if lambda_llegadas == 0:
        Wq = 0.0
    else:
        Wq = Lq / lambda_llegadas

    return {
        "rho": round(rho, 3),
        "Lq": round(Lq, 3),
        "Wq": round(Wq, 3)
    }