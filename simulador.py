# Simulador de rede de filas
# Simulacao e Metodos Analiticos - PUCRS
# Estudantes: Christian Kossmann, Anderson Sprenger & Gabriel Dalbem
# 
# Uso: python3 simulador.py [modelo.yml]

import sys

INFINITO = float("inf")

A, C, M = 1664525, 1013904223, 2 ** 32


# ---------------------------------------------------------------
# LEITURA DO MODELO
# ---------------------------------------------------------------

def numero(texto):
    return float(texto) if "." in texto or "e" in texto else int(texto)


def le_modelo(caminho):
    modelo = {"arrivals": {}, "queues": {}, "network": {}, "rndnumbers": [],
              "seeds": [], "rndnumbersPerSeed": 0}
    secao = None
    fila = None
    rota = None

    for bruta in open(caminho, encoding="utf-8"):
        linha = bruta.split("#")[0].rstrip()
        if not linha.strip() or linha.strip().startswith("!"):
            continue
        recuo = len(linha) - len(linha.lstrip())
        texto = linha.strip()

        # chave de primeiro nivel: arrivals, queues, network, ...
        if recuo == 0 and not texto.startswith("-"):
            secao = texto.split(":")[0].strip()
            valor = texto.partition(":")[2].strip()
            if valor:
                modelo[secao] = numero(valor)
            fila = None
            continue

        # item de lista
        if texto.startswith("-"):
            texto = texto[1:].strip()
            if secao == "rndnumbers":
                modelo["rndnumbers"].append(float(texto))
                continue
            if secao == "seeds":
                modelo["seeds"].append(int(texto))
                continue
            rota = {}

        chave, _, valor = texto.partition(":")
        chave, valor = chave.strip(), valor.strip()

        if secao == "arrivals":
            modelo["arrivals"][chave] = float(valor)
        elif secao == "queues":
            if valor == "":
                fila = {"servers": 1, "capacity": INFINITO}
                modelo["queues"][chave] = fila
            else:
                fila[chave] = numero(valor)
        elif secao == "network":
            rota[chave] = float(valor) if chave == "probability" else valor
            if len(rota) == 3:
                modelo["network"].setdefault(rota["source"], []).append(
                    (rota["target"], rota["probability"]))

    return modelo


# ---------------------------------------------------------------
# NUMEROS PSEUDOALEATORIOS
# ---------------------------------------------------------------

class Gerador:
    # congruente linear; se receber uma lista pronta, usa ela no lugar
    def __init__(self, semente=0, quantidade=0, numeros=None):
        self.numeros = numeros
        self.posicao = 0
        self.anterior = semente
        self.restantes = len(numeros) if numeros else quantidade

    def proximo(self):
        self.restantes -= 1
        if self.numeros is not None:
            valor = self.numeros[self.posicao]
            self.posicao += 1
            return valor
        self.anterior = (A * self.anterior + C) % M
        return self.anterior / M


# ---------------------------------------------------------------
# SIMULACAO
# ---------------------------------------------------------------

# filas com capacidade finita ja comecam com todos os estados no relatorio
def estados(fila):
    return 1 if fila["capacity"] == INFINITO else int(fila["capacity"]) + 1


