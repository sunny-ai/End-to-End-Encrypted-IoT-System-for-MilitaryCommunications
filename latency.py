import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ace_tools as tools

# Parameters
num_nodes = 50
area_size = 2000  # meters
esp_range = 300   # meters
lora_range = 8000 # meters (for backhaul hops)

positions = {i: (np.random.uniform(0, area_size), np.random.uniform(0, area_size)) for i in range(num_nodes)}

G_esp = nx.Graph()
G_lora = nx.Graph()

G_esp.add_nodes_from(positions)
G_lora.add_nodes_from(positions)

for i in positions:
    for j in positions:
        if i < j:
            dist = np.hypot(positions[i][0] - positions[j][0], positions[i][1] - positions[j][1])
            if dist <= esp_range:
                latency = 20 + 0.05 * dist + np.random.normal(0, 2)
                G_esp.add_edge(i, j, weight=latency)
            if dist <= lora_range:
                latency = 200 + 0.01 * dist + np.random.normal(0, 5)
                G_lora.add_edge(i, j, weight=latency)

samples = 100
results = []
for _ in range(samples):
    a, b = np.random.choice(num_nodes, size=2, replace=False)
    straight_dist = np.hypot(positions[a][0] - positions[b][0], positions[a][1] - positions[b][1])
    if straight_dist <= esp_range and nx.has_path(G_esp, a, b):
        latency = nx.shortest_path_length(G_esp, a, b, weight='weight')
        proto = 'ESP-NOW'
    elif nx.has_path(G_lora, a, b):
        latency = nx.shortest_path_length(G_lora, a, b, weight='weight')
        proto = 'LoRa'
    else:
        latency = np.nan
        proto = 'No Path'
    results.append((a, b, straight_dist, proto, latency))

df = pd.DataFrame(results, columns=['Src', 'Dst', 'Distance_m', 'Protocol', 'Latency_ms']).dropna()

tools.display_dataframe_to_user(name="Network Simulation Sample Results", dataframe=df.head(20))

plt.figure(figsize=(6,4))
for proto, group in df.groupby('Protocol'):
    plt.scatter(group['Distance_m'], group['Latency_ms'], label=proto, alpha=0.7)
plt.xlabel('Distance (m)')
plt.ylabel('Latency (ms)')
plt.title('Simulated Network Latency vs Distance')
plt.legend()
plt.tight_layout()
plt.show()
