import simpy
import numpy as np
import hashlib
import time
from scipy.stats import lognorm, rayleigh

GRID_SIZE = 2000  
CELL_SIZE = 100   
NUM_CELLS = GRID_SIZE // CELL_SIZE
SIM_DURATION = 3600 * 1_000_000 
KEY_ROTATION_INTERVAL = 15 * 60 * 1_000_000  
KEY_ROTATION_JITTER = 1 * 60 * 1_000_000 
AES_CTR_DELAY_US = 150  
HMAC_SHA256_DELAY_US = 200 

class BattlefieldSim:
    def __init__(self, env, num_nodes):
        self.env = env
        self.nodes = [Node(env, i, self) for i in range(num_nodes)]
        self.global_clock = GlobalClock(env)
        self.jammer = Jammer(env)
        self.logger = Logger()

class GlobalClock:
    def __init__(self, env):
        self.env = env
        self.utc_time = 0
        self.process = env.process(self.sync_clock())

    def sync_clock(self):
        while True:
            yield self.env.timeout(KEY_ROTATION_INTERVAL + np.random.randint(-KEY_ROTATION_JITTER, KEY_ROTATION_JITTER))
            self.utc_time = self.env.now
            print(f"[{self.env.now}] Clock synchronized.")

class Node:
    def __init__(self, env, node_id, sim):
        self.env = env
        self.id = node_id
        self.sim = sim
        self.location = np.random.randint(0, GRID_SIZE, size=2)
        self.process = env.process(self.run())

    def run(self):
        while True:
            delay = np.random.randint(500_000, 1_000_000)  
            yield self.env.timeout(delay)

            start = self.env.now
            data = b"Hello"
            encrypted = self.encrypt(data)
            hmac = self.compute_hmac(encrypted)
            propagation_delay = self.propagate()
            yield self.env.timeout(propagation_delay)

            success = self.sim.jammer.affects(self.location)
            latency = self.env.now - start
            self.sim.logger.log_packet(latency, success)

    def encrypt(self, data):
        yield self.env.timeout(AES_CTR_DELAY_US)
        return data  #

    def compute_hmac(self, data):
        yield self.env.timeout(HMAC_SHA256_DELAY_US)
        return hashlib.sha256(data).digest()

    def propagate(self):
        distance = np.linalg.norm(self.location - np.random.randint(0, GRID_SIZE, size=2))
        shadowing = lognorm(s=0.2).rvs()  
        fading = rayleigh(scale=1).rvs() 
        base_delay = distance / 300_000_000 * 1e6  
        return int(base_delay * shadowing * fading)

class Jammer:
    def __init__(self, env):
        self.env = env
        self.active = True
        self.spectral_density = -90  
        self.jamming_zone = [1000, 1000] 
        self.radius = 500  

    def affects(self, location):
        dist = np.linalg.norm(np.array(location) - self.jamming_zone)
        return dist < self.radius

class Logger:
    def __init__(self):
        self.packets = []

    def log_packet(self, latency, success):
        self.packets.append({
            'latency_us': latency,
            'success': success
        })

def run_simulation():
    env = simpy.Environment()
    sim = BattlefieldSim(env, num_nodes=10)
    env.run(until=SIM_DURATION)
    return sim.logger

if __name__ == "__main__":
    logger = run_simulation()
    latencies = [p['latency_us'] for p in logger.packets if p['success']]
    print(f"Delivered packets: {len(latencies)}")
    print(f"Average latency: {np.mean(latencies):.2f} µs")
