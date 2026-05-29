# ============================================
# NIVEL DE SERVICIO SIMPLE
# ============================================

def nivel_servicio(demora):

    if demora <= 10:
        return "A"

    elif demora <= 20:
        return "B"

    elif demora <= 35:
        return "C"

    elif demora <= 55:
        return "D"

    elif demora <= 80:
        return "E"

    else:
        return "F"