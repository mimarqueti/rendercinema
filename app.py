from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import os

app = Flask(__name__)
CORS(app)

@app.route('/calcular', methods=['POST'])
def calcular_trajetoria():
    dados = request.json
    
    # Extract input data
    v0 = float(dados.get('velocidade'))
    angulo_graus = float(dados.get('angulo'))
    g = float(dados.get('gravidade'))
    massa = float(dados.get('massa'))
    c_d = float(dados.get('coeficienteArrasto'))
    y0 = float(dados.get('alturaInicial', 0.0))

    print(f"Calculando com ARRASTO para: Velocidade={v0}m/s, Ângulo={angulo_graus}°, Cd={c_d}")

    # Physical environment configuration
    if g == 1.62:       # Lua
        rho_ar = 0.0
    elif g == 3.71:     # Marte
        rho_ar = 0.020
    elif g == 24.79:    # Júpiter
        rho_ar = 0.133
    else:               # Terra
        rho_ar = 1.204
    
    diametro_projetil = 0.10
    area_frontal = np.pi * (diametro_projetil / 2) ** 2

    # Initial velocity decomposition
    theta = np.radians(angulo_graus)
    vx = v0 * np.cos(theta)
    vy = v0 * np.sin(theta)

    # Simulation loop state
    x_atual = 0.0
    y_atual = y0
    t = 0.0
    dt = 0.01

    trajetoria_formatada = []

    while y_atual >= 0:
        trajetoria_formatada.append({
            'x': float(x_atual),
            'y': float(y_atual)
        })

        v = np.hypot(vx, vy)

        # Calculate drag force
        if v > 1e-5:
            forca_arrasto = 0.5 * c_d * rho_ar * area_frontal * (v ** 2)
            ax_arrasto = -(forca_arrasto / massa) * (vx / v)
            ay_arrasto = -(forca_arrasto / massa) * (vy / v)
        else:
            ax_arrasto = 0.0
            ay_arrasto = 0.0

        # Total accelerations
        ax_total = ax_arrasto
        ay_total = -g + ay_arrasto

        # Update velocities (Euler method)
        vx += ax_total * dt
        vy += ay_total * dt

        # Update positions
        x_atual += vx * dt
        y_atual += vy * dt
        t += dt

        # Safety break
        if t > 100.0:
            break

    # Calculate summary metrics
    v_final = np.hypot(vx, vy)
    energia_cinetica_final = 0.5 * massa * (v_final ** 2)
    altura_maxima = max([ponto['y'] for ponto in trajetoria_formatada]) if trajetoria_formatada else y0
    alcance_maximo = x_atual

    # Build response
    resposta_completa = {
        "trajetoria": trajetoria_formatada,
        "alcance": float(alcance_maximo),
        "alturaMaxima": float(altura_maxima),
        "tempoVoo": float(t),
        "velocidadeFinal": float(v_final),
        "energiaCineticaFinal": float(energia_cinetica_final)
    }

    return jsonify(resposta_completa)

if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=porta)
