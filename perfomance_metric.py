import time
import os
import cProfile
import pstats
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

NUM_PACKETS = 10_000
PACKET_SIZE = 148  
PPS = 50

def encrypt_decrypt_round(key, iv, data):
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    decryptor = cipher.decryptor()
    ct = encryptor.update(data) + encryptor.finalize()
    pt = decryptor.update(ct) + decryptor.finalize()
    return pt

def generate_hmac(key, data):
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(data)
    return h.finalize()

def verify_hmac(key, data, tag):
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(data)
    h.verify(tag)

aes_key = os.urandom(16)
hmac_key = os.urandom(32)
iv = os.urandom(16)
data = os.urandom(PACKET_SIZE)

start = time.perf_counter()
for _ in range(NUM_PACKETS):
    encrypt_decrypt_round(aes_key, iv, data)
end = time.perf_counter()
elapsed = end - start
throughput_mbps = (NUM_PACKETS * PACKET_SIZE * 8) / (elapsed * 1e6)

def ecdh_handshake():
    priv1 = ec.generate_private_key(ec.SECP256R1(), default_backend())
    priv2 = ec.generate_private_key(ec.SECP256R1(), default_backend())
    pub1 = priv1.public_key()
    pub2 = priv2.public_key()
    ss1 = priv1.exchange(ec.ECDH(), pub2)
    ss2 = priv2.exchange(ec.ECDH(), pub1)
    return ss1, ss2

start = time.perf_counter()
for _ in range(100):
    ecdh_handshake()
end = time.perf_counter()
key_exchange_time_ms = ((end - start) / 100) * 1e3

tamper_failures = 0
for _ in range(NUM_PACKETS):
    tag = generate_hmac(hmac_key, data)
    bad_tag = bytearray(tag)
    bad_tag[0] ^= 0xFF
    try:
        verify_hmac(hmac_key, data, bytes(bad_tag))
    except Exception:
        tamper_failures += 1
tamper_detection_rate = (tamper_failures / NUM_PACKETS) * 100

def handshake_and_profile():
    priv1 = ec.generate_private_key(ec.SECP256R1(), default_backend())
    priv2 = ec.generate_private_key(ec.SECP256R1(), default_backend())
    pub1 = priv1.public_key()
    priv1.exchange(ec.ECDH(), pub1)

profiler = cProfile.Profile()
profiler.enable()
for _ in range(200):
    handshake_and_profile()
profiler.disable()
stats = pstats.Stats(profiler)
aes_time = stats.total_tt  

print(f"Encryption Throughput: {throughput_mbps:.2f} Mbps")
print(f"Key Exchange Time: {key_exchange_time_ms:.1f} ms")
print(f"Tamper Detection Rate: {tamper_detection_rate:.2f} %")
print(f"Handshake Cryptographic Overhead (approx): {aes_time/200*1e3:.1f} ms per handshake")