class Simulacao:
    def __init__(self, modelo, gerador):
        self.filas = modelo["queues"]
        self.rede = modelo["network"]
        self.chegadas = modelo["arrivals"]
        self.rnd = gerador

        self.tempo = 0.0
        self.status = {nome: 0 for nome in self.filas}
        self.perdas = {nome: 0 for nome in self.filas}
        self.tempos = {nome: [0.0] * estados(f) for nome, f in self.filas.items()}
        self.escalonador = []

    # --- apoio ---

    def sorteia(self, minimo, maximo):
        return minimo + (maximo - minimo) * self.rnd.proximo()

    def agenda(self, tempo, tipo, origem=None, destino=None):
        self.escalonador.append((tempo, tipo, origem, destino))

    def proximo_evento(self):
        evento = min(self.escalonador, key=lambda e: e[0])
        self.escalonador.remove(evento)
        return evento

    def acumula_tempo(self, tempo):
        decorrido = tempo - self.tempo
        for nome in self.filas:
            estado = self.status[nome]
            acumulado = self.tempos[nome]
            while len(acumulado) <= estado:
                acumulado.append(0.0)
            acumulado[estado] += decorrido
        self.tempo = tempo

    # para qual fila o cliente vai depois de ser atendido (None = sai da rede)
    def sorteia_destino(self, fila):
        rotas = self.rede.get(fila, [])
        if not rotas:
            return None
        if len(rotas) == 1 and rotas[0][1] >= 1.0:
            return rotas[0][0]
        if self.rnd.restantes == 0:
            return None
        sorteado = self.rnd.proximo()
        acumulado = 0.0
        for destino, probabilidade in rotas:
            acumulado += probabilidade
            if sorteado < acumulado:
                return destino
        return None

    def agenda_atendimento(self, tempo, fila):
        if self.rnd.restantes == 0:
            return
        f = self.filas[fila]
        instante = tempo + self.sorteia(f["minService"], f["maxService"])
        destino = self.sorteia_destino(fila)
        if destino is None:
            self.agenda(instante, "SAIDA", origem=fila)
        else:
            self.agenda(instante, "PASSAGEM", origem=fila, destino=destino)

    # cliente entra na fila
    def entra(self, tempo, fila):
        f = self.filas[fila]
        if self.status[fila] < f["capacity"]:
            self.status[fila] += 1
            if self.status[fila] <= f["servers"]:
                self.agenda_atendimento(tempo, fila)
        else:
            self.perdas[fila] += 1

    # cliente termina o atendimento e deixa a fila
    def sai(self, tempo, fila):
        self.status[fila] -= 1
        if self.status[fila] >= self.filas[fila]["servers"]:
            self.agenda_atendimento(tempo, fila)

    # --- eventos ---

    def chegada(self, tempo, fila):
        self.acumula_tempo(tempo)
        self.entra(tempo, fila)
        if self.rnd.restantes > 0:
            f = self.filas[fila]
            self.agenda(tempo + self.sorteia(f["minArrival"], f["maxArrival"]),
                        "CHEGADA", destino=fila)

    def passagem(self, tempo, origem, destino):
        self.acumula_tempo(tempo)
        self.sai(tempo, origem)
        self.entra(tempo, destino)

    def saida(self, tempo, fila):
        self.acumula_tempo(tempo)
        self.sai(tempo, fila)

    # --- laco principal ---

    def executa(self):
        for nome, instante in self.chegadas.items():
            self.agenda(instante, "CHEGADA", destino=nome)

        while self.rnd.restantes > 0 and self.escalonador:
            tempo, tipo, origem, destino = self.proximo_evento()
            if tipo == "CHEGADA":
                self.chegada(tempo, destino)
            elif tipo == "PASSAGEM":
                self.passagem(tempo, origem, destino)
            else:
                self.saida(tempo, origem)


# ---------------------------------------------------------------
# RELATORIO
# ---------------------------------------------------------------

def descreve(nome, fila):
    capacidade = fila["capacity"]
    texto = "G/G/%d" % fila["servers"]
    if capacidade != INFINITO:
        texto += "/%d" % capacidade
    if "minArrival" in fila:
        texto += ", chegadas entre %g..%g" % (fila["minArrival"], fila["maxArrival"])
    return "%s (%s, atendimento entre %g..%g)" % (
        nome, texto, fila["minService"], fila["maxService"])


def relatorio(sim):
    total = sim.tempo
    for nome, fila in sim.filas.items():
        print("=" * 56)
        print(descreve(nome, fila))
        print("-" * 56)
        print("%6s %20s %16s" % ("Estado", "Tempo acumulado", "Probabilidade"))
        for estado, acumulado in enumerate(sim.tempos[nome]):
            print("%6d %20.4f %15.2f%%" % (estado, acumulado, 100 * acumulado / total))
        print("Perdas: %d" % sim.perdas[nome])
    print("=" * 56)
    print("Tempo global da simulacao: %.4f" % total)


# ---------------------------------------------------------------

def main():
    caminho = sys.argv[1] if len(sys.argv) > 1 else "model.yml"
    modelo = le_modelo(caminho)

    if modelo["seeds"]:
        execucoes = [Gerador(semente=s, quantidade=modelo["rndnumbersPerSeed"])
                     for s in modelo["seeds"]]
    else:
        execucoes = [Gerador(numeros=modelo["rndnumbers"])]

    for indice, gerador in enumerate(execucoes):
        if len(execucoes) > 1:
            print("\n##### Execucao %d (semente %d)" % (indice + 1, modelo["seeds"][indice]))
        sim = Simulacao(modelo, gerador)
        sim.executa()
        relatorio(sim)


if __name__ == "__main__":
    main()
