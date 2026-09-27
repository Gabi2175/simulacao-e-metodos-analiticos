# Simulador de rede de filas

Simulação e Métodos Analíticos - PUCRS - T1

Simulador por eventos discretos escrito em Python. Lê o modelo de um arquivo
`.yml` e simula uma rede de filas com topologia qualquer: cada fila tem seus
próprios servidores, capacidade e tempo de atendimento, e os clientes são
roteados entre as filas por probabilidade.

Não usa nenhuma biblioteca externa, só o Python 3.

## Como executar

```
python3 simulador.py model.yml
```

Se nenhum arquivo for informado, ele procura por `model.yml` na pasta atual.

O programa imprime, para cada fila, o tempo acumulado e a probabilidade de cada
estado (de 0 até a capacidade) e o número de clientes perdidos. No final, mostra
o tempo global da simulação.

## O arquivo de modelo

O formato é o mesmo usado pelo simulador do módulo 3. A linha `!PARAMETERS`
marca onde começam os dados e tudo que vem depois de `#` é comentário.

```yaml
!PARAMETERS
arrivals:
   Q1: 2.0

queues:
   Q1:
      servers: 1
      minArrival: 2.0
      maxArrival: 4.0
      minService: 1.0
      maxService: 2.0
   Q2:
      servers: 2
      capacity: 5
      minService: 4.0
      maxService: 6.0

network:
-  source: Q1
   target: Q2
   probability: 0.2

rndnumbersPerSeed: 100000
seeds:
- 42
```

`arrivals` diz em que instante chega o primeiro cliente vindo de fora, para cada
fila que recebe chegadas externas. Filas que só recebem clientes de outras filas
não aparecem aqui e não precisam de `minArrival`/`maxArrival`.

Em `queues`, `servers` é o número de servidores e `capacity` a capacidade da
fila. Se `capacity` for omitido, a fila tem capacidade infinita.
`minService`/`maxService` são o intervalo do tempo de atendimento.

`network` é a lista de rotas. Cada rota tem origem, destino e probabilidade. O
que faltar para somar 1.0 nas rotas de uma fila são os clientes que vão embora
da rede. No exemplo acima, 80% dos clientes atendidos na Q1 saem do sistema. Uma
fila sem nenhuma rota manda 100% dos clientes para fora. Uma rota pode apontar
para a própria fila de origem.

Para os números pseudoaleatórios existem duas opções:

- `rndnumbersPerSeed` junto com `seeds`: o gerador congruente linear produz essa
  quantidade de números a partir de cada semente da lista, e a simulação roda uma
  vez para cada semente.
- `rndnumbers`: uma lista de números entre 0 e 1 já prontos, usados na ordem em
  que aparecem. É ignorada se `seeds` estiver no arquivo.

A simulação termina quando o último número aleatório é usado.

## Como funciona

São três tipos de evento, como no pseudocódigo da disciplina:

- `CHEGADA`: cliente entra na rede por uma fila.
- `PASSAGEM`: cliente termina o atendimento em uma fila e entra em outra.
- `SAIDA`: cliente termina o atendimento e vai embora da rede.

Ao terminar um atendimento, sorteia-se um número entre 0 e 1 e vê-se em qual
faixa de probabilidade ele cai para decidir o destino do cliente. Quando a fila
tem um único destino possível nenhum número é gasto nesse sorteio. O tempo de um
intervalo `(min, max)` sai de `min + (max - min) * aleatório`.
