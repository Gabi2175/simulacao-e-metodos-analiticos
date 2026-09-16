# Simulador de rede de filas (filas em tandem)

Simulação e Métodos Analíticos - PUCRS - Etapa 2

Simulador por eventos discretos escrito em Python, sem dependências externas.
Nesta etapa ele modela duas filas em tandem, mas a estrutura já aceita uma rede
de filas com topologia genérica (roteamento por probabilidade).

## Como executar

Requer apenas Python 3.

```
python3 simulador.py
```

O resultado é impresso no terminal: para cada fila, o tempo acumulado e a
probabilidade de cada estado (0 até a capacidade) e o número de perdas; ao
final, o tempo global da simulação.

## Como configurar o modelo

Os parâmetros ficam no início de `simulador.py`.

```python
FILAS = {
    "Fila1": {"servidores": 2, "capacidade": 3, "chegada": (1.0, 5.0), "atendimento": (4.0, 5.0)},
    "Fila2": {"servidores": 1, "capacidade": 5, "atendimento": (1.0, 3.0)},
}
```

- `servidores`: número de servidores da fila.
- `capacidade`: número máximo de clientes na fila (contando os em atendimento).
- `atendimento`: intervalo (mínimo, máximo) do tempo de atendimento.
- `chegada`: intervalo (mínimo, máximo) entre chegadas vindas de fora da rede.
  Filas que só recebem clientes de outras filas não têm essa chave.

O roteamento entre filas é uma lista de tuplas `(origem, destino, probabilidade)`:

```python
REDE = [
    ("Fila1", "Fila2", 1.0),
]
```

Se a soma das probabilidades de saída de uma fila for menor que 1.0, o restante
corresponde a clientes que deixam o sistema. Uma fila sem nenhuma linha em `REDE`
envia 100% dos clientes para fora. Exemplo de rede com três filas:

```python
REDE = [
    ("Fila1", "Fila2", 0.7),   # 70% vai para a Fila2
    ("Fila1", "Fila3", 0.3),   # 30% vai para a Fila3
    ("Fila2", "Fila3", 0.5),   # 50% vai para a Fila3, 50% sai do sistema
    ("Fila3", "Fila1", 0.2),   # 20% volta para a Fila1, 80% sai do sistema
]
```

Outros parâmetros:

- `PRIMEIRA_CHEGADA`: instante da primeira chegada (2.5 no caso de teste).
- `QTD_ALEATORIOS`: quantidade de números pseudoaleatórios; a simulação
  encerra quando todos forem usados (100000 no caso de teste).
- `SEMENTE`, `A`, `C`, `M`: parâmetros do gerador congruente linear.

## Funcionamento

Os eventos são de três tipos, seguindo o pseudocódigo da disciplina:

- `CHEGADA`: cliente chega de fora da rede em uma fila.
- `PASSAGEM`: cliente termina o atendimento em uma fila e entra em outra.
- `SAIDA`: cliente termina o atendimento e deixa o sistema.

Ao terminar um atendimento, o destino é sorteado conforme `REDE`. Quando há um
único destino com probabilidade 1.0 nenhum número aleatório é gasto no sorteio.
O tempo de um intervalo `(min, max)` é obtido por `min + (max - min) * aleatório`.
