from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import os

app = Flask(__name__)
CORS(app)  # Permite que seu JS converse com o Python sem bloqueios de segurança

@app.route('/calcular', methods=['POST'])
def calcular_trajetoria():
    dados = request.json
    
    # 1. Captura os dados enviados pelo seu JavaScript
    v0 = float(dados.get('velocidade'))
    angulo_graus = float(dados.get('angulo'))
    g = float(dados.get('gravidade'))
    massa = float(dados.get('massa'))
    c_d = float(dados.get('coeficienteArrasto'))  # 0.47 para esfera, 1.05 para cubo, etc.
    y0 = float(dados.get('alturaInicial', 0.0))

    print(f"Calculando com ARRASTO para: Velocidade={v0}m/s, Ângulo={angulo_graus}°, Cd={c_d}")

    # 2. Configurações físicas do Meio (Ar Atmosférico) e do Projétil
    if g == 1.62:       # Lua
        rho_ar = 0.0    # Vácuo
    elif g == 3.71:     # Marte
        rho_ar = 0.020  # Rarefeita
    elif g == 24.79:    # Júpiter
        rho_ar = 0.133  # Gasosa superior
    else:               # Terra (9.81) ou qualquer outro
        rho_ar = 1.204
    diametro_projetil = 0.10  # Diâmetro padrão do objeto (m)
    area_frontal = np.pi * (diametro_projetil / 2) ** 2

    # Conversão do ângulo para radianos e decomposição da velocidade inicial
    theta = np.radians(angulo_graus)
    vx = v0 * np.cos(theta)
    vy = v0 * np.sin(theta)

    # 3. Variáveis de estado para o Loop de Simulação
    x_atual = 0.0
    y_atual = y0
    t = 0.0
    dt = 0.01  # Passo de tempo minúsculo (10 milissegundos) para precisão numérica

    trajetoria_formatada = []

    # O loop roda calculando a posição passo a passo até a bolinha tocar o chão (y < 0)
    while y_atual >= 0:
        # Guarda a posição atual no formato que o JavaScript espera
        trajetoria_formatada.append({
            'x': float(x_atual),
            'y': float(y_atual)
        })

        # Velocidade resultante no instante atual
        v = np.hypot(vx, vy)

        # Se a velocidade for zero (módulo muito baixo), o arrasto é zero para evitar divisão por zero
        if v > 1e-5:
            # Fórmula da Força de Arrasto (Fm = 0.5 * Cd * rho * A * v²)
            forca_arrasto = 0.5 * c_d * rho_ar * area_frontal * (v ** 2)
            
            # Decompõe a força de arrasto nos eixos X e Y (ela sempre se opõe ao movimento)
            ax_arrasto = -(forca_arrasto / massa) * (vx / v)
            ay_arrasto = -(forca_arrasto / massa) * (vy / v)
        else:
            ax_arrasto = 0.0
            ay_arrasto = 0.0

        # Acelerações totais (Arrasto + Gravidade)
        ax_total = ax_arrasto
        ay_total = -g + ay_arrasto  # A gravidade puxa para baixo, o arrasto também (se estiver subindo)

        # Atualiza as velocidades usando o método de Euler
        vx += ax_total * dt
        vy += ay_total * dt

        # Atualiza as posições na tela
        x_atual += vx * dt
        y_atual += vy * dt
        t += dt

        # Trava de segurança para o servidor não travar se o objeto nunca cair
        if t > 100.0:
            break

    # Envia a lista completa de coordenadas geradas de volta para o JavaScript
    return jsonify(trajetoria_formatada)

if __name__ == '__main__':
    # O Render avisa o Python em qual porta rodar através dessa variável de ambiente
    porta = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=porta)
