# Simulador de rede de filas (etapa 2: filas em tandem)
# Simulacao e Metodos Analiticos - PUCRS
#
# Uso: python3 simulador.py
# Os parametros do modelo ficam no bloco abaixo.

# ---------------------------------------------------------------
# PARAMETROS DO MODELO (edite aqui)
# ---------------------------------------------------------------

# Cada fila tem: servidores, capacidade, atendimento (min, max) e,
# se recebe clientes de fora da rede, chegada (min, max).
FILAS = {
    "Fila1": {"servidores": 2, "capacidade": 3, "chegada": (1.0, 5.0), "atendimento": (4.0, 5.0)},
    "Fila2": {"servidores": 1, "capacidade": 5, "atendimento": (1.0, 3.0)},
}

# Roteamento: (origem, destino, probabilidade).
# A soma das probabilidades de saida de uma fila que nao chega a 1.0
# corresponde a clientes que saem do sistema. Fila sem linha aqui = 100% sai.
REDE = [
    ("Fila1", "Fila2", 1.0),
]

PRIMEIRA_CHEGADA = 2.5      # instante da primeira chegada (filas com chegada externa)
QTD_ALEATORIOS = 100000     # a simulacao para quando usar todos

# Gerador congruente linear
SEMENTE = 42
A, C, M = 1664525, 1013904223, 2**32

# ---------------------------------------------------------------
# GERADOR DE NUMEROS PSEUDOALEATORIOS
# ---------------------------------------------------------------

anterior = SEMENTE
contador = QTD_ALEATORIOS

def next_random():
    global anterior, contador
    anterior = (A * anterior + C) % M
    contador -= 1
    return anterior / M

def sorteia(intervalo):
    minimo, maximo = intervalo
    return minimo + (maximo - minimo) * next_random()

# ---------------------------------------------------------------
# ESTADO DA SIMULACAO
# ---------------------------------------------------------------

tempo_global = 0.0
status = {nome: 0 for nome in FILAS}                              # clientes em cada fila
perdas = {nome: 0 for nome in FILAS}                              # clientes perdidos por fila
tempos = {nome: [0.0] * (f["capacidade"] + 1) for nome, f in FILAS.items()}  # tempo acumulado por estado
escalonador = []                                                  # eventos: (tempo, tipo, origem, destino)

def agenda(tempo, tipo, origem=None, destino=None):
    escalonador.append((tempo, tipo, origem, destino))

def proximo_evento():
    ev = min(escalonador, key=lambda e: e[0])
    escalonador.remove(ev)
    return ev

def acumula_tempo(tempo):
    global tempo_global
    for nome in FILAS:
        tempos[nome][status[nome]] += tempo - tempo_global
    tempo_global = tempo

def sorteia_destino(fila):
    rotas = [(destino, p) for origem, destino, p in REDE if origem == fila]
    if not rotas:
        return None                       # sai do sistema
    if len(rotas) == 1 and rotas[0][1] >= 1.0:
        return rotas[0][0]                # unico destino, nao gasta aleatorio
    r = next_random()
    acumulado = 0.0
    for destino, p in rotas:
        acumulado += p
        if r < acumulado:
            return destino
    return None

def agenda_atendimento(tempo, fila):
    t = tempo + sorteia(FILAS[fila]["atendimento"])
    destino = sorteia_destino(fila)
    if destino is None:
        agenda(t, "SAIDA", origem=fila)
    else:
        agenda(t, "PASSAGEM", origem=fila, destino=destino)

# Cliente entra na fila (parte "chegada" do pseudocodigo)
def entra(tempo, fila):
    f = FILAS[fila]
    if status[fila] < f["capacidade"]:
        status[fila] += 1
        if status[fila] <= f["servidores"]:
            agenda_atendimento(tempo, fila)
    else:
        perdas[fila] += 1

# Cliente deixa a fila (parte "saida" do pseudocodigo)
def sai(tempo, fila):
    status[fila] -= 1
    if status[fila] >= FILAS[fila]["servidores"]:
        agenda_atendimento(tempo, fila)

# ---------------------------------------------------------------
# EVENTOS
# ---------------------------------------------------------------

def chegada(tempo, fila):
    acumula_tempo(tempo)
    entra(tempo, fila)
    agenda(tempo + sorteia(FILAS[fila]["chegada"]), "CHEGADA", destino=fila)

def passagem(tempo, origem, destino):
    acumula_tempo(tempo)
    sai(tempo, origem)
    entra(tempo, destino)

def saida(tempo, fila):
    acumula_tempo(tempo)
    sai(tempo, fila)

# ---------------------------------------------------------------
# LACO PRINCIPAL
# ---------------------------------------------------------------

def simula():
    for nome, f in FILAS.items():
        if "chegada" in f:
            agenda(PRIMEIRA_CHEGADA, "CHEGADA", destino=nome)

    while contador > 0:
        tempo, tipo, origem, destino = proximo_evento()
        if tipo == "CHEGADA":
            chegada(tempo, destino)
        elif tipo == "PASSAGEM":
            passagem(tempo, origem, destino)
        else:
            saida(tempo, origem)

def relatorio():
    for nome, f in FILAS.items():
        print("=" * 52)
        print(f"{nome} (G/G/{f['servidores']}/{f['capacidade']})")
        if "chegada" in f:
            print(f"Chegada:     {f['chegada'][0]} .. {f['chegada'][1]}")
        print(f"Atendimento: {f['atendimento'][0]} .. {f['atendimento'][1]}")
        print("-" * 52)
        print(f"{'Estado':>6} {'Tempo acumulado':>20} {'Probabilidade':>16}")
        for estado, t in enumerate(tempos[nome]):
            print(f"{estado:>6} {t:>20.4f} {100 * t / tempo_global:>15.2f}%")
        print(f"Perdas: {perdas[nome]}")
    print("=" * 52)
    print(f"Tempo global da simulacao: {tempo_global:.4f}")
    print(f"Aleatorios usados: {QTD_ALEATORIOS - contador}")

if __name__ == "__main__":
    simula()
    relatorio()
